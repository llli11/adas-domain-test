<script setup>
import { h, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NCard, NForm, NFormItem, NInput, NInputNumber, NModal, NPopconfirm, NSelect, NSpace, NTabPane, NTabs, NTag, NGrid, NGi } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import api from '@/api'

defineOptions({ name: '人员考核管理' })

const router = useRouter()
const activeTab = ref('record')
const $table = ref(null)
const queryItems = ref({})
const staffOptions = ref([])
const staffScores = ref([])
const loading = ref(false)

// modal for recording mistake/reward
const modalVisible = ref(false)
const modalLoading = ref(false)
const selectedStaff = ref(null)
const modalForm = ref({
  staff_id: null,
  type: 'mistake',
  count: 1,
  record_date: new Date().toISOString().slice(0, 10),
  remark: '',
})
const modalFormRef = ref(null)

const typeOptions = [
  { label: '犯错', value: 'mistake' },
  { label: '奖励', value: 'reward' },
]

onMounted(() => {
  loadStaff()
  loadScores()
})

async function loadStaff() {
  const res = await api.getContractorStaffList({ page_size: 999, status: '在职' })
  if (res.data) {
    staffOptions.value = res.data.map(s => ({ label: s.name, value: s.id }))
  }
}

async function loadScores() {
  loading.value = true
  try {
    const res = await api.getStaffScores()
    if (res.data) {
      staffScores.value = res.data
    }
  } finally {
    loading.value = false
  }
}

function handleOpenModal(staff) {
  selectedStaff.value = staff
  modalForm.value = {
    staff_id: staff.staff_id,
    type: 'mistake',
    count: 1,
    record_date: new Date().toISOString().slice(0, 10),
    remark: '',
  }
  modalVisible.value = true
}

async function handleSave() {
  modalLoading.value = true
  try {
    await api.createAssessment(modalForm.value)
    $message?.success('记录成功')
    modalVisible.value = false
    loadScores()
    if ($table.value) {
      $table.value.handleSearch()
    }
  } finally {
    modalLoading.value = false
  }
}

async function handleTabChange(tab) {
  if (tab === 'detail') {
    await nextTick()
    $table.value?.handleSearch()
  }
}

const detailColumns = [
  { title: '人员', key: 'staff_name', width: 100, align: 'center' },
  { title: '类型', key: 'type', width: 80, align: 'center', render(row) {
    return h(NTag, { type: row.type === 'mistake' ? 'error' : 'success', size: 'small' }, { default: () => row.type === 'mistake' ? '犯错' : '奖励' })
  }},
  { title: '次数', key: 'count', width: 60, align: 'center' },
  { title: '日期', key: 'record_date', width: 100, align: 'center' },
  { title: '备注', key: 'remark', width: 150, align: 'center', ellipsis: { tooltip: true } },
  { title: '记录时间', key: 'created_at', width: 150, align: 'center', render(row) {
    return row.created_at ? row.created_at.slice(0, 19) : '-'
  }},
  { title: '操作', key: 'actions', width: 100, align: 'center', fixed: 'right', render(row) {
    return h(NPopconfirm, { onPositiveClick: () => handleDelete(row) }, {
      trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }),
      default: () => h('div', {}, '确定删除该记录吗?'),
    })
  }},
]

async function handleDelete(row) {
  await api.deleteAssessment({ record_id: row.id })
  $message?.success('删除成功')
  loadScores()
  if ($table.value) {
    $table.value.handleSearch()
  }
}

function getScoreColor(score) {
  if (score >= 10) return 'success'
  if (score >= 9) return 'warning'
  return 'error'
}
</script>

<template>
  <CommonPage show-footer title="人员考核管理">
    <template #action>
      <NButton type="primary" @click="router.push('/contractor/evaluation')">
        查看月度考评
      </NButton>
    </template>
    <NTabs v-model:value="activeTab" type="line" display-directive="show" @update:value="handleTabChange">
      <NTabPane name="record" tab="考评记录">
        <NSpace vertical :size="16" style="width: 100%;">
          <div v-if="loading" style="text-align: center; padding: 40px; color: #999;">加载中...</div>
          <NGrid v-else :cols="4" :x-gap="12" :y-gap="12">
            <NGi v-for="item in staffScores" :key="item.staff_id">
              <NCard size="small" hoverable>
                <template #header>
                  <div style="font-weight: bold; font-size: 14px;">{{ item.staff_name }}</div>
                </template>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 12px; color: #666;">犯错: {{ item.mistake_count }}次</span>
                    <span style="font-size: 12px; color: #666;">奖励: {{ item.reward_count }}次</span>
                  </div>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <NTag :type="getScoreColor(item.score)" size="small" round>
                      得分: {{ item.score.toFixed(1) }}
                    </NTag>
                    <NButton size="small" type="primary" @click="handleOpenModal(item)">
                      记录
                    </NButton>
                  </div>
                </div>
              </NCard>
            </NGi>
          </NGrid>
          <div v-if="!loading && staffScores.length === 0" style="text-align: center; padding: 40px; color: #999;">
            暂无在职人员数据
          </div>
        </NSpace>
      </NTabPane>

      <NTabPane name="detail" tab="明细">
        <CrudTable ref="$table" v-model:query-items="queryItems" :columns="detailColumns" :get-data="api.getAssessmentList">
          <template #queryBar>
            <QueryBarItem label="人员" :label-width="40">
              <NSelect v-model:value="queryItems.staff_id" clearable :options="staffOptions" placeholder="请选择人员" />
            </QueryBarItem>
            <QueryBarItem label="类型" :label-width="40">
              <NSelect v-model:value="queryItems.type" clearable :options="typeOptions" placeholder="请选择类型" />
            </QueryBarItem>
            <QueryBarItem label="日期" :label-width="40">
              <NInput v-model:value="queryItems.record_date" clearable placeholder="YYYY-MM-DD" />
            </QueryBarItem>
          </template>
        </CrudTable>
      </NTabPane>
    </NTabs>

    <!-- 记录弹窗 -->
    <NModal v-model:show="modalVisible" preset="card" title="考核记录" style="width: 480px;" :mask-closable="false">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="80" :model="modalForm">
        <NFormItem label="人员">
          <span>{{ selectedStaff?.staff_name || '' }}</span>
        </NFormItem>
        <NFormItem label="类型" path="type">
          <NSelect v-model:value="modalForm.type" :options="typeOptions" placeholder="请选择类型" />
        </NFormItem>
        <NFormItem label="次数" path="count">
          <NInputNumber v-model:value="modalForm.count" :min="1" placeholder="请输入次数" />
        </NFormItem>
        <NFormItem label="日期" path="record_date">
          <NInput v-model:value="modalForm.record_date" clearable placeholder="YYYY-MM-DD" />
        </NFormItem>
        <NFormItem label="备注" path="remark">
          <NInput v-model:value="modalForm.remark" type="textarea" clearable placeholder="请输入备注" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="modalVisible = false">取消</NButton>
          <NButton type="primary" :loading="modalLoading" @click="handleSave">保存</NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>
