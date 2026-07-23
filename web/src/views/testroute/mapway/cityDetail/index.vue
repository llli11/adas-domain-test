<template>
  <div class="page-container" ref="pageContainerRef">
    <div class="header-row">
      <n-button @click="$router.push('/testroute')" class="back-btn" text>
        <template #icon>
          <n-icon size="18">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </n-icon>
        </template>
        合作项目区域
      </n-button>
      <span class="page-title">{{ cityName }} - 测试路线详情</span>
    </div>
    <n-card class="card-flex">
      <div class="top-section" ref="topSectionRef">
        <div class="mb-4" style="display: flex; align-items: center; gap: 12px;">
          <n-button type="primary" v-if="canCreateRoute" @click="addRoute">新增路线</n-button>
          <n-form-item label="推荐测试天数" style="flex: 1; margin-bottom: 0;">
            <n-input
              v-model:value="commonRecommendDays"
              placeholder="统一设置"
              :readonly="!canUpdateRoute"
              @update:value="updateAllRecommendDays"
            />
          </n-form-item>
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
            ref="tableRef"
            :columns="columns"
            :data="currentGroupData"
            :bordered="true"
            :single-line="false"
            :row-key="(row) => row.id"
            :max-height="wrapperHeight"
            :scroll-x="totalWidth"
            :virtual-scroll="false"
          />
          <n-empty v-if="!loading && currentGroupData.length === 0" description="暂无路线数据" />
        </div>
        <div v-if="loading" class="loading-overlay">
          <n-spin :show="true" description="数据加载中，请稍候..." />
        </div>
      </div>
    </n-card>
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
defineOptions({ name: '合作项目城市详情' })
import { ref, computed, h, onMounted, nextTick, onBeforeUnmount, watch, onActivated } from 'vue'
import { useRoute } from 'vue-router'
import { NButton, NInput, NSelect, NUpload, NPopconfirm, NTag, NEmpty, useMessage, NFormItem, NGrid, NGi, NSpin, NModal } from 'naive-ui'
import mapwayApi from '@/api/mapway'
import { NIcon } from 'naive-ui'
import { usePermissionStore } from '@/store'
import { useRouteCacheStore } from '@/store'

const permissionStore = usePermissionStore()
const routeCacheStore = useRouteCacheStore()
function hasPermission(method, path) {
  const api = `${method.toLowerCase()}${path}`
  return permissionStore.accessApis.includes(api)
}
const previewSrc = ref('')
const previewShow = ref(false)
const canCreateRoute = computed(() => hasPermission('POST', '/api/v1/mapway/route/create'))
const canUpdateRoute = computed(() => hasPermission('POST', '/api/v1/mapway/route/update'))
const canDeleteRoute = computed(() => hasPermission('DELETE', '/api/v1/mapway/route/delete'))

const route = useRoute()
const message = useMessage()
const cityName = route.params.city
const loading = ref(false)
const groups = ref([])
const activeTab = ref('CNCA')
const commonRecommendDays = ref('')
const tableRef = ref(null)
const topSectionRef = ref(null)
const pageContainerRef = ref(null)
const tableWrapperRef = ref(null)
const wrapperHeight = ref(600)
const debounceTimers = {}
let recommendTimer = null
let highlightTimer = null

const tabOptions = [
  { label: 'CNCA', value: 'CNCA', type: 'warning' },
  { label: 'HNCA', value: 'HNCA', type: 'error' },
]

const routeTypeMap = { CNCA: '城区工况', HNCA: '高速工况' }

function getGroupCount(routeType) {
  const group = groups.value.find(g => g.route_type === routeType)
  return group ? group.items.length : 0
}

const currentGroupData = computed(() => {
  const group = groups.value.find(g => g.route_type === activeTab.value)
  return group ? group.items : []
})

function getStorageKey() {
  return `route_scroll_${cityName}_${route.query.routeOrder || 'none'}`
}
function hasAlreadyScrolled() {
  return sessionStorage.getItem(getStorageKey()) === 'true'
}
function markAsScrolled() {
  sessionStorage.setItem(getStorageKey(), 'true')
}
function clearScrollMark() {
  Object.keys(sessionStorage).forEach(key => {
    if (key.startsWith('route_scroll_')) {
      sessionStorage.removeItem(key)
    }
  })
}

