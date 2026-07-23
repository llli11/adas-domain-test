<template>
  <n-card size="small">
    <n-space :size="8" style="margin-bottom: 12px;">
      <n-input v-model:value="yearMonth" placeholder="YYYY-MM" size="small" style="width: 120px;" />
      <n-button size="small" type="primary" @click="doQuery">查询</n-button>
      <n-button size="small" type="success" @click="exportExcel">生成月度结算单</n-button>
    </n-space>
    <n-data-table :columns="engineerColumns" :data="tableData" :loading="loading" size="small"
      :single-line="false" :max-height="600" :scroll-x="scrollX" :pagination="pagination" />
  </n-card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { NCard, NSpace, NInput, NButton, NDataTable } from 'naive-ui'
import expenseApi from '@/api/expense'

const yearMonth = ref('')
const loading = ref(false)
const tableData = ref([])
const daysInMonth = ref(31)
const page = ref(1)
const pageSize = ref(50)

const pagination = computed(() => ({
  page: page.value, pageSize: pageSize.value,
  itemCount: tableData.value.length, showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  onChange: (p) => { page.value = p },
  onUpdatePageSize: (ps) => { pageSize.value = ps; page.value = 1 },
}))

const DATE_W = 38
const scrollX = computed(() => 50 + 80 + 100 + 200 + daysInMonth.value * DATE_W + 100 + 130 + 100)

const engineerColumns = computed(() => {
  const cols = [
    { title: '序号\nNo.', key: '_index', width: 50, align: 'center', fixed: 'left' },
    { title: '姓名', key: 'person_name', width: 80, fixed: 'left' },
    { title: '专业', key: 'major', width: 100 },
    { title: '属性', key: 'property', width: 200, ellipsis: { tooltip: true } },
  ]
  for (let d = 1; d <= daysInMonth.value; d++) {
    cols.push({ title: d, key: 'day_' + d, width: DATE_W, align: 'center',
      render: (row) => row.days?.[String(d)] || '' })
  }
  cols.push({ title: '合计总工时', key: 'total_hours', width: 100, align: 'center',
    render: (row) => (row.total_hours || 0).toFixed(1) })
  cols.push({ title: '备注', key: 'test_order_no', width: 130, ellipsis: { tooltip: true } })
  return cols
})

function buildRows(data) {
  daysInMonth.value = data.days_in_month || 31
  return (data.records || []).map((r, i) => ({
    ...r, _index: i + 1,
    major: '智能驾驶专项',
    property: `${r.project_name || r.series || ''}\n${r.responsible || r.person_name || ''}`,
  }))
}

async function doQuery() {
  if (!yearMonth.value) { window.$message?.warning('请输入月份'); return }
  loading.value = true; page.value = 1
  try {
    const r = await expenseApi.getEngineerAttendanceQuery({ year_month: yearMonth.value })
    tableData.value = buildRows(r.data || {})
  } catch (e) { console.error(e) } finally { loading.value = false }
}

async function exportExcel() {
  if (!yearMonth.value) { window.$message?.warning('请输入月份'); return }
  try {
    const res = await expenseApi.exportEngineerSettlement({ year_month: yearMonth.value })
    const blob = res instanceof Blob ? res : new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `工程师月度结算-${yearMonth.value}.xlsx`
    a.click()
    window.URL.revokeObjectURL(url)
    window.$message?.success('导出成功')
  } catch (e) { console.error(e); window.$message?.error('导出失败') }
}

onMounted(() => {
  const now = new Date()
  yearMonth.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  doQuery()
})
</script>
