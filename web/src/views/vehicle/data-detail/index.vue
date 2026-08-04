<script setup>
import { onMounted, onBeforeUnmount, ref, h, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { reverseGeocode } from '@/utils/reverseGeocode'
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
  NPopconfirm,
  NDivider,
} from 'naive-ui'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import { notifyVehicleDataChanged } from '@/utils/vehicleSync'
import { formatRate } from '@/utils/common/common'

defineOptions({ name: '车辆数据详情' })

const router = useRouter()
const $message = useMessage()

// 表格数据
const loading = ref(false)
const tableData = ref([])
const checkedRowKeys = ref([])
const page = ref(1)
const pageSize = ref(20)
const itemCount = ref(0)
const tableMaxHeight = ref(400)

function calcTableHeight() {
  tableMaxHeight.value = Math.max(300, window.innerHeight - 200)
}

// 详情视图（点击行 / 点击编辑按钮 统一行为）
const showDetail = ref(false)
const selectedVehicle = ref(null)

// 内联详情编辑模式
const editMode = ref(false)
const isCreating = ref(false)  // 新增模式 vs 编辑模式
const editForm = ref({})
const saving = ref(false)

// 部门筛选
const filterDeptL1 = ref(null)  // 显示全部
const filterDeptL2 = ref(null)
const deptL1Options = ref([])
const deptL2Options = ref([])

// 全字段筛选
const fieldOptions = ref([
  { label: '车辆VN', value: 'vn' },
  { label: '车辆编号', value: 'vehicle_code' },
  { label: '车型项目', value: 'vehicle_model' },
  { label: '动力类型', value: 'power_type' },
  { label: '颜色', value: 'color' },
  { label: '车辆阶段', value: 'vehicle_phase' },
  { label: '车型配置', value: 'vehicle_model_config' },
  { label: '车辆状态', value: 'vehicle_status' },
  { label: '车辆状态备注', value: 'vehicle_status_note' },
  { label: '任务状态', value: 'task_status' },
  { label: '试验任务', value: 'test_task' },
  { label: '测试人员', value: 'tester' },
  { label: '驾驶人员', value: 'driver' },
  { label: '借用人', value: 'borrower' },
  { label: '借车人账号', value: 'borrower_account' },
  { label: '借车人电话', value: 'borrower_phone' },
  { label: '一级部门', value: 'dept_l1' },
  { label: '二级部门', value: 'dept_l2' },
  { label: '出差状态', value: 'travel_status' },
  { label: '试验城市', value: 'test_city' },
  { label: '车辆所在省', value: 'province' },
  { label: '车辆所在市', value: 'city' },
  { label: '详细地址', value: 'address_detail' },
  { label: '保险区域', value: 'insurance_area' },
  { label: '临牌区域', value: 'temp_plate_area' },
  { label: '临牌信息', value: 'temp_plate_info' },
  { label: '钥匙位置', value: 'key_location' },
  { label: '车管', value: 'vehicle_manager' },
  { label: '出门单', value: 'exit_permit' },
  { label: '停车位', value: 'parking_spot' },
  { label: '是否监控', value: 'is_monitored' },
  { label: '监控方式', value: 'monitor_method' },
  { label: '电池包状态', value: 'battery_pack_status' },
  { label: '是否VIN最早', value: 'is_first_vin_record' },
  { label: '改制中', value: 'is_under_modification' },
  { label: '数据来源', value: 'data_source' },
])
const searchField1 = ref(null)
const searchFieldValue1 = ref(null)
const searchFieldValueOptions1 = ref([])
const valueLoading1 = ref(false)

// 值选择器远程搜索防抖
let valueSearchTimer = null

function onFieldValueSearch(query) {
  if (valueSearchTimer) clearTimeout(valueSearchTimer)
  valueSearchTimer = setTimeout(async () => {
    if (!searchField1.value) return
    valueLoading1.value = true
    try {
      const res = await api.getFieldValues({ field: searchField1.value, keyword: query || undefined })
      searchFieldValueOptions1.value = (res.data?.values || []).map(val => ({ label: val, value: val }))
    } catch (e) {
      console.error('[data-detail] field value search failed:', e)
    } finally {
      valueLoading1.value = false
    }
  }, 300)
}

function onField1Change(v) {
  searchFieldValue1.value = null
  if (!v) { searchFieldValueOptions1.value = []; return }
  onFieldValueSearch('')
}

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