const editableFields = [
  { key: 'route_order', title: '路线序号', type: 'text' },
  { key: 'priority', title: '优先级', type: 'text' },
  { key: 'author', title: '编写人', type: 'text' },
  { key: 'route_type', title: '路线类型', type: 'select', options: [{ label: '城区工况', value: '城区工况' }, { label: '高速工况', value: '高速工况' }] },
  { key: 'mileage', title: '路线里程数', type: 'text' },
  { key: 'duration', title: '路线时长', type: 'text' },
  { key: 'waypoints', title: '途经点信息', type: 'textarea', width: 250 },
  { key: 'route_preference', title: '路线偏好', type: 'text' },
  { key: 'near_store', title: '是否通过门店附近', type: 'text' },
  { key: 'merge_in_num', title: '汇入匝道个数', type: 'number' },
  { key: 'merge_out_num', title: '汇出匝道个数', type: 'number' },
  { key: 'y_intersection_num', title: 'Y型路口个数', type: 'number' },
  { key: 'roundabout_num', title: '环岛个数', type: 'number' },
  { key: 'u_turn_num', title: '掉头次数', type: 'number' },
  { key: 'straight_intersection_num', title: '直行路口个数', type: 'number' },
  { key: 'protected_left_num', title: '有保护左转路口个数', type: 'number' },
  { key: 'unprotected_left_num', title: '无保护左转路口个数', type: 'number' },
  { key: 'protected_right_num', title: '有保护右转路口个数', type: 'number' },
  { key: 'unprotected_right_num', title: '无保护右转路口个数', type: 'number' },
  { key: 'normal_traffic_light_num', title: '正常红绿灯个数', type: 'number' },
  { key: 'flashing_yellow_num', title: '黄灯常闪或常亮个数', type: 'number' },
  { key: 'disabled_traffic_light_num', title: '未启用红绿灯个数', type: 'number' },
  { key: 'special_traffic_light_num', title: '特殊红绿灯个数', type: 'number' },
  { key: 'main_side_switch_num', title: '主辅路切换个数', type: 'number' },
  { key: 'right_turn_lane_num', title: '右转专用道个数', type: 'number' },
  { key: 'variable_lane_num', title: '可变车道个数', type: 'number' },
  { key: 'waiting_lane_num', title: '待转车道个数', type: 'number' },
  { key: 'complexity', title: '路线复杂程度', type: 'text' },
  { key: 'remark', title: '备注', type: 'text' },
]

const totalWidth = computed(() => {
  let sum = 0
  editableFields.forEach(field => {
    sum += field.width || (field.type === 'number' ? 100 : 120)
  })
  sum += 250
  sum += 80
  return sum
})

