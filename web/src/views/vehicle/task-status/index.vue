<script setup>
import { onMounted, ref, computed, onBeforeUnmount } from 'vue'
import { NTag, NSelect, NInput, NButton, NEmpty, NSpin, useMessage } from 'naive-ui'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import { isAreaMismatch } from '@/utils/cityProvinceMap'
import { getVehicleDataTimestamp, getAutoSyncEnabled } from '@/utils/vehicleSync'
import { formatRate } from '@/utils/common/common'
import VehicleTaskDetail from './detail.vue'
import VehicleMap from '@/components/common/VehicleMap.vue'

defineOptions({ name: '车辆任务状态' })

const $message = useMessage()
const loading = ref(false)
const vehicles = ref([])
const filterTaskStatus = ref(null)
const filterProject = ref(null)
const filterKeyword = ref('')
const showDetailModal = ref(false)
const currentVehicle = ref(null)
const showMap = ref(true)
const filterDeptL1 = ref('产品验证中心')
const filterDeptL2 = ref('智驾域测试')
const deptL1Options = ref([])
const deptL2Options = ref([])

const projectOptions = computed(() => {
  const set = new Set()
  vehicles.value.forEach(v => { if (v.vehicle_model) set.add(v.vehicle_model) })
  return Array.from(set).map(v => ({ label: v, value: v }))
})

const taskStatusOptions = [
  { label: '全部', value: null }, { label: '待开始', value: '待开始' }, { label: '空', value: '空' },
  { label: '进行中', value: '进行中' }, { label: '已完成', value: '已完成' }, { label: '故障或事故', value: '故障或事故' },
]

const statusColorMap = { '待开始': 'default', '空': 'default', '进行中': 'info', '已完成': 'success', '故障或事故': 'error' }
const statusOrder = { '故障或事故': 0, '进行中': 1, '待开始': 2, '已完成': 3, '空': 4 }

// 项目颜色
const PROJECT_COLORS = ['#2080f0','#18a058','#f0a020','#d03050','#7c3aed','#0891b2','#ea580c','#4f46e5','#0d9488','#be185d']
function getProjectColor(name) {
  if (!name) return '#333'
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return PROJECT_COLORS[Math.abs(hash) % PROJECT_COLORS.length]
}

// 日期状态 badge
function getDateBadge(dateStr) {
  if (!dateStr) return null
  const d = new Date(dateStr); if (isNaN(d.getTime())) return null
  const today = new Date(); today.setHours(0,0,0,0)
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const diff = Math.ceil((target - today) / 86400000)
  if (diff < 0) return { type: 'expired', label: '已过期', color: '#d03050', bg: '#FFF1F0' }
  if (diff <= 7) return { type: 'warning', label: '即将到期', color: '#f0a020', bg: '#FFF7E6' }
  return null
}

// 利用率颜色
function getRateColor(rate) {
  if (rate == null) return '#999'
  const n = Number(rate)
  if (isNaN(n)) return '#999'
  const pct = n < 1 ? n * 100 : n
  if (pct <= 10) return '#FF4D4F'
  if (pct < 50) return '#FA8C16'
  return '#52C41A'
}


const filteredVehicles = computed(() => {
  let list = [...vehicles.value]
  if (filterTaskStatus.value) list = list.filter(v => v.task_status === filterTaskStatus.value)
  if (filterProject.value) list = list.filter(v => v.vehicle_model === filterProject.value)
  if (filterKeyword.value) {
    const kw = filterKeyword.value.toLowerCase()
    list = list.filter(v =>
      (v.vehicle_code && v.vehicle_code.toLowerCase().includes(kw)) ||
      (v.vn && v.vn.toLowerCase().includes(kw)) ||
      (v.borrower && v.borrower.toLowerCase().includes(kw)) ||
      (v.vehicle_model && v.vehicle_model.toLowerCase().includes(kw))
    )
  }
  if (filterDeptL1.value) list = list.filter(v => v.dept_l1 === filterDeptL1.value)
  if (filterDeptL2.value) list = list.filter(v => v.dept_l2 === filterDeptL2.value)
  // 排序：填充字段数（状态/任务/测试/驾驶）从高到低，项目名称从低到高
  list.sort((a, b) => {
    const countA = [a.task_status, a.test_task, a.tester, a.driver].filter(v => v && v !== '空').length
    const countB = [b.task_status, b.test_task, b.tester, b.driver].filter(v => v && v !== '空').length
    if (countB !== countA) return countB - countA
    return (a.vehicle_model || '').localeCompare(b.vehicle_model || '', 'zh')
  })
  return list
})

