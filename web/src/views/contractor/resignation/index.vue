<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NSelect, NDatePicker, NTag, NPopconfirm } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '离职管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const approveModalVisible = ref(false)
const approveForm = ref({})
const approveFormRef = ref(null)

const { modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef, handleEdit, handleDelete, handleAdd } = useCRUD({
  name: '离职申请',
  initForm: {},
  doCreate: api.createContractorResignation,
  doUpdate: api.updateContractorResignation,
  doDelete: api.deleteContractorResignation,
  refresh: () => $table.value?.handleSearch(),
})

const statusOptions = [
  { label: '待审批', value: '待审批' },
  { label: '已通过', value: '已通过' },
  { label: '已驳回', value: '已驳回' },
]

onMounted(() => {
  $table.value?.handleSearch()
})

function handleApprove(row) {
  approveForm.value = { id: row.id, approval_status: '已通过', approver: '' }
  approveModalVisible.value = true
}

async function handleApproveSave() {
  approveFormRef.value?.validate(async (err) => {
    if (err) return
    await api.approveContractorResignation(approveForm.value)
    $message.success('审批完成')
    approveModalVisible.value = false
    $table.value?.handleSearch()
  })
}

const columns = [
  { title: '人员姓名', key: 'staff_name', width: 80, align: 'center' },
  { title: '离职原因', key: 'reason', width: 120, align: 'center', ellipsis: { tooltip: true } },
  { title: '交接状态', key: 'handover_status', width: 80, align: 'center' },
  { title: '审批状态', key: 'approval_status', width: 80, align: 'center', render(row) {
    const typeMap = { 待审批: 'warning', 已通过: 'success', 已驳回: 'error' }
    return h(NTag, { type: typeMap[row.approval_status] || 'default', size: 'small' }, { default: () => row.approval_status })
  }},
  { title: '审批人', key: 'approver', width: 60, align: 'center' },
  { title: '操作', key: 'actions', width: 180, align: 'center', fixed: 'right', render(row) {
    const btns = [
      withDirectives(h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => handleEdit(row) },
        { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }), [[vPermission, 'post/api/v1/contractor/resignation/update']]),
    ]
    if (row.approval_status === '待审批') {
      btns.push(withDirectives(h(NButton, { size: 'small', type: 'info', style: 'margin-right: 8px;', onClick: () => handleApprove(row) },
        { default: () => '审批', icon: renderIcon('material-symbols:check-circle-outline', { size: 16 }) }), [[vPermission, 'post/api/v1/contractor/resignation/approve']]))
    }
    btns.push(h(NPopconfirm, { onPositiveClick: () => handleDelete({ resignation_id: row.id }) }, {
      trigger: () => withDirectives(h(NButton, { size: 'small', type: 'error', style: 'margin-right: 8px;' },
        { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }), [[vPermission, 'delete/api/v1/contractor/resignation/delete']]),
      default: () => h('div', {}, '确定删除该离职记录吗?'),
    }))
    return btns
  }},
]

const rules = {
  staff_id: [{ required: true, message: '请输入人员ID', trigger: ['input', 'blur'] }],
}
const approveRules = {
  approval_status: [{ required: true, message: '请选择审批结果', trigger: ['blur', 'change'] }],
  approver: [{ required: true, message: '请输入审批人', trigger: ['input', 'blur'] }],
}
</script>

<template>
  <CommonPage show-footer title="离职管理">
    <template #action>
      <NButton v-permission="'post/api/v1/contractor/resignation/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />提交离职申请
      </NButton>
    </template>
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getContractorResignationList">
      <template #queryBar>
        <QueryBarItem label="人员ID" :label-width="50">
          <NInput v-model:value="queryItems.staff_id" clearable placeholder="请输入人员ID" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="审批状态" :label-width="60">
          <NSelect v-model:value="queryItems.approval_status" clearable :options="statusOptions" placeholder="请选择状态" />
        </QueryBarItem>
      </template>
    </CrudTable>
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="100" :model="modalForm" :rules="rules">
        <NFormItem label="人员ID" path="staff_id"><NInput v-model:value="modalForm.staff_id" clearable placeholder="请输入人员ID" /></NFormItem>
        <NFormItem label="预计离职日期" path="expected_date"><NDatePicker v-model:value="modalForm.expected_date" type="date" clearable placeholder="请选择预计离职日期" /></NFormItem>
        <NFormItem label="离职原因" path="reason"><NInput v-model:value="modalForm.reason" type="textarea" clearable placeholder="请输入离职原因" /></NFormItem>
        <NFormItem label="交接状态" path="handover_status"><NInput v-model:value="modalForm.handover_status" clearable placeholder="请输入交接状态" /></NFormItem>
        <NFormItem label="备注" path="remark"><NInput v-model:value="modalForm.remark" type="textarea" clearable placeholder="请输入备注" /></NFormItem>
      </NForm>
    </CrudModal>
    <CrudModal v-model:visible="approveModalVisible" title="离职审批" @save="handleApproveSave">
      <NForm ref="approveFormRef" label-placement="left" label-align="left" :label-width="100" :model="approveForm" :rules="approveRules">
        <NFormItem label="审批结果" path="approval_status">
          <NSelect v-model:value="approveForm.approval_status" :options="[{label:'已通过',value:'已通过'},{label:'已驳回',value:'已驳回'}]" placeholder="请选择审批结果" />
        </NFormItem>
        <NFormItem label="审批人" path="approver">
          <NInput v-model:value="approveForm.approver" clearable placeholder="请输入审批人" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
