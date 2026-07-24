<template>
  <div>
    <n-data-table :columns="columns" :data="tableData" :loading="loading" :pagination="pagination" size="small" />
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NDataTable, NButton, NSpace } from 'naive-ui'
import api from '@/api'

const loading = ref(false)
const tableData = ref([])
const columns = [
  { title: '日期', key: 'record_date', width: 110 },
  { title: '人员', key: 'person_name', width: 100 },
  { title: '项目', key: 'project_name', width: 150 },
  { title: '试验任务', key: 'test_task', width: 100 },
  { title: '车辆编号', key: 'car_number', width: 100 },
  { title: '工时(h)', key: 'total_hours', width: 80 },
  { title: '工作地点', key: 'work_location', width: 120 },
  { title: '审批人', key: 'approver2', width: 100 },
  {
    title: '操作', key: 'action', width: 170,
    render(row) {
      const isApproved = row.approver2_result === '通过'
      return h(NSpace, { size: 4, wrap: true, wrapItem: false }, () => [
        isApproved
          ? h(NButton, { size: 'tiny', type: 'success', disabled: true }, '已通过')
          : h(NButton, { size: 'tiny', type: 'success', onClick: () => approve(row) }, '通过'),
        isApproved
          ? null
          : h(NButton, { size: 'tiny', type: 'error', onClick: () => reject(row) }, '驳回'),
      ])
    }
  },
]
const pagination = { pageSize: 10 }

async function approve(row) {
  await api.approveRecord({ record_id: row.id, record_model: row.record_model })
  window.$message?.success('已通过'); fetchList()
}
async function reject(row) {
  await api.rejectRecord({ record_id: row.id, record_model: row.record_model })
  window.$message?.success('已驳回'); fetchList()
}
async function fetchList() {
  loading.value = true
  try { const res = await api.getPendingApprovalList(); tableData.value = res.data || [] }
  catch (e) { console.error(e) } finally { loading.value = false }
}
onMounted(() => fetchList())
</script>