// ===================== 表格列定义 — 34列对齐飞书小程序 =====================
const columns = [
  { type: 'selection', width: 40, fixed: 'left' },
  { title: 'VIN', key: 'vn', width: 170, fixed: 'left' },
  { title: '车型项目', key: 'vehicle_model', width: 100, fixed: 'left' },
  { title: '车辆阶段', key: 'vehicle_phase', width: 80 },
  { title: '车辆编号', key: 'vehicle_code', width: 80 },
  { title: '动力配置', key: 'power_type', width: 75 },
  { title: '车型配置', key: 'vehicle_model_config', width: 100 },
  { title: '电池包状态', key: 'battery_pack_status', width: 90 },
  { title: '临牌信息', key: 'temp_plate_info', width: 110 },
  { title: '临牌到期', key: 'temp_plate_expire_date', width: 105, render: (row) => fmtDate(row.temp_plate_expire_date) },
  { title: '临牌区域', key: 'temp_plate_area', width: 180 },
  { title: '借车人', key: 'borrower', width: 70 },
  { title: '电话', key: 'borrower_phone', width: 110 },
  { title: '二级部门', key: 'dept_l2', width: 80 },
  { title: '一级部门', key: 'dept_l1', width: 80 },
  { title: '借车时间', key: 'borrow_time', width: 85 },
  { title: '预计归还时间', key: 'borrow_expire_date', width: 100, render: (row) => fmtDate(row.borrow_expire_date) },
  { title: '车辆所在省', key: 'province', width: 90 },
  { title: '车辆所在市', key: 'city', width: 90 },
  { title: '详细地址', key: 'address_detail', width: 180 },
  { title: '最后更新时间', key: 'updated_at', width: 100, render: (row) => fmtDate(row.updated_at) },
  { title: '7日利用率', key: 'borrower_7day_rate', width: 85, render: (row) => formatRate(row.borrower_7day_rate) },
  { title: '停车位', key: 'parking_spot', width: 70 },
  { title: '车辆状态', key: 'vehicle_status', width: 75 },
  { title: '车管', key: 'vehicle_manager', width: 65 },
  { title: '改制中', key: 'is_under_modification', width: 65 },
  { title: '任务状态', key: 'task_status', width: 85 },
  { title: '试验任务', key: 'test_task', width: 80 },
  { title: '测试人员', key: 'tester', width: 70 },
  { title: '驾驶人员', key: 'driver', width: 70 },
  { title: '出差状态', key: 'travel_status', width: 65,
    render(row) { if (!row.travel_status) return ''; return h(NTag, { type: travelStatusColorMap[row.travel_status] || 'default', size: 'small', bordered: false, round: true }, { default: () => row.travel_status }) },
  },
  { title: '试验城市', key: 'test_city', width: 80 },
  { title: '出门单', key: 'exit_permit', width: 75 },
  { title: '来源', key: 'data_source', width: 55,
    render(row) { return h(NTag, { type: 'info', size: 'small', bordered: false }, { default: () => dataSourceLabelMap[row.data_source] || row.data_source || '' }) },
  },
  { title: '操作', key: 'actions', width: 45, fixed: 'right',
    render(row) { return h(NButton, { size: 'tiny', text: true, type: 'primary', onClick: (e) => { e.stopPropagation(); handleRowClick(row) } }, { default: () => '编辑' }) },
  },
]

