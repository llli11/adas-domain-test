<script setup>
import { onMounted, ref, computed } from 'vue'
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

function handleSearch() {
  loading.value = true
  api
    .getECUList({ search: searchVin.value || undefined })
    .then((res) => {
      ecuList.value = res.data || []
    })
    .finally(() => {
      loading.value = false
    })
}

function handleClickCard(vin) {
  router.push(`/ecu/detail/${vin}`)
}

onMounted(() => {
  handleSearch()
})
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
            @keyup.enter="handleSearch"
          />
<NButton type="primary" @click="handleSearch">
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
          <div class="vin-label">{{ item.vin }}</div>
        </NCard>
        <div v-if="ecuList.length === 0 && !loading" class="empty-tip">
          暂无数据
        </div>
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
}

.toolbar {
  margin-bottom: 16px;
}

.ecu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
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

.vin-label {
  text-align: center;
  font-size: 16px;
  font-weight: 500;
  padding: 20px 0;
}

.empty-tip {
  grid-column: 1 / -1;
  text-align: center;
  color: #999;
  padding: 40px 0;
}
</style>
