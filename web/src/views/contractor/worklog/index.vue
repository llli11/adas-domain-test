<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NSelect, NTag, NPopconfirm, NInputNumber } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: '工作日志审核' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const projectOptions = ref([])
const staffOptions = ref([])
const userStore = useUserStore()

const { modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef, handleAdd, handleEdit, handleDelete } = useCRUD({
  name: '工作日志',
  initForm: { status: '待确认', normal_hours: 8, overtime_hours: 0, advance_payment: 0, mistake_count: 0 },
  doCreate: api.createContractorWorkLog,
  doUpdate: api.updateContractorWorkLog,
  doDelete: api.deleteContractorWorkLog,
  refresh: () => $table.value?.handleSearch(),
})

function handleModalSave() {
  if (modalAction.value === 'confirm') {
    doConfirm()
  } else {
    handleSave()
  }
}

const statusOptions = [
  { label: '待确认', value: '待确认' },
  { label: '已确认', value: '已确认' },
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
  const res = await api.getContractorStaffList({ page_size: 999 })
  if (res.data) {
    staffOptions.value = res.data.map(s => ({ label: s.name, value: s.id }))
  }
}

function handleConfirm(row) {
  modalForm.value = { id: row.id, mistake_count: 0, confirmed_by_user_id: userStore.userId || 0 }
  modalTitle.value = '确认工作日志'
  modalAction.value = 'confirm'
  modalVisible.value = true
}

async function doConfirm() {
  await api.confirmContractorWorkLog(modalForm.value)
  $message?.success('确认成功')
  modalVisible.value = false
  $table.value?.handleSearch()
}

const columns = [
  { title: '人员', key: 'staff_name', width: 80, align: 'center' },
  { title: '日期', key: 'work_date', width: 100, align: 'center' },
  { title: '下班时间', key: 'check_out_time', width: 80, align: 'center' },
  { title: '打卡截图', key: 'check_out_image', width: 120, align: 'center', render(row) {
    return row.check_out_image
      ? h('img', { src: row.check_out_image, style: 'width:80px;height:60px;object-fit:cover;border-radius:4px;cursor:pointer;', onClick: () => window.open(row.check_out_image, '_blank') })
      : h('span', { style: 'color: #ccc;' }, '-')
  }},
  { title: '垫付证明', key: 'advance_payment_image', width: 120, align: 'center', render(row) {
    return row.advance_payment_image
      ? h('img', { src: row.advance_payment_image, style: 'width:80px;height:60px;object-fit:cover;border-radius:4px;cursor:pointer;', onClick: () => window.open(row.advance_payment_image, '_blank') })
      : h('span', { style: 'color: #ccc;' }, '-')
  }},
  { title: '正常工时', key: 'normal_hours', width: 60, align: 'center' },
  { title: '加班工时', key: 'overtime_hours', width: 60, align: 'center' },
  { title: '工作内容', key: 'work_content', width: 80, align: 'center' },
  { title: '项目', key: 'project_name', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '垫付费用', key: 'advance_payment', width: 80, align: 'center' },
  { title: '请假', key: 'leave_type', width: 80, align: 'center', render(row) {
    return row.leave_type ? h(NTag, { type: 'warning', size: 'small' }, { default: () => row.leave_type }) : '-'
  }},
  { title: '状态', key: 'status', width: 80, align: 'center', render(row) {
    return h(NTag, { type: row.status === '已确认' ? 'success' : 'warning', size: 'small' }, { default: () => row.status })
  }},
  { title: '犯错次数', key: 'mistake_count', width: 60, align: 'center' },
  { title: '操作', key: 'actions', width: 200, align: 'center', fixed: 'right', render(row) {
    const btns = []
    if (row.status === '待确认') {
      btns.push(
        h(NButton, { size: 'small', type: 'success', style: 'margin-right: 8px;', onClick: () => handleConfirm(row) },
          { default: () => '确认' }),
      )
    }
    btns.push(
      withDirectives(h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => handleEdit(row) },
        { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }), [[vPermission, 'post/api/v1/contractor/worklog/update']]),
      h(NPopconfirm, { onPositiveClick: () => handleDelete({ log_id: row.id }) }, {
        trigger: () => withDirectives(h(NButton, { size: 'small', type: 'error' },
          { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }), [[vPermission, 'delete/api/v1/contractor/worklog/delete']]),
        default: () => h('div', {}, '确定删除该日志吗?'),
      }),
    )
    return btns
  }},
]
</script>

<template>
  <CommonPage show-footer title="工作日志审核">
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getContractorWorkLogList">
      <template #queryBar>
        <QueryBarItem label="人员" :label-width="40">
          <NSelect v-model:value="queryItems.staff_id" clearable :options="staffOptions" placeholder="请选择人员" />
        </QueryBarItem>
        <QueryBarItem label="项目" :label-width="40">
          <NSelect v-model:value="queryItems.project_id" clearable :options="projectOptions" placeholder="请选择项目" />
        </QueryBarItem>
        <QueryBarItem label="日期" :label-width="40">
          <NInput v-model:value="queryItems.work_date" clearable placeholder="YYYY-MM-DD" />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
          <NSelect v-model:value="queryItems.status" clearable :options="statusOptions" placeholder="请选择状态" />
        </QueryBarItem>
      </template>
    </CrudTable>
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleModalSave">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="100" :model="modalForm">
        <NFormItem label="犯错次数" path="mistake_count"><NInputNumber v-model:value="modalForm.mistake_count" :min="0" placeholder="请输入当天犯错次数" /></NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
