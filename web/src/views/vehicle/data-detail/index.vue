<script setup>
import { onMounted, ref, h } from 'vue'
import { useRouter } from 'vue-router'
import {
  NDataTable,
  NButton,
  NTag,
  NInput,
  NSelect,
  NSpace,
  NPagination,
  NEmpty,
  NSpin,
  useMessage,
  NForm,
  NFormItem,
  NGrid,
  NGi,
  NDatePicker,
} from 'naive-ui'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '车辆数据详情' })

const router = useRouter()
const $message = useMessage()

// 表格数据
const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const pageSize = ref(20)
const itemCount = ref(0)

// 详情视图（点击行 / 点击编辑按钮 统一行为）
const showDetail = ref(false)
const selectedVehicle = ref(null)

// 内联详情编辑模式
const editMode = ref(false)
const isCreating = ref(false)  // 新增模式 vs 编辑模式
const editForm = ref({})
const saving = ref(false)

// 搜索条件
const searchVN = ref('')
const searchBorrower = ref('')
const searchStatus = ref(null)
const searchModel = ref('')

// 枚举选项
const taskStatusOptions = [
  { label: '待开始', value: '待开始' },
  { label: '空', value: '空' },
  { label: '进行中', value: '进行中' },
  { label: '已完成', value: '已完成' },
  { label: '故障或事故', value: '故障或事故' },
]

const statusColorMap = {
  '待开始': 'default',
  '空': 'default',
  '进行中': 'info',
  '已完成': 'success',
  '故障或事故': 'error',
}

const powerTypeOptions = [
  { label: '纯电', value: '纯电' },
  { label: '混动', value: '混动' },
  { label: '燃油', value: '燃油' },
]

const travelStatusOptions = [
  { label: '在厂', value: '在厂' },
  { label: '出差', value: '出差' },
  { label: '返程', value: '返程' },
]

const travelStatusColorMap = {
  '在厂': 'info',
  '出差': 'warning',
  '返程': 'success',
}

const dataSourceLabelMap = {
  'feishu': '外部飞书导入',
  'csv': '外部CSV导入',
  'manual': '系统导入',
}

// 格式化日期
function fmtDate(date) {
  if (!date) return ''
  const d = new Date(date)
  return d.toISOString().slice(0, 10)
}

// ===================== 表格列定义 =====================
const columns = [
  { title: 'VN', key: 'vn', width: 140, align: 'center' },
  { title: '编号', key: 'vehicle_code', width: 95, align: 'center' },
  { title: '车型', key: 'vehicle_model', width: 80, align: 'center' },
  { title: '动力', key: 'power_type', width: 75, align: 'center' },
  { title: '颜色', key: 'color', width: 60, align: 'center' },
  {
    title: '任务状态', key: 'task_status', width: 90, align: 'center',
    render(row) { return h(NTag, { type: statusColorMap[row.task_status] || 'default', size: 'small', bordered: false, round: true }, { default: () => row.task_status || '' }) },
  },
  { title: '试验任务', key: 'test_task', width: 85, align: 'center' },
  { title: '测试人员', key: 'tester', width: 75, align: 'center' },
  { title: '驾驶人员', key: 'driver', width: 75, align: 'center' },
  { title: '借用人', key: 'borrower', width: 75, align: 'center' },
  { title: '临牌到期', key: 'temp_plate_expire_date', width: 90, align: 'center', render: (row) => fmtDate(row.temp_plate_expire_date) },
  { title: '借用到期', key: 'borrow_expire_date', width: 90, align: 'center', render: (row) => fmtDate(row.borrow_expire_date) },
  { title: '保险区域', key: 'insurance_area', width: 85, align: 'center' },
  {
    title: '出差', key: 'travel_status', width: 65, align: 'center',
    render(row) { if (!row.travel_status) return ''; return h(NTag, { type: travelStatusColorMap[row.travel_status] || 'default', size: 'small', bordered: false, round: true }, { default: () => row.travel_status }) },
  },
  { title: '城市', key: 'test_city', width: 70, align: 'center' },
  { title: '出门单', key: 'exit_permit', width: 85, align: 'center' },
  { title: '纬度', key: 'latitude', width: 65, align: 'center', render: (row) => row.latitude != null ? row.latitude.toFixed(4) : '' },
  { title: '经度', key: 'longitude', width: 65, align: 'center', render: (row) => row.longitude != null ? row.longitude.toFixed(4) : '' },
  { title: '停车位', key: 'parking_spot', width: 70, align: 'center' },
  { title: '来源', key: 'data_source', width: 55, align: 'center',
    render(row) { return h(NTag, { type: 'info', size: 'small', bordered: false }, { default: () => dataSourceLabelMap[row.data_source] || row.data_source || '' }) },
  },
  {
    title: '操作', key: 'actions', width: 45, align: 'center',
    render(row) { return h(NButton, { size: 'tiny', text: true, type: 'primary', onClick: (e) => { e.stopPropagation(); handleRowClick(row) } }, { default: () => '编辑' }) },
  },
]

