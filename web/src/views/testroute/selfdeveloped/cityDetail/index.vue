<template>
  <div class="page-container" ref="pageContainerRef">
    <div class="header-row">
      <n-button @click="$router.push('/testroute/selfdeveloped')" class="back-btn" text>
        <template #icon>
          <n-icon size="18">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </n-icon>
        </template>
        自研项目区域
      </n-button>
      <span class="page-title">{{ cityName }} - 自研测试路线详情</span>
    </div>
    <n-card class="card-flex">
      <div class="top-section" ref="topSectionRef">
        <div class="mb-4" style="display: flex; align-items: center; gap: 12px;">
          <n-button type="primary" v-if="canCreateRoute" @click="addRoute">新增路线</n-button>
        </div>
      </div>

      <div class="content-layout">
        <div class="sidebar-tabs">
          <div
            v-for="tab in tabOptions"
            :key="tab.value"
            :class="['sidebar-tab', { active: activeTab === tab.value }]"
            @click="activeTab = tab.value"
          >
            <n-tag :type="tab.type" size="small" class="tab-tag">{{ tab.label }}</n-tag>
            <span class="tab-count">{{ getGroupCount(tab.value) }}</span>
          </div>
        </div>
        <div class="table-wrapper" ref="tableWrapperRef">
          <n-data-table
            v-if="!loading && currentGroupData.length > 0"
            :columns="columns"
            :data="currentGroupData"
            :bordered="true"
            :single-line="false"
            :row-key="(row) => row.id"
            :max-height="wrapperHeight"
            :scroll-x="totalWidth"
          />
          <n-empty v-if="!loading && currentGroupData.length === 0" description="暂无路线数据" />
        </div>
        <div v-if="loading" class="loading-overlay">
          <n-spin :show="true" description="数据加载中，请稍候..." />
        </div>
      </div>
    </n-card>

    <!-- 新增/编辑弹窗 -->
    <n-modal v-model:show="showModal" :title="modalTitle" style="width: 800px" preset="card" :mask-closable="false">
      <n-form :model="formData" ref="formRef" label-placement="left" label-width="120">
        <n-grid cols="2" x-gap="12">
          <n-gi>
            <n-form-item label="路线编号" path="route_code">
              <n-input v-model:value="formData.route_code" placeholder="请输入路线编号" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="推荐维度" path="recommend_dimension">
              <n-select v-model:value="formData.recommend_dimension" :options="dimensionOptions" placeholder="请选择" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="路线类型" path="route_type">
              <n-select v-model:value="formData.route_type" :options="routeTypeOptions" placeholder="请选择" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="里程KM" path="mileage">
              <n-input v-model:value="formData.mileage" placeholder="里程数" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="起点" path="start_point">
              <n-input v-model:value="formData.start_point" placeholder="起点" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="终点" path="end_point">
              <n-input v-model:value="formData.end_point" placeholder="终点" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="收费站" path="toll_station">
              <n-input-number v-model:value="formData.toll_station" :min="0" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="服务区" path="service_area">
              <n-input-number v-model:value="formData.service_area" :min="0" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="匝道" path="ramp">
              <n-input-number v-model:value="formData.ramp" :min="0" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="施工场景" path="construction_scene">
              <n-input-number v-model:value="formData.construction_scene" :min="0" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="路线链接">
          <n-input v-model:value="formData.route_link" placeholder="请输入路线链接" />
        </n-form-item>
        <n-form-item label="百度地图截图">
          <n-upload
            multiple
            :default-file-list="defaultFileList"
            @update:file-list="onFileListChange"
            list-type="image-card"
            :max="6"
          >
            <n-button>上传图片</n-button>
          </n-upload>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="submitForm">保存</n-button>
        </n-space>
      </template>
    </n-modal>
    <n-modal
      v-model:show="previewShow"
      :mask-closable="true"
      :close-on-esc="true"
      :transform-origin="'center'"
      style="width: auto; max-width: 90vw"
    >
      <div style="display:flex;justify-content:center;align-items:center;padding:16px">
        <img :src="previewSrc" style="max-width:90vw;max-height:85vh;object-fit:contain" />
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, h, onMounted, nextTick, onBeforeUnmount, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage, useDialog, NButton, NTag, NIcon, NEmpty, NInputNumber, NUpload, NInput, NSelect, NPopconfirm, NSpin, NModal } from 'naive-ui'
import mapwayApi from '@/api/mapway'
import { usePermissionStore } from '@/store'
import { useRouteCacheStore } from '@/store'

