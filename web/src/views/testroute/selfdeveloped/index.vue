d:\adastest-copy\adas-domain-test\web\src\views\testroute\selfdeveloped\index.vue
<template>
  <div class="p-4">
    <n-card title="自研项目区域管理" :bordered="false" class="mb-4">
      <n-form :model="searchForm" label-placement="left">
        <n-space>
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
          </n-form-item>
        </n-space>
      </n-form>
    </n-card>

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
        <n-button text style="height: 34px" @click="toggleSearchOrder" :type="searchOrder === 'desc' ? 'warning' : 'default'">
          {{ searchOrder === 'desc' ? '🔽' : '🔼' }}
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
import { ref, reactive, computed, h, onMounted } from 'vue'
import { useMessage, useDialog, NButton, NSpin } from 'naive-ui'
import mapwayApi from '@/api/mapway'
import { useRouter } from 'vue-router'
import { usePermissionStore } from '@/store'
import { useRouteCacheStore } from '@/store'
const permissionStore = usePermissionStore()
function hasPermission(method, path) {
  const api = `${method.toLowerCase()}${path}`
  return permissionStore.accessApis.includes(api)
}
const canCreateArea = computed(() => hasPermission('POST', '/api/v1/mapway/create'))
const canUpdateArea = computed(() => hasPermission('POST', '/api/v1/mapway/update'))
const canDeleteArea = computed(() => hasPermission('DELETE', '/api/v1/mapway/delete'))

const message = useMessage()
const dialog = useDialog()
const router = useRouter()

const searchForm = reactive({ keyword: '' })
function handleSearch() { fetchData(1) }
function resetSearch() { searchForm.keyword = ''; fetchData(1) }

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 10, itemCount: 0 })

const searchField = ref('recommend_dimension')
const searchOrder = ref('desc')
const showSearchModal = ref(false)
const searchLoading = ref(false)
const searchTableData = ref([])
const searchPage = ref(1)
const searchPageSize = ref(20)
const searchTotal = ref(0)
const searchAllData = ref([])

const searchFieldsOptions = [
  { label: '推荐维度', value: 'recommend_dimension' },
  { label: '里程KM', value: 'mileage' },
  { label: '收费站', value: 'toll_station' },
  { label: '服务区', value: 'service_area' },
  { label: '匝道', value: 'ramp' },
  { label: '施工场景', value: 'construction_scene' },
]

const searchColumns = computed(() => [
  { title: 'ID', key: 'id', width: 80 },
  { title: '路线编号', key: 'route_code', width: 120 },
  { title: '城市', key: 'city', width: 100 },
  {
    title: searchFieldsOptions.find(f => f.value === searchField.value)?.label || '字段值',
    key: searchField.value,
    width: 150,
  },
  {
    title: '操作', key: 'actions', width: 100,
    render: (row) => h(NButton, { size: 'small', onClick: () => {
      const targetPath = `/testroute/selfdeveloped/city/${encodeURIComponent(row.city)}`
      const query = { routeCode: String(row.route_code), routeType: row.route_type || '' }
      router.push({ path: targetPath, query })
    } }, { default: () => '查看详情' })
  }
])

async function handleAdvancedSearch() {
  if (!searchField.value) {
    message.warning('请选择检索字段')
    return
  }
  searchPage.value = 1
  await fetchSearchResults()
  showSearchModal.value = true
}

function toggleSearchOrder() {
  searchOrder.value = searchOrder.value === 'desc' ? 'asc' : 'desc'
}

async function fetchSearchResults() {
  searchLoading.value = true
  try {
    const res = await mapwayApi.searchSelfDevelopedRouteDetail({
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
            router.push(`/testroute/selfdeveloped/city/${encodeURIComponent(city.trim())}`)
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
      project_type: 'self_developed',
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

const showModal = ref(false)
const isEdit = ref(false)
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
    await mapwayApi.updateMapway({ id: formData.id, area: formData.area, city: formData.city, project_type: 'self_developed' })
    message.success('更新成功')
  } else {
    await mapwayApi.createMapway({ area: formData.area, city: formData.city, project_type: 'self_developed'  })
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
      e.preventDefault()
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
        fetchData()
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
  fetchData(1).then(() => {
    const cities = tableData.value.map(r => r.city).filter(Boolean)
    if (cities.length > 0) {
      routeCacheStore.preloadAllSelfDeveloped(cities, 800)
    }
  })
})
</script>

<style scoped>
.p-4 { padding: 16px; }
.mb-4 { margin-bottom: 16px; }
.ml-2 { margin-left: 8px; }
</style>