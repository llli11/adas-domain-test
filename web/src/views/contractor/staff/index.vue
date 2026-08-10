<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NSelect, NDatePicker, NTag, NPopconfirm, NCard, NSpace, NStatistic, NModal, NImage, NDivider } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '人员台账' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const dashboardData = ref([])

const { modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef, handleEdit, handleDelete, handleAdd } = useCRUD({
  name: '人员',
  initForm: { status: '在职' },
  doCreate: api.createContractorStaff,
  doUpdate: api.updateContractorStaff,
  doDelete: api.deleteContractorStaff,
  refresh: () => {
    $table.value?.handleSearch()
    loadDashboard()
  },
})

const statusOptions = [
  { label: '在职', value: '在职' },
  { label: '试用期', value: '试用期' },
  { label: '离职中', value: '离职中' },
  { label: '离职', value: '离职' },
  { label: '流转中', value: '流转中' },
]
const typeOptions = [
  { label: '工程师', value: '工程师' },
  { label: '驾驶员', value: '驾驶员' },
]
const genderOptions = [
  { label: '男', value: '男' },
  { label: '女', value: '女' },
]
const projectOptions = ref([])
const userOptions = ref([])

onMounted(() => {
  $table.value?.handleSearch()
  loadDashboard()
  loadProjects()
  loadUsers()
})

async function loadDashboard() {
  const res = await api.getContractorStaffDashboard()
  if (res.data) {
    dashboardData.value = res.data
  }
}

async function loadProjects() {
  const res = await api.getContractorProjects()
  if (res.data) {
    projectOptions.value = res.data.map(d => ({ label: d.name, value: d.id, responsible_user_id: d.responsible_user_id }))
  }
}

function onProjectChange(value) {
  const proj = projectOptions.value.find(p => p.value === value)
  if (proj?.responsible_user_id) {
    modalForm.responsible_user_id = proj.responsible_user_id
  }
}

async function loadUsers() {
  const res = await api.getUserList({ page_size: 999 })
  if (res.data) {
    userOptions.value = res.data.map(u => ({ label: u.alias || u.username, value: u.id }))
  }
}

function handleResign(row) {
  api.resignContractorStaff({ staff_id: row.id }).then(() => {
    $message?.success('离职操作成功')
    $table.value?.handleSearch()
    loadDashboard()
  })
}

// ===== 项目管理 =====
const projModalVisible = ref(false)
const projModalTitle = ref('项目管理')
const projForm = ref({ id: null, name: '', desc: '', order: 0, responsible_user_id: null })
const projLoading = ref(false)

function handleProjAdd() {
  projForm.value = { id: null, name: '', desc: '', order: 0, responsible_user_id: null }
  projModalTitle.value = '新增项目'
  projModalVisible.value = true
}

function handleProjEdit(row) {
  projForm.value = { id: row.id, name: row.name, desc: row.desc || '', order: row.order || 0, responsible_user_id: row.responsible_user_id || null }
  projModalTitle.value = '编辑项目'
  projModalVisible.value = true
}

async function handleProjSave() {
  projLoading.value = true
  try {
    if (projForm.value.id) {
      await api.updateContractorProject(projForm.value)
    } else {
      await api.createContractorProject(projForm.value)
    }
    projModalVisible.value = false
    loadProjects()
    $message?.success('保存成功')
  } catch (e) {
    $message?.error('保存失败')
  } finally {
    projLoading.value = false
  }
}

async function handleProjDelete(row) {
  try {
    await api.deleteContractorProject({ proj_id: row.id })
    loadProjects()
    $message?.success('删除成功')
  } catch (e) {
    $message?.error('删除失败')
  }
}

function openProjManager() {
  loadProjectsForManager()
  projModalTitle.value = '项目管理'
  projModalVisible.value = true
}

const projectListForManager = ref([])
async function loadProjectsForManager() {
  const res = await api.getContractorProjects({ page_size: 999 })
  if (res.data) {
    projectListForManager.value = res.data
  }
}

