<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NForm, NFormItem, NInput, NSelect, NSpace, NTag } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import api from '@/api'

defineOptions({ name: '考评管理' })

const $table = ref(null)
const queryItems = ref({})
const staffOptions = ref([])

const modalVisible = ref(false)
const modalTitle = ref('评分')
const modalLoading = ref(false)
const modalForm = ref({})
const modalFormRef = ref(null)

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

function handleRate(row) {
  modalForm.value = {
    staff_id: row.staff_id,
    evaluation_month: row.evaluation_month,
    attitude_score: row.attitude_score || 0,
    ability_score: row.ability_score || 0,
    achievement_score: row.achievement_score || 0,
    assessor: '',
  }
  modalTitle.value = '填写质量评分'
  modalVisible.value = true
}

async function handleSave() {
  modalLoading.value = true
  try {
    await api.rateContractorEvaluation(modalForm.value)
    $message?.success('评分成功')
    modalVisible.value = false
    $table.value?.handleSearch()
  } finally {
    modalLoading.value = false
  }
}

function handleGenerate() {
  const month = queryItems.value.evaluation_month || new Date().toISOString().slice(0, 7)
  api.generateContractorEvaluation({ evaluation_month: month }).then(() => {
    $message?.success('考评生成成功')
    $table.value?.handleSearch()
  })
}

const columns = [
  { title: '人员', key: 'staff_name', width: 80, align: 'center' },
  { title: '考核月份', key: 'evaluation_month', width: 100, align: 'center' },
  { title: '工作态度', key: 'attitude_score', width: 80, align: 'center' },
  { title: '工作能力', key: 'ability_score', width: 80, align: 'center' },
  { title: '工作达成', key: 'achievement_score', width: 80, align: 'center' },
  { title: '任务质量', key: 'quality_score', width: 80, align: 'center' },
  { title: '犯错次数', key: 'mistake_total', width: 60, align: 'center' },
  { title: '犯错减分', key: 'mistake_deduction', width: 60, align: 'center' },
  { title: '最终得分', key: 'final_score', width: 80, align: 'center', render(row) {
    return h(NTag, { type: row.final_score >= 8 ? 'success' : row.final_score >= 6 ? 'warning' : 'error', size: 'small' }, { default: () => row.final_score })
  }},
  { title: '考核人', key: 'assessor', width: 80, align: 'center' },
  { title: '操作', key: 'actions', width: 120, align: 'center', fixed: 'right', render(row) {
    return h(NButton, { size: 'small', type: 'primary', onClick: () => handleRate(row) }, { default: () => '评分' })
  }},
]
</script>

<template>
  <CommonPage show-footer title="考评管理">
    <template #action>
      <NButton type="primary" @click="handleGenerate">
        生成本月考评
      </NButton>
    </template>
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getContractorEvaluationList">
      <template #queryBar>
        <QueryBarItem label="人员" :label-width="40">
          <NSelect v-model:value="queryItems.staff_id" clearable :options="staffOptions" placeholder="请选择人员" />
        </QueryBarItem>
        <QueryBarItem label="月份" :label-width="40">
          <NInput v-model:value="queryItems.evaluation_month" clearable placeholder="YYYY-MM" />
        </QueryBarItem>
      </template>
    </CrudTable>
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="100" :model="modalForm">
        <NFormItem label="工作态度" path="attitude_score"><NInput v-model:value="modalForm.attitude_score" clearable placeholder="0-10" /></NFormItem>
        <NFormItem label="工作能力" path="ability_score"><NInput v-model:value="modalForm.ability_score" clearable placeholder="0-10" /></NFormItem>
        <NFormItem label="工作达成" path="achievement_score"><NInput v-model:value="modalForm.achievement_score" clearable placeholder="0-10" /></NFormItem>
        <NFormItem label="考核人" path="assessor"><NInput v-model:value="modalForm.assessor" clearable placeholder="请输入考核人" /></NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
