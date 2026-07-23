<template>
  <n-card size="small">
    <!-- 筛选区 -->
    <n-space :size="8" style="margin-bottom: 12px;">
      <n-select v-model:value="personType" :options="personTypeOpts" size="small" style="width: 100px;" placeholder="人员类型" />
      <n-input v-model:value="yearMonth" placeholder="YYYY-MM" size="small" style="width: 120px;" />
      <n-select
        v-model:value="testOrderId"
        :options="testOrderOpts"
        size="small"
        style="width: 180px;"
        placeholder="选择试验需求编号"
        clearable
        filterable
      />
      <n-button size="small" type="primary" @click="querySettlement">查询</n-button>
      <n-button v-if="personType === '工程师'" size="small" @click="generateEngineerSettlement">生成月度结算</n-button>
      <n-button size="small" @click="querySettlement">刷新列表</n-button>
    </n-space>

    <!-- 驾驶员结算：按日展示 -->
    <n-data-table
      v-if="personType === '驾驶员'"
      :columns="driverColumns"
      :data="driverTableData"
      :loading="loading"
      size="small"
      :single-line="false"
      :max-height="500"
    />

    <!-- 工程师结算：汇总展示 -->
    <n-data-table
      v-else
      :columns="engineerColumns"
      :data="engineerTableData"
      :loading="loading"
      :pagination="pagination"
      size="small"
    />
  </n-card>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { NCard, NSpace, NSelect, NInput, NButton, NDataTable } from 'naive-ui'
import expenseApi from '@/api/expense'

const yearMonth = ref('')
const personType = ref('驾驶员')
const testOrderId = ref(null)
const loading = ref(false)

const personTypeOpts = [
  { label: '驾驶员', value: '驾驶员' },
  { label: '工程师', value: '工程师' },
]
const testOrderOpts = ref([])

// ---- 工程师结算 ----
const engineerTableData = ref([])
const engineerColumns = [
  { title: '结算月份', key: 'year_month', width: 110 },
  { title: '试验需求编号', key: 'test_order_no', width: 130 },
  { title: '人工费用', key: 'labor_cost', width: 100 },
  { title: '垫付费用', key: 'advance_payment', width: 100 },
  { title: '总金额', key: 'total_amount', width: 100 },
  { title: '备注', key: 'remark', width: 150, ellipsis: { tooltip: true } },
]
const pagination = { pageSize: 10 }

// ---- 驾驶员结算 ----
const daysInMonth = ref(31)
const driverTableData = ref([])
const driverColumns = computed(() => {
  const cols = [
    { title: '服务人员姓名', key: 'person_name', width: 110, fixed: 'left' },
    { title: '供应商', key: 'supplier', width: 80 },
    { title: '属性', key: 'attribute', width: 60 },
    { title: '服务类别', key: 'service_code', width: 130 },
  ]
  for (let d = 1; d <= daysInMonth.value; d++) {
    cols.push({
      title: d + '日',
      key: 'day_' + d,
      width: 55,
      align: 'center',
      render: (row) => {
        const hours = row.days?.[String(d)]
        return hours ? hours.toFixed(1) + 'h' : ''
      },
    })
  }
  cols.push({ title: '合计天数', key: 'total_days', width: 80, align: 'center' })
  return cols
})

// 将后端数据转为表格行
function buildDriverRows(data) {
  daysInMonth.value = data.days_in_month || 31
  const rows = data.records || []
  return rows.map((r) => {
    const row = { ...r }
    for (let d = 1; d <= daysInMonth.value; d++) {
      row['day_' + d] = r.days?.[String(d)] || 0
    }
    return row
  })
}

// 加载试验单列表
async function loadTestOrders() {
  try {
    const r = await expenseApi.getTestOrderList({})
    testOrderOpts.value = (r.data || []).map(item => ({
      label: item.test_order_no,
      value: item.id,
    }))
  } catch (e) {
    console.error(e)
  }
}

// 查询
async function querySettlement() {
  if (!yearMonth.value) { window.$message?.warning('请输入月份(YYYY-MM)'); return }

  loading.value = true
  try {
    if (personType.value === '驾驶员') {
      const params = { year_month: yearMonth.value }
      if (testOrderId.value) params.test_order_id = testOrderId.value
      const r = await expenseApi.getDriverMonthlySettlement(params)
      driverTableData.value = buildDriverRows(r.data || {})
    } else {
      const params = {}
      if (yearMonth.value) params.year_month = yearMonth.value
      if (testOrderId.value) params.test_order_id = testOrderId.value
      const r = await expenseApi.getMonthlySettlementList(params)
      engineerTableData.value = r.data || []
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 生成工程师月度结算
async function generateEngineerSettlement() {
  if (!yearMonth.value) { window.$message?.warning('请输入月份(YYYY-MM)'); return }
  try {
    await expenseApi.generateMonthlySettlement({ year_month: yearMonth.value })
    window.$message?.success('生成成功')
    querySettlement()
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadTestOrders()
  const now = new Date()
  yearMonth.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
})

// 切换人员类型时重新查询
watch(personType, () => {
  driverTableData.value = []
  engineerTableData.value = []
  querySettlement()
})
</script>
