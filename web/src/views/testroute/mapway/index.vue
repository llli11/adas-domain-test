<!-- web/src/views/mapway/index.vue -->
<template>
  <div class="p-4">
    <!-- 搜索栏 -->
    <n-card title="合作项目区域管理" :bordered="false" class="mb-4">
      <n-form :model="searchForm" label-placement="left">
        <n-space align="center">
          <n-form-item label="关键词">
            <n-input
              v-model:value="searchForm.keyword"
              placeholder="区域名称或城市"
              clearable
              style="width: 260px"
            />
          </n-form-item>
          <n-form-item>
            <n-button type="primary" @click="handleSearch">查询</n-button>
            <n-button class="ml-2" @click="resetSearch">重置</n-button>
            <n-button class="ml-2" :type="showFilter ? 'warning' : 'default'" @click="showFilter = !showFilter">
              <template #icon><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" /></svg></template>
              筛选
            </n-button>
          </n-form-item>
        </n-space>
      </n-form>
      <n-modal v-model:show="showFilter" title="筛选条件" style="width: 620px" preset="card" :mask-closable="true">
        <div class="filter-conditions">
          <div v-for="(cond, idx) in filterConditions" :key="idx" class="filter-row">
            <n-select
              v-model:value="cond.field"
              :options="filterFieldOptions"
              placeholder="选择字段"
              filterable
              size="small"
              style="width: 180px"
            />
            <n-select
              v-model:value="cond.operator"
              :options="getOperatorOptions(cond.field)"
              placeholder="条件"
              size="small"
              style="width: 130px"
            />
            <n-input
              v-if="!isNoValueOperator(cond.operator)"
              v-model:value="cond.value"
              placeholder="输入值"
              size="small"
              style="width: 160px"
            />
            <n-button text size="small" type="error" @click="removeFilterCondition(idx)">
              <template #icon><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg></template>
            </n-button>
          </div>
          <n-button dashed size="small" @click="addFilterCondition" style="margin-top: 4px">+ 添加条件</n-button>
        </div>
        <div class="filter-footer" v-if="filterConditions.length > 1">
          <n-radio-group v-model:value="filterLogic" size="small">
            <n-radio value="and">符合所有条件</n-radio>
            <n-radio value="or">符合任一条件</n-radio>
          </n-radio-group>
        </div>
        <div class="filter-actions">
          <n-button type="primary" size="small" @click="applyFilter">筛选</n-button>
          <n-button size="small" @click="resetFilter">重置</n-button>
        </div>
      </n-modal>
    </n-card>

    <!--  (区域管理) 之后，新增高级检索卡片 -->

    <!-- 高级检索弹窗 -->
    <n-modal v-model:show="showSearchModal" title="高级检索" style="width: 800px" preset="card" :mask-closable="false">
      <n-space vertical>
      <n-spin :show="searchLoading" description="检索中，请稍候...">
        <n-data-table
          :columns="searchColumns"
          :data="searchTableData"
          :loading="searchLoading"
          :pagination="false"
        />
        <n-flex justify="center" style="margin-top: 12px">
          <n-pagination
            :page="searchPage"
            :page-size="searchPageSize"
            :item-count="searchTotal"
            :page-sizes="[10, 20, 50, 100]"
            show-size-picker
            @update:page="onSearchPageChange"
            @update:page-size="onSearchPageSizeChange"
          />
        </n-flex>
        </n-spin>
      </n-space>
    </n-modal>

    <!-- 筛选结果弹窗 -->
    <n-modal v-model:show="filterActive" title="筛选结果" style="width: 900px" preset="card" :mask-closable="true">
      <n-spin :show="filterLoading" description="筛选中，请稍候...">
        <div style="margin-bottom: 8px">共 <strong>{{ filteredData.length }}</strong> 条路线</div>
        <n-data-table
          :columns="filterResultColumns"
          :data="filterPaginatedData"
          :bordered="true"
          :pagination="false"
        />
        <n-flex justify="center" style="margin-top: 12px">
          <n-pagination
            :page="filterPage"
            :page-size="filterPageSize"
            :item-count="filteredData.length"
            :page-sizes="[20, 50, 100]"
            show-size-picker
            @update:page="filterPage = $event"
            @update:page-size="filterPageSize = $event; filterPage = 1"
          />
        </n-flex>
      </n-spin>
    </n-modal>

    <!-- 数据表格 -->
    <n-card :bordered="false">
        <n-space class="mb-4">
          <n-form-item label="检索字段" label-placement="left">
            <n-select
              v-model:value="searchField"
              :options="searchFieldsOptions"
              placeholder="选择字段"
              style="width: 200px"
            />
          </n-form-item>
          <n-button text style="height: 34px" @click="toggleSearchOrder" :type="searchOrder === 'asc' ? 'warning' : 'default'">
            {{ searchOrder === 'asc' ? '🔼' : '🔽' }}
          </n-button>
          <n-button type="primary" :loading="searchLoading" @click="handleAdvancedSearch">详情检索</n-button>
          <n-button type="primary" v-if="canCreateArea" @click="handleCreate">新增区域</n-button>
        </n-space>
        <n-data-table
          :columns="columns"
          :data="tableData"
          :loading="loading"
          :pagination="pagination"
          :row-props="getRowProps"
          @update:page="onPageChange"
          @update:page-size="onPageSizeChange"
        />
    </n-card>

    <!-- 新增/编辑弹窗 -->
    <n-modal v-model:show="showModal" :title="modalTitle">
      <n-card style="width: 600px" :bordered="false" size="small">
        <n-form :model="formData" :rules="formRules" ref="formRef">
          <n-form-item label="区域名称" path="area">
            <n-input v-model:value="formData.area" placeholder="请输入区域名称" />
          </n-form-item>
          <n-form-item label="城市列表" path="city">
            <n-input
              type="textarea"
              v-model:value="formData.city"
              placeholder="多个城市用中文顿号分隔，如：郑州、石家庄、太原"
              :autosize="{ minRows: 3, maxRows: 6 }"
            />
          </n-form-item>
        </n-form>
        <template #footer>
          <n-space justify="end">
            <n-button @click="showModal = false">取消</n-button>
            <n-button type="primary" @click="submitForm">保存</n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup>
