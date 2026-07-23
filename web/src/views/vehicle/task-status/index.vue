<script setup>
import { onMounted, ref, computed } from 'vue'
import { NTag, NSelect, NInput, NButton, NEmpty, useMessage } from 'naive-ui'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
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
  list.sort((a, b) => (statusOrder[a.task_status] ?? 99) - (statusOrder[b.task_status] ?? 99))
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
  currentVehicle.value = { ...vehicle }
  showDetailModal.value = true
}

function handleResetFilters() {
  filterTaskStatus.value = null
  filterProject.value = null
  filterKeyword.value = ''
}

function onSaved(vehicle) {
  const idx = vehicles.value.findIndex(v => v.id === vehicle.id)
  if (idx !== -1) {
    vehicles.value[idx] = { ...vehicles.value[idx], ...vehicle }
  }
  fetchData()
}

function getStatusType(status) { return statusColorMap[status] || 'default' }

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="task-status-root">
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <div class="filter-left">
          <NSelect v-model:value="filterTaskStatus" :options="taskStatusOptions" placeholder="状态筛选" style="width:130px" />
          <NSelect v-model:value="filterProject" :options="projectOptions" placeholder="项目筛选" filterable style="width:150px" />
          <NInput v-model:value="filterKeyword" placeholder="搜索..." clearable style="width:200px" />
          <NButton text @click="handleResetFilters">重置</NButton>
          <span class="count">{{ filteredVehicles.length }}辆</span>
        </div>
      </div>

      <!-- 状态条 -->
      <div class="status-strip">
        <div v-for="o in taskStatusOptions.filter(x=>x.value)" :key="o.value"
          class="chip" :class="{ active: filterTaskStatus === o.value }"
          @click="filterTaskStatus = filterTaskStatus === o.value ? null : o.value">
          <NTag :type="getStatusType(o.value)" :bordered="false" size="small" round>{{ o.label }}</NTag>
          <span class="chip-n">{{ statusCounts[o.value] || 0 }}</span>
        </div>
      </div>

      <!-- 左右分栏 -->
      <div class="split-layout">
        <!-- 左侧：4列卡片网格 -->
        <div class="left-panel">
          <div v-if="filteredVehicles.length" class="card-grid">
              <div class="v-card" v-for="v in filteredVehicles" :key="v.id"
                :class="{ 'card-fault': v.task_status==='故障或事故', 'card-active': v.task_status==='进行中' }"
                @click="handleCardClick(v)">
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
                </div>
              </div>
          </div>
          <NEmpty v-else description="暂无数据" class="mt-60" />
        </div>

        <!-- 右侧地图 -->
        <div class="right-panel">
          <VehicleMap :markers="mapVehicles" :projectColorMap="projectColorMap" height="100%" />
        </div>
      </div>

      <VehicleTaskDetail v-model:visible="showDetailModal" :vehicle="currentVehicle" @saved="onSaved" />
  </div>
</template>

<style scoped>
.task-status-root { height: 100%; display: flex; flex-direction: column; overflow: hidden; position: relative; }

.filter-bar { display: flex; align-items: center; margin-bottom: 6px; flex-shrink: 0; }
.filter-left { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.count { font-size: 12px; color: #999; }

.status-strip { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 8px; flex-shrink: 0; }
.chip { display: flex; align-items: center; gap: 2px; padding: 1px 7px 1px 2px; border-radius: 12px; background: #f5f6fa; cursor: pointer; border: 1.5px solid transparent; font-size: 11px; }
.chip:hover { background: #edf0f5; }
.chip.active { background: #e8f4fd; border-color: #2080f0; }
.chip-n { font-weight: 600; color: #666; }

.split-layout { flex: 1; display: flex; gap: 0; overflow: hidden; min-height: 0; }

/* 左侧 */
.left-panel { width: 52%; overflow-y: auto; }
.card-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; align-content: start; }

.v-card { background: #fff; border-radius: 8px; border: 1px solid #eef0f4; cursor: pointer; transition: all .15s; display: flex; overflow: hidden; min-height: 100px; }
.v-card:hover { border-color: #c8d0e0; box-shadow: 0 2px 8px rgba(0,0,0,.05); transform: translateY(-1px); }
.card-bar { width: 3px; flex-shrink: 0; }
.card-bar.bar-error { background: #d03050; } .card-bar.bar-info { background: #2080f0; } .card-bar.bar-success { background: #18a058; } .card-bar.bar-default { background: #ccc; }

.card-body { flex: 1; padding: 10px 11px; display: flex; flex-direction: column; gap: 0; min-width: 0; }
.card-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 10px; }
.card-line { display: flex; align-items: center; gap: 4px; font-size: 12px; line-height: 1.8; overflow: hidden; }
.clabel { font-size: 11px; color: #999; min-width: 26px; flex-shrink: 0; }
.cval { font-size: 12px; color: #333; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.c-default { color: #666; } .c-info { color: #2080f0; } .c-success { color: #18a058; } .c-error { color: #d03050; } .c-warning { color: #f0a020; }
.c-dim { font-size: 10px; color: #999; }

/* 右侧地图 */
.right-panel { width: 48%; height: 100%; min-width: 200px; overflow: hidden; padding-right: 3px; }

.mt-60 { margin-top: 60px; }
.wh-full { width: 100%; height: 100%; }
</style>