// 详情面板字段定义
const taskFields = [
  { key: 'task_status', label: '任务状态', type: 'select' },
  { key: 'test_task', label: '试验任务', type: 'select' },
  { key: 'tester', label: '测试人员', type: 'input' },
  { key: 'driver', label: '驾驶人员', type: 'input' },
  { key: 'travel_status', label: '出差状态', type: 'select' },
  { key: 'test_city', label: '试验城市', type: 'input' },
  { key: 'exit_permit', label: '出门单', type: 'input' },
  { key: 'parking_spot', label: '停车位', type: 'input' },
  { key: 'location_info', label: '位置信息', type: 'input' },
  { key: 'latitude', label: '纬度', type: 'input' },
  { key: 'longitude', label: '经度', type: 'input' },
]
const vehicleInfoFields = [
  { key: 'vn', label: 'VIN' }, { key: 'vehicle_code', label: '车辆编号' },
  { key: 'vehicle_model', label: '车型项目' }, { key: 'power_type', label: '动力类型' },
  { key: 'vehicle_phase', label: '车辆阶段' }, { key: 'vehicle_model_config', label: '车型配置' },
  { key: 'color', label: '颜色' }, { key: 'vehicle_status', label: '车辆状态' },
  { key: 'vehicle_status_note', label: '状态备注' }, { key: 'has_controlled_items', label: '管制物品' },
  { key: 'borrower', label: '借用人' }, { key: 'borrower_account', label: '借车人账号' },
  { key: 'borrower_id', label: '借车人ID' }, { key: 'borrower_phone', label: '电话' },
  { key: 'borrow_time', label: '借车时间' }, { key: 'borrow_expire_date', label: '预计归还' },
  { key: 'borrow_days', label: '借用天数' }, { key: 'temp_plate_expire_date', label: '临牌到期' },
  { key: 'temp_plate_area', label: '临牌区域' }, { key: 'temp_plate_valid_area', label: '临牌有效区域' },
  { key: 'temp_plate_info', label: '临牌信息' }, { key: 'temp_plate_insurance_count', label: '办理次数' },
  { key: 'insurance_area', label: '保险区域' }, { key: 'key_location', label: '钥匙位置' },
  { key: 'vehicle_manager', label: '车管' }, { key: 'vehicle_manager_id', label: '车管ID' },
  { key: 'parking_spot', label: '停车位' }, { key: 'dept_l1', label: '一级部门' },
  { key: 'dept_l2', label: '二级部门' }, { key: 'province', label: '所在省' },
  { key: 'city', label: '所在市' }, { key: 'address_detail', label: '详细地址' },
  { key: 'storage_days', label: '在库时长' }, { key: 'qr_code', label: '二维码' },
  { key: 'is_monitored', label: '是否监控' }, { key: 'monitor_method', label: '监控方式' },
  { key: 'is_first_vin_record', label: '是否VIN最早' }, { key: 'engine_no', label: '发动机号' },
  { key: 'battery_pack_status', label: '电池包状态' }, { key: 'battery_pack_trace', label: '电池包溯源码' },
  { key: 'battery_pack_part_no', label: '电池包零件号' }, { key: 'battery_pack_rated', label: '电池包额定电量' },
  { key: 'front_motor_no', label: '前电机号' }, { key: 'rear_motor_no', label: '后电机号' },
  { key: 'trial_plan', label: '试验策划' }, { key: 'trial_plan_id', label: '试验策划ID' },
  { key: 'borrower_7day_rate', label: '7日利用率', render: formatRate },
  { key: 'data_source', label: '数据来源' },
  { key: 'test_date', label: '试验日期' },
]

const visibleTaskFields = computed(() => {
  if (!selectedVehicle.value) return []
  return taskFields.filter(f => selectedVehicle.value[f.key] != null && selectedVehicle.value[f.key] !== '')
})
const visibleVehicleFields = computed(() => {
  if (!selectedVehicle.value) return []
  return vehicleInfoFields.filter(f => selectedVehicle.value[f.key] != null && selectedVehicle.value[f.key] !== '')
})
function handleRowClick(row) {
  selectedVehicle.value = { ...row }
  editMode.value = false
  isCreating.value = false
  showDetail.value = true
  // 有经纬度时自动显示行政位置
  if (row.latitude != null && row.longitude != null) {
    reverseGeocode(row.latitude, row.longitude).then(addr => {
      if (addr && selectedVehicle.value) selectedVehicle.value.location_info = addr
    })
  }
}

function handleAdd() {
  editForm.value = buildEmptyForm()
  selectedVehicle.value = null
  isCreating.value = true
  editMode.value = true
  showDetail.value = true
}

function buildEmptyForm() {
  const form = { id: null }
  const allFields = [...taskFields, ...vehicleInfoFields]
  allFields.forEach(f => { form[f.key] = f.key.endsWith('_date') ? null : '' })
  form.data_source = 'manual'
  return form
}

// ===================== 内联详情编辑 =====================
function startEdit() {
  const v = selectedVehicle.value
  const form = { id: v.id }
  const allFields = [...taskFields, ...vehicleInfoFields]
  allFields.forEach(f => {
    const val = v[f.key]
    if (f.key.endsWith('_date') && val) { form[f.key] = new Date(val).getTime() }
    else if (f.key === 'latitude' || f.key === 'longitude') { form[f.key] = val != null ? String(val) : '' }
    else { form[f.key] = val != null ? val : '' }
  })
  editForm.value = form
  editMode.value = true
}