defineOptions({ name: '测试路线' })
import { ref, reactive, computed, h, onMounted, onActivated, onDeactivated, nextTick, watch } from 'vue'
import { useMessage, useDialog, NButton, NSpin, NRadioGroup, NRadio, NTag } from 'naive-ui'
import mapwayApi from '@/api/mapway' 
import { useRouter } from 'vue-router'
import { usePermissionStore } from '@/store'
import { useRouteCacheStore } from '@/store'
const permissionStore = usePermissionStore()
function hasPermission(method, path) {
  const api = `${method.toLowerCase()}${path}` // 实际存储格式：post/api/v1/mapway/create
  return permissionStore.accessApis.includes(api)
}
const canCreateArea = computed(() => hasPermission('POST', '/api/v1/mapway/create'))

const POPUP_KEY = 'mapway_popup_state'
let _popupSaved = false
function savePopupState() {
  if (_popupSaved) return
  _popupSaved = true
  sessionStorage.setItem(POPUP_KEY, JSON.stringify({
    filterActive: !!filterActive.value,
    showSearchModal: !!showSearchModal.value,
    showFilter: !!showFilter.value || _filterWasOpenBeforeResults,
    filterConditions: filterConditions.value,
    filterLogic: filterLogic.value,
    searchField: searchField.value,
    searchOrder: searchOrder.value,
  }))
}
async function restorePopupState() {
  try {
    const raw = sessionStorage.getItem(POPUP_KEY)
    if (!raw) return
    const state = JSON.parse(raw)
    sessionStorage.removeItem(POPUP_KEY)
    _popupSaved = false
    if (state.filterActive) {
      filterConditions.value = state.filterConditions
      filterLogic.value = state.filterLogic
      if (state.showFilter) _filterWasOpenBeforeResults = true
      await applyFilter()
    } else if (state.showFilter) {
      showFilter.value = true
    }
    if (state.showSearchModal) {
      searchField.value = state.searchField
      searchOrder.value = state.searchOrder
      await fetchSearchResults()
      showSearchModal.value = true
    }
  } catch { /* ignore */ }
}
let _filterWasOpenBeforeResults = false