const permissionStore = usePermissionStore()
const routeCacheStore = useRouteCacheStore()
function hasPermission(method, path) {
  return permissionStore.accessApis.includes(`${method.toLowerCase()}${path}`)
}
const previewSrc = ref('')
const previewShow = ref(false)
const canCreateRoute = computed(() => hasPermission('POST', '/api/v1/mapway/self-developed/route/create'))
const canUpdateRoute = computed(() => hasPermission('POST', '/api/v1/mapway/self-developed/route/update'))
const canDeleteRoute = computed(() => hasPermission('DELETE', '/api/v1/mapway/self-developed/route/delete'))

const route = useRoute()
const message = useMessage()
const dialog = useDialog()
const cityName = route.params.city

const loading = ref(false)
const groups = ref([])
const activeTab = ref('HNOA')
const pageContainerRef = ref(null)
const topSectionRef = ref(null)
const tableWrapperRef = ref(null)
const wrapperHeight = ref(600)
const debounceTimers = {}
let highlightTimer = null

function getStorageKey() {
  return `route_scroll_self_${cityName}_${route.query.routeCode || 'none'}`
}
function hasAlreadyScrolled() {
  return sessionStorage.getItem(getStorageKey()) === 'true'
}
function markAsScrolled() {
  sessionStorage.setItem(getStorageKey(), 'true')
}
function clearScrollMark() {
  Object.keys(sessionStorage).forEach(key => {
    if (key.startsWith('route_scroll_self_')) {
      sessionStorage.removeItem(key)
    }
  })
}

const dimensionOptions = [
  { label: '高', value: '高' },
  { label: '中', value: '中' },
  { label: '低', value: '低' },
]
const routeTypeOptions = [
  { label: 'HNOA', value: 'HNOA' },
  { label: 'CNOA', value: 'CNOA' },
  { label: 'LCC', value: 'LCC' },
]

const totalWidth = computed(() => {
  return 80 + 80 + 130 + 100 + 100 + 180 + 250 + 100 + 130 + 130 + 80 + 80 + 80 + 100 + 80
})

function tagType(rt) {
  return rt === 'HNOA' ? 'error' : rt === 'CNOA' ? 'warning' : 'info'
}

const tabOptions = [
  { label: 'HNOA', value: 'HNOA', type: 'error' },
  { label: 'CNOA', value: 'CNOA', type: 'warning' },
  { label: 'LCC', value: 'LCC', type: 'info' },
]

function getGroupCount(routeType) {
  const group = groups.value.find(g => g.route_type === routeType)
  return group ? group.items.length : 0
}

const currentGroupData = computed(() => {
  const group = groups.value.find(g => g.route_type === activeTab.value)
  return group ? group.items : []
})

function updateField(row, field, value) {
  row[field] = value
  if (!row.id) return
  const key = `${row.id}_${field}`
  if (debounceTimers[key]) clearTimeout(debounceTimers[key])
  debounceTimers[key] = setTimeout(async () => {
    try {
      await mapwayApi.updateSelfDevelopedRouteDetail({ id: row.id, [field]: value })
    } catch (e) {
      message.error('保存失败')
    }
  }, 500)
}