async function handleSave() {
  saving.value = true
  try {
    const data = { ...editForm.value }
    if (!data.id) { $message.warning('车辆ID无效'); saving.value = false; return }
    const allFields = [...taskFields, ...vehicleInfoFields]
    allFields.forEach(f => {
      if (f.key.endsWith('_date') && typeof data[f.key] === 'number') {
        data[f.key] = new Date(data[f.key]).toISOString().substring(0, 10)
      }
    });
    ['latitude','longitude','borrower_7day_rate'].forEach(k => {
      if (data[k] != null && data[k] !== '') data[k] = parseFloat(data[k]); else data[k] = null
    })
    if (data.borrow_days != null && data.borrow_days !== '') data.borrow_days = parseInt(data.borrow_days); else data.borrow_days = null
    // 有经纬度但没有行政位置时，逆地理编码
    if (data.latitude != null && data.longitude != null && !data.location_info) {
      data.location_info = await reverseGeocode(data.latitude, data.longitude)
    }
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
    notifyVehicleDataChanged()
    fetchData()
  } catch (e) { $message.error(isCreating.value ? '新增失败' : '保存失败') }
  finally { saving.value = false }
}

async function handleDelete() {
  try {
    await api.deleteVehicle({ vehicle_id: selectedVehicle.value.id })
    $message.success('删除成功')
    showDetail.value = false
    notifyVehicleDataChanged()
    fetchData()
  } catch (e) {
    $message.error('删除失败')
  }
}

// ===================== 部门选项 =====================
async function loadDeptOptions() {
  try {
    const res = await api.getFieldValues({ field: 'dept_l1' })
    deptL1Options.value = (res.data?.values || []).map(v => ({ label: v, value: v }))
  } catch (e) { console.error('[data-detail] loadDeptOptions failed:', e) }
}
async function updateDeptL2Options() {
  try {
    const res = await api.getFieldValues({ field: 'dept_l2' })
    deptL2Options.value = (res.data?.values || []).map(v => ({ label: v, value: v }))
  } catch (e) { console.error('[data-detail] updateDeptL2Options failed:', e) }
}

// 监听部门变更
watch(filterDeptL1, () => { filterDeptL2.value = null; updateDeptL2Options(); handleSearch() })
watch(filterDeptL2, () => { handleSearch() })
// 监听字段选择
watch(searchField1, (v) => onField1Change(v))
// 选择值后自动触发搜索
watch(searchFieldValue1, () => { handleSearch() })

// ===================== 数据加载 =====================
async function fetchData() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      dept_l1: filterDeptL1.value || undefined,
      dept_l2: filterDeptL2.value || undefined,
    }
    if (searchField1.value && searchFieldValue1.value) {
      params.field1 = searchField1.value; params.value1 = searchFieldValue1.value
    }

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

const batchDeleting = ref(false)
const hasChecked = computed(() => checkedRowKeys.value.length > 0)

async function handleBatchDelete() {
  if (checkedRowKeys.value.length === 0) { $message.warning('请先勾选要删除的数据'); return }
  batchDeleting.value = true
  try {
    const res = await api.batchDeleteVehicles(checkedRowKeys.value)
    $message.success('批量删除成功，共删除 ' + (res.data?.deleted || checkedRowKeys.value.length) + ' 条')
    checkedRowKeys.value = []
    notifyVehicleDataChanged()
    fetchData()
  } catch (e) { $message.error('批量删除失败') }
  finally { batchDeleting.value = false }
}

function handleCheck(rowKeys) { checkedRowKeys.value = rowKeys }

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
  filterDeptL1.value = null; filterDeptL2.value = null; deptL2Options.value = []
  searchField1.value = null; searchFieldValue1.value = null; searchFieldValueOptions1.value = []
  page.value = 1
  checkedRowKeys.value = []
  fetchData()
}

onMounted(async () => {
  calcTableHeight()
  window.addEventListener('resize', calcTableHeight)
  await loadDeptOptions()
  fetchData()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', calcTableHeight)
  showDetail.value = false
  selectedVehicle.value = null
  editMode.value = false
  isCreating.value = false
})
</script>

