<script setup>
import { onMounted, ref, h } from 'vue'
import { NCard, NDataTable, NSelect, NButton, NSpace, NSpin, NPagination } from 'naive-ui'
import api from '@/api'

defineOptions({ name: '操作记录' })

const loading = ref(false)
const stats = ref({
  vehicle_total: 0,
  vehicle_today: 0,
  vehicle_month: 0,
  target_total: 0,
  target_today: 0,
  target_month: 0,
})
const chartData = ref([])
const logList = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const operatorOptions = ref([])

const operationTypeOptions = [
  { label: '全部', value: '' },
  { label: '更新车辆', value: '更新车辆' },
  { label: '对比基线', value: '对比基线' },
  { label: '删除车辆', value: '删除车辆' },
  { label: '新建基线', value: '新建基线' },
  { label: '更新基线', value: '更新基线' },
  { label: '删除基线', value: '删除基线' },
]

const filterParams = ref({
  operation_type: '',
  operator: '',
})

const operationTypeColors = {
  '更新车辆': '#52c41a',
  '对比基线': '#1890ff',
  '删除车辆': '#ff4d4f',
  '新建基线': '#722ed1',
  '更新基线': '#faad14',
  '删除基线': '#eb2f96',
}

const maxChartValue = ref(1)

const columns = [
  { title: '时间', key: 'created_at', width: '20%', resizable: true },
  { title: '操作账号', key: 'operator', width: '20%', resizable: true },
  {
    title: '操作类型',
    key: 'operation_type',
    width: '20%',
    resizable: true,
    render: (row) => {
      const color = operationTypeColors[row.operation_type] || '#999'
      return h('span', { style: { color, fontWeight: 500 } }, row.operation_type)
    },
  },
  {
    title: '操作对象',
    key: 'target',
    width: '40%',
    resizable: true,
    render: (row) => row.target_vin || row.target_name || '-',
  },
]

function loadStats() {
  api.getOperationStats().then((res) => {
    if (res.code === 200) {
      stats.value = res.data
    }
  })
}

function loadChart() {
  api.getOperationChart({ days: 30 }).then((res) => {
if (res.code === 200) {
      chartData.value = res.data
      const rawMax = Math.max(
        1,
        ...res.data.flatMap((d) => Object.values(d).filter((v) => typeof v === 'number'))
      )
      maxChartValue.value = Math.ceil(rawMax / 10) * 10
    }
  })
}

function loadOperators() {
  api.getLogOperators().then((res) => {
    if (res.code === 200) {
      operatorOptions.value = res.data.map((op) => ({ label: op, value: op }))
    }
  })
}

function loadLogList() {
  loading.value = true
  api
    .getOperationLogList({
      page: page.value,
      page_size: pageSize.value,
      operation_type: filterParams.value.operation_type || undefined,
      operator: filterParams.value.operator || undefined,
    })
    .then((res) => {
      if (res.code === 200) {
        logList.value = res.data || []
        total.value = res.total || 0
      }
    })
    .finally(() => {
      loading.value = false
    })
}

function handlePageChange(newPage) {
  page.value = newPage
  loadLogList()
}

function handleSearch() {
  page.value = 1
  loadLogList()
}

function getBarHeight(value) {
  return (value / maxChartValue.value) * 100
}

onMounted(() => {
  loadStats()
  loadChart()
  loadOperators()
  loadLogList()
})
</script>

<template>
  <div class="logs-page">
    <NCard :bordered="false" class="stats-card">
      <div class="stats-row">
        <div class="stats-item">
          <div class="stats-label">车辆总数</div>
          <div class="stats-value">{{ stats.vehicle_total }}</div>
        </div>
        <div class="stats-item">
          <div class="stats-label">车辆当日更新数</div>
          <div class="stats-value highlight">{{ stats.vehicle_today }}</div>
        </div>
        <div class="stats-item">
          <div class="stats-label">车辆当月更新数</div>
          <div class="stats-value">{{ stats.vehicle_month }}</div>
        </div>
      </div>
      <div class="stats-row">
        <div class="stats-item">
          <div class="stats-label">基线总数</div>
          <div class="stats-value">{{ stats.target_total }}</div>
        </div>
        <div class="stats-item">
          <div class="stats-label">基线当日更新数</div>
          <div class="stats-value highlight">{{ stats.target_today }}</div>
        </div>
        <div class="stats-item">
          <div class="stats-label">基线当月更新数</div>
          <div class="stats-value">{{ stats.target_month }}</div>
        </div>
      </div>
    </NCard>

    <NCard :bordered="false" class="chart-card">
      <template #header>
        <span>近30天操作统计</span>
      </template>
      <div class="chart-container">
        <div class="chart-y-axis">
          <span>{{ maxChartValue }}</span>
          <span>{{ Math.round(maxChartValue / 2) }}</span>
          <span>0</span>
        </div>
        <div class="chart-bars">
          <div v-for="day in chartData" :key="day.date" class="chart-day">