const columns = computed(() => {
  const cols = []
  let imageColInserted = false

  editableFields.forEach((field) => {
    const col = {
      title: field.title,
      key: field.key,
      width: field.width || (field.type === 'number' ? 100 : 120),
      titleAlign: 'center',
      render: (row) => {
        const val = row[field.key] != null ? String(row[field.key]) : ''
        if (field.type === 'select') {
          return h(NSelect, {
            value: val,
            size: 'small',
            options: field.options || [],
            readonly: !canUpdateRoute.value,
            clearable: true,
            onUpdateValue: (v) => updateField(row, field.key, v),
          })
        }
        if (field.type === 'textarea') {
          return h(NInput, {
            value: val,
            size: 'small',
            type: 'textarea',
            autosize: { minRows: 1, maxRows: 8 },
            readonly: !canUpdateRoute.value,
            onUpdateValue: (v) => updateField(row, field.key, v),
          })
        }
        return h(NInput, {
          value: val,
          size: 'small',
          type: field.type === 'number' ? 'number' : 'text',
          readonly: !canUpdateRoute.value,
          onUpdateValue: (v) => updateField(row, field.key, v),
        })
      },
    }
    if (field.key === 'route_order') {
      col.fixed = 'left'
    }
    cols.push(col)

    if (field.key === 'waypoints' && !imageColInserted) {
      cols.push({
        title: '路线示意图',
    key: 'route_image',
        width: 250,
        titleAlign: 'center',
        render: (row) => {
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
              {
                size: 'small',
                listType: 'image',
                showFileList: false,
                customRequest: ({ file, onFinish, onError }) => {
                  const reader = new FileReader()
                  reader.onload = async (e) => {
                    const base64 = e.target.result
                    const res = await mapwayApi.getRouteImage({ route_id: row.id })
                    const imgData = res.data || {}
                    let list = []
                    if (imgData.route_image) { try { list = JSON.parse(imgData.route_image) } catch (_) {} }
                    list.push(base64)
                    row.imageList = list
                    row.route_image = JSON.stringify(list)
                    row.image_count = list.length
                    saveRow(row).then(() => { onFinish(); message.success('图片已添加') }).catch(() => { onError(); message.error('保存失败') })
                  }
                  reader.onerror = () => { onError(); message.error('读取文件失败') }
                  reader.readAsDataURL(file.file)
                },
              },
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
            {
              size: 'small',
              listType: 'image',
              showFileList: false,
              customRequest: ({ file, onFinish, onError }) => {
                const reader = new FileReader()
                reader.onload = (e) => {
                  const base64 = e.target.result
                  const newList = [...(row.imageList || []), base64]
                  row.imageList = newList
                  row.route_image = JSON.stringify(newList)
                  row.image_count = newList.length
                  saveRow(row).then(() => { onFinish(); message.success('图片已添加') }).catch(() => { onError(); message.error('保存失败') })
                }
                reader.onerror = () => { onError(); message.error('读取文件失败') }
                reader.readAsDataURL(file.file)
              },
            },
            { default: () => h('span', { style: { color: '#18a058', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold' } }, '+') }
          ) : null
          return h('div', { style: { display: 'flex', flexDirection: 'column', gap: '2px' } }, [
            h('div', { style: { display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' } }, imageItems),
            addBtn ? h('div', {}, [addBtn]) : null,
          ])
        },
      })
      imageColInserted = true
    }
  })

  cols.push({
    title: '操作',
    key: 'actions',
    width: 80,
    render: (row) => {
      if (!canDeleteRoute.value) return null
      return h(
        NPopconfirm,
        { onPositiveClick: () => deleteRow(row.id) },
        {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
          default: () => '确认删除？',
        }
      )
    },
  })

  return cols
})

async function scrollToTargetRow(routeOrder) {
  if (!routeOrder || hasAlreadyScrolled()) return

  let targetGroup = null
  let targetIndex = -1
  for (const group of groups.value) {
    const idx = (group.items || []).findIndex(r => String(r.route_order) === String(routeOrder))
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

  const wrapper = tableWrapperRef.value
  if (!wrapper) return
  const table = wrapper.querySelector('.n-data-table')
  if (!table) return
  const rows = Array.from(table.querySelectorAll('tr.n-data-table-tr')).filter(tr =>
    !tr.classList.contains('n-data-table-empty-row')
  )
  if (targetIndex >= rows.length) return
  const rowEl = rows[targetIndex]
  rowEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
  markAsScrolled()
  rowEl.style.backgroundColor = '#fff3cd'
  if (highlightTimer) clearTimeout(highlightTimer)
  highlightTimer = setTimeout(() => { rowEl.style.backgroundColor = '' }, 3000)
}

async function fetchData(forceRefresh = false) {
  const cached = routeCacheStore.getCooperative(cityName)
  if (cached && !forceRefresh) {
    groups.value = cached
    let firstRecommendDays = ''
    for (const g of cached) {
      if (g.items?.length > 0) {
        firstRecommendDays = String(g.items[0].recommend_days || '')
        break
      }
    }
    commonRecommendDays.value = firstRecommendDays
    await nextTick()
    if (route.query.routeOrder) {
      setTimeout(() => scrollToTargetRow(route.query.routeOrder), 300)
    }
    nextTick(() => updateLayout())
    fetchData(true)
    return
  }
  if (!cached) {
    loading.value = true
  }
  try {
    const res = await mapwayApi.getRouteDetailList({
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
    routeCacheStore.setCooperative(cityName, data)
    groups.value = data
    let firstRecommendDays = ''
    for (const g of data) {
      if (g.items?.length > 0) {
        firstRecommendDays = String(g.items[0].recommend_days || '')
        break
      }
    }
    commonRecommendDays.value = firstRecommendDays
  } catch (e) {
    if (!cached) {
      message.error('加载路线数据失败')
    }
  } finally {
    loading.value = false
    await nextTick()
    if (route.query.routeOrder) {
      setTimeout(() => scrollToTargetRow(route.query.routeOrder), 300)
    }
    nextTick(() => updateLayout())
  }
}

// 业务函数
async function updateAllRecommendDays(newVal) {
  const allRows = groups.value.flatMap(g => g.items || [])
  if (!allRows.length) return
  allRows.forEach(row => { row.recommend_days = newVal })
  if (recommendTimer) clearTimeout(recommendTimer)
  recommendTimer = setTimeout(async () => {
    try {
      await Promise.all(allRows.map(row => mapwayApi.updateRouteDetail({ id: row.id, recommend_days: newVal })))
      message.success('推荐测试天数已同步更新')
    } catch (e) {
      message.error('部分更新失败')
    }
  }, 500)
}

async function updateField(row, field, value) {
  row[field] = value
  if (!row.id) {
    try {
      await mapwayApi.createRouteDetail({ city: cityName })
      message.success('新记录已创建，继续编辑')
      routeCacheStore.invalidateCooperative(cityName)
      await fetchData(true)
    } catch (e) {
      message.error('创建失败')
    }
    return
  }
  const key = `${row.id}_${field}`
  if (debounceTimers[key]) clearTimeout(debounceTimers[key])
  debounceTimers[key] = setTimeout(async () => {
    try {
      await mapwayApi.updateRouteDetail({ id: row.id, [field]: value })
    } catch (e) {
      message.error('保存失败')
    }
  }, 500)
}

async function loadRouteImage(row, previewIndex) {
  if (row.imageLoading) return
  if (row.imageList !== null) {
    previewImage(row, previewIndex)
    return
  }
  row.imageLoading = true
  try {
    const res = await mapwayApi.getRouteImage({ route_id: row.id })
    const imgData = res.data || {}
    if (imgData.route_image) {
      try { row.imageList = JSON.parse(imgData.route_image) } catch (e) { row.imageList = [] }
    } else {
      row.imageList = []
    }
    row.route_image = imgData.route_image
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
  const res = await mapwayApi.getRouteImage({ route_id: row.id })
  const imgData = res.data || {}
  let list = []
  if (imgData.route_image) { try { list = JSON.parse(imgData.route_image) } catch (_) {} }
  if (index < 0 || index >= list.length) return
  list.splice(index, 1)
  row.imageList = list
  row.route_image = JSON.stringify(list)
  row.image_count = list.length
  await saveRow(row)
  message.success('图片已删除')
}

async function saveRow(row) {
  if (!row.id) return
  await mapwayApi.updateRouteDetail({ id: row.id, route_image: row.route_image })
}

async function removeImage(row, index) {
  const newList = [...row.imageList]
  newList.splice(index, 1)
  row.imageList = newList
  row.route_image = JSON.stringify(newList)
  await saveRow(row)
  message.success('图片已删除')
}

async function addRoute() {
  try {
    const routeTypeValue = routeTypeMap[activeTab.value] || '城区工况'
    await mapwayApi.createRouteDetail({ city: cityName, route_type: routeTypeValue })
    message.success('新增一行，请编辑')
    routeCacheStore.invalidateCooperative(cityName)
    await fetchData(true)
  } catch (e) {
    message.error('新增失败')
  }
}

async function deleteRow(id) {
  if (!id) return
  try {
    await mapwayApi.deleteRouteDetail({ route_id: id })
    message.success('已删除')
    routeCacheStore.invalidateCooperative(cityName)
    await fetchData(true)
  } catch (e) {
    message.error('删除失败')
  }
}

let resizeObserver = null
function updateLayout() {
  if (!pageContainerRef.value || !topSectionRef.value) return
  const topBottom = topSectionRef.value.getBoundingClientRect().bottom
  // 增加底部偏移量，让底部留空更多
  const available = window.innerHeight - topBottom - 120
  wrapperHeight.value = Math.max(available, 200)
}

watch(
  () => [route.params.city, route.query.routeOrder],
  (newVal, oldVal) => {
    if (newVal[0] !== oldVal?.[0] || newVal[1] !== oldVal?.[1]) {
      clearScrollMark()
      fetchData(true)
    }
  }
)

onActivated(() => {
  clearScrollMark()
  nextTick(() => updateLayout())
  if (route.query.routeOrder) {
    setTimeout(() => scrollToTargetRow(route.query.routeOrder), 300)
  }
})

onMounted(() => {
  clearScrollMark()
  fetchData()
  nextTick(() => {
    updateLayout()
    window.addEventListener('resize', updateLayout)
    if (topSectionRef.value) {
      resizeObserver = new ResizeObserver(() => updateLayout())
      resizeObserver.observe(topSectionRef.value)
    }
  })
})

onBeforeUnmount(() => {
  Object.values(debounceTimers).forEach(clearTimeout)
  if (recommendTimer) clearTimeout(recommendTimer)
  window.removeEventListener('resize', updateLayout)
  if (resizeObserver) resizeObserver.disconnect()
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
</style>