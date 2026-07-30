<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NSelect, NTag, NPopconfirm } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '流动管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const projectOptions = ref([])
const staffOptions = ref([])

const { modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef, handleEdit, handleDelete, handleAdd } = useCRUD({
  name: '流转记录',
  initForm: { transfer_type: '流转', status: '待确认' },
  doCreate: api.createContractorTransfer,
  doUpdate: api.updateContractorTransfer,
  doDelete: api.deleteContractorTransfer,
  refresh: () => $table.value?.handleSearch(),
})

const typeOptions = [
  { label: '入职', value: '入职' },
  { label: '流转', value: '流转' },
  { label: '离职', value: '离职' },
]
const statusOptions = [
  { label: '待确认', value: '待确认' },
  { label: '已确认', value: '已确认' },
  { label: '已驳回', value: '已驳回' },
]

onMounted(() => {
  $table.value?.handleSearch()
  loadProjects()
  loadStaff()
})

async function loadProjects() {
  const res = await api.getDepts()
  if (res.data) {
    projectOptions.value = res.data.map(d => ({ label: d.name, value: d.id }))
  }
}

async function loadStaff() {
  const res = await api.getContractorStaffList({ page_size: 999, status: '在职' })
  if (res.data) {
    staffOptions.value = res.data.map(s => ({ label: s.name, value: s.id }))
  }
}

function handleConfirm(row, status) {
  const confirmUserId = 1 // TODO: 使用当前登录用户ID
  api.confirmContractorTransfer({ id: row.id, status, confirm_user_id: confirmUserId }).then(() => {
    $message?.success('处理成功')
    $table.value?.handleSearch()
  })
}

const columns = [
  { title: '人员', key: 'staff_name', width: 80, align: 'center' },
  { title: '类型', key: 'transfer_type', width: 80, align: 'center' },
  { title: '原项目', key: 'from_project_name', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '目标项目', key: 'to_project_name', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '发起人', key: 'initiator_user_name', width: 80, align: 'center' },
  { title: '确认人', key: 'confirm_user_name', width: 80, align: 'center' },
  { title: '状态', key: 'status', width: 80, align: 'center', render(row) {
    const typeMap = { 待确认: 'warning', 已确认: 'success', 已驳回: 'error' }
    return h(NTag, { type: typeMap[row.status] || 'default', size: 'small' }, { default: () => row.status })
  }},
  { title: '操作', key: 'actions', width: 200, align: 'center', fixed: 'right', render(row) {
    const btns = []
    if (row.status === '待确认') {
      btns.push(
        h(NButton, { size: 'small', type: 'success', style: 'margin-right: 8px;', onClick: () => handleConfirm(row, '已确认') },
          { default: () => '确认' }),
        h(NButton, { size: 'small', type: 'warning', style: 'margin-right: 8px;', onClick: () => handleConfirm(row, '已驳回') },
          { default: () => '驳回' }),
      )
    }
    btns.push(
      withDirectives(h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => handleEdit(row) },
        { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }), [[vPermission, 'post/api/v1/contractor/transfer/update']]),
      h(NPopconfirm, { onPositiveClick: () => handleDelete({ transfer_id: row.id }) }, {
        trigger: () => withDirectives(h(NButton, { size: 'small', type: 'error' },
          { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }), [[vPermission, 'delete/api/v1/contractor/transfer/delete']]),
        default: () => h('div', {}, '确定删除该流转记录吗?'),
      }),
    )
    return btns
  }},
]

const rules = {
  staff_id: [{ required: true, message: '请选择人员', trigger: ['input', 'blur'] }],
  transfer_type: [{ required: true, message: '请选择类型', trigger: ['input', 'blur'] }],
}
</script>

<template>
  <CommonPage show-footer :show-header="false" title="流动管理">
    <template #action>
      <NButton v-permission="'post/api/v1/contractor/transfer/apply'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />发起流转
      </NButton>
    </template>
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getContractorTransferList">
      <template #queryBar>
        <QueryBarItem label="人员" :label-width="40">
          <NSelect v-model:value="queryItems.staff_id" clearable :options="staffOptions" placeholder="请选择人员" />
        </QueryBarItem>
        <QueryBarItem label="类型" :label-width="40">
          <NSelect v-model:value="queryItems.transfer_type" clearable :options="typeOptions" placeholder="请选择类型" />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
          <NSelect v-model:value="queryItems.status" clearable :options="statusOptions" placeholder="请选择状态" />
        </QueryBarItem>
      </template>
    </CrudTable>
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="100" :model="modalForm" :rules="rules">
        <NFormItem label="人员" path="staff_id"><NSelect v-model:value="modalForm.staff_id" :options="staffOptions" placeholder="请选择人员" /></NFormItem>
        <NFormItem label="流转类型" path="transfer_type"><NSelect v-model:value="modalForm.transfer_type" :options="typeOptions" placeholder="请选择类型" /></NFormItem>
        <NFormItem label="原项目" path="from_project_id"><NSelect v-model:value="modalForm.from_project_id" clearable :options="projectOptions" placeholder="请选择原项目" /></NFormItem>
        <NFormItem label="目标项目" path="to_project_id"><NSelect v-model:value="modalForm.to_project_id" clearable :options="projectOptions" placeholder="请选择目标项目" /></NFormItem>
        <NFormItem label="备注" path="remark"><NInput v-model:value="modalForm.remark" type="textarea" clearable placeholder="请输入备注" /></NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
