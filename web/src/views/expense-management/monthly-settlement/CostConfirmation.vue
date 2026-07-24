<template>
  <n-card size="small">
    <n-space :size="8" style="margin-bottom: 12px;">
      <n-input v-model:value="yearMonth" placeholder="YYYY-MM" size="small" style="width: 120px;" />
      <n-input v-model:value="responsiblePerson" placeholder="筛选责任人" size="small" style="width: 140px;" clearable @keyup.enter="doQuery" @clear="doQuery" />
      <n-button size="small" type="primary" @click="doQuery">查询</n-button>
    </n-space>

    <n-data-table :columns="columns" :data="tableData" :loading="loading" size="small" :max-height="600" />
  </n-card>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NCard, NSpace, NInput, NButton, NDataTable, NTag } from 'naive-ui'
import expenseApi from '@/api/expense'

const loading = ref(false)
const yearMonth = ref('')
const responsiblePerson = ref('')
const tableData = ref([])

function fmt(v) { return v != null ? Number(v).toFixed(2) : '0.00' }

function statusTag(status) {
  const type = status === '已确认' ? 'success' : status === '更正' ? 'error' : 'warning'
  return h(NTag, { type, size: 'small' }, () => status)
}

const columns = [
  { title: '试验单号', key: 'test_order_no', width: 200, ellipsis: { tooltip: true } },
  { title: '责任人', key: 'responsible_person', width: 90 },
  { title: '工程师工时', key: 'engineer_hours', width: 90, align: 'center' },
  { title: '驾驶员工时', key: 'driver_hours', width: 90, align: 'center' },
  { title: '垫付', key: 'advance_total', width: 90, align: 'right', render: r => fmt(r.advance_total) },
  { title: '工程师单价', key: 'engineer_price', width: 90, align: 'right', render: r => r.engineer_price ? `${fmt(r.engineer_price)}元/时` : '-' },
  { title: '驾驶员单价', key: 'driver_price', width: 90, align: 'right', render: r => r.driver_price ? `${fmt(r.driver_price)}元/天` : '-' },
  { title: '合计金额', key: 'total_amount', width: 100, align: 'right', render: r => fmt(r.total_amount) },
  { title: '状态', key: 'confirm_status', width: 80, align: 'center', render: r => statusTag(r.confirm_status) },
  { title: '操作', key: 'action', width: 160, render(row) {
    const btns = []
    if (row.confirm_status !== '已确认') {
      btns.push(h('button', {
        style: 'color:#18a058;border:1px solid #18a058;background:#fff;padding:2px 8px;border-radius:3px;cursor:pointer;font-size:12px',
        onClick: () => doUpdate(row, '已确认')
      }, '确认'))
    }
    if (row.confirm_status !== '更正') {
      btns.push(h('button', {
        style: 'color:#d03050;border:1px solid #d03050;background:#fff;padding:2px 8px;border-radius:3px;cursor:pointer;font-size:12px',
        onClick: () => doUpdate(row, '更正')
      }, '更正'))
    }
    return h('div', { style: 'display:flex;flex-wrap:wrap;gap:6px' }, btns)
  }},
]

async function doQuery() {
  if (!yearMonth.value) { window.$message?.warning('请输入月份(YYYY-MM)'); return }
  loading.value = true
  try {
    const params = { year_month: yearMonth.value }
    if (responsiblePerson.value) params.responsible_person = responsiblePerson.value
    const r = await expenseApi.getCostConfirmation(params)
    tableData.value = r.data || []
  } catch (e) { console.error(e) } finally { loading.value = false }
}

async function doUpdate(row, status) {
  try {
    await expenseApi.updateCostConfirmation({
      test_order_id: row.test_order_id,
      year_month: row.year_month,
      status,
    })
    window.$message?.success(`状态已更新为${status}`)
    await doQuery()
  } catch (e) { console.error(e); window.$message?.error('操作失败') }
}

onMounted(() => {
  const now = new Date()
  now.setMonth(now.getMonth() - 1)
  yearMonth.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  doQuery()
})
</script>
