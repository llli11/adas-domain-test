<template>
<CommonPage class="page-wrap">
  <div class="title-bar">
    <h2 class="title">版本指标管理</h2>
    <NSpace>
      <NButton type="primary" @click="openViewModal">查看</NButton>
      <NButton type="primary" @click="openEditModal">编辑</NButton>
    </NSpace>
  </div>

  <NCard v-if="hasFilter" title="基础指标数据" class="mb-3">
    <div class="info-row">
      <span><b>项目类型：</b>{{ getLabelById(projectTypes, viewQuery.projectId) }}</span>
      <span><b>车型：</b>{{ getLabelById(carModels, viewQuery.carId) }}</span>
      <span><b>版本号：</b>{{ viewQuery.versionCode }}</span>
    </div>
  </NCard>

  <NCard class="mt-1" title="指标数据">
    <div v-if="loadingSavedData" class="text-center py-6">加载中...</div>
    <div v-else-if="!hasFilter">
      <NEmpty description="请点击右上角【查看】筛选数据" />
    </div>
    <div v-else>
      <div class="cate-block" v-for="cateItem in Object.values(groupByCategory)" :key="cateItem.cateName">
        <div class="cate-title"><h3>【{{ cateItem.cateName }}】</h3></div>
        <div class="sub-block" v-for="subItem in cateItem.subWrap" :key="subItem.subId">
          <div class="sub-name"><span>指标子项：{{ subItem.name }}</span></div>
          <div class="form-row" v-for="item in subItem.itemList" :key="item.id">
            <label style="width: 220px; font-weight: bold">{{ item.name }}：</label>
            <span>{{ pageShowIndicator[item.name] ?? '-' }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="text-right mt-4">
      <NButton type="primary" @click="openEditModal">编辑填写指标</NButton>
    </div>
  </NCard>

  <!-- 查看弹窗 draggable可拖动 强制纯白 -->
  <NModal
    v-model:show="viewModal"
    title="筛选查看指标"
    width="500"
    zIndex="9999"
    mask-closable="false"
    draggable
    class="modal-force-white"
  >
    <div class="p-4 modal-scroll">
      <div class="mb-3">
        <label class="block mb-1">项目类型</label>
        <NSelect v-model:value="viewQuery.projectId" placeholder="请选择" clearable :options="projectTypes" label-field="name" value-field="id"/>
      </div>
      <div class="mb-3">
        <label class="block mb-1">车型</label>
        <NSelect v-model:value="viewQuery.carId" placeholder="请选择" clearable :options="carModels" label-field="name" value-field="id"/>
      </div>
      <div class="mb-3">
        <label class="block mb-1">版本号</label>
        <NSelect v-model:value="viewQuery.versionCode" placeholder="请选择版本" clearable :options="versionCodeList" value-field="name" label-field="name"/>
      </div>
      <div class="text-right mt-4">
        <NButton @click="viewModal = false" class="mr-2">取消</NButton>
        <NButton type="primary" @click="confirmViewFilter">确认查看</NButton>
      </div>
    </div>
  </NModal>

  <!-- 编辑弹窗 缩小宽高+可拖动+全局强制纯白 -->
  <NModal
    v-model:show="editModal"
    title="统一管理配置&填写指标"
    width="700"
    zIndex="1000000"
    mask-closable="false"
    draggable
    class="modal-force-white modal-sm-edit"
  >
    <div class="p-3 modal-scroll">
      <NTabs v-model:value="form.tabKey">
        <NTabPane name="project" tab="项目类型管理">
          <div class="flex gap-2 mb-3">
            <NInput v-model:value="form.newProjectType" placeholder="新增项目类型名称" class="flex-1"/>
            <NButton type="primary" @click="addProjectType">新增</NButton>
          </div>
          <div v-for="item in projectTypes" :key="item.id" class="flex gap-2 mb-2">
            <NInput :value="item.name" readonly class="flex-1"/>
            <NButton type="error" @click="deleteProjectType(item.id)">删除</NButton>
          </div>
        </NTabPane>
        <NTabPane name="car" tab="车型管理">
          <div class="flex gap-2 mb-3">
            <NInput v-model:value="form.newCarModel" placeholder="新增车型名称" class="flex-1"/>
            <NButton type="primary" @click="addCarModel">新增</NButton>
          </div>
          <div v-for="item in carModels" :key="item.id" class="flex gap-2 mb-2">
            <NInput :value="item.name" readonly class="flex-1"/>
            <NButton type="error" @click="deleteCarModel(item.id)">删除</NButton>
          </div>
        </NTabPane>
        <NTabPane name="version" tab="版本号管理">
          <div class="flex gap-2 mb-3">
            <NInput v-model:value="form.newVersionCode" placeholder="新增版本号，如V1.0.0" class="flex-1"/>
            <NButton type="primary" @click="addVersionCode">新增版本号</NButton>
          </div>
          <div v-for="item in versionCodeList" :key="item.id" class="flex gap-2 mb-2">
            <NInput :value="item.name" readonly class="flex-1"/>
            <NButton type="error" @click="deleteVersionCode(item.id)">删除</NButton>
          </div>
        </NTabPane>
        <NTabPane name="category" tab="指标大类管理">
          <div class="flex gap-2 mb-3">
            <NInput v-model:value="form.newCategory" placeholder="新增指标大类" class="flex-1"/>
            <NButton type="primary" @click="addIndexCategory">新增</NButton>
          </div>
          <div v-for="item in indexCategories" :key="item.id" class="flex gap-2 mb-2">
            <NInput :value="item.name" readonly class="flex-1"/>
            <NButton type="error" @click="deleteIndexCategory(item.id)">删除</NButton>
          </div>
        </NTabPane>
        <NTabPane name="sub" tab="指标子项管理">
          <div class="flex gap-2 mb-3 items-center">
            <NSelect v-model:value="form.selectedCategory" @change="handleCategoryChange" placeholder="先选择大类" :options="indexCategories" label-field="name" value-field="id" style="width:180px"/>
            <NInput v-model:value="form.newSubItem" placeholder="新增子项名称" class="flex-1"/>
            <NButton type="primary" @click="addIndexSubItem">新增</NButton>
          </div>
          <div v-for="item in indexSubItems" :key="item.id" class="flex gap-2 mb-2">
            <NInput :value="item.name" readonly class="flex-1"/>
            <NButton type="error" @click="deleteIndexSubItem(item.id)">删除</NButton>
          </div>
        </NTabPane>
        <NTabPane name="item" tab="指标填写">
          <div class="flex gap-2 mb-3 items-center">
            <NSelect v-model:value="form.selectedCategory" @change="handleCategoryChange" placeholder="选择大类" :options="indexCategories" label-field="name" value-field="id" style="width:180px"/>
            <NSelect v-model:value="form.selectedSubItem" @change="handleSubChange" placeholder="选择子项" :options="indexSubItems" label-field="name" value-field="id" style="width:180px"/>
          </div>
          <div class="flex gap-2 mb-3">
            <NInput v-model:value="form.newIndexItem" placeholder="新增指标名称" class="flex-1"/>
            <NButton type="primary" @click="addIndexItem">新增指标</NButton>
          </div>
          <div v-for="item in indexItems" :key="item.id" class="flex gap-2 mb-2 items-center">
            <label style="width:200px">{{ item.name }}：</label>
            <NInput v-model:value="indicatorValues[item.name]" placeholder="填写指标值" class="flex-1"/>
            <NButton type="error" @click="deleteIndexItem(item.id)">删除</NButton>
          </div>
        </NTabPane>
      </NTabs>
      <NCard title="保存条件（必选）" class="mt-4">
        <div class="flex flex-wrap gap-3 mb-2">
          <NSelect v-model:value="viewQuery.projectId" placeholder="选择项目类型" clearable :options="projectTypes" label-field="name" value-field="id" style="width:240px"/>
          <NSelect v-model:value="viewQuery.carId" placeholder="选择车型" clearable :options="carModels" label-field="name" value-field="id" style="width:240px"/>
          <NSelect v-model:value="viewQuery.versionCode" placeholder="选择版本" clearable :options="versionCodeList" style="width:240px" value-field="name" label-field="name"/>
          <NSelect v-model:value="form.selectedCategory" placeholder="选择指标大类" clearable :options="indexCategories" label-field="name" value-field="id" @change="handleCategoryChange" style="width:260px"/>
          <NSelect v-model:value="form.selectedSubItem" placeholder="选择指标子项" clearable :options="indexSubItems" label-field="name" value-field="id" @change="handleSubChange" style="width:260px"/>
        </div>
      </NCard>
      <div class="text-right mt-3">
        <NButton type="primary" @click="handleSaveData">保存数据</NButton>
      </div>
      <div class="text-right mt-4">
        <NButton @click="editModal = false">关闭</NButton>
      </div>
    </div>
  </NModal>
</CommonPage>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { NButton, NInput, NSelect, NModal, NTabs, NTabPane, NSpace, NCard, NEmpty } from 'naive-ui'
import { useMessage } from 'naive-ui'
import api from '@/api/versionIndex'
const message = useMessage()

// 下拉数据源
const projectTypes = ref([])
const carModels = ref([])
const indexCategories = ref([])
const versionCodeList = ref([])
const indexSubItems = ref([])
const indexItems = ref([])
// 编辑输入框绑定值（内存中转，最终入库）
const indicatorValues = ref({})
// 页面顶部展示数据
const pageShowIndicator = ref({})
const loadingSavedData = ref(false)
const hasFilter = ref(false)
const groupByCategory = ref({})
const viewModal = ref(false)
const editModal = ref(false)
// 筛选条件
const viewQuery = reactive({
  projectId: null,
  carId: null,
  versionCode: ''
})
const form = reactive({
  newProjectType: '',
  newCarModel: '',
  newVersionCode: '',
  newCategory: '',
  newSubItem: '',
  newIndexItem: '',
  selectedCategory: null,
  selectedSubItem: null,
  tabKey: 'project'
})

// 页面初始化
onMounted(async () => {
  // 加载基础下拉列表
  await loadBaseData()
  // 仅恢复筛选下拉值，不自动加载指标数据（避免接口卡死页面）
  try {
    const cache = localStorage.getItem('indexFilterCache')
    if (cache) {
      const filter = JSON.parse(cache)
      viewQuery.projectId = filter.projectId
      viewQuery.carId = filter.carId
      viewQuery.versionCode = filter.versionCode
    }
  } catch (e) {
    localStorage.removeItem('indexFilterCache')
  }
})

// 加载基础下拉
async function loadBaseData() {
  try {
    const [pRes, cRes, vRes, catRes] = await Promise.all([
      api.getProjectTypes(),
      api.getCarModels(),
      api.getVersionCodes(),
      api.getIndexCategories()
    ])
    projectTypes.value = pRes.data
    carModels.value = cRes.data
    versionCodeList.value = vRes.data
    indexCategories.value = catRes.data
  } catch (err) {
    message.error('加载下拉失败：' + err.message)
  }
}

const getLabelById = (list, id) => {
  const row = list.find(x => x.id === id)
  return row ? row.name : ''
}

// 打开查看弹窗（同步无阻塞，点击立刻弹出）
function openViewModal() {
  viewModal.value = true
}
// 打开编辑弹窗
async function openEditModal() {
  await nextTick()
  editModal.value = true
}

async function handleCategoryChange(cid) {
  if (!cid) { indexSubItems.value = []; indexItems.value = []; return }
  const res = await api.getIndexSubItems(cid)
  indexSubItems.value = res.data
  indexItems.value = []
}
async function handleSubChange(sid) {
  if (!sid) { indexItems.value = []; return }
  const res = await api.getIndexItems(sid)
  indexItems.value = res.data
}

// 确认筛选：缓存筛选 + 数据库读取数据（多账号共享）
async function confirmViewFilter() {
  const { projectId, carId, versionCode } = viewQuery
  if (!projectId || !carId || !versionCode) return message.warning('必填项不能为空')
  viewModal.value = false
  localStorage.setItem('indexFilterCache', JSON.stringify({ projectId, carId, versionCode }))
  loadingSavedData.value = true
  hasFilter.value = true
  try {
    const res = await api.getSavedData({ project_id: projectId, car_id: carId, version_code: versionCode })
    const map = {}
    res.data.forEach(i => map[i.indicator_name] = i.indicator_value)
    pageShowIndicator.value = { ...map }
    indicatorValues.value = { ...map }
    await loadPageFilterData()
  } catch (err) {
    message.error('加载指标失败：' + err.message)
  } finally {
    loadingSavedData.value = false
  }
}

// 保存数据写入数据库，所有登录账号可见
async function handleSaveData() {
  const { projectId, carId, versionCode } = viewQuery
  const { selectedCategory, selectedSubItem } = form
  if (!projectId || !carId || !versionCode || !selectedCategory || !selectedSubItem) {
    return message.warning('请完整选择所有筛选条件')
  }
  const submit = {
    project_id: projectId,
    car_id: carId,
    version_code: versionCode,
    category_id: selectedCategory,
    sub_id: selectedSubItem,
    indicator_data: { ...indicatorValues.value }
  }
  try {
    await api.saveVersionData(submit)
    message.success('保存成功，数据存入数据库，其他账号登录可查看')
    pageShowIndicator.value = { ...indicatorValues.value }
    localStorage.setItem('indexFilterCache', JSON.stringify({ projectId, carId, versionCode }))
    await loadPageFilterData()
  } catch (err) {
    message.error('保存失败：' + err.message)
  }
}

// 项目类型增删
async function addProjectType() {
  const name = form.newProjectType.trim()
  if (!name) return message.warning('名称不能为空')
  try {
    await api.addProjectType({ name })
    message.success(`新增${name}成功`)
    form.newProjectType = ''
    await nextTick()
    await loadBaseData()
  } catch (err) { message.error(err.message) }
}
async function deleteProjectType(id) {
  try { await api.deleteProjectType(id); message.success('删除成功'); await loadBaseData() } catch (err) { message.error(err.message) }
}
// 车型增删
async function addCarModel() {
  const name = form.newCarModel.trim()
  if (!name) return message.warning('名称不能为空')
  try {
    await api.addCarModel({ name })
    message.success(`新增${name}成功`)
    form.newCarModel = ''
    await nextTick()
    await loadBaseData()
  } catch (err) { message.error(err.message) }
}
async function deleteCarModel(id) {
  try { await api.deleteCarModel(id); message.success('删除成功'); await loadBaseData() } catch (err) { message.error(err.message) }
}
// 版本号增删
async function addVersionCode() {
  const code = form.newVersionCode.trim()
  if (!code) return message.warning('版本号不能为空')
  try {
    await api.addVersionCode({ code })
    message.success(`版本${code}新增成功`)
    form.newVersionCode = ''
    await nextTick()
    await loadBaseData()
  } catch (err) { message.error(err.message) }
}
async function deleteVersionCode(id) {
  try { await api.deleteVersionCode(id); message.success('删除成功'); await loadBaseData() } catch (err) { message.error(err.message) }
}
// 指标大类增删
async function addIndexCategory() {
  const name = form.newCategory.trim()
  if (!name) return message.warning('名称不能为空')
  try {
    await api.addIndexCategory({ name })
    message.success(`新增大类${name}成功`)
    form.newCategory = ''
    await nextTick()
    await loadBaseData()
  } catch (err) { message.error(err.message) }
}
async function deleteIndexCategory(id) {
  try { await api.deleteIndexCategory(id); message.success('删除成功'); await loadBaseData() } catch (err) { message.error(err.message) }
}
// 指标子项增删（绑定大类）
async function addIndexSubItem() {
  const name = form.newSubItem.trim()
  const cid = form.selectedCategory
  if (!name || !cid) return message.warning('请先选择大类再填写名称')
  try {
    await api.addIndexSubItem({ category_id: cid, name })
    message.success(`子项${name}新增成功`)
    form.newSubItem = ''
    await nextTick()
    await handleCategoryChange(cid)
  } catch (err) { message.error(err.message) }
}
async function deleteIndexSubItem(id) {
  try { await api.deleteIndexSubItem(id); message.success('删除成功'); await handleCategoryChange(form.selectedCategory) } catch (err) { message.error(err.message) }
}
// 具体指标增删
async function addIndexItem() {
  const name = form.newIndexItem.trim()
  const sid = form.selectedSubItem
  if (!name || !sid) return message.warning('请先选择子项再填写指标名称')
  try {
    await api.addIndexItem({ sub_id: sid, name })
    message.success(`指标${name}新增成功`)
    form.newIndexItem = ''
    await nextTick()
    await handleSubChange(sid)
    if (pageShowIndicator.value[name]) indicatorValues.value[name] = pageShowIndicator.value[name]
  } catch (err) { message.error(err.message) }
}
async function deleteIndexItem(id) {
  try { await api.deleteIndexItem(id); message.success('指标删除成功'); await handleSubChange(form.selectedSubItem) } catch (err) { message.error(err.message) }
}

// 页面分组渲染数据加载
async function loadPageFilterData() {
  const { projectId, carId, versionCode } = viewQuery
  if (!projectId || !carId || !versionCode) return
  const res = await api.getSavedData({ project_id: projectId, car_id: carId, version_code: versionCode })
  const dataMap = {}
  res.data.forEach(row => dataMap[row.indicator_name] = row.indicator_value)
  pageShowIndicator.value = { ...dataMap }
  indicatorValues.value = { ...dataMap }
  const groupObj = {}
  for (const cate of indexCategories.value) {
    const subRes = await api.getIndexSubItems(cate.id)
    const subWrapList = []
    for (const sub of subRes.data) {
      const itemRes = await api.getIndexItems(sub.id)
      subWrapList.push({ subId: sub.id, name: sub.name, itemList: itemRes.data })
    }
    groupObj[cate.id] = { cateName: cate.name, subWrap: subWrapList }
  }
  groupByCategory.value = groupObj
}
</script>

<style scoped>
.title-bar {display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;}
.title {margin:0;font-size:22px;font-weight:500;}
.info-row {display:flex;gap:32px;flex-wrap:wrap;}
.cate-block {margin-bottom:20px;border-bottom:1px solid #eee;padding-bottom:16px;}
.cate-title h3 {margin:6px 0 10px 0;font-size:17px;color:#222;}
.sub-block {margin:8px 0 12px 24px;}
.sub-name {margin-bottom:8px;font-weight:500;color:#444;}
.form-row {display:flex;align-items:center;margin-bottom:12px;gap:8px;padding-left:12px;}
.flex {display:flex;align-items:center;}
.flex-wrap {flex-wrap:wrap;}
.gap-2 {gap:8px;}.gap-3 {gap:12px;}
.mb-2 {margin-bottom:8px;}.mb-3 {margin-bottom:12px;}.mt-1 {margin-top:4px;}.mt-4 {margin-top:16px;}
.flex-1 {flex:1;}.text-right {text-align:right;}.text-center {text-align:center;}.p-4 {padding:16px;}
.block {display:block;}.mb-1 {margin-bottom:4px;}.mr-2 {margin-right:8px;}.py-6 {padding:24px 0;}
</style>

<style>
/* 全局页面底色纯白 */
html,body,#app,.n-layout,.n-layout-main,.n-layout-content,.n-page,.n-page__content {
  background: #ffffff !important;
}
.n-layout-header,.n-layout-sider,.n-card {
  background: #ffffff !important;
}

/* 遮罩层：仅背景页面变灰，弹窗不受影响 */
.modal-force-white + .n-modal-mask {
  background: rgba(0,0,0,0.35) !important;
}

/* 弹窗所有层级强制纯白，彻底解决灰色底色 */
.modal-force-white .n-modal-container,
.modal-force-white .n-modal-content,
.modal-force-white .n-modal-header-wrapper,
.modal-force-white .n-modal-header,
.modal-force-white .n-modal-body,
.modal-force-white .n-modal-footer {
  background: #ffffff !important;
  background-color: #ffffff !important;
}

/* 拖拽标题光标 */
.modal-force-white .n-modal-header {
  cursor: move !important;
  user-select: none;
}

/* 弹窗内容滚动限制高度 */
.modal-scroll {
  max-height: 78vh;
  overflow-y: auto;
  background: #fff !important;
}

/* 编辑弹窗尺寸缩小 */
.modal-sm-edit .n-modal-content {
  border-radius: 6px;
}

/* 清除伪元素灰色叠加层 */
.modal-force-white .n-modal-content::before,
.modal-force-white .n-modal-body::before {
  display: none !important;
  background: transparent !important;
}
</style>