const columns = [
  { title: '姓名', key: 'name', width: 80, align: 'center', ellipsis: { tooltip: true } },
  { title: '属性', key: 'type', width: 80, align: 'center' },
  { title: '性别', key: 'gender', width: 60, align: 'center' },
  { title: '手机号', key: 'phone', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '公司', key: 'company', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '所属项目', key: 'project_name', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '责任人', key: 'responsible_user_name', width: 80, align: 'center' },
  { title: '入职日期', key: 'entry_date', width: 100, align: 'center', render(row) { return row.entry_date ? formatDate(row.entry_date) : '-' } },
  { title: '状态', key: 'status', width: 80, align: 'center', render(row) {
    const typeMap = { 在职: 'success', 试用期: 'warning', 离职中: 'error', 离职: 'default', 流转中: 'warning' }
    return h(NTag, { type: typeMap[row.status] || 'default', size: 'small' }, { default: () => row.status })
  }},
  { title: '当前车辆', key: 'current_vehicle', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '当前任务', key: 'current_task', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '操作', key: 'actions', width: 200, align: 'center', fixed: 'right', render(row) {
    return [
      withDirectives(h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => handleEdit(row) },
        { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }), [[vPermission, 'post/api/v1/contractor/staff/update']]),
      h(NPopconfirm, { onPositiveClick: () => handleDelete({ staff_id: row.id }) }, {
        trigger: () => withDirectives(h(NButton, { size: 'small', type: 'error', style: 'margin-right: 8px;' },
          { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }), [[vPermission, 'delete/api/v1/contractor/staff/delete']]),
        default: () => h('div', {}, '确定删除该人员吗?'),
      }),
      h(NPopconfirm, { onPositiveClick: () => handleResign(row) }, {
        trigger: () => h(NButton, { size: 'small', type: 'warning' },
          { default: () => '离职', icon: renderIcon('material-symbols:exit-to-app', { size: 16 }) }),
        default: () => h('div', {}, '确定将该人员设为离职吗?'),
      }),
    ]
  }},
]

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: ['input', 'blur'] }],
}
</script>

