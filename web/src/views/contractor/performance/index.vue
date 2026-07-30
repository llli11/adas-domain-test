<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NPopconfirm } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '绩效管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const { modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef, handleEdit, handleDelete, handleAdd } = useCRUD({
  name: '绩效',
  initForm: {},
  doCreate: api.createContractorPerformance,
  doUpdate: api.updateContractorPerformance,
  doDelete: api.deleteContractorPerformance,
  refresh: () => $table.value?.handleSearch(),
})

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  { title: '人员姓名', key: 'staff_name', width: 80, align: 'center' },
  { title: '考核周期', key: 'assessment_period', width: 80, align: 'center' },
  { title: '质量评分', key: 'quality_score', width: 60, align: 'center' },
  { title: '效率评分', key: 'efficiency_score', width: 60, align: 'center' },
  { title: '协作评分', key: 'teamwork_score', width: 60, align: 'center' },
  { title: '综合评分', key: 'overall_score', width: 60, align: 'center' },
  { title: '考核人', key: 'assessor', width: 60, align: 'center' },
  { title: '操作', key: 'actions', width: 120, align: 'center', fixed: 'right', render(row) {
    return [
      withDirectives(h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => handleEdit(row) },
        { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }), [[vPermission, 'post/api/v1/contractor/performance/update']]),
      h(NPopconfirm, { onPositiveClick: () => handleDelete({ performance_id: row.id }) }, {
        trigger: () => withDirectives(h(NButton, { size: 'small', type: 'error', style: 'margin-right: 8px;' },
          { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }), [[vPermission, 'delete/api/v1/contractor/performance/delete']]),
        default: () => h('div', {}, '确定删除该绩效记录吗?'),
      }),
    ]
  }},
]

const rules = {
  staff_id: [{ required: true, message: '请输入人员ID', trigger: ['input', 'blur'] }],
  assessment_period: [{ required: true, message: '请输入考核周期', trigger: ['input', 'blur'] }],
}
</script>

<template>
  <CommonPage show-footer :show-header="false" title="绩效管理">
    <template #action>
      <NButton v-permission="'post/api/v1/contractor/performance/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新增绩效
      </NButton>
    </template>
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getContractorPerformanceList">
      <template #queryBar>
        <QueryBarItem label="人员ID" :label-width="50">
          <NInput v-model:value="queryItems.staff_id" clearable placeholder="请输入人员ID" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="考核周期" :label-width="60">
          <NInput v-model:value="queryItems.assessment_period" clearable placeholder="YYYY-MM" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="100" :model="modalForm" :rules="rules">
        <NFormItem label="人员ID" path="staff_id"><NInput v-model:value="modalForm.staff_id" clearable placeholder="请输入人员ID" /></NFormItem>
        <NFormItem label="考核周期" path="assessment_period"><NInput v-model:value="modalForm.assessment_period" clearable placeholder="YYYY-MM" /></NFormItem>
        <NFormItem label="质量评分" path="quality_score"><NInput v-model:value="modalForm.quality_score" clearable placeholder="0-100" /></NFormItem>
        <NFormItem label="效率评分" path="efficiency_score"><NInput v-model:value="modalForm.efficiency_score" clearable placeholder="0-100" /></NFormItem>
        <NFormItem label="协作评分" path="teamwork_score"><NInput v-model:value="modalForm.teamwork_score" clearable placeholder="0-100" /></NFormItem>
        <NFormItem label="综合评分" path="overall_score"><NInput v-model:value="modalForm.overall_score" clearable placeholder="0-100" /></NFormItem>
        <NFormItem label="评语" path="comment"><NInput v-model:value="modalForm.comment" type="textarea" clearable placeholder="请输入评语" /></NFormItem>
        <NFormItem label="考核人" path="assessor"><NInput v-model:value="modalForm.assessor" clearable placeholder="请输入考核人" /></NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