// 地图数据：排除状态筛选，地图始终与重置后一致（只受项目/搜索影响）
const mapVehicles = computed(() => {
  let list = [...vehicles.value]
  if (filterProject.value) list = list.filter(v => v.vehicle_model === filterProject.value)
  if (filterKeyword.value) {
    const kw = filterKeyword.value.toLowerCase()
    list = list.filter(v =>
      (v.vehicle_code && v.vehicle_code.toLowerCase().includes(kw)) ||
      (v.vn && v.vn.toLowerCase().includes(kw)) ||
      (v.borrower && v.borrower.toLowerCase().includes(kw)) ||
      (v.vehicle_model && v.vehicle_model.toLowerCase().includes(kw))
    )
  }
  if (filterDeptL1.value) list = list.filter(v => v.dept_l1 === filterDeptL1.value)
  if (filterDeptL2.value) list = list.filter(v => v.dept_l2 === filterDeptL2.value)
  return list.filter(v => v.latitude && v.longitude && v.latitude !== 0 && v.longitude !== 0)
})

// 所有有坐标车辆 → 车型项目颜色映射
const allCoordsVehicles = computed(() =>
  vehicles.value.filter(v => v.latitude && v.longitude && v.latitude !== 0 && v.longitude !== 0)
)

const projectColorMap = computed(() => {
  const projects = [...new Set(allCoordsVehicles.value.map(v => v.vehicle_model).filter(Boolean))]
  const palette = ['#2080f0','#18a058','#f0a020','#d03050','#7c3aed','#0891b2','#ea580c','#4f46e5','#0d9488','#be185d']
  const map = {}
  projects.forEach((p, i) => { map[p] = palette[i % palette.length] })
  return map
})

const statusCounts = computed(() => {
  const counts = {}
  vehicles.value.forEach(v => { const s = v.task_status || '未知'; counts[s] = (counts[s] || 0) + 1 })
  return counts
})

async function fetchData() {
  loading.value = true
  try {
    const res = await api.getVehicleList({ page: 1, page_size: 9999 })
    vehicles.value = res.data || []
    const d1s = new Set(), d2s = new Set()
    vehicles.value.forEach(v => { if (v.dept_l1) d1s.add(v.dept_l1); if (v.dept_l2) d2s.add(v.dept_l2) })
    deptL1Options.value = [...d1s].sort().map(v => ({ label: v, value: v }))
    deptL2Options.value = [...d2s].sort().map(v => ({ label: v, value: v }))
  } catch (e) {
    console.error('获取车辆数据失败', e)
  } finally {
    loading.value = false
  }
}

function handleCardClick(vehicle) {
  // 点击同一张卡片：关闭详情
  if (currentVehicle.value?.id === vehicle.id && showDetailModal.value) {
    showDetailModal.value = false
    currentVehicle.value = null
    return
  }
  // 仅左键点击，且有文字选中时不触发（避免复制文字误入）
  if (window.getSelection()?.toString()) return
  currentVehicle.value = { ...vehicle }
  showDetailModal.value = true
}

function handleResetFilters() {
  filterTaskStatus.value = null
  filterProject.value = null
  filterKeyword.value = ''
  filterDeptL1.value = '产品验证中心'
  filterDeptL2.value = '智驾域测试'
}

function onSaved(vehicle) {
  const idx = vehicles.value.findIndex(v => v.id === vehicle.id)
  if (idx !== -1) {
    vehicles.value[idx] = { ...vehicles.value[idx], ...vehicle }
  }
}

function getStatusType(status) { return statusColorMap[status] || 'default' }
function getStatusColor(status) {
  const map = { '故障或事故':'#d03050','进行中':'#2080f0','待开始':'#f0a020','已完成':'#18a058','空':'#909399' }
  return map[status] || '#909399'
}

const syncing = ref(false)
let pollTimer = null

async function autoSyncFromFeishu() {
  if (!getAutoSyncEnabled()) return
  syncing.value = true
  try {
    // 触发后台同步
    await api.syncFromFeishu()
    // 轮询等待结果（最多 60 次 × 5 秒 = 5 分钟）
    for (let i = 0; i < 60; i++) {
      await new Promise(r => setTimeout(r, 5000))
      const status = await api.getSyncStatus()
      const result = status?.data
      if (result && !result.running) {
        if (result.success) {
          $message.success(`[From Feishu] ${result.message || '同步完成'}`)
        }
        break
      }
    }
  } catch (e) {
    console.warn('[Feishu] 同步异常:', e?.message || e)
  } finally {
    syncing.value = false
  }
}

onMounted(() => {
  autoSyncFromFeishu()
  fetchData()
  pollTimer = setInterval(() => {
    fetchData()
  }, 30000)
})

onBeforeUnmount(() => {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  showDetailModal.value = false
  currentVehicle.value = null
})
</script>