// ===================== 点击行 / 编辑按钮 → 统一打开详情面板 =====================
function handleRowClick(row) {
  selectedVehicle.value = { ...row }
  editMode.value = false
  isCreating.value = false
  showDetail.value = true
}

// ===================== 新增车辆 =====================
function handleAdd() {
  const now = new Date()
  editForm.value = {
    id: null,
    vn: '',
    vehicle_code: '',
    vehicle_model: '',
    power_type: null,
    color: '',
    has_controlled_items: '',
    borrower: '',
    borrow_expire_date: null,
    temp_plate_expire_date: null,
    insurance_area: '',
    test_date: null,
    task_status: null,
    test_task: null,
    tester: '',
    driver: '',
    travel_status: null,
    test_city: '',
    exit_permit: '',
    parking_spot: '',
    location_info: '',
    latitude: '',
    longitude: '',
    data_source: 'manual',
  }
  selectedVehicle.value = null
  isCreating.value = true
  editMode.value = true
  showDetail.value = true
}

// ===================== 内联详情编辑 =====================
function startEdit() {
  const v = selectedVehicle.value
  editForm.value = {
    id: v.id,
    vn: v.vn,
    vehicle_code: v.vehicle_code,
    vehicle_model: v.vehicle_model,
    power_type: v.power_type,
    color: v.color,
    has_controlled_items: v.has_controlled_items || '',
    borrower: v.borrower || '',
    borrow_expire_date: v.borrow_expire_date ? new Date(v.borrow_expire_date).getTime() : null,
    temp_plate_expire_date: v.temp_plate_expire_date ? new Date(v.temp_plate_expire_date).getTime() : null,
    insurance_area: v.insurance_area || '',
    test_date: v.test_date ? new Date(v.test_date).getTime() : null,
    task_status: v.task_status || null,
    test_task: v.test_task || null,
    tester: v.tester || '',
    driver: v.driver || '',
    travel_status: v.travel_status || null,
    test_city: v.test_city || '',
    exit_permit: v.exit_permit || '',
    parking_spot: v.parking_spot || '',
    location_info: v.location_info || '',
    latitude: v.latitude != null ? String(v.latitude) : '',
    longitude: v.longitude != null ? String(v.longitude) : '',
    data_source: v.data_source || 'manual',
  }
  editMode.value = true
}