const canUpdateArea = computed(() => hasPermission('POST', '/api/v1/mapway/update'))
const canDeleteArea = computed(() => hasPermission('DELETE', '/api/v1/mapway/delete'))

const message = useMessage()
const dialog = useDialog()
const router = useRouter()

// ---------- 搜索 ----------
const searchForm = reactive({ keyword: '' })
function handleSearch() { fetchData(1) }
function resetSearch() { searchForm.keyword = ''; fetchData(1) }

const searchFieldsOptions = [
  { label: '路线序号', value: 'route_order' },
  { label: '优先级', value: 'priority' },
  { label: '编写人', value: 'author' },
  { label: '路线类型', value: 'route_type' },
  { label: '路线里程数', value: 'mileage' },
  { label: '路线时长', value: 'duration' },
  { label: '途经点信息', value: 'waypoints' },
  { label: '路线偏好', value: 'route_preference' },
  { label: '是否通过门店附近', value: 'near_store' },
  { label: '汇入匝道个数', value: 'merge_in_num' },
  { label: '汇出匝道个数', value: 'merge_out_num' },
  { label: 'Y型路口个数', value: 'y_intersection_num' },
  { label: '环岛个数', value: 'roundabout_num' },
  { label: '掉头次数', value: 'u_turn_num' },
  { label: '直行路口个数', value: 'straight_intersection_num' },
  { label: '有保护左转路口个数', value: 'protected_left_num' },
  { label: '无保护左转路口个数', value: 'unprotected_left_num' },
  { label: '有保护右转路口个数', value: 'protected_right_num' },
  { label: '无保护右转路口个数', value: 'unprotected_right_num' },
  { label: '正常红绿灯个数', value: 'normal_traffic_light_num' },
  { label: '黄灯常闪或常亮个数', value: 'flashing_yellow_num' },
  { label: '未启用红绿灯个数', value: 'disabled_traffic_light_num' },
  { label: '特殊红绿灯个数', value: 'special_traffic_light_num' },
  { label: '主辅路切换个数', value: 'main_side_switch_num' },
  { label: '右转专用道个数', value: 'right_turn_lane_num' },
  { label: '可变车道个数', value: 'variable_lane_num' },
  { label: '待转车道个数', value: 'waiting_lane_num' },
  { label: '路线复杂程度', value: 'complexity' },
  { label: '备注', value: 'remark' },
]

// ---------- 筛选 ----------
const showFilter = ref(false)
const filterActive = ref(false)
const filterLogic = ref('and')
const filterConditions = ref([{ field: null, operator: null, value: '' }])
const filterPage = ref(1)
const filterPageSize = ref(20)
const filterAllRouteData = ref([])

const filterFieldOptions = searchFieldsOptions
const filterLoading = ref(false)

const numericFieldKeys = new Set([
  'mileage', 'duration',
  'merge_in_num', 'merge_out_num', 'y_intersection_num', 'roundabout_num',
  'u_turn_num', 'straight_intersection_num', 'protected_left_num',
  'unprotected_left_num', 'protected_right_num', 'unprotected_right_num',
  'normal_traffic_light_num', 'flashing_yellow_num', 'disabled_traffic_light_num',
  'special_traffic_light_num', 'main_side_switch_num', 'right_turn_lane_num',
  'variable_lane_num', 'waiting_lane_num',
])

const baseOperators = [
  { label: '等于', value: 'equals' },
  { label: '不等于', value: 'not_equals' },
  { label: '包含', value: 'contains' },
  { label: '不包含', value: 'not_contains' },
  { label: '为空', value: 'is_empty' },
  { label: '不为空', value: 'is_not_empty' },
]
const numericExtraOperators = [
  { label: '大于', value: 'greater_than' },
  { label: '小于', value: 'less_than' },
]

function getOperatorOptions(fieldKey) {
  if (numericFieldKeys.has(fieldKey)) return [...baseOperators, ...numericExtraOperators]
  return baseOperators
}