<div class="bar-group">
              <template
                v-for="(value, key) in {
                  '更新车辆': day['更新车辆'],
                  '对比基线': day['对比基线'],
                  '删除车辆': day['删除车辆'],
                  '新建基线': day['新建基线'],
                  '更新基线': day['更新基线'],
                  '删除基线': day['删除基线'],
                }"
                :key="key"
              >
                <div
                  v-if="value > 0"
                  class="bar-stack"
                  :style="{
                    height: getBarHeight(value) + '%',
                    backgroundColor: operationTypeColors[key],
                  }"
                  :title="`${key}: ${value}`"
                >
                  <span class="bar-value">{{ value }}</span>
                </div>
              </template>
            </div>
            <div class="chart-date">{{ day.date.slice(5) }}</div>
          </div>
        </div>
      </div>
      <div class="chart-legend">
        <div v-for="(color, type) in operationTypeColors" :key="type" class="legend-item">
          <span class="legend-color" :style="{ backgroundColor: color }"></span>
          <span class="legend-text">{{ type }}</span>
        </div>
      </div>
    </NCard>

    <NCard :bordered="false" class="log-card">
      <template #header>
        <span>操作日志</span>
      </template>
      <div class="filter-bar">
        <NSpace>
          <NSelect
            v-model:value="filterParams.operation_type"
            :options="operationTypeOptions"
            placeholder="操作类型"
            style="width: 150px"
            clearable
          />
          <NSelect
            v-model:value="filterParams.operator"
            :options="operatorOptions"
            placeholder="操作账号"
            style="width: 150px"
            clearable
            filterable
            tag
          />
          <NButton type="primary" @click="handleSearch">搜索</NButton>
        </NSpace>
      </div>
      <NSpin :show="loading">
        <div class="table-wrapper">
<NDataTable
            :columns="columns"
            :data="logList"
            :bordered="false"
            size="small"
            :pagination="false"
            virtual-scroll
          />
        </div>
      </NSpin>
      <div class="pagination-wrapper">
<NPagination
          v-model:page="page"
          :page-size="pageSize"
          :item-count="total"
          show-quick-jumper
          @update:page="handlePageChange"
        />
      </div>
    </NCard>
  </div>
</template>

<style scoped>
.logs-page {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 120px);
  overflow-y: auto;
}

.stats-card {
  flex-shrink: 0;
}

.stats-row {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.stats-row:last-child {
  margin-bottom: 0;
}

.stats-item {
  flex: 1;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  text-align: center;
}

.stats-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.stats-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.stats-value.highlight {
  color: #1890ff;
}

.chart-card {
  flex-shrink: 0;
}

.chart-container {
  display: flex;
  height: 250px;
  padding: 10px 0;
}

.chart-y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-right: 10px;
  font-size: 12px;
  color: #999;
  width: 40px;
  text-align: right;
}

.chart-bars {
  flex: 1;
  display: flex;
  gap: 4px;
  overflow-x: auto;
}

.chart-day {
  flex: 1;
  min-width: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bar-group {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 1px;
}

.bar-stack {
  width: 100%;
  min-height: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: height 0.3s;
}

.bar-value {
  font-size: 10px;
  color: #fff;
  white-space: nowrap;
}

.chart-date {
  font-size: 11px;
  color: #666;
  margin-top: 8px;
  text-align: center;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 14px;
  height: 14px;
  border-radius: 2px;
}

.legend-text {
  font-size: 12px;
  color: #666;
}

.log-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.log-card :deep(.n-card__content) {
  display: flex;
  flex-direction: column;
  background: #fff;
  padding-bottom: 16px;
}

.table-wrapper {
  flex: 1;
  overflow: visible;
}

.filter-bar {
  margin-bottom: 16px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 16px 0 0;
}
</style>