async function handleSave() {
  saving.value = true
  try {
    const data = { ...editForm.value }
    // 日期转换
    if (data.borrow_expire_date && typeof data.borrow_expire_date === 'number') data.borrow_expire_date = new Date(data.borrow_expire_date).toISOString().substring(0, 10)
    if (data.temp_plate_expire_date && typeof data.temp_plate_expire_date === 'number') data.temp_plate_expire_date = new Date(data.temp_plate_expire_date).toISOString().substring(0, 10)
    if (data.test_date && typeof data.test_date === 'number') data.test_date = new Date(data.test_date).toISOString().substring(0, 10)
    if (data.latitude != null && data.latitude !== '') data.latitude = parseFloat(data.latitude)
    else data.latitude = null
    if (data.longitude != null && data.longitude !== '') data.longitude = parseFloat(data.longitude)
    else data.longitude = null

    if (isCreating.value) {
      await api.createVehicle(data)
      $message.success('新增成功')
    } else {
      await api.updateVehicle(data)
      $message.success('保存成功')
    }
    showDetail.value = false
    isCreating.value = false
    editMode.value = false
    fetchData()
  } catch (e) {
    $message.error(isCreating.value ? '新增失败' : '保存失败')
  } finally { saving.value = false }
}

async function handleDelete() {
  try {
    await api.deleteVehicle({ vehicle_id: selectedVehicle.value.id })
    $message.success('删除成功')
    showDetail.value = false
    fetchData()
  } catch (e) {
    $message.error('删除失败')
  }
}

// ===================== 数据加载 =====================
async function fetchData() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (searchVN.value) params.vn = searchVN.value
    if (searchBorrower.value) params.borrower = searchBorrower.value
    if (searchStatus.value) params.task_status = searchStatus.value
    if (searchModel.value) params.vehicle_model = searchModel.value

    const res = await api.getVehicleList(params)
    if (res.code === 200) {
      tableData.value = res.data || []
      itemCount.value = res.total || 0
    }
  } catch (e) {
    console.error('获取车辆列表失败', e)
    $message.error('获取车辆列表失败')
  } finally {
    loading.value = false
  }
}

function handlePageChange(p) {
  page.value = p
  fetchData()
}

function handlePageSizeChange(size) {
  pageSize.value = size
  page.value = 1
  fetchData()
}

function handleSearch() {
  page.value = 1
  fetchData()
}