function isNoValueOperator(op) {
  return op === 'is_empty' || op === 'is_not_empty'
}

function addFilterCondition() {
  filterConditions.value.push({ field: null, operator: null, value: '' })
}

function removeFilterCondition(idx) {
  filterConditions.value.splice(idx, 1)
}

function matchRow(row, cond) {
  if (!cond.field || !cond.operator) return true
  const val = row[cond.field]
  const strVal = val != null ? String(val) : ''
  const condVal = cond.value || ''
  switch (cond.operator) {
    case 'equals': return strVal === condVal
    case 'not_equals': return strVal !== condVal
    case 'contains': return strVal.includes(condVal)
    case 'not_contains': return !strVal.includes(condVal)
    case 'is_empty': return strVal === ''
    case 'is_not_empty': return strVal !== ''
    case 'greater_than': return numericFieldKeys.has(cond.field) && Number(val) > Number(condVal)
    case 'less_than': return numericFieldKeys.has(cond.field) && Number(val) < Number(condVal)
    default: return true
  }
}

const filteredData = computed(() => {
  if (!filterActive.value) return []
  const allRows = filterAllRouteData.value
  const validConditions = filterConditions.value.filter(c => c.field && c.operator && (isNoValueOperator(c.operator) || c.value))
  if (validConditions.length === 0) return allRows
  return allRows.filter(row => {
    if (filterLogic.value === 'and') {
      return validConditions.every(cond => matchRow(row, cond))
    } else {
      return validConditions.some(cond => matchRow(row, cond))
    }
  })
})

const filterPaginatedData = computed(() => {
  const start = (filterPage.value - 1) * filterPageSize.value
  return filteredData.value.slice(start, start + filterPageSize.value)
})

const filterResultColumns = computed(() => {
  const cols = [
    { title: '路线序号', key: 'route_order', width: 120 },
    { title: '路线类型', key: 'route_type', width: 100 },
    { title: '城市', key: 'city', width: 80 },
  ]
  const usedFields = new Set(filterConditions.value.filter(c => c.field).map(c => c.field))
  usedFields.forEach(fieldKey => {
    const fieldDef = searchFieldsOptions.find(f => f.value === fieldKey)
    if (fieldDef && !['route_order', 'route_type', 'city'].includes(fieldKey)) {
      cols.push({ title: fieldDef.label, key: fieldKey, width: 120 })
    }
  })
  cols.push({
    title: '操作', key: 'actions', width: 100,
    render: (row) => h(NButton, { size: 'small', onClick: () => {
      savePopupState()
      _filterWasOpenBeforeResults = false
      filterActive.value = false
      showFilter.value = false
      nextTick(() => {
        router.push({ path: `/testroute/city/${encodeURIComponent(row.city)}`, query: { routeOrder: String(row.route_order) } })
      })
    } }, { default: () => '查看详情' }),
  })
  return cols
})

async function applyFilter() {
  const validConditions = filterConditions.value.filter(c => c.field && c.operator && (isNoValueOperator(c.operator) || c.value))
  if (validConditions.length === 0) {
    message.warning('请至少填写一个完整的筛选条件')
    return
  }
  try {
    filterLoading.value = true
    filterPage.value = 1
    const res = await mapwayApi.filterRoutes(
      validConditions.map(c => ({ field: c.field, operator: c.operator, value: c.value || '' })),
      { logic: filterLogic.value, page: 1, page_size: 9999 }
    )
    filterAllRouteData.value = res.data || []
    filterActive.value = true          // ← 数据加载完再开弹窗
  } catch (e) {
    message.error('筛选失败')
  } finally {
    filterLoading.value = false
  }
}

function resetFilter() {
  filterConditions.value = [{ field: null, operator: null, value: '' }]
  filterLogic.value = 'and'
  filterActive.value = false
  filterAllRouteData.value = []
}

// ---------- 表格 ----------
const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 10, itemCount: 0 })


