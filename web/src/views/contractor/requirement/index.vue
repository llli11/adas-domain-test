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

defineOptions({ name: '需求管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const projectOptions = ref([])
const userOptions = ref([])

const { modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef, handleEdit, handleDelete, handleAdd } = useCRUD({
  name: '需求单',
  initForm: { type: '工程师', quantity: 1, status: '待审批' },
  doCreate: api.createContractorRequirement,
  doUpdate: api.updateContractorRequirement,
  doDelete: api.deleteContractorRequirement,
  refresh: () => $table.value?.handleSearch(),
})

const typeOptions = [
  { label: '工程师', value: '工程师' },
  { label: '驾驶员', value: '驾驶员' },
]
const statusOptions = [
  { label: '待审批', value: '待审批' },
  { label: '已通过', value: '已通过' },
  { label: '已驳回', value: '已驳回' },
]

onMounted(() => {
  $table.value?.handleSearch()
  loadProjects()
  loadUsers()
})

async function loadProjects() {
  const res = await api.getDepts()
  if (res.data) {
    projectOptions.value = res.data.map(d => ({ label: d.name, value: d.id }))
  }
}

async function loadUsers() {
  const res = await api.getUserList({ page_size: 999 })
  if (res.data) {
    userOptions.value = res.data.map(u => ({ label: u.alias || u.username, value: u.id }))
  }
}

function handleApprove(row, status) {
  // 默认审批人取当前登录用户，实际应使用全局用户信息
  const approverId = 1
  api.approveContractorRequirement({ id: row.id, status, approver_user_id: approverId }).then(() => {
    $message?.success('审批完成')
    $table.value?.handleSearch()
  })
}

const columns = [
  { title: '项目', key: 'project_name', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '类型', key: 'type', width: 80, align: 'center' },
  { title: '需求时间', key: 'demand_date', width: 100, align: 'center' },
  { title: '数量', key: 'quantity', width: 60, align: 'center' },
  { title: '周期', key: 'period', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '状态', key: 'status', width: 80, align: 'center', render(row) {
    const typeMap = { 待审批: 'warning', 已通过: 'success', 已驳回: 'error' }
    return h(NTag, { type: typeMap[row.status] || 'default', size: 'small' }, { default: () => row.status })
  }},
  { title: '审批人', key: 'approver_user_name', width: 80, align: 'center' },
  { title: '操作', key: 'actions', width: 200, align: 'center', fixed: 'right', render(row) {
    const btns = []
    if (row.status === '待审批') {
      btns.push(
        h(NButton, { size: 'small', type: 'success', style: 'margin-right: 8px;', onClick: () => handleApprove(row, '已通过') },
          { default: () => '通过' }),
        h(NButton, { size: 'small', type: 'warning', style: 'margin-right: 8px;', onClick: () => handleApprove(row, '已驳回') },
          { default: () => '驳回' }),
      )
    }
    btns.push(
      withDirectives(h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => handleEdit(row) },
        { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }), [[vPermission, 'post/api/v1/contractor/requirement/update']]),
      h(NPopconfirm, { onPositiveClick: () => handleDelete({ req_id: row.id }) }, {
        trigger: () => withDirectives(h(NButton, { size: 'small', type: 'error' },
          { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }), [[vPermission, 'delete/api/v1/contractor/requirement/delete']]),
        default: () => h('div', {}, '确定删除该需求单吗?'),
      }),
    )
    return btns
  }},
]

const rules = {
  type: [{ required: true, message: '请选择类型', trigger: ['input', 'blur'] }],
}
</script>

<template>
  <CommonPage show-footer :show-header="false" title="需求管理">
    <template #action>
      <NButton v-permission="'post/api/v1/contractor/requirement/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />提交需求
      </NButton>
    </template>
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getContractorRequirementList">
      <template #queryBar>
        <QueryBarItem label="项目" :label-width="40">
          <NSelect v-model:value="queryItems.project_id" clearable :options="projectOptions" placeholder="请选择项目" />
        </QueryBarItem>
        <QueryBarItem label="类型" :label-width="40">
          <NSelect v-model:value="queryItems.type" clearable :options="typeOptions" placeholder="请选择类型" />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
          <NSelect v-model:value="queryItems.status" clearable :options="statusOptions" placeholder="请选择状态" />
        </QueryBarItem>
      </template>
    </CrudTable>
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="100" :model="modalForm" :rules="rules">
        <NFormItem label="需求项目" path="project_id"><NSelect v-model:value="modalForm.project_id" clearable :options="projectOptions" placeholder="请选择项目" /></NFormItem>
        <NFormItem label="需求类型" path="type"><NSelect v-model:value="modalForm.type" :options="typeOptions" placeholder="请选择类型" /></NFormItem>
        <NFormItem label="需求时间" path="demand_date"><NInput v-model:value="modalForm.demand_date" clearable placeholder="YYYY-MM-DD" /></NFormItem>
        <NFormItem label="数量" path="quantity"><NInput v-model:value="modalForm.quantity" clearable placeholder="请输入数量" /></NFormItem>
        <NFormItem label="周期" path="period"><NInput v-model:value="modalForm.period" clearable placeholder="请输入周期" /></NFormItem>
        <NFormItem label="备注" path="remark"><NInput v-model:value="modalForm.remark" type="textarea" clearable placeholder="请输入备注" /></NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
