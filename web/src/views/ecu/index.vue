<script setup>
import { onMounted, onUnmounted, ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NInput,
  NSpace,
  NModal,
  NForm,
  NFormItem,
  NUpload,
  NSpin,
  NSelect,
  useMessage,
} from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { useUserStore } from '@/store'

defineOptions({ name: '整车ECU版本管理' })

const router = useRouter()
const message = useMessage()
const userStore = useUserStore()

const searchVin = ref('')
const ecuList = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(true)
const pageForLoad = ref(1)
const pageSize = 20

const updateModalVisible = ref(false)
const updateLoading = ref(false)
const updateForm = ref({
  vin: '',
  file: null,
})

const vinExtracted = ref(false)
const vinOptions = ref([])
const vinSelectValue = ref(null)
const vinManualMode = ref(false)

const vinInputDisabled = computed(() => {
  if (vinManualMode.value) return false
  if (!updateForm.value.file) return true
  return vinExtracted.value
})

const vinPlaceholder = computed(() => {
  if (!updateForm.value.file) return '请先上传HTML文件'
  if (vinManualMode.value) return '请输入VIN'
  return '正在解析VIN...'
})

function cleanVin(value) {
  if (!value) return ''
  return value.replace(/\0/g, '').trim()
}

function isValidVin(value) {
  const cleaned = cleanVin(value)
  return cleaned.length >= 10
}

function parseVinFromHtml(text) {
  const countMap = {}
  const f190Regex = /F190<\/td[^>]*>\s*<td[^>]*>[^<]*<\/td[^>]*>\s*<td[^>]*>([^<]*)<\/td[^>]*>/gi
  let match
  while ((match = f190Regex.exec(text)) !== null) {
    const raw = match[1].trim()
    const cleaned = cleanVin(raw)
    if (cleaned && isValidVin(cleaned)) {
      countMap[cleaned] = (countMap[cleaned] || 0) + 1
    }
  }
  return Object.entries(countMap)
    .map(([vin, count]) => ({ vin, count }))
    .sort((a, b) => b.count - a.count)
}

function handleFileChange(options) {
  const file = options.file.file
  updateForm.value.file = file

  vinExtracted.value = false
  vinOptions.value = []
  vinSelectValue.value = null
  vinManualMode.value = false
  updateForm.value.vin = ''

  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    const text = e.target.result
    const foundVins = parseVinFromHtml(text)

    if (foundVins.length === 0) {
      vinManualMode.value = true
      message.info('未从文件中解析到VIN，请手动输入')
    } else if (foundVins.length === 1) {
      updateForm.value.vin = foundVins[0].vin
      vinExtracted.value = true
    } else {
      const best = foundVins[0]
      vinOptions.value = foundVins.map(({ vin, count }) => ({
        label: `${vin} (x${count})`,
        value: vin,
      }))
      vinSelectValue.value = best.vin
      updateForm.value.vin = best.vin
      vinExtracted.value = true
    }
  }
  reader.readAsText(file)
}

function handleFileRemove() {
  updateForm.value.file = null
  vinExtracted.value = false
  vinOptions.value = []
  vinSelectValue.value = null
  vinManualMode.value = false
  updateForm.value.vin = ''
}

function handleVinSelect(value) {
  updateForm.value.vin = value
}

function showUpdateModal() {
  updateModalVisible.value = true
  updateForm.value = { vin: '', file: null }
  vinExtracted.value = false
  vinOptions.value = []
  vinSelectValue.value = null
  vinManualMode.value = false
}

function handleUpdate() {
  if (!updateForm.value.vin) {
    message.warning('请输入VIN')
    return
  }
  if (!updateForm.value.file) {
    message.warning('请上传文件')
    return
  }

  updateLoading.value = true
  const formData = new FormData()
  formData.append('vin', updateForm.value.vin)
  formData.append('file', updateForm.value.file)

  api
    .updateECU(formData)
    .then((res) => {
      message.success('更新成功')
      const vin = updateForm.value.vin
      updateModalVisible.value = false
      updateForm.value = { vin: '', file: null }
      handleSearch()
      api.addOperationLog({
        operation_type: '更新车辆',
        target_vin: vin,
        operator: userStore.name || 'system',
      })
    })
    .catch((err) => {
      message.error(err.message || '更新失败')
    })
    .finally(() => {
      updateLoading.value = false
    })
}

async function handleSearch() {
  const kw = searchVin.value?.trim() || ''
  sessionStorage.setItem('ecu_list_search', kw)
  pageForLoad.value = 1
  hasMore.value = true
  loading.value = true
  try {
    const res = await api.getECUList({ search: kw || undefined, page: 1, page_size: pageSize })
    ecuList.value = res.data || []
    hasMore.value = (res.data || []).length >= pageSize
  } finally {
    loading.value = false
  }
}

