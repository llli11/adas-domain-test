<template>
  <n-card size="small">
    <n-space :size="8" style="margin-bottom: 12px;">
      <n-input v-model:value="yearMonth" placeholder="YYYY-MM" size="small" style="width: 120px;" />
      <n-select
        v-model:value="testOrderId"
        :options="testOrderOpts"
        size="small"
        style="width: 300px;"
        placeholder="选择试验需求编号"
        clearable
        filterable
      />
      <n-button size="small" type="primary" @click="doQuery">筛选</n-button>
      <n-button size="small" type="success" @click="exportExcel">生成月度结算单</n-button>
    </n-space>

    <n-data-table
      :columns="driverColumns"
      :data="pagedData"
      :loading="loading"
      size="small"
      :single-line="false"
      :max-height="600"
      :scroll-x="scrollX"
      :pagination="pagination"
    />
  </n-card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { NCard, NSpace, NInput, NSelect, NButton, NDataTable } from 'naive-ui'
import expenseApi from '@/api/expense'

const yearMonth = ref('')
const testOrderId = ref(null)
const loading = ref(false)
const testOrderOpts = ref([])
const daysInMonth = ref(31)
const driverTableData = ref([])
const personSummary = ref({})
const page = ref(1)
const pageSize = ref(50)

const pagination = computed(() => ({
  page: page.value,
  pageSize: pageSize.value,
  itemCount: driverTableData.value.length,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  onChange: (p) => { page.value = p },
  onUpdatePageSize: (ps) => { pageSize.value = ps; page.value = 1 },
}))

const pagedData = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return driverTableData.value.slice(start, start + pageSize.value)
})

const DATE_CELL_W = 44
const FIXED_W = 50 + 160 + 110 + 200 + 80 + 60
const SUM_COLS_W = 120 + 120 + 120 + 100
const scrollX = computed(() => FIXED_W + SUM_COLS_W + daysInMonth.value * DATE_CELL_W)

const driverColumns = computed(() => {
  const cols = [
    { title: '序号\nNO.', key: '_index', width: 50, align: 'center', fixed: 'left' },
    { title: '合同号', key: 'contract_no', width: 160, fixed: 'left' },
    { title: '服务人员姓名', key: 'person_name', width: 110, fixed: 'left' },
    { title: '服务类别', key: 'service_category', width: 200, ellipsis: { tooltip: true } },
    { title: '服务等级', key: 'service_level', width: 80 },
    { title: '属性', key: 'attribute', width: 60 },
  ]
  for (let d = 1; d <= daysInMonth.value; d++) {
    cols.push({
      title: d,
      key: 'day_' + d,
      width: DATE_CELL_W,
      align: 'center',
      render: (row) => {
        const hours = row.days?.[String(d)]
        return hours ? hours : ''
      },
    })
  }
  cols.push({
    title: '合计正常服务天数',
    key: '_normal_days',
    width: 120,
    align: 'center',
    render: (row) => {
      if (row.attribute !== '正常') return ''
      const sum = Object.values(row.days || {}).reduce((s, v) => s + Number(v || 0), 0)
      return sum > 0 ? sum.toFixed(3) : ''
    },
  })
  cols.push({
    title: '合计额外服务天数',
    key: '_overtime_days',
    width: 120,
    align: 'center',
    render: (row) => {
      if (row.attribute !== '加班') return ''
      const sum = Object.values(row.days || {}).reduce((s, v) => s + Number(v || 0), 0)
      return sum > 0 ? sum.toFixed(3) : ''
    },
  })
  cols.push({
    title: '合计总服务天数',
    key: '_total_days',
    width: 120,
    align: 'center',
    render: (row) => {
      // 正常行 = 正常天数，加班行 = 加班天数
      const sum = Object.values(row.days || {}).reduce((s, v) => s + Number(v || 0), 0)
      return sum > 0 ? sum.toFixed(3) : ''
    },
  })
  cols.push({ title: '备注', key: 'remark', width: 100 })
  return cols
})

function buildDriverRows(data) {
  daysInMonth.value = data.days_in_month || 31
  personSummary.value = data.person_summary || {}
  return (data.records || []).map((r, i) => {
    const row = { ...r, _index: i + 1 }
    for (let d = 1; d <= daysInMonth.value; d++) {
      row['day_' + d] = r.days?.[String(d)] || 0
    }
    return row
  })
}

async function loadTestOrders() {
  try {
    const r = await expenseApi.getTestOrderList({})
    // 只显示含驾驶员的试验单（list_test_orders 已返回 person_types）
    testOrderOpts.value = (r.data || [])
      .filter(item => (item.person_types || []).includes("驾驶员"))
      .map(item => ({ label: item.test_order_no, value: item.id }))
  } catch (e) { console.error(e) }
}

async function doQuery() {
  if (!yearMonth.value) { window.$message?.warning('请输入月份(YYYY-MM)'); return }
  loading.value = true
  page.value = 1
  try {
    const params = { year_month: yearMonth.value }
    if (testOrderId.value) params.test_order_id = testOrderId.value
    const r = await expenseApi.getDriverMonthlySettlement(params)
    driverTableData.value = buildDriverRows(r.data || {})
  } catch (e) { console.error(e) } finally { loading.value = false }
}

async function exportExcel() {
  if (!yearMonth.value) { window.$message?.warning('请输入月份(YYYY-MM)'); return }
  try {
    const params = { year_month: yearMonth.value }
    if (testOrderId.value) params.test_order_id = testOrderId.value
    const res = await expenseApi.exportDriverSettlement(params)
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `驾驶员月度结算-${yearMonth.value}.xlsx`
    a.click()
    window.URL.revokeObjectURL(url)
    window.$message?.success('导出成功')
  } catch (e) { console.error(e); window.$message?.error('导出失败') }
}

onMounted(async () => {
  await loadTestOrders()
  const now = new Date()
  yearMonth.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  doQuery()
})
</script>