function handleReset() {
  searchVN.value = ''
  searchBorrower.value = ''
  searchStatus.value = null
  searchModel.value = ''
  page.value = 1
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="data-detail-root">
    <!-- 搜索筛选栏 -->
    <div class="search-bar">
      <div class="search-left">
        <NInput
          v-model:value="searchVN"
          placeholder="车辆 VN"
          clearable
          style="width: 130px"
          @keypress.enter="handleSearch"
        >
          <template #prefix>
            <TheIcon icon="material-symbols:search" :size="17" />
          </template>
        </NInput>
        <NInput
          v-model:value="searchBorrower"
          placeholder="借用人"
          clearable
          style="width: 120px"
          @keypress.enter="handleSearch"
        />
        <NSelect
          v-model:value="searchStatus"
          :options="taskStatusOptions"
          placeholder="任务状态"
          clearable
          style="width: 130px"
        />
        <NInput
          v-model:value="searchModel"
          placeholder="车型项目"
          clearable
          style="width: 130px"
          @keypress.enter="handleSearch"
        />
        <NButton type="primary" @click="handleSearch">
          <template #icon>
            <TheIcon icon="material-symbols:search" :size="17" />
          </template>
          搜索
        </NButton>
        <NButton text @click="handleReset">
          <template #icon>
            <TheIcon icon="material-symbols:refresh" :size="16" />
          </template>
        </NButton>
      </div>
      <div class="search-right">
        <NButton type="primary" @click="handleAdd">
          <template #icon>
            <TheIcon icon="material-symbols:add" :size="17" />
          </template>
          新增数据
        </NButton>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-wrapper">
      <NSpin :show="loading">
        <NDataTable
          :columns="columns"
          :data="tableData"
          :bordered="false"
          :single-line="false"
          striped
          size="small"
          :row-props="(row) => ({
            style: 'cursor: pointer;',
            onClick: () => handleRowClick(row),
          })"
        >
          <template #empty>
            <NEmpty description="暂无车辆数据" class="mt-40" />
          </template>
        </NDataTable>
      </NSpin>
    </div>

    <!-- 分页器 -->
    <div class="pagination-bar">
      <NPagination
        v-model:page="page"
        :page-size="pageSize"
        :item-count="itemCount"
        :page-sizes="[10, 20, 50, 100]"
        show-size-picker
        show-quick-jumper
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </div>

    <!-- 详情面板（点击行 / 编辑按钮 统一入口，内联展示，不覆盖标签页） -->
    <div v-if="showDetail" class="detail-overlay">
      <div class="detail-panel-inline">
        <div class="detail-hdr">
          <span>{{ isCreating ? '新增车辆' : `车辆详情 — ${selectedVehicle?.vehicle_code || selectedVehicle?.vn || ''}` }}</span>
          <NSpace>
            <NButton v-if="!editMode && !isCreating" type="error" size="small" @click="handleDelete">删除</NButton>
            <NButton v-if="!editMode && !isCreating" type="primary" size="small" @click="startEdit">编辑</NButton>
            <NButton v-if="editMode" @click="showDetail = false; isCreating = false; editMode = false">取消</NButton>
            <NButton v-if="editMode" type="primary" size="small" :loading="saving" @click="handleSave">保存</NButton>
            <NButton v-if="!editMode" size="small" @click="showDetail = false">关闭</NButton>
          </NSpace>
        </div>
        <div class="detail-bd">
          <!-- 查看模式 -->
          <div v-if="!editMode" class="detail-grid">
            <div class="dg-item"><span class="dg-label">车辆VN</span><span class="dg-val">{{ selectedVehicle?.vn }}</span></div>
            <div class="dg-item"><span class="dg-label">车辆编号</span><span class="dg-val">{{ selectedVehicle?.vehicle_code }}</span></div>
            <div class="dg-item"><span class="dg-label">车型项目</span><span class="dg-val">{{ selectedVehicle?.vehicle_model }}</span></div>
            <div class="dg-item"><span class="dg-label">动力类型</span><span class="dg-val">{{ selectedVehicle?.power_type }}</span></div>
            <div class="dg-item"><span class="dg-label">颜色</span><span class="dg-val">{{ selectedVehicle?.color }}</span></div>
            <div class="dg-item"><span class="dg-label">管制物品</span><span class="dg-val">{{ selectedVehicle?.has_controlled_items || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">借用人</span><span class="dg-val">{{ selectedVehicle?.borrower || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">借用到期</span><span class="dg-val">{{ selectedVehicle?.borrow_expire_date || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">临牌到期</span><span class="dg-val">{{ selectedVehicle?.temp_plate_expire_date || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">保险区域</span><span class="dg-val">{{ selectedVehicle?.insurance_area || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">任务状态</span><span class="dg-val">{{ selectedVehicle?.task_status || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">试验任务</span><span class="dg-val">{{ selectedVehicle?.test_task || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">试验日期</span><span class="dg-val">{{ selectedVehicle?.test_date || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">测试人员</span><span class="dg-val">{{ selectedVehicle?.tester || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">驾驶人员</span><span class="dg-val">{{ selectedVehicle?.driver || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">出差状态</span><span class="dg-val">{{ selectedVehicle?.travel_status || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">试验城市</span><span class="dg-val">{{ selectedVehicle?.test_city || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">出门单</span><span class="dg-val">{{ selectedVehicle?.exit_permit || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">停车位</span><span class="dg-val">{{ selectedVehicle?.parking_spot || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">位置信息</span><span class="dg-val">{{ selectedVehicle?.location_info || '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">纬度</span><span class="dg-val">{{ selectedVehicle?.latitude != null ? selectedVehicle.latitude : '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">经度</span><span class="dg-val">{{ selectedVehicle?.longitude != null ? selectedVehicle.longitude : '--' }}</span></div>
            <div class="dg-item"><span class="dg-label">数据来源</span><span class="dg-val">{{ selectedVehicle?.data_source || '--' }}</span></div>
          </div>
          <!-- 编辑模式 -->
          <NForm v-else :model="editForm" label-placement="top" size="small">
            <NGrid :cols="2" :x-gap="16">
              <NGi><NFormItem label="车辆VN"><NInput v-model:value="editForm.vn" :disabled="!isCreating" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="车辆编号"><NInput v-model:value="editForm.vehicle_code" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="车型项目"><NInput v-model:value="editForm.vehicle_model" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="动力类型"><NInput v-model:value="editForm.power_type" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="颜色"><NInput v-model:value="editForm.color" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="管制物品"><NInput v-model:value="editForm.has_controlled_items" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="借用人"><NInput v-model:value="editForm.borrower" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="借用到期"><NDatePicker v-model:value="editForm.borrow_expire_date" type="date" /></NFormItem></NGi>
              <NGi><NFormItem label="临牌到期"><NDatePicker v-model:value="editForm.temp_plate_expire_date" type="date" /></NFormItem></NGi>
              <NGi><NFormItem label="保险区域"><NInput v-model:value="editForm.insurance_area" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="试验日期"><NDatePicker v-model:value="editForm.test_date" type="date" /></NFormItem></NGi>
              <NGi><NFormItem label="任务状态"><NSelect v-model:value="editForm.task_status" :options="taskStatusOptions" :disabled="isCreating" /></NFormItem></NGi>
              <NGi><NFormItem label="试验任务"><NInput v-model:value="editForm.test_task" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="测试人员"><NInput v-model:value="editForm.tester" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="驾驶人员"><NInput v-model:value="editForm.driver" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="出差状态"><NSelect v-model:value="editForm.travel_status" :options="[{label:'出差',value:'出差'},{label:'未出差',value:'未出差'}]" /></NFormItem></NGi>
              <NGi><NFormItem label="试验城市"><NInput v-model:value="editForm.test_city" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="出门单"><NInput v-model:value="editForm.exit_permit" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="停车位"><NInput v-model:value="editForm.parking_spot" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="位置信息"><NInput v-model:value="editForm.location_info" :disabled="isCreating" placeholder="请输入" /></NFormItem></NGi>
              <NGi><NFormItem label="纬度"><NInput v-model:value="editForm.latitude" placeholder="请输入" :disabled="isCreating" /></NFormItem></NGi>
              <NGi><NFormItem label="经度"><NInput v-model:value="editForm.longitude" placeholder="请输入" :disabled="isCreating" /></NFormItem></NGi>
              <NGi><NFormItem label="数据来源"><NInput v-model:value="editForm.data_source" disabled /></NFormItem></NGi>
            </NGrid>
          </NForm>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.data-detail-root { display: flex; flex-direction: column; height: 100%; min-height: 0; position: relative; }

.search-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 12px; flex-shrink: 0; }
.search-left { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.search-right { flex-shrink: 0; }
.hint-text { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #999; }

.table-wrapper { flex: 1; overflow: auto; min-height: 0; max-height: calc(100vh - 256px); }

:deep(.n-data-table td) { white-space: normal !important; word-break: break-all; }
:deep(.n-data-table .n-data-table-tbody tr) { cursor: pointer; }
:deep(.n-data-table .n-data-table-tbody tr:hover) { background-color: #f0f7ff !important; }

.pagination-bar {
  display: flex; justify-content: flex-end; padding: 10px 0; flex-shrink: 0; margin-top: auto;
}

/* 内联详情面板 */
.detail-overlay { position: absolute; inset: 0; background: #fff; z-index: 10; display: flex; flex-direction: column; overflow: hidden; }
.detail-panel-inline { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.detail-hdr { display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; border-bottom: 1px solid #eee; font-size: 15px; font-weight: 600; background: #fafafa; flex-shrink: 0; }
.detail-bd { flex: 1; overflow-y: auto; padding: 16px; }
.detail-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.dg-item { background: #f8f9fb; padding: 10px 14px; border-radius: 8px; display: flex; flex-direction: column; gap: 3px; }
.dg-label { font-size: 11px; color: #999; }
.dg-val { font-size: 14px; color: #333; font-weight: 500; word-break: break-all; }
.mt-40 { margin-top: 40px; }
</style>