<template>
  <div class="data-detail-root vehicle-card">
    <!-- 搜索筛选栏 -->
    <div class="search-bar">
      <div class="search-left">
        <span class="dept-label">部门：</span>
        <NSelect v-model:value="filterDeptL1" :options="deptL1Options" placeholder="一级部门" clearable filterable style="width: 140px" />
        <NSelect v-model:value="filterDeptL2" :options="deptL2Options" placeholder="二级部门" clearable filterable style="width: 140px" />
        <span class="dept-sep" />
        <NSelect v-model:value="searchField1" :options="fieldOptions" placeholder="全字段搜索" clearable filterable style="width: 150px" />
        <NSelect
          v-model:value="searchFieldValue1"
          :options="searchFieldValueOptions1"
          :loading="valueLoading1"
          placeholder="输入关键字搜索值"
          clearable
          filterable
          :filter="() => true"
          @search="onFieldValueSearch"
          style="width: 200px"
          :disabled="!searchField1"
        />
        <NButton type="primary" size="small" @click="handleSearch">
          <template #icon><TheIcon icon="material-symbols:search" :size="16" /></template>
          搜索
        </NButton>
        <NButton size="small" @click="handleReset">重置</NButton>
        <span class="data-total">共 {{ itemCount }} 条</span>
      </div>
      <div class="search-right">
        <NSpace>
          <NPopconfirm @positive-click="handleBatchDelete">
            <template #trigger>
              <NButton type="error" size="small" :loading="batchDeleting" :disabled="!hasChecked" ghost>
                <template #icon><TheIcon icon="material-symbols:delete-outline" :size="16" /></template>
                批量删除{{ hasChecked ? '（' + checkedRowKeys.length + '）' : '' }}
              </NButton>
            </template>
            确定要删除选中的 {{ checkedRowKeys.length }} 条数据吗？此操作不可恢复。
          </NPopconfirm>
          <NButton type="primary" size="small" @click="handleAdd">
            <template #icon><TheIcon icon="material-symbols:add" :size="16" /></template>
            新增数据
          </NButton>
        </NSpace>
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
          :row-key="(row) => row.id"
          :checked-row-keys="checkedRowKeys"
          @update:checked-row-keys="handleCheck"
          :row-props="(row) => ({
            style: 'cursor: pointer;',
            onClick: (e) => { if (e.button === 0 && !window.getSelection()?.toString()) handleRowClick(row) },
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

        <!-- 详情面板 — 分区显示 -->
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
          <template v-if="!editMode">
            <div class="sec-title">✏️ 任务状态信息</div>
            <NGrid :cols="6" :x-gap="6">
              <NGi v-for="f in taskFields" :key="f.key">
                <div class="info-item"><span class="info-lbl">{{ f.label }}</span><span class="info-val">{{ selectedVehicle && selectedVehicle[f.key] != null ? selectedVehicle[f.key] : '--' }}</span></div>
              </NGi>
            </NGrid>
            <NDivider />
            <div class="sec-title">🚗 车辆信息</div>
            <NGrid :cols="6" :x-gap="6">
              <NGi v-for="f in vehicleInfoFields" :key="f.key">
                <div class="info-item"><span class="info-lbl">{{ f.label }}</span><span class="info-val">{{ selectedVehicle && selectedVehicle[f.key] != null ? (f.render ? f.render(selectedVehicle[f.key]) : selectedVehicle[f.key]) : '--' }}</span></div>
              </NGi>
            </NGrid>
          </template>
          <!-- 编辑模式 -->
          <template v-else>
            <div class="sec-title">✏️ 任务状态信息</div>
            <NGrid :cols="4" :x-gap="6">
              <NGi v-for="f in taskFields" :key="f.key">
                <NFormItem :label="f.label" size="small">
                  <NInput v-if="f.type==='input'" v-model:value="editForm[f.key]" size="small" :placeholder="'请输入'+f.label" />
                  <NSelect v-else-if="f.type==='select'" v-model:value="editForm[f.key]" :options="f.key==='task_status' ? taskStatusOptions : f.key==='test_task' ? [{label:'城市NCA',value:'城市NCA'},{label:'高速NCA',value:'高速NCA'},{label:'泊车测试',value:'泊车测试'},{label:'L0L1',value:'L0L1'},{label:'用列点检',value:'用列点检'},{label:'车辆整备',value:'车辆整备'},{label:'静态测试',value:'静态测试'},{label:'内场测试',value:'内场测试'}] : [{label:'出差',value:'出差'},{label:'未出差',value:'未出差'}]" size="small" />
                </NFormItem>
              </NGi>
            </NGrid>
            <NDivider />
            <div class="sec-title">🚗 车辆信息</div>
            <NGrid :cols="4" :x-gap="6">
              <NGi v-for="f in vehicleInfoFields" :key="f.key">
                <NFormItem :label="f.label" size="small">
                  <NInput v-if="f.key==='borrow_expire_date'||f.key==='temp_plate_expire_date'||f.key==='test_date'" type="date" v-model:value="editForm[f.key]" size="small" />
                  <NInput v-else v-model:value="editForm[f.key]" size="small" />
                </NFormItem>
              </NGi>
            </NGrid>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.data-detail-root { display: flex; flex-direction: column; height: 100%; position: relative; overflow: hidden; }