function handleClearSearch() {
  searchVin.value = ''
  nextTick(() => handleSearch())
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  const nextPage = pageForLoad.value + 1
  try {
    const res = await api.getECUList({ search: searchVin.value || undefined, page: nextPage, page_size: pageSize })
    const newItems = res.data || []
    if (newItems.length > 0) {
      ecuList.value = [...ecuList.value, ...newItems]
      pageForLoad.value = nextPage
    }
    hasMore.value = newItems.length >= pageSize
  } finally {
    loadingMore.value = false
  }
}

function handleScroll() {
  const scrollBottom = document.documentElement.scrollHeight - window.scrollY - window.innerHeight
  if (scrollBottom < 100) {
    loadMore()
  }
}

onMounted(() => {
  const saved = sessionStorage.getItem('ecu_list_search')
  if (saved) {
    searchVin.value = saved
  }
  handleSearch()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

function handleClickCard(vin) {
  router.push(`/ecu/detail/${vin}`)
}

</script>

<template>
  <div class="ecu-page">
    <NCard :bordered="false" class="ecu-card">
      <div class="toolbar">
        <NSpace>
          <NInput
            v-model:value="searchVin"
            placeholder="搜索"
            clearable
            @clear="handleClearSearch"
            @keyup.enter="handleSearch()"
          />
<NButton type="primary" @click="handleSearch()">
            <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />
            搜索
          </NButton>
          <NButton type="success" @click="showUpdateModal">
            <TheIcon icon="material-symbols:add" :size="16" class="mr-5" />
            更新
          </NButton>
        </NSpace>
      </div>

      <div class="ecu-grid">
        <NCard
          v-for="item in ecuList"
          :key="item.id"
          class="ecu-box"
          hoverable
          @click="handleClickCard(item.vin)"
        >
          <div class="card-no">{{ item.vehicle_no || '-' }}</div>
          <div class="card-info">
            <div class="card-row"><span class="card-label">车型</span><span class="card-val">{{ item.vehicle_model || '-' }}</span></div>
            <div class="card-row"><span class="card-label">VIN</span><span class="card-val">{{ item.vin }}</span></div>
            <div class="card-row"><span class="card-label">使用人</span><span class="card-val">{{ item.user_name || '-' }}</span></div>
          </div>
        </NCard>
        <div v-if="ecuList.length === 0 && !loading" class="empty-tip">
          暂无数据
        </div>
      </div>
      <div v-if="loadingMore" class="loading-more">
        <NSpin size="small" /> 加载中...
      </div>
      <div v-if="!hasMore && ecuList.length > 0" class="loading-more">
        已加载全部
      </div>
    </NCard>

    <NModal
      v-model:show="updateModalVisible"
      title="更新ECU信息"
      preset="card"
      style="width: 500px"
      :mask-closable="false"
    >
      <NForm label-placement="left" label-width="80px">
        <NFormItem label="VIN" required>
          <template v-if="vinOptions.length > 1">
            <NSelect
              :value="vinSelectValue"
              :options="vinOptions"
              filterable
              @update:value="handleVinSelect"
            />
          </template>
          <template v-else>
            <NInput
              v-model:value="updateForm.vin"
              :disabled="vinInputDisabled"
              :placeholder="vinPlaceholder"
            />
          </template>
        </NFormItem>
        <NFormItem label="文件" required>
          <NUpload
            accept=".html,.htm"
            :max="1"
            :custom-request="handleFileChange"
            @remove="handleFileRemove"
          >
            <NButton>点击上传HTML文件</NButton>
          </NUpload>
        </NFormItem>
      </NForm>
      <template #footer>
        <div style="display: flex; justify-content: flex-end">
          <NButton @click="updateModalVisible = false">取消</NButton>
          <NButton type="primary" style="margin-left: 16px" :loading="updateLoading" @click="handleUpdate">
            确认
          </NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.ecu-page {
  padding: 16px;
}

.ecu-card {
  min-height: calc(100vh - 100px);
  overflow: visible;
}

.toolbar {
  margin-bottom: 16px;
}

.ecu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.ecu-box {
  cursor: pointer;
  transition: all 0.3s;
}

.ecu-box:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-no {
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  padding: 16px 0 12px;
  color: #1a6fb5;
}

.card-info {
  padding: 0 8px 16px;
}

.card-row {
  display: flex;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}

.card-label {
  color: #999;
  width: 56px;
  flex-shrink: 0;
}

.card-val {
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-tip {
  grid-column: 1 / -1;
  text-align: center;
  color: #999;
  padding: 40px 0;
}

.loading-more {
  text-align: center;
  color: #999;
  padding: 24px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
</style>
