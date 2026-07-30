<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NSelect, NDatePicker, NTag, NPopconfirm, NCard, NSpace, NStatistic, NModal, NImage } from 'naive-ui'
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

// 二维码弹窗
const qrModalVisible = ref(false)
const qrData = ref({ token: '', url: '', name: '' })

const { modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef, handleEdit, handleDelete, handleAdd } = useCRUD({
  name: '人员',
  initForm: { status: '在职', task_status: '空闲', is_idle: true },
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
const taskStatusOptions = [
  { label: '空闲', value: '空闲' },
  { label: '任务中', value: '任务中' },
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

function handleResign(row) {
  api.resignContractorStaff({ staff_id: row.id }).then(() => {
    $message?.success('离职操作成功')
    $table.value?.handleSearch()
    loadDashboard()
  })
}

async function handleGenerateQR(row) {
  const res = await api.generateContractorStaffQRToken({ staff_id: row.id })
  if (res.code === 200 && res.data) {
    const fullUrl = window.location.origin + res.data.qr_page_url
    qrData.value = {
      token: res.data.token,
      url: fullUrl,
      name: res.data.staff_name || row.name,
    }
    qrModalVisible.value = true
  } else {
    $message?.error(res.msg || '生成二维码失败')
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
  { title: '任务状态', key: 'task_status', width: 80, align: 'center', render(row) {
    return h(NTag, { type: row.task_status === '任务中' ? 'error' : 'success', size: 'small' }, { default: () => row.task_status })
  }},
  { title: '当前车辆', key: 'current_vehicle', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '当前任务', key: 'current_task', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '操作', key: 'actions', width: 240, align: 'center', fixed: 'right', render(row) {
    return [
      withDirectives(h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => handleEdit(row) },
        { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }), [[vPermission, 'post/api/v1/contractor/staff/update']]),
      h(NButton, { size: 'small', type: 'info', style: 'margin-right: 8px;', onClick: () => handleGenerateQR(row) },
        { default: () => '二维码', icon: renderIcon('material-symbols:qr-code', { size: 16 }) }),
      h(NPopconfirm, { onPositiveClick: () => handleDelete({ staff_id: row.id }) }, {
        trigger: () => withDirectives(h(NButton, { size: 'small', type: 'error', style: 'margin-right: 8px;' },
          { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }), [[vPermission, 'delete/api/v1/contractor/staff/delete']]),
        default: () => h('div', {}, '确定删除该人员吗?'),
      }),
      h(NPopconfirm, { onPositiveClick: () => handleResign(row) }, {
        trigger: () => h(NButton, { size: 'small', type: 'warning' },
          { default: () => '离职', icon: renderIcon('material-symbols:exit-to-app-outline', { size: 16 }) }),
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
  <CommonPage show-footer :show-header="false" title="人员台账">
    <template #action>
      <NButton v-permission="'post/api/v1/contractor/staff/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新增入职
      </NButton>
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
          <NSelect v-model:value="queryItems.project_id" clearable :options="projectOptions" placeholder="请选择项目" />
        </QueryBarItem>
        <QueryBarItem label="任务状态" :label-width="60">
          <NSelect v-model:value="queryItems.task_status" clearable :options="taskStatusOptions" placeholder="请选择任务状态" />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
          <NSelect v-model:value="queryItems.status" clearable :options="statusOptions" placeholder="请选择状态" />
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
        <NFormItem label="所属项目" path="project_id"><NSelect v-model:value="modalForm.project_id" clearable :options="projectOptions" placeholder="请选择项目" /></NFormItem>
        <NFormItem label="责任人" path="responsible_user_id"><NSelect v-model:value="modalForm.responsible_user_id" clearable :options="userOptions" placeholder="请选择责任人" /></NFormItem>
        <NFormItem label="入职日期" path="entry_date"><NDatePicker v-model:value="modalForm.entry_date" type="date" clearable placeholder="请选择入职日期" /></NFormItem>
        <NFormItem label="状态" path="status"><NSelect v-model:value="modalForm.status" :options="statusOptions" placeholder="请选择状态" /></NFormItem>
        <NFormItem label="备注" path="remark"><NInput v-model:value="modalForm.remark" type="textarea" clearable placeholder="请输入备注" /></NFormItem>
      </NForm>
    </CrudModal>

    <!-- 二维码弹窗 -->
    <NModal v-model:show="qrModalVisible" title="外委人员二维码" preset="card" style="width: 400px;" :closable="true">
      <div style="text-align: center;">
        <p style="margin-bottom: 12px; font-weight: bold;">{{ qrData.name }}</p>
        <img v-if="qrData.url" :src="`https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(qrData.url)}`" alt="二维码" style="width: 250px; height: 250px;" />
        <p style="margin-top: 12px; color: #666; font-size: 12px; word-break: break-all;">{{ qrData.url }}</p>
        <NButton type="primary" style="margin-top: 12px;" @click="() => { const a = document.createElement('a'); a.href = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(qrData.url)}`; a.download = `${qrData.name}_二维码.png`; a.click(); }">
          下载二维码
        </NButton>
      </div>
    </NModal>
  </CommonPage>
</template>