.dept-label { font-size: 12px; color: #999; white-space: nowrap; }
.dept-sep { width: 1px; height: 24px; background: #e0e0e0; margin: 0 2px; }
.data-total { font-size: 13px; color: #666; white-space: nowrap; margin-left: 4px; }

.search-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0; gap: 12px; flex-shrink: 0; background: #fff; padding: 8px 0 4px; }
.search-left { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.search-right { flex-shrink: 0; }

.table-wrapper { flex: 1; overflow: auto; min-height: 0; }
:deep(.n-data-table-thead) { position: sticky; top: 0; z-index: 10; background: #fafafc; }
:deep(.n-data-table td) { white-space: nowrap !important; overflow: hidden; text-overflow: ellipsis; }
:deep(.n-data-table th) { white-space: nowrap !important; }
:deep(.n-data-table .n-data-table-tbody tr) { cursor: pointer; }
:deep(.n-data-table .n-data-table-tbody tr:hover) { background-color: #f0f7ff !important; }

:deep(.n-data-table td:nth-child(1)), :deep(.n-data-table th:nth-child(1)) { position: sticky; left: 0; z-index: 5; background: #fff; }
:deep(.n-data-table td:nth-child(1)::after), :deep(.n-data-table th:nth-child(1)::after) { content: ''; position: absolute; right: -1px; top: 0; bottom: 0; width: 1px; background: #e8eaed; }
:deep(.n-data-table tr:nth-child(even) td:nth-child(1)) { background: #fafafc; }
:deep(.n-data-table td:nth-child(2)), :deep(.n-data-table th:nth-child(2)) { position: sticky; left: 40px; z-index: 4; background: #fff; }
:deep(.n-data-table td:nth-child(2)::after), :deep(.n-data-table th:nth-child(2)::after) { content: ''; position: absolute; right: -1px; top: 0; bottom: 0; width: 1px; background: #e8eaed; }
:deep(.n-data-table tr:nth-child(even) td:nth-child(2)) { background: #fafafc; }
:deep(.n-data-table td:nth-child(3)), :deep(.n-data-table th:nth-child(3)) { position: sticky; left: 210px; z-index: 3; background: #fff; }
:deep(.n-data-table td:nth-child(3)::after), :deep(.n-data-table th:nth-child(3)::after) { content: ''; position: absolute; right: -1px; top: 0; bottom: 0; width: 1px; background: #e8eaed; }
:deep(.n-data-table tr:nth-child(even) td:nth-child(3)) { background: #fafafc; }
:deep(.n-data-table td:last-child), :deep(.n-data-table th:last-child) { position: sticky; right: 0; z-index: 2; background: #fff; }
:deep(.n-data-table td:last-child::before), :deep(.n-data-table th:last-child::before) { content: ''; position: absolute; left: -1px; top: 0; bottom: 0; width: 1px; background: #e8eaed; }
:deep(.n-data-table tr:nth-child(even) td:last-child) { background: #fafafc; }

.pagination-bar { display: flex; justify-content: flex-end; padding: 10px 0; flex-shrink: 0; margin-top: auto; }

.detail-overlay { position: absolute; inset: 0; background: #fff; z-index: 10; display: flex; flex-direction: column; overflow: hidden; }
.detail-panel-inline { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.detail-hdr { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; border-bottom: 1px solid #eee; font-size: 14px; font-weight: 600; background: #fafafa; flex-shrink: 0; }
.detail-bd { flex: 1; overflow-y: auto; padding: 10px 12px; }
.sec-title { font-size: 13px; font-weight: 600; color: #333; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 2px solid #2080f0; }
.info-item { background: #f0f6ff; padding: 5px 8px; border-radius: 4px; margin-bottom: 4px; }
.info-lbl { font-size: 12px; color: #2080f0; display: block; margin-bottom: 1px; }
.info-val { font-size: 14px; color: #1a1a1a; font-weight: 500; word-break: break-all; }
.mt-40 { margin-top: 40px; }
</style>