// ----- 高级检索相关 -----
const searchField = ref('merge_in_num') // 默认检索字段，可调整
const searchOrder = ref('desc') // 排序方式 desc/asc
const showSearchModal = ref(false)
const searchLoading = ref(false)
const searchTableData = ref([])
const searchPage = ref(1)
const searchPageSize = ref(20)
const searchTotal = ref(0)
const searchAllData = ref([])

// 弹窗状态保持（keepalive 组件导航时自动保存/恢复）
watch(filterActive, (newVal) => {
  if (newVal && showFilter.value) {
    _filterWasOpenBeforeResults = true
    showFilter.value = false
  } else if (!newVal && _filterWasOpenBeforeResults) {
    nextTick(() => {
      showFilter.value = true
      _filterWasOpenBeforeResults = false
    })
  }
})

onDeactivated(() => {
  savePopupState()
  _filterWasOpenBeforeResults = false
  filterActive.value = false
  showSearchModal.value = false
  showFilter.value = false
})

onActivated(() => {
  nextTick(() => { restorePopupState() })
})

// 检索结果表格列定义（动态显示城市、字段值及操作）
const searchColumns = computed(() => [
  { title: 'ID', key: 'id', width: 80, hidden: true },
  { title: '路线序号', key: 'route_order', width: 120 },
  { 
    title: searchFieldsOptions.find(f => f.value === searchField.value)?.label || '字段值',
    key: searchField.value,
    width: 150,
  },
  { 
    title: '操作', key: 'actions', width: 100,
    render: (row) => h(NButton, { size: 'small', onClick: () => {
      savePopupState()
      showSearchModal.value = false
      nextTick(() => {
        const targetPath = `/testroute/city/${encodeURIComponent(row.city)}`
        const query = { routeOrder: String(row.route_order) }
        router.push({ path: targetPath, query })
      })
    } }, { default: () => '查看详情' })
  }
])

// 高级检索触发
async function handleAdvancedSearch() {
  if (!searchField.value) {
    message.warning('请选择检索字段')
    return
  }
  searchPage.value = 1
  await fetchSearchResults()
  showSearchModal.value = true   // 打开结果弹窗
}

function toggleSearchOrder() {
  searchOrder.value = searchOrder.value === 'desc' ? 'asc' : 'desc'
}

async function fetchSearchResults() {
  searchLoading.value = true
  try {
    const res = await mapwayApi.searchRouteDetail({
      field: searchField.value,
      page: 1,
      page_size: 9999,
      order: searchOrder.value,
    })
    searchAllData.value = res.data || []
    searchTotal.value = searchAllData.value.length
    searchPage.value = 1
    searchTableData.value = searchAllData.value.slice(0, searchPageSize.value)
  } catch (e) {
    message.error('检索失败')
  } finally {
    searchLoading.value = false
  }
}

function onSearchPageChange(page) {
  searchPage.value = page
  searchTableData.value = searchAllData.value.slice((page - 1) * searchPageSize.value, page * searchPageSize.value)
}
function onSearchPageSizeChange(pageSize) {
  searchPageSize.value = pageSize
  searchPage.value = 1
  searchTableData.value = searchAllData.value.slice(0, pageSize)
}


// ★ 列 key 必须和模型字段完全一致：area, city
const columns = [
  { title: '区域名称', key: 'area' },
  {
    title: '城市列表',
    key: 'city',
    ellipsis: false,
    render(row) {
      const cities = row.city ? row.city.split('、') : []
      return h('div', cities.map(city =>
        h('span', {
          draggable: 'true',
          style: {
            color: 'var(--primary-color)',
            cursor: 'pointer',
            marginRight: '8px',
            textDecoration: 'underline',
            padding: '2px 4px',
            borderRadius: '4px',
            transition: 'background 0.2s',
          },
          onClick: () => {
            // 点击跳转详情页
            router.push(`/testroute/city/${encodeURIComponent(city.trim())}`)
          },
          onDragstart: (e) => {
            e.dataTransfer.setData('text/plain', JSON.stringify({
              city: city.trim(),
              fromAreaId: row.id
            }))
            e.target.style.opacity = '0.5'
          },
          onDragend: (e) => {
            e.target.style.opacity = '1'
          }
        }, city.trim())
      ))
    }
  },
  { title: '创建时间', key: 'created_at', width: 180 },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    render(row) {
      const buttons = []
      if (canUpdateArea.value) {
        buttons.push(h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }))
      }
      if (canDeleteArea.value) {
        buttons.push(h(NButton, { size: 'small', type: 'error', class: 'ml-2', onClick: () => handleDelete(row.id) }, { default: () => '删除' }))
      }
      return h('div', buttons)
    }
  }
]

