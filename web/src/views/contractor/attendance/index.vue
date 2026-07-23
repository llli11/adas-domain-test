<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NSelect, NPopconfirm } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '考勤管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const { modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef, handleEdit, handleDelete, handleAdd } = useCRUD({
  name: '考勤',
  initForm: { status: '正常' },
  doCreate: api.createContractorAttendance,
  doUpdate: api.updateContractorAttendance,
  doDelete: api.deleteContractorAttendance,
  refresh: () => $table.value?.handleSearch(),
})

const statusOptions = [
  { label: '正常', value: '正常' },
  { label: '迟到', value: '迟到' },
  { label: '早退', value: '早退' },
  { label: '缺勤', value: '缺勤' },
  { label: '请假', value: '请假' },
]

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  { title: '人员姓名', key: 'staff_name', width: 80, align: 'center' },
  { title: '日期', key: 'date', width: 80, align: 'center' },
  { title: '签到时间', key: 'check_in', width: 80, align: 'center' },
  { title: '签退时间', key: 'check_out', width: 80, align: 'center' },
  { title: '工作时长', key: 'work_hours', width: 60, align: 'center' },
  { title: '状态', key: 'status', width: 60, align: 'center', render(row) {
    const typeMap = { 正常: 'success', 迟到: 'warning', 早退: 'warning', 缺勤: 'error', 请假: 'info' }
    return h(NTag, { type: typeMap[row.status] || 'default', size: 'small' }, { default: () => row.status })
  }},
  { title: '打卡地点', key: 'location', width: 100, align: 'center', ellipsis: { tooltip: true } },
  { title: '操作', key: 'actions', width: 120, align: 'center', fixed: 'right', render(row) {
    return [
      withDirectives(h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => handleEdit(row) },
        { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }), [[vPermission, 'post/api/v1/contractor/attendance/update']]),
      h(NPopconfirm, { onPositiveClick: () => handleDelete({ attendance_id: row.id }) }, {
        trigger: () => withDirectives(h(NButton, { size: 'small', type: 'error', style: 'margin-right: 8px;' },
          { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }), [[vPermission, 'delete/api/v1/contractor/attendance/delete']]),
        default: () => h('div', {}, '确定删除该考勤记录吗?'),
      }),
    ]
  }},
]

const rules = {
  staff_id: [{ required: true, message: '请输入人员ID', trigger: ['input', 'blur'] }],
  date: [{ required: true, message: '请输入日期', trigger: ['input', 'blur'] }],
}
</script>

<template>
  <CommonPage show-footer title="考勤管理">
    <template #action>
      <NButton v-permission="'post/api/v1/contractor/attendance/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新增考勤
      </NButton>
    </template>
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getContractorAttendanceList">
      <template #queryBar>
        <QueryBarItem label="人员ID" :label-width="50">
          <NInput v-model:value="queryItems.staff_id" clearable placeholder="请输入人员ID" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="日期" :label-width="40">
          <NInput v-model:value="queryItems.date" clearable placeholder="YYYY-MM-DD" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
          <NSelect v-model:value="queryItems.status" clearable :options="statusOptions" placeholder="请选择状态" />
        </QueryBarItem>
      </template>
    </CrudTable>
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="100" :model="modalForm" :rules="rules">
        <NFormItem label="人员ID" path="staff_id"><NInput v-model:value="modalForm.staff_id" clearable placeholder="请输入人员ID" /></NFormItem>
        <NFormItem label="日期" path="date"><NInput v-model:value="modalForm.date" clearable placeholder="YYYY-MM-DD" /></NFormItem>
        <NFormItem label="签到时间" path="check_in"><NInput v-model:value="modalForm.check_in" clearable placeholder="09:00" /></NFormItem>
        <NFormItem label="签退时间" path="check_out"><NInput v-model:value="modalForm.check_out" clearable placeholder="18:00" /></NFormItem>
        <NFormItem label="工作时长" path="work_hours"><NInput v-model:value="modalForm.work_hours" clearable placeholder="8" /></NFormItem>
        <NFormItem label="状态" path="status"><NSelect v-model:value="modalForm.status" :options="statusOptions" placeholder="请选择状态" /></NFormItem>
        <NFormItem label="打卡地点" path="location"><NInput v-model:value="modalForm.location" clearable placeholder="请输入打卡地点" /></NFormItem>
        <NFormItem label="备注" path="remark"><NInput v-model:value="modalForm.remark" type="textarea" clearable placeholder="请输入备注" /></NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