<template>
  <CommonPage show-footer title="人员台账">
    <template #action>
      <NSpace vertical :size="8">
        <NButton v-permission="'post/api/v1/contractor/staff/create'" type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新增入职
        </NButton>
        <NButton type="primary" @click="openProjManager">
          <TheIcon icon="material-symbols:folder-managed-outline" :size="18" class="mr-5" />项目管理
        </NButton>
      </NSpace>
    </template>

    <!-- 看板统计 -->
    <NSpace class="mb-20" wrap>
      <NCard v-for="item in dashboardData" :key="item.project_id" style="width: 240px;">
        <NStatistic :label="item.project_name" :value="item.total">
          <template #suffix>
            <span style="font-size: 14px; color: #666;">人</span>
          </template>
        </NStatistic>
        <NSpace class="mt-10">
          <NTag type="success" size="small">空闲 {{ item.idle }}</NTag>
          <NTag type="error" size="small">任务中 {{ item.busy }}</NTag>
        </NSpace>
      </NCard>
    </NSpace>

    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getContractorStaffList">
      <template #queryBar>
        <QueryBarItem label="姓名" :label-width="40">
          <NInput v-model:value="queryItems.name" clearable placeholder="请输入姓名" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="公司" :label-width="40">
          <NInput v-model:value="queryItems.company" clearable placeholder="请输入公司" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="项目" :label-width="40">
          <NSelect v-model:value="queryItems.project_id" clearable :options="projectOptions" placeholder="请选择项目" style="width: 180px" />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
          <NSelect v-model:value="queryItems.status" clearable :options="statusOptions" placeholder="请选择状态" style="width: 140px" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="100" :model="modalForm" :rules="rules">
        <NFormItem label="姓名" path="name"><NInput v-model:value="modalForm.name" clearable placeholder="请输入姓名" /></NFormItem>
        <NFormItem label="属性" path="type"><NSelect v-model:value="modalForm.type" clearable :options="typeOptions" placeholder="请选择属性" /></NFormItem>
        <NFormItem label="性别" path="gender"><NSelect v-model:value="modalForm.gender" clearable :options="genderOptions" placeholder="请选择性别" /></NFormItem>
        <NFormItem label="身份证号" path="id_card"><NInput v-model:value="modalForm.id_card" clearable placeholder="请输入身份证号" /></NFormItem>
        <NFormItem label="手机号" path="phone"><NInput v-model:value="modalForm.phone" clearable placeholder="请输入手机号" /></NFormItem>
        <NFormItem label="所属公司" path="company"><NInput v-model:value="modalForm.company" clearable placeholder="请输入所属公司" /></NFormItem>
        <NFormItem label="岗位" path="position"><NInput v-model:value="modalForm.position" clearable placeholder="请输入岗位" /></NFormItem>
        <NFormItem label="所属项目" path="project_id"><NSelect v-model:value="modalForm.project_id" clearable :options="projectOptions" placeholder="请选择项目" @update:value="onProjectChange" /></NFormItem>
        <NFormItem label="责任人" path="responsible_user_id"><NSelect v-model:value="modalForm.responsible_user_id" clearable :options="userOptions" placeholder="请选择责任人" /></NFormItem>
        <NFormItem label="入职日期" path="entry_date"><NDatePicker v-model:value="modalForm.entry_date" type="date" clearable placeholder="请选择入职日期" /></NFormItem>
        <NFormItem label="状态" path="status"><NSelect v-model:value="modalForm.status" :options="statusOptions" placeholder="请选择状态" /></NFormItem>
        <NFormItem label="备注" path="remark"><NInput v-model:value="modalForm.remark" type="textarea" clearable placeholder="请输入备注" /></NFormItem>
      </NForm>
    </CrudModal>

    <!-- 项目管理弹窗 -->
    <NModal v-model:show="projModalVisible" :title="projModalTitle" preset="card" style="width: 500px;" :closable="true">
      <!-- 项目列表 -->
      <NForm ref="$projFormRef" label-placement="left" label-align="left" :label-width="80" :model="projForm">
        <NFormItem label="项目名称" path="name">
          <NInput v-model:value="projForm.name" placeholder="请输入项目名称" />
        </NFormItem>
<NFormItem label="排序" path="order">
          <NInput v-model:value="projForm.order" type="number" placeholder="数字越小越靠前" />
        </NFormItem>
        <NFormItem label="责任人" path="responsible_user_id">
          <NSelect v-model:value="projForm.responsible_user_id" clearable :options="userOptions" placeholder="请选择责任人" />
        </NFormItem>
      </NForm>
      <div style="display: flex; gap: 8px; margin-bottom: 16px;">
        <NButton type="primary" @click="handleProjSave" :loading="projLoading">{{ projForm.id ? '更新' : '新增' }}</NButton>
        <NButton v-if="projForm.id" @click="projForm = { id: null, name: '', desc: '', order: 0, responsible_user_id: null }; projModalTitle = '新增项目'">取消编辑</NButton>
      </div>
      <NDivider />
      <div style="max-height: 240px; overflow-y: auto;">
        <div v-for="item in projectListForManager" :key="item.id" style="display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0;">
          <span>{{ item.name }}<span v-if="item.responsible_user_name" style="color: #999; margin-left: 8px; font-size: 12px;">{{ item.responsible_user_name }}</span></span>
          <NSpace>
            <NButton size="tiny" type="primary" @click="handleProjEdit(item)">编辑</NButton>
            <NPopconfirm @positive-click="() => handleProjDelete(item)">
              <template #trigger><NButton size="tiny" type="error">删除</NButton></template>
              确定删除项目「{{ item.name }}」？
            </NPopconfirm>
          </NSpace>
        </div>
        <div v-if="!projectListForManager.length" style="text-align: center; color: #999; padding: 20px;">暂无项目</div>
      </div>
    </NModal>
  </CommonPage>
</template>
