<script setup>
import { computed, h, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NDivider, NForm, NFormItem, NInput, NInputNumber, NModal, NSelect, NSpace, NTag } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import api from '@/api'

defineOptions({ name: '考评管理' })

const router = useRouter()
const $table = ref(null)
const queryItems = ref({})
const staffOptions = ref([])

// 生成近12个月的月份选项
const now = new Date()
const monthOptions = []
for (let i = 11; i >= 0; i--) {
  const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
  const val = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  monthOptions.push({ label: val, value: val })
}

const modalVisible = ref(false)
const modalTitle = ref('评分')
const modalLoading = ref(false)
const modalForm = ref({})
const modalFormRef = ref(null)

onMounted(async () => {
  await nextTick()
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
  modalTitle.value = `评分 - ${row.staff_name} (${row.evaluation_month})`
  modalVisible.value = true
}

async function handleSave() {
  modalLoading.value = true
  try {
    const res = await api.rateContractorEvaluation(modalForm.value)
    $message?.success(`评分成功，最终得分: ${res.data?.final_score || '—'}`)
    modalVisible.value = false
    $table.value?.handleSearch()
  } finally {
    modalLoading.value = false
  }
}

// 图表弹窗
const chartVisible = ref(false)
const chartMonth = ref('')
const chartData = ref([])

// SVG 布局常量
const CHART_W = 800
const CHART_H = 360
const PAD_L = 60
const PAD_R = 30
const PAD_T = 20
const PAD_B = 80
const plotW = CHART_W - PAD_L - PAD_R
const plotH = CHART_H - PAD_T - PAD_B

const chartPoints = computed(() => {
  const list = chartData.value
  if (!list.length) return []
  const n = list.length
  return list.map((item, i) => {
    const x = PAD_L + (n === 1 ? plotW / 2 : i * plotW / (n - 1))
    const score = Number(item.final_score) || 0
    const y = PAD_T + plotH * (1 - score / 10)
    return { x, y, ...item }
  })
})

const chartPolyline = computed(() => {
  return chartPoints.value.map(p => `${p.x},${p.y}`).join(' ')
})

const yTicks = computed(() => {
  const ticks = []
  for (let v = 0; v <= 10; v += 2) {
    ticks.push({ value: v, y: PAD_T + plotH * (1 - v / 10) })
  }
  return ticks
})

async function handleGenerate() {
  const month = queryItems.value.evaluation_month || new Date().toISOString().slice(0, 7)
  await api.generateContractorEvaluation({ evaluation_month: month })
  $message?.success('考评生成成功')
  $table.value?.handleSearch()

  // 拉取当月数据用于图表
  const res = await api.getContractorEvaluationList({ evaluation_month: month, page_size: 999 })
  if (res.data && res.data.length > 0) {
    chartData.value = [...res.data].sort((a, b) => (Number(a.final_score) || 0) - (Number(b.final_score) || 0))
    chartMonth.value = month
    chartVisible.value = true
  } else {
    $message?.warning('该月份暂无考评数据')
  }
}

function goToAssessment(staffId) {
  router.push({ path: '/contractor/assessment' })
}

const columns = [
  { title: '人员', key: 'staff_name', width: 80, align: 'center' },
  { title: '考核月份', key: 'evaluation_month', width: 100, align: 'center' },
  { title: '当月犯错', key: 'mistake_total', width: 70, align: 'center', render(row) {
    return h('span', { style: row.mistake_total > 0 ? 'color: #d03050; font-weight: bold;' : 'color: #999;' }, row.mistake_total || 0)
  }},
  { title: '犯错减分', key: 'mistake_deduction', width: 70, align: 'center', render(row) {
    const v = Number(row.mistake_deduction) || 0
    return h('span', { style: 'color: #d03050;' }, `-${v.toFixed(1)}`)
  }},
  { title: '当月奖励', key: 'reward_total', width: 70, align: 'center', render(row) {
    return h('span', { style: row.reward_total > 0 ? 'color: #18a058; font-weight: bold;' : 'color: #999;' }, row.reward_total || 0)
  }},
  { title: '奖励加分', key: 'reward_bonus', width: 70, align: 'center', render(row) {
    const v = Number(row.reward_bonus) || 0
    return h('span', { style: 'color: #18a058;' }, `+${v.toFixed(1)}`)
  }},
  { title: '考核得分', key: 'quality_score', width: 80, align: 'center', render(row) {
    const s = row.quality_score
    return h(NTag, { type: s >= 10 ? 'success' : s >= 8 ? 'warning' : 'error', size: 'small' }, { default: () => (s ?? 10).toFixed(1) })
  }},
  { title: '主观评分', key: 'subjective', width: 90, align: 'center', render(row) {
    const a = Number(row.attitude_score) || 0
    const b = Number(row.ability_score) || 0
    const c = Number(row.achievement_score) || 0
    if (a + b + c === 0) return h('span', { style: 'color: #999;' }, '未评')
    const avg = ((a + b + c) / 3).toFixed(1)
    return h('span', {}, `态${a}/能${b}/达${c} (均${avg})`)
  }},
  { title: '最终得分', key: 'final_score', width: 80, align: 'center', render(row) {
    const s = Number(row.final_score)
    if (!s && s !== 0) return h('span', { style: 'color: #999;' }, '—')
    return h(NTag, { type: s >= 8 ? 'success' : s >= 6 ? 'warning' : 'error', size: 'small' }, { default: () => s.toFixed(1) })
  }},
  { title: '考核人', key: 'assessor', width: 70, align: 'center' },
  { title: '操作', key: 'actions', width: 160, align: 'center', fixed: 'right', render(row) {
    return h(NSpace, { justify: 'center' }, {
      default: () => [
        h(NButton, { size: 'small', type: 'primary', onClick: () => handleRate(row) }, { default: () => '评分' }),
        h(NButton, { size: 'small', onClick: () => goToAssessment(row.staff_id) }, { default: () => '考核明细' }),
      ]
    })
  }},
]
</script>

<template>
  <CommonPage show-footer title="考评管理">
    <template #action>
      <NSpace>
        <NButton type="primary" @click="handleGenerate">
          生成本月考评
        </NButton>
      </NSpace>
    </template>
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getContractorEvaluationList">
      <template #queryBar>
        <QueryBarItem label="人员" :label-width="40">
          <NSelect v-model:value="queryItems.staff_id" clearable filterable :options="staffOptions" placeholder="输入姓名搜索" @update:value="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="月份" :label-width="40">
          <NSelect v-model:value="queryItems.evaluation_month" clearable filterable :options="monthOptions" placeholder="输入月份筛选" @update:value="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <template #default>
        <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="100" :model="modalForm">
          <NFormItem label="工作态度" path="attitude_score">
            <NInputNumber v-model:value="modalForm.attitude_score" :min="0" :max="10" :step="0.5" placeholder="0-10" style="width: 100%" />
          </NFormItem>
          <NFormItem label="工作能力" path="ability_score">
            <NInputNumber v-model:value="modalForm.ability_score" :min="0" :max="10" :step="0.5" placeholder="0-10" style="width: 100%" />
          </NFormItem>
          <NFormItem label="工作达成" path="achievement_score">
            <NInputNumber v-model:value="modalForm.achievement_score" :min="0" :max="10" :step="0.5" placeholder="0-10" style="width: 100%" />
          </NFormItem>
          <NDivider />
          <div style="font-size: 12px; color: #999; line-height: 1.8;">
            最终得分 = 考核得分(来自加减分记录) × 60% + 主观评分均值 × 40%
          </div>
          <NFormItem label="考核人" path="assessor">
            <NInput v-model:value="modalForm.assessor" clearable placeholder="请输入考核人" />
          </NFormItem>
        </NForm>
      </template>
    </CrudModal>
    <!-- 月度考评图表弹窗 -->
    <NModal v-model:show="chartVisible" preset="card" title="月度考评可视图" style="width: 880px;" :mask-closable="false">
      <div v-if="chartData.length" style="text-align: center;">
        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">{{ chartMonth }} 各人员最终得分（由低到高）</div>
        <svg :viewBox="`0 0 ${CHART_W} ${CHART_H}`" width="100%" style="max-height: 380px;">
          <!-- Y轴网格线 -->
          <line v-for="t in yTicks" :key="'g'+t.value" :x1="PAD_L" :y1="t.y" :x2="CHART_W - PAD_R" :y2="t.y" stroke="#e8e8e8" stroke-width="1" />
          <line :x1="PAD_L" :y1="PAD_T" :x2="PAD_L" :y2="CHART_H - PAD_B" stroke="#ccc" stroke-width="1" />
          <line :x1="PAD_L" :y1="CHART_H - PAD_B" :x2="CHART_W - PAD_R" :y2="CHART_H - PAD_B" stroke="#ccc" stroke-width="1" />
          <!-- Y轴刻度 -->
          <text v-for="t in yTicks" :key="'y'+t.value" :x="PAD_L - 8" :y="t.y + 5" text-anchor="end" font-size="12" fill="#999">{{ t.value }}</text>
          <!-- 折线 -->
          <polyline :points="chartPolyline" fill="none" stroke="#2080f0" stroke-width="2.5" stroke-linejoin="round" />
          <!-- 数据点 & 标签 -->
          <template v-for="(p, i) in chartPoints" :key="i">
            <circle :cx="p.x" :cy="p.y" r="5" fill="#fff" stroke="#2080f0" stroke-width="2.5" />
            <text :x="p.x" :y="p.y - 10" text-anchor="middle" font-size="11" font-weight="bold" :fill="(Number(p.final_score) || 0) >= 8 ? '#18a058' : (Number(p.final_score) || 0) >= 6 ? '#f0a020' : '#d03050'">{{ (Number(p.final_score) || 0).toFixed(1) }}</text>
            <text :x="p.x" :y="CHART_H - PAD_B + 16" text-anchor="middle" font-size="11" fill="#333">{{ p.staff_name }}</text>
          </template>
        </svg>
      </div>
      <div v-else style="text-align: center; padding: 60px; color: #999;">暂无数据</div>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="chartVisible = false">关闭</NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>
