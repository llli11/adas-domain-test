<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NSelect, NTag, NPopconfirm } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: '请假管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const staffOptions = ref([])
const userStore = useUserStore()

const { modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef, handleEdit, handleDelete } = useCRUD({
  name: '请假申请',
  initForm: { status: '待审批' },
  doCreate: api.createContractorLeave,
  doUpdate: api.updateContractorLeave,
  doDelete: api.deleteContractorLeave,
  refresh: () => $table.value?.handleSearch(),
})

const statusOptions = [
  { label: '待审批', value: '待审批' },
  { label: '已批准', value: '已批准' },
  { label: '已驳回', value: '已驳回' },
]
const leaveTypeOptions = [
  { label: '事假', value: '事假' },
  { label: '病假', value: '病假' },
  { label: '年假', value: '年假' },
]

onMounted(() => {
  $table.value?.handleSearch()
  loadStaff()
})

async function loadStaff() {
  const res = await api.getContractorStaffList({ page_size: 999 })
  if (res.data) {
    staffOptions.value = res.data.map(s => ({ label: s.name, value: s.id }))
  }
}

function handleApprove(row, status) {
  api.approveContractorLeave({ id: row.id, status, approved_by_user_id: userStore.userId || 0 }).then(() => {
    $message?.success('审批完成')
    $table.value?.handleSearch()
  })
}

const columns = [
  { title: '人员', key: 'staff_name', width: 80, align: 'center' },
  { title: '请假日期', key: 'leave_date', width: 100, align: 'center' },
  { title: '请假类型', key: 'leave_type', width: 80, align: 'center' },
  { title: '原因', key: 'reason', width: 150, align: 'center', ellipsis: { tooltip: true } },
  { title: '状态', key: 'status', width: 80, align: 'center', render(row) {
    const typeMap = { 待审批: 'warning', 已批准: 'success', 已驳回: 'error' }
    return h(NTag, { type: typeMap[row.status] || 'default', size: 'small' }, { default: () => row.status })
  }},
  { title: '审批人', key: 'approved_by_user_name', width: 80, align: 'center' },
  { title: '操作', key: 'actions', width: 200, align: 'center', fixed: 'right', render(row) {
    const btns = []
    if (row.status === '待审批') {
      btns.push(
        h(NButton, { size: 'small', type: 'success', style: 'margin-right: 8px;', onClick: () => handleApprove(row, '已批准') },
          { default: () => '批准' }),
        h(NButton, { size: 'small', type: 'warning', style: 'margin-right: 8px;', onClick: () => handleApprove(row, '已驳回') },
          { default: () => '驳回' }),
      )
    }
    btns.push(
      withDirectives(h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => handleEdit(row) },
        { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }), [[vPermission, 'post/api/v1/contractor/leave/update']]),
      h(NPopconfirm, { onPositiveClick: () => handleDelete({ leave_id: row.id }) }, {
        trigger: () => withDirectives(h(NButton, { size: 'small', type: 'error' },
          { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }), [[vPermission, 'delete/api/v1/contractor/leave/delete']]),
        default: () => h('div', {}, '确定删除该请假记录吗?'),
      }),
    )
    return btns
  }},
]
</script>

<template>
  <CommonPage show-footer :show-header="false" title="请假管理">
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getContractorLeaveList">
      <template #queryBar>
        <QueryBarItem label="人员" :label-width="40">
          <NSelect v-model:value="queryItems.staff_id" clearable :options="staffOptions" placeholder="请选择人员" />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
          <NSelect v-model:value="queryItems.status" clearable :options="statusOptions" placeholder="请选择状态" />
        </QueryBarItem>
      </template>
    </CrudTable>
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="100" :model="modalForm">
        <NFormItem label="人员" path="staff_id"><NSelect v-model:value="modalForm.staff_id" :options="staffOptions" placeholder="请选择人员" /></NFormItem>
        <NFormItem label="请假日期" path="leave_date"><NInput v-model:value="modalForm.leave_date" clearable placeholder="YYYY-MM-DD" /></NFormItem>
        <NFormItem label="请假类型" path="leave_type"><NSelect v-model:value="modalForm.leave_type" clearable :options="leaveTypeOptions" placeholder="请选择类型" /></NFormItem>
        <NFormItem label="原因" path="reason"><NInput v-model:value="modalForm.reason" type="textarea" clearable placeholder="请输入原因" /></NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