<template>
  <div class="task-status-root">
      <!-- 第一层（详情打开时隐藏） -->
      <Transition name="layer-fade">
      <div v-if="!showDetailModal">
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <div class="filter-left">
          <NSelect v-model:value="filterDeptL1" :options="deptL1Options" placeholder="一级部门" clearable filterable style="width:140px" />
          <NSelect v-model:value="filterDeptL2" :options="deptL2Options" placeholder="二级部门" clearable filterable style="width:140px" />
          <NSelect v-model:value="filterProject" :options="projectOptions" placeholder="项目筛选" filterable style="width:150px" />
          <NSelect v-model:value="filterTaskStatus" :options="taskStatusOptions" placeholder="状态筛选" style="width:130px" />
          <NInput v-model:value="filterKeyword" placeholder="搜索..." clearable style="width:200px" />
          <span class="count">{{ filteredVehicles.length }}辆</span>
          <NButton text size="small" @click="handleResetFilters">重置</NButton>
          <NButton size="small" :type="showMap ? 'primary' : 'default'" @click="showMap = !showMap" style="flex-shrink:0">
            <template #icon><TheIcon :icon="showMap ? 'material-symbols:map' : 'material-symbols:map-outline'" :size="16" /></template>
            {{ showMap ? '隐藏地图' : '显示地图' }}
          </NButton>
          <span v-if="syncing" style="display:inline-flex;align-items:center;gap:4px;color:#2e7d32;font-size:12px;white-space:nowrap"><NSpin size="small" /> 同步中…</span>
        </div>
        <div class="status-strip-inline">
          <div v-for="o in taskStatusOptions.filter(x=>x.value)" :key="o.value"
            class="chip" :class="{ active: filterTaskStatus === o.value }"
            @click="filterTaskStatus = filterTaskStatus === o.value ? null : o.value">
            <NTag :type="getStatusType(o.value)" :bordered="false" size="small" round>{{ o.label }}</NTag>
            <span class="chip-n">{{ statusCounts[o.value] || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- 左右分栏 -->
      <div class="split-layout" :class="{ 'no-map': !showMap }">
        <div class="left-panel">
          <div v-if="filteredVehicles.length" class="card-grid" :class="showMap ? 'card-grid-3' : 'card-grid-6'">
              <div class="v-card" v-for="v in filteredVehicles" :key="v.id"
                :class="{ 'card-fault': v.task_status==='故障或事故', 'card-active': v.task_status==='进行中' }"
                @click.left="handleCardClick(v)">
                <div class="card-bar" :class="'bar-'+((statusColorMap[v.task_status]||'default'))" />
                <div class="card-body">
                  <div class="card-grid-2">
                    <div class="card-line"><span class="clabel">项目</span><span class="cval">{{ v.vehicle_model||'--' }}</span></div>
                    <div class="card-line"><span class="clabel">编号</span><span class="cval">{{ v.vehicle_code||v.vn||'--' }}</span></div>
                    <div class="card-line"><span class="clabel">状态</span><NTag :type="getStatusType(v.task_status)" :bordered="false" size="small" round>{{ v.task_status||'--' }}</NTag></div>
                    <div class="card-line"><span class="clabel">任务</span><span class="cval" :class="'c-'+getStatusType(v.task_status)">{{ v.test_task||'--' }}</span></div>
                    <div class="card-line"><span class="clabel">测试</span><span class="cval">{{ v.tester||'--' }}</span></div>
                    <div class="card-line"><span class="clabel">驾驶</span><span class="cval">{{ v.driver||'--' }}</span></div>
                  </div>
                  <div class="card-extras">
                    <div class="card-line"><span class="clabel">城市</span><span class="cval">{{ v.test_city||'--' }}</span></div>
                    <div class="card-line card-full"><span class="clabel">临牌区域</span><span class="cval cval-2line">{{ v.temp_plate_area||'--' }}</span></div>
                    <div class="card-line card-full"><span class="clabel">借用到期</span><span class="cval cval-wrap">{{ v.borrow_expire_date||'--' }}</span></div>
                  </div>
                  <div class="card-badges">
                    <span class="badge badge-fault" v-if="v.task_status==='故障或事故'">故障或事故</span>
                    <span class="badge badge-mismatch" v-if="isAreaMismatch(v)">区域不匹配</span>
                    <span class="badge" v-if="getDateBadge(v.borrow_expire_date)" :style="{background:getDateBadge(v.borrow_expire_date).bg,color:getDateBadge(v.borrow_expire_date).color}">
                      归还{{ getDateBadge(v.borrow_expire_date).label }}
                    </span>
                    <span class="badge" v-if="getDateBadge(v.temp_plate_expire_date)" :style="{background:getDateBadge(v.temp_plate_expire_date).bg,color:getDateBadge(v.temp_plate_expire_date).color}">
                      临保{{ getDateBadge(v.temp_plate_expire_date).label }}
                    </span>
                    <span class="badge badge-rate" v-if="v.borrower_7day_rate != null" :style="{ background: getRateColor(v.borrower_7day_rate) }">
                      利用率 {{ formatRate(v.borrower_7day_rate) }}
                    </span>
                  </div>
                </div>
              </div>
          </div>
          <NEmpty v-else description="暂无数据" class="mt-60" />
        </div>

        <!-- 右侧地图 -->
        <div v-if="showMap" class="right-panel">
          <VehicleMap :markers="mapVehicles" :projectColorMap="projectColorMap" height="100%" @marker-click="handleCardClick" />
        </div>
      </div>
      </div>
      </Transition>

      <VehicleTaskDetail v-model:visible="showDetailModal" :vehicle="currentVehicle" @saved="onSaved" @close="showDetailModal = false; currentVehicle = null" />
  </div>
</template>

<style scoped>
.task-status-root { height: 100%; display: flex; flex-direction: column; overflow: hidden; position: relative; }
.task-status-root > :deep(.layer-fade-enter-active),
.task-status-root > :deep(.layer-fade-leave-active),
.task-status-root > div { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.layer-fade-enter-active, .layer-fade-leave-active { transition: opacity 0.15s ease; }
.layer-fade-enter-from, .layer-fade-leave-to { opacity: 0; }

.filter-bar { display: flex; align-items: center; margin-bottom: 6px; flex-shrink: 0; gap: 8px; }
.filter-left { display: flex; gap: 8px; align-items: center; }
.filter-right { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }
.filter-left { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.filter-right { display: flex; gap: 8px; align-items: center; }
.count { font-size: 12px; color: #999; white-space: nowrap; }

.status-strip-inline { display: flex; gap: 4px; flex-wrap: wrap; margin-left: auto; }
.chip { display: flex; align-items: center; gap: 2px; padding: 1px 7px 1px 2px; border-radius: 12px; background: #f5f6fa; cursor: pointer; border: 1.5px solid transparent; font-size: 11px; }
.chip:hover { background: #edf0f5; }
.chip.active { background: #e8f4fd; border-color: #2080f0; }
.chip-n { font-weight: 600; color: #666; }

.split-layout { flex: 1; display: flex; gap: 0; min-height: 0; overflow: hidden; }
.split-layout.no-map .left-panel { flex: 1; width: auto; }

/* 左侧 */
.left-panel { width: 52%; overflow-y: auto; }
.card-grid { display: grid; gap: 8px; align-content: start; grid-auto-rows: 1fr; }
.card-grid-3 { grid-template-columns: repeat(3, 1fr); }
.card-grid-6 { grid-template-columns: repeat(6, 1fr); }

.v-card { background: #fff; border-radius: 10px; border: 1.5px solid #e0e0e0; cursor: pointer; display: flex; overflow: hidden; min-height: 140px; }
.v-card:hover { border-color: #c8d0e0; box-shadow: 0 2px 8px rgba(0,0,0,.05); }
.card-bar { width: 4px; flex-shrink: 0; }
.card-bar.bar-error { background: #d03050; } .card-bar.bar-info { background: #2080f0; } .card-bar.bar-success { background: #18a058; } .card-bar.bar-default { background: #ccc; }

.card-body { flex: 1; padding: 10px 11px; display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.card-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 10px; min-height: 80px; }
.card-line { display: flex; align-items: center; gap: 4px; font-size: 12px; line-height: 1.8; overflow: hidden; }
.clabel { font-size: 11px; color: #54698b; min-width: 40px; flex-shrink: 0; }
.cval { font-size: 12px; color: #333; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cval-wrap { white-space: normal; word-break: break-all; overflow: visible; }
.cval-2line { min-height: 4.2em; max-height: 4.2em; overflow: hidden; white-space: normal; word-break: break-all; }
.card-area { white-space: normal; word-break: break-all; }

/* 额外信息行 */
.card-extras { border-top: 1px solid #f0f0f0; margin-top: 4px; padding-top: 4px; display: flex; flex-direction: column; gap: 1px; }
.card-full { width: 100%; }

/* badge 行 */
.card-badges { display: flex; flex-wrap: wrap; gap: 3px; min-height: 48px; align-content: flex-start; margin-top: auto; padding-top: 4px; border-top: 1px solid #f0f0f0; }
.badge { font-size: 10px; padding: 2px 6px; border-radius: 3px; font-weight: 600; line-height: 1.6; border: 1px solid transparent; }
.badge-fault { background: #FFF1F0; color: #FF4D4F; border-color: #FF4D4F; }
.badge-mismatch { background: #FFF7E6; color: #FA8C16; border-color: #FA8C16; }
.badge-rate { color: #fff !important; font-weight: 700; border: none; }

/* 右侧地图 */
.right-panel { width: 48%; height: 100%; min-width: 200px; overflow: hidden; }

.mt-60 { margin-top: 60px; }
.wh-full { width: 100%; height: 100%; }
</style>