const columns = computed(() => {
  const cols = [
    { title: '编号', key: 'id', width: 80, fixed: 'left' },
    {
      title: '城市', key: 'city', width: 80,
      render(row) { return h('span', row.city || '-') }
    },
    {
      title: '路线编号', key: 'route_code', width: 130,
      render(row) {
      return h(NInput, { value: row.route_code, size: 'small', readonly: !canUpdateRoute.value, onUpdateValue: (v) => updateField(row, 'route_code', v) })
    }
    },
    {
      title: '推荐维度', key: 'recommend_dimension', width: 100,
      render(row) {
        return h(NSelect, { value: row.recommend_dimension, size: 'small', options: dimensionOptions, readonly: !canUpdateRoute.value, clearable: true, onUpdateValue: (v) => updateField(row, 'recommend_dimension', v) })
      }
    },
    {
      title: '路线类型', key: 'route_type', width: 120,
      render(row) {
        return h(NSelect, { value: row.route_type, size: 'small', options: routeTypeOptions, readonly: !canUpdateRoute.value, clearable: true, onUpdateValue: (v) => updateField(row, 'route_type', v) })
      }
    },
    {
      title: '路线链接', key: 'route_link', width: 180,
      render(row) {
        return h(NInput, { value: row.route_link, size: 'small', readonly: !canUpdateRoute.value, onUpdateValue: (v) => updateField(row, 'route_link', v) })
      }
    },
    {
      title: '百度地图截图', key: 'baidu_map_screenshot', width: 180,
      render(row) {
        if (row.imageLoading) {
          return h(NSpin, { size: 'small' })
        }
        const count = row.image_count || 0
        if (row.imageList === null) {
          if (count === 0) return null
          const items = []
          for (let i = 0; i < count; i++) {
            items.push(h('div', {
              style: { position: 'relative', display: 'inline-block', marginRight: '8px', marginBottom: '4px' },
              onMouseenter: (e) => {
                const del = e.currentTarget.querySelector('.img-del')
                if (del) del.style.display = 'flex'
              },
              onMouseleave: (e) => {
                const del = e.currentTarget.querySelector('.img-del')
                if (del) del.style.display = 'none'
              },
            }, [
              h('span', {
                style: { color: '#18a058', cursor: 'pointer', fontSize: '13px' },
                onClick: () => loadRouteImage(row, i),
              }, `截图${i + 1}`),
              canUpdateRoute.value ? h('div', {
                class: 'img-del',
                style: { display: 'none', position: 'absolute', top: '-8px', right: '-8px', width: '16px', height: '16px', borderRadius: '50%', background: '#d03050', color: '#fff', fontSize: '11px', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', lineHeight: '16px', textAlign: 'center' },
                onClick: (e) => { e.stopPropagation(); removeImageLazy(row, i) },
              }, '×') : null,
            ]))
          }
          const addBtn = canUpdateRoute.value ? h(
            NUpload,
            { size: 'small', listType: 'image', showFileList: false, customRequest: ({ file, onFinish, onError }) => {
              const reader = new FileReader()
              reader.onload = async (e) => {
                const base64 = e.target.result
                const res = await mapwayApi.getSelfDevelopedRouteImage({ route_id: row.id })
                const imgData = res.data || {}
                let list = []
                if (imgData.baidu_map_screenshot) { try { list = JSON.parse(imgData.baidu_map_screenshot) } catch (_) {} }
                list.push(base64)
                row.imageList = list
                row.baidu_map_screenshot = JSON.stringify(list)
                row.image_count = list.length
                saveRow(row).then(() => { onFinish(); message.success('图片已添加') }).catch(() => { onError(); message.error('保存失败') })
              }
              reader.onerror = () => { onError(); message.error('读取文件失败') }
              reader.readAsDataURL(file.file)
            }},
            { default: () => h('span', { style: { color: '#18a058', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold' } }, '+') }
          ) : null
          return h('div', { style: { display: 'flex', flexDirection: 'column', gap: '2px' } }, [
            h('div', { style: { display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' } }, items),
            addBtn ? h('div', {}, [addBtn]) : null,
          ])
        }
        const imageList = row.imageList || []
        const imageItems = imageList.map((img, index) =>
          h('div', {
            style: { position: 'relative', display: 'inline-block', marginRight: '8px', marginBottom: '4px' },
            onMouseenter: (e) => {
              const del = e.currentTarget.querySelector('.img-del')
              if (del) del.style.display = 'flex'
            },
            onMouseleave: (e) => {
              const del = e.currentTarget.querySelector('.img-del')
              if (del) del.style.display = 'none'
            },
          }, [
            h('span', {
              style: { color: '#18a058', cursor: 'pointer', fontSize: '13px' },
              onClick: () => previewImage(row, index),
            }, `截图${index + 1}`),
            canUpdateRoute.value ? h('div', {
              class: 'img-del',
              style: { display: 'none', position: 'absolute', top: '-8px', right: '-8px', width: '16px', height: '16px', borderRadius: '50%', background: '#d03050', color: '#fff', fontSize: '11px', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', lineHeight: '16px', textAlign: 'center' },
              onClick: (e) => { e.stopPropagation(); removeImage(row, index) },
            }, '×') : null,
          ])
        )
        const addBtn = canUpdateRoute.value ? h(
          NUpload,
          { size: 'small', listType: 'image', showFileList: false, customRequest: ({ file, onFinish, onError }) => {
            const reader = new FileReader()
            reader.onload = (e) => {
              const base64 = e.target.result
              const newList = [...(row.imageList || []), base64]
              row.imageList = newList
              row.baidu_map_screenshot = JSON.stringify(newList)
              row.image_count = newList.length
              saveRow(row).then(() => { onFinish(); message.success('图片已添加') }).catch(() => { onError(); message.error('保存失败') })
            }
            reader.onerror = () => { onError(); message.error('读取文件失败') }
            reader.readAsDataURL(file.file)
          }},
          { default: () => h('span', { style: { color: '#18a058', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold' } }, '+') }
        ) : null
        return h('div', { style: { display: 'flex', flexDirection: 'column', gap: '2px' } }, [
          h('div', { style: { display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' } }, imageItems),
          addBtn ? h('div', {}, [addBtn]) : null,
        ])
      }
    },
    {
      title: '里程KM', key: 'mileage', width: 100,
      render(row) {
        return h(NInput, { value: row.mileage, size: 'small', readonly: !canUpdateRoute.value, onUpdateValue: (v) => updateField(row, 'mileage', v) })
      }
    },
    {
      title: '起点', key: 'start_point', width: 130,
      render(row) {
        return h(NInput, { value: row.start_point, size: 'small', readonly: !canUpdateRoute.value, onUpdateValue: (v) => updateField(row, 'start_point', v) })
      }
    },
    {
      title: '终点', key: 'end_point', width: 130,
      render(row) {
        return h(NInput, { value: row.end_point, size: 'small', readonly: !canUpdateRoute.value, onUpdateValue: (v) => updateField(row, 'end_point', v) })
      }
    },
    {
      title: '收费站', key: 'toll_station', width: 80,
      render(row) {
        return h(NInputNumber, { value: row.toll_station, size: 'small', min: 0, showButton: false, readonly: !canUpdateRoute.value, onUpdateValue: (v) => updateField(row, 'toll_station', v) })
      }
    },
    {
      title: '服务区', key: 'service_area', width: 80,
      render(row) {
        return h(NInputNumber, { value: row.service_area, size: 'small', min: 0, showButton: false, readonly: !canUpdateRoute.value, onUpdateValue: (v) => updateField(row, 'service_area', v) })
      }
    },
    {
      title: '匝道', key: 'ramp', width: 80,
      render(row) {
        return h(NInputNumber, { value: row.ramp, size: 'small', min: 0, showButton: false, readonly: !canUpdateRoute.value, onUpdateValue: (v) => updateField(row, 'ramp', v) })
      }
    },
    {
      title: '施工场景', key: 'construction_scene', width: 100,
      render(row) {
        return h(NInputNumber, { value: row.construction_scene, size: 'small', min: 0, showButton: false, readonly: !canUpdateRoute.value, onUpdateValue: (v) => updateField(row, 'construction_scene', v) })
      }
    },
  ]
  if (canDeleteRoute.value) {
    cols.push({
      title: '操作', key: 'actions', width: 80, fixed: 'right',
      render(row) {
        return h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
          default: () => '确认删除？'
        })
      }
    })
  }
  return cols
})

async function scrollToTargetRow(routeCode) {
  if (!routeCode || hasAlreadyScrolled()) return
  markAsScrolled()
  let targetGroup = null
  let targetIndex = -1
  for (const group of groups.value) {
    const idx = (group.items || []).findIndex(r => String(r.route_code) === String(routeCode))
    if (idx !== -1) {
      targetGroup = group.route_type
      targetIndex = idx
      break
    }
  }
  if (!targetGroup) return
  activeTab.value = targetGroup
  await nextTick()
  await nextTick()
  const table = tableWrapperRef.value?.querySelector('.n-data-table')
  if (!table) return
  const rows = Array.from(table.querySelectorAll('tr.n-data-table-tr')).filter(tr =>
    !tr.classList.contains('n-data-table-empty-row')
  )
  if (targetIndex >= rows.length) return
  const rowEl = rows[targetIndex]
  rowEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
  rowEl.style.backgroundColor = '#fff3cd'
  if (highlightTimer) clearTimeout(highlightTimer)
  highlightTimer = setTimeout(() => { rowEl.style.backgroundColor = '' }, 3000)
}

async function fetchData(forceRefresh = false) {
  const cached = routeCacheStore.getSelfDeveloped(cityName)
  if (cached && !forceRefresh) {
    groups.value = cached
    await nextTick()
    updateLayout()
    if (route.query.routeType) {
      activeTab.value = route.query.routeType
    }
    if (route.query.routeCode) {
      setTimeout(() => scrollToTargetRow(route.query.routeCode), 300)
    }
    fetchData(true)
    return
  }
  if (!cached) {
    loading.value = true
  }
  try {
    const res = await mapwayApi.getSelfDevelopedRouteDetailList({
      city: cityName,
      page_size: 1000,
    })
    const data = res.data || []
    data.forEach(g => {
      (g.items || []).forEach(row => {
        row.imageList = null
        row.imageLoading = false
      })
    })
    routeCacheStore.setSelfDeveloped(cityName, data)
    groups.value = data
  } catch (e) {
    if (!cached) {
      message.error('加载路线数据失败')
    }
    console.error(e)
  } finally {
    loading.value = false
    await nextTick()
    updateLayout()
    if (route.query.routeType) {
      activeTab.value = route.query.routeType
    }
    if (route.query.routeCode) {
      setTimeout(() => scrollToTargetRow(route.query.routeCode), 300)
    }
  }
}

const showModal = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const formData = reactive({
  id: null, route_code: '', recommend_dimension: null, route_type: null,
  route_link: '', baidu_map_screenshot: '', mileage: '',
  start_point: '', end_point: '',
  toll_station: null, service_area: null, ramp: null, construction_scene: null,
})
const defaultFileList = ref([])
const modalTitle = computed(() => isEdit.value ? '编辑路线' : '新增路线')

function resetForm() {
  const intFields = ['toll_station', 'service_area', 'ramp', 'construction_scene']
  Object.keys(formData).forEach(k => {
    if (k === 'id') {
      formData[k] = null
    } else if (intFields.includes(k)) {
      formData[k] = null
    } else {
      formData[k] = ''
    }
  })
  defaultFileList.value = []
}

function onFileListChange(fileList) {
  const urls = fileList.map(f => f.url || URL.createObjectURL(f.file))
  formData.baidu_map_screenshot = JSON.stringify(urls)
}

function addRoute() {
  mapwayApi.createSelfDevelopedRouteDetail({ city: cityName }).then(() => {
    message.success('新增一行，请编辑')
    routeCacheStore.invalidateSelfDeveloped(cityName)
    fetchData(true)
  }).catch(() => {
    message.error('新增失败')
  })
}

function handleEdit(row) {
  isEdit.value = true
  showModal.value = true
  Object.assign(formData, {
    id: row.id, route_code: row.route_code, recommend_dimension: row.recommend_dimension,
    route_type: row.route_type, route_link: row.route_link, mileage: row.mileage,
    start_point: row.start_point, end_point: row.end_point,
    toll_station: row.toll_station, service_area: row.service_area,
    ramp: row.ramp, construction_scene: row.construction_scene,
  })
  formData.baidu_map_screenshot = row.baidu_map_screenshot || ''
  if (row.baidu_map_screenshot) {
    try {
      defaultFileList.value = JSON.parse(row.baidu_map_screenshot).map((url, i) => ({ id: `img${i}`, url, status: 'finished' }))
    } catch { defaultFileList.value = [] }
  } else {
    defaultFileList.value = []
  }
}

async function submitForm() {
  const payload = {
    city: cityName,
    id: formData.id,
    route_code: formData.route_code,
    recommend_dimension: formData.recommend_dimension,
    route_type: formData.route_type,
    route_link: formData.route_link,
    baidu_map_screenshot: formData.baidu_map_screenshot,
    mileage: formData.mileage,
    start_point: formData.start_point,
    end_point: formData.end_point,
    toll_station: formData.toll_station !== null && formData.toll_station !== '' ? Number(formData.toll_station) : null,
    service_area: formData.service_area !== null && formData.service_area !== '' ? Number(formData.service_area) : null,
    ramp: formData.ramp !== null && formData.ramp !== '' ? Number(formData.ramp) : null,
    construction_scene: formData.construction_scene !== null && formData.construction_scene !== '' ? Number(formData.construction_scene) : null,
  }
  if (isEdit.value) {
    await mapwayApi.updateSelfDevelopedRouteDetail(payload)
    message.success('更新成功')
  } else {
    await mapwayApi.createSelfDevelopedRouteDetail(payload)
    message.success('创建成功')
  }
  showModal.value = false
  routeCacheStore.invalidateSelfDeveloped(cityName)
  fetchData(true)
}

function handleDelete(id) {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除该路线吗？',
    positiveText: '确定',
    onPositiveClick: async () => {
      await mapwayApi.deleteSelfDevelopedRouteDetail({ route_id: id })
      message.success('删除成功')
      routeCacheStore.invalidateSelfDeveloped(cityName)
      fetchData(true)
    }
  })
}

async function loadRouteImage(row, previewIndex) {
  if (row.imageLoading) return
  if (row.imageList !== null) {
    previewImage(row, previewIndex)
    return
  }
  row.imageLoading = true
  try {
    const res = await mapwayApi.getSelfDevelopedRouteImage({ route_id: row.id })
    const imgData = res.data || {}
    if (imgData.baidu_map_screenshot) {
      try { row.imageList = JSON.parse(imgData.baidu_map_screenshot) } catch (e) { row.imageList = [] }
    } else {
      row.imageList = []
    }
    row.baidu_map_screenshot = imgData.baidu_map_screenshot
    row.image_count = row.imageList.length
    nextTick(() => previewImage(row, previewIndex))
  } catch (e) {
    row.imageList = []
  } finally {
    row.imageLoading = false
  }
}

function previewImage(row, index) {
  const list = row.imageList || []
  if (list.length === 0) return
  const i = index ?? 0
  previewSrc.value = list[i]
  previewShow.value = true
}

async function removeImageLazy(row, index) {
  const res = await mapwayApi.getSelfDevelopedRouteImage({ route_id: row.id })
  const imgData = res.data || {}
  let list = []
  if (imgData.baidu_map_screenshot) { try { list = JSON.parse(imgData.baidu_map_screenshot) } catch (_) {} }
  if (index < 0 || index >= list.length) return
  list.splice(index, 1)
  row.imageList = list
  row.baidu_map_screenshot = JSON.stringify(list)
  row.image_count = list.length
  await saveRow(row)
  message.success('图片已删除')
}

async function saveRow(row) {
  if (!row.id) return
  await mapwayApi.updateSelfDevelopedRouteDetail({ id: row.id, baidu_map_screenshot: row.baidu_map_screenshot })
}

function removeImage(row, index) {
  const newList = [...row.imageList]
  newList.splice(index, 1)
  row.imageList = newList
  row.baidu_map_screenshot = JSON.stringify(newList)
  saveRow(row).then(() => message.success('图片已删除')).catch(() => message.error('删除失败'))
}

function updateLayout() {
  if (!pageContainerRef.value || !topSectionRef.value) return
  const topBottom = topSectionRef.value.getBoundingClientRect().bottom
  const available = window.innerHeight - topBottom - 120
  wrapperHeight.value = Math.max(available, 200)
}

onMounted(() => {
  clearScrollMark()
  fetchData()
  nextTick(() => {
    updateLayout()
    window.addEventListener('resize', updateLayout)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateLayout)
  Object.values(debounceTimers).forEach(clearTimeout)
})
</script>

<style scoped>
.page-container { height: 100vh; display: flex; flex-direction: column; padding: 16px; }
.header-row { flex-shrink: 0; display: flex; align-items: center; justify-content: center; position: relative; margin-bottom: 12px; }
.page-title { font-size: 16px; font-weight: 600; color: #ff6a00; }
.back-btn { position: absolute; left: 0; color: #ff6a00 !important; font-size: 16px; }
.back-btn:hover { color: #3347ff !important; }
.card-flex { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.top-section { flex-shrink: 0; }
.content-layout { flex: 1; min-height: 0; display: flex; gap: 0; overflow: hidden; position: relative; }
.loading-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.7); z-index: 100; }
.sidebar-tabs { flex-shrink: 0; display: flex; flex-direction: column; gap: 0; border-right: 1px solid #e0e0e0; padding: 0; background: #fafafa; }
.sidebar-tab { padding: 14px 16px; cursor: pointer; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid #e8e8e8; transition: all 0.2s; }
.sidebar-tab:hover { background: #f0f0f0; }
.sidebar-tab.active { background: #fff; border-right: 3px solid #18a058; }
.tab-tag { min-width: 50px; justify-content: center; }
.tab-count { color: #999; font-size: 12px; }
.table-wrapper { flex: 1; min-height: 0; overflow: auto; }
.mb-4 { margin-bottom: 16px; }
.table-wrapper :deep(.n-data-table-thead) { position: sticky; top: 0; z-index: 10; background: #fff; }
.route-link-cell { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; color: #2080f0; }
.route-link-cell:hover { text-decoration: underline; }
</style>