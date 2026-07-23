<template>
  <div>
    <n-space :size="8" style="margin-bottom: 12px;">
      <n-date-picker v-model:value="filterDate" type="date" placeholder="筛选日期" size="small" clearable />
      <n-input v-model:value="filterPerson" placeholder="筛选人员" size="small" clearable style="width: 150px" />
      <n-button size="small" type="primary" @click="fetchList">查询</n-button>
    </n-space>
    <n-data-table :columns="columns" :data="tableData" :loading="loading" :pagination="pagination" size="small" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { NSpace, NDataTable, NButton, NInput, NDatePicker } from 'naive-ui'
import api from '@/api'

const filterDate = ref(null)
const filterPerson = ref('')
const loading = ref(false)
const tableData = ref([])
const columns = [
  { title: '日期', key: 'record_date', width: 110 },
  { title: '人员', key: 'person_name', width: 100 },
  { title: '项目', key: 'project_name', width: 150 },
  { title: '试验任务', key: 'test_task', width: 100 },
  { title: '车辆编号', key: 'car_number', width: 100 },
  { title: '工时(h)', key: 'total_hours', width: 80 },
  { title: '垫付费用', key: 'daily_advance_total', width: 100 },
  { title: '审批状态', key: 'approver2_result', width: 100 },
]
const pagination = { pageSize: 10 }

async function fetchList() {
  loading.value = true
  try {
    const params = {}
    if (filterDate.value) { const d=new Date(filterDate.value); params.record_date = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` }
    if (filterPerson.value) params.person_name = filterPerson.value
    const res = await api.getDriverAttendanceList(params)
    tableData.value = res.data || []
  } catch (e) { console.error(e) } finally { loading.value = false }
}
onMounted(() => fetchList())
</script>