async function fetchData(page) {
  loading.value = true
  try {
    const res = await mapwayApi.getMapwayList({
      page: page || pagination.page,
      page_size: pagination.pageSize,
      area: searchForm.keyword,
      project_type: 'cooperative',
    })
    tableData.value = res.data || []
    pagination.itemCount = res.total || 0
    pagination.page = res.page || 1
  } catch (e) {
    message.error('加载区域数据失败，请稍后重试')
    console.error(e)
  } finally {
    loading.value = false
  }
}

// ---------- CRUD ----------
const showModal = ref(false)
const isEdit = ref(false)
// ★ 表单字段改为 area 和 city
const formData = reactive({ id: null, area: '', city: '' })
const formRef = ref(null)
const formRules = {
  area: { required: true, message: '请输入区域名称', trigger: 'blur' },
  city: { required: true, message: '请输入城市列表', trigger: 'blur' },
}
const modalTitle = computed(() => isEdit.value ? '编辑区域' : '新增区域')

function resetForm() {
  formData.id = null; formData.area = ''; formData.city = ''
}
function handleCreate() { resetForm(); isEdit.value = false; showModal.value = true }
function handleEdit(row) {
  isEdit.value = true; showModal.value = true
  formData.id = row.id
  formData.area = row.area
  formData.city = row.city
}

async function submitForm() {
  await formRef.value?.validate()
  if (isEdit.value) {
    await mapwayApi.updateMapway({ id: formData.id, area: formData.area, city: formData.city, project_type: 'cooperative' })
    message.success('更新成功')
  } else {
    await mapwayApi.createMapway({ area: formData.area, city: formData.city, project_type: 'cooperative' })
    message.success('创建成功')
  }
  showModal.value = false
  fetchData()
}

function handleDelete(id) {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除该区域吗？',
    positiveText: '确定',
    onPositiveClick: async () => {
      await mapwayApi.deleteMapway({ mapway_id: id })
      message.success('删除成功')
      fetchData()
    }
  })
}

function getRowProps(row) {
  return {
    ondragover: (e) => {
      e.preventDefault() // 必须阻止才能接受 drop
    },
    ondrop: async (e) => {
      e.preventDefault()
      try {
        const data = JSON.parse(e.dataTransfer.getData('text/plain'))
        if (data.fromAreaId === row.id) {
          message.warning('不能移动到同一区域')
          return
        }
        await mapwayApi.moveCity({
          city: data.city,
          from_area_id: data.fromAreaId,
          to_area_id: row.id
        })
        message.success(`已将 ${data.city} 移动到 ${row.area}`)
        fetchData() // 刷新列表
      } catch (err) {
        message.error('移动失败')
      }
    }
  }
}

const routeCacheStore = useRouteCacheStore()

function onPageChange(page) { fetchData(page) }
function onPageSizeChange(size) { pagination.pageSize = size; fetchData(1) }
onMounted(() => {
  nextTick(() => { restorePopupState() })
  fetchData(1).then(() => {
    const cities = tableData.value.map(r => r.city).filter(Boolean)
    if (cities.length > 0) {
      routeCacheStore.preloadAllCooperative(cities, 800)
    }
  })
})

</script>

<style scoped>
.p-4 { padding: 16px; }
.mb-4 { margin-bottom: 16px; }
.ml-2 { margin-left: 8px; }
.filter-conditions { display: flex; flex-direction: column; gap: 6px; }
.filter-row { display: flex; align-items: center; gap: 8px; }
.filter-footer { margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee; }
.filter-actions { margin-top: 8px; display: flex; gap: 8px; }
</style>