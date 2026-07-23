<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NCard, NDescriptions, NDescriptionsItem, NSpin, NEmpty, NButton, NPopconfirm, NModal, NUpload } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { useUserStore } from '@/store'

defineOptions({ name: '基线详情' })

const userStore = useUserStore()

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const targetDetail = ref(null)

const ecuInfo = computed(() => {
  if (!targetDetail.value?.ecu_info) return {}
  const { _did_map, ...ecus } = targetDetail.value.ecu_info
  return ecus
})

const didMap = computed(() => {
  if (!targetDetail.value?.ecu_info?._did_map) return {}
  return targetDetail.value.ecu_info._did_map
})

const ecuList = computed(() => {
  return Object.keys(ecuInfo.value)
})

function loadDetail() {
  const target_name = route.params.target_name
  if (!target_name) {
    router.push('/ecu/target')
    return
  }

  loading.value = true
  api
    .getTargetDetail(target_name)
    .then((res) => {
      targetDetail.value = res.data
    })
    .catch(() => {
      targetDetail.value = null
    })
    .finally(() => {
      loading.value = false
    })
}

function goBack() {
  router.push('/ecu/target')
}

async function deleteTarget() {
  const target_name = route.params.target_name
  console.log('[DEBUG] Deleting target:', target_name)
  try {
    await api.deleteTarget(target_name)
    window.$message?.success('删除成功')
    router.replace('/ecu/target')
    api.addOperationLog({
      operation_type: '删除基线',
      target_name: target_name,
      operator: userStore.name || 'system',
    })
  } catch (err) {
    console.error('[DEBUG] Delete failed:', err)
    window.$message?.error(err.message || '删除失败')
  }
}

const updateModalVisible = ref(false)
const updateLoading = ref(false)
const updateFile = ref(null)

function openUpdateModal() {
  updateModalVisible.value = true
  updateFile.value = null
}

function handleUpdateFileChange(options) {
  updateFile.value = { file: options.file.file }
}

function handleUpdate() {
  if (!updateFile.value) {
    window.$message?.warning('请选择Excel文件')
    return
  }
  const target_name = route.params.target_name
  updateLoading.value = true
  const formData = new FormData()
  formData.append('target_name', target_name)
  formData.append('file', updateFile.value.file)
  api
    .updateTarget(formData)
    .then(() => {
      window.$message?.success('更新成功')
      updateModalVisible.value = false
      loadDetail()
      api.addOperationLog({
        operation_type: '更新基线',
        target_name: target_name,
        operator: userStore.name || 'system',
      })
    })
    .catch((err) => {
      window.$message?.error(err.message || '更新失败')
    })
    .finally(() => {
      updateLoading.value = false
    })
}

function formatTime(t) {
  if (!t) return '-'
  const s = String(t)
  return s.length > 19 ? s.slice(0, 19) : s
}

onMounted(() => {
  loadDetail()
})
</script>

<template>
  <div class="target-detail-page">
    <NCard :bordered="false" class="detail-card">
      <template #header>
        <div class="header">
          <NButton text @click="goBack">
            <TheIcon icon="arrow-left" :size="20" class="mr-5" />
            返回
          </NButton>
          <span class="title">基线详情 - {{ route.params.target_name }}</span>
          <div class="header-actions">
            <NButton quaternary type="warning" @click="openUpdateModal">
              <TheIcon icon="material-symbols:refresh" :size="18" />
            </NButton>
            <NPopconfirm
              @positive-click="() => { console.log('[DEBUG] Popconfirm confirmed'); deleteTarget() }"
            >
              <template #trigger>
                <NButton quaternary type="error">
                  <TheIcon icon="material-symbols:delete-outline" :size="18" />
                </NButton>
              </template>
              确定要删除该基线版本吗？此操作不可恢复。
            </NPopconfirm>
          </div>
        </div>
      </template>

      <NSpin :show="loading">
        <template v-if="targetDetail">
          <NCard title="数据详情" size="small" style="margin-bottom: 16px">
            <div class="info-tags">
              <div class="info-tag-item">
                <span class="tag-label">基线版本名称</span>
                <span class="tag-value">{{ targetDetail.target_name }}</span>
              </div>
              <div class="info-tag-item">
                <span class="tag-label">创建时间</span>
                <span class="tag-value">{{ formatTime(targetDetail.created_at) }}</span>
              </div>
              <div class="info-tag-item">
                <span class="tag-label">更新时间</span>
                <span class="tag-value">{{ formatTime(targetDetail.updated_at) }}</span>
              </div>
            </div>
          </NCard>

          <div class="ecu-sections">
            <div v-for="ecuName in ecuList" :key="ecuName" class="ecu-section">
              <NCard :title="ecuName" size="small" class="ecu-card">
                <div class="ecu-info-list">
                  <div
                    v-for="(value, key) in ecuInfo[ecuName]"
                    :key="key"
                    class="info-item"
                  >
                    <span class="info-label">{{ didMap[key] || key }}</span>
                    <span class="info-value">{{ value || '-' }}</span>
                  </div>
                </div>
              </NCard>
            </div>
          </div>
        </template>
        <NEmpty v-else-if="!loading" description="未找到数据" />
      </NSpin>
    </NCard>

    <NModal
      v-model:show="updateModalVisible"
      title="更新基线信息"
      preset="card"
      style="width: 500px"
      :mask-closable="false"
    >
      <NForm label-placement="left" label-width="100px">
        <NFormItem label="基线名称">
          <NInput v-model:value="route.params.target_name" disabled />
        </NFormItem>
        <NFormItem label="文件" required>
          <NUpload
            accept=".xlsx,.xls"
            :max="1"
            :custom-request="handleUpdateFileChange"
          >
            <NButton>点击上传Excel文件</NButton>
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
.target-detail-page {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.detail-card {
  min-height: 100%;
}

.header {
  display: flex;
  align-items: center;
  flex: 1;
}

.header-actions {
  margin-left: auto;
}

.title {
  margin-left: 12px;
  font-size: 16px;
  font-weight: 500;
}

.ecu-sections {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.ecu-section {
  width: calc(50% - 8px);
}

.ecu-card {
  border-radius: 8px;
}

.ecu-info-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  align-items: center;
}

.info-label {
  flex: 0 0 200px;
  color: #666;
  font-size: 13px;
}

.info-value {
  flex: 1;
  color: #333;
  font-size: 13px;
  word-break: break-all;
}

.info-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.info-tag-item {
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 6px;
  min-width: 120px;
}

.tag-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.tag-value {
  font-size: 14px;
  color: #333;
  word-break: break-all;
}
</style>