<script setup>
import { ref, onMounted, computed } from 'vue'
import {
  NButton,
  NCard,
  NInput,
  NTag,
  NAlert,
  NSpin,
  NUpload,
  NSwitch,
  useMessage,
} from 'naive-ui'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import { notifyVehicleDataChanged, getAutoSyncEnabled, setAutoSyncEnabled } from '@/utils/vehicleSync'

defineOptions({ name: '数据源管理' })

const $message = useMessage()

// ===== 数据统计 =====
const dataSourceCounts = ref({ feishu: 0, csv: 0, manual: 0 })

// ===== 自动同步开关 =====
const autoSyncEnabled = ref(getAutoSyncEnabled())

function handleAutoSyncToggle(value) {
  autoSyncEnabled.value = value
  setAutoSyncEnabled(value)
  $message.info(value ? '已开启进入车辆管理时自动同步飞书数据' : '已关闭自动同步')
}

async function loadDataSourceCounts() {
  try {
    const res = await api.getVehicleList({ page: 1, page_size: 9999 })
    const list = res.data?.items || res.data || []
    const counts = { feishu: 0, csv: 0, manual: 0 }
    list.forEach(v => {
      const src = v.data_source || 'manual'
      if (counts[src] !== undefined) counts[src]++
      else counts[src] = 1
    })
    dataSourceCounts.value = counts
  } catch (e) {
    console.error('获取数据源统计失败', e)
  }
}

// ===== 加载用户保存的飞书配置 =====
const userBaseId = ref('')
const userTableId = ref('')

async function loadUserConfig() {
  try {
    const res = await api.getFeishuConfig()
    if (res.data) {
      userBaseId.value = res.data.base_id || ''
      userTableId.value = res.data.table_id || ''
    }
  } catch (e) {
    console.error('加载飞书配置失败', e)
  }
}

onMounted(() => {
  loadDataSourceCounts()
  loadUserConfig()
})

// ===== 数据源1：外部飞书导入（预置配置） =====
const syncingSource1 = ref(false)
const source1Result = ref(null)

async function handleSyncSource1() {
  syncingSource1.value = true
  source1Result.value = null
  try {
    const res = await api.syncFromFeishu()
    source1Result.value = res.data
    if (res.data?.success) {
      $message.success(
        `同步完成：读取 ${res.data.total_records || 0} 条，新增 ${res.data.created || 0} 条，更新 ${res.data.updated || 0} 条`
      )
    } else {
      $message.warning(res.data?.message || '同步未获取到数据')
    }
    loadDataSourceCounts()
  } catch (e) {
    $message.error('同步失败: ' + (e.message || '未知错误'))
    source1Result.value = { success: false, message: e.message }
  } finally {
    syncingSource1.value = false
  }
}

// ===== 数据源2：外部飞书导入（用户自定义配置） =====
const syncingSource2 = ref(false)
const source2Result = ref(null)
const savingConfig = ref(false)

async function handleSaveAndSyncSource2() {
  if (!userBaseId.value.trim() || !userTableId.value.trim()) {
    $message.warning('请输入 Base ID 和 Table ID')
    return
  }
  savingConfig.value = true
  source2Result.value = null
  syncingSource2.value = true
  try {
    const res = await api.saveFeishuConfig({
      base_id: userBaseId.value.trim(),
      table_id: userTableId.value.trim(),
    })
    const data = res.data
    if (data?.config_saved) {
      $message.success('配置保存成功，已自动同步')
    }
    if (data?.sync_result) {
      source2Result.value = data.sync_result
      if (data.sync_result.success) {
        $message.success(
          `同步完成：读取 ${data.sync_result.total_records || 0} 条，新增 ${data.sync_result.created || 0} 条，更新 ${data.sync_result.updated || 0} 条`
        )
      } else {
        $message.warning(data.sync_result.message || '同步未获取到数据')
      }
    }
    loadDataSourceCounts()
  } catch (e) {
    $message.error('保存或同步失败: ' + (e.message || '未知错误'))
    source2Result.value = { success: false, message: e.message }
  } finally {
    savingConfig.value = false
    syncingSource2.value = false
  }
}

// ===== 数据源3：外部CSV导入 =====
const csvUploading = ref(false)
const csvImportResult = ref(null)
const csvFileName = ref('')

async function handleCsvFileChange(file) {
  csvUploading.value = true
  csvImportResult.value = null
  csvFileName.value = file.name
  try {
    const res = await api.importCsv(file)
    csvImportResult.value = res.data
    if (res.data?.success) {
      $message.success(
        `CSV 导入完成：新增 ${res.data.created || 0} 条，更新 ${res.data.updated || 0} 条`
      )
    } else {
      $message.warning(res.data?.message || '导入未获取到数据')
    }
    loadDataSourceCounts()
  } catch (e) {
    $message.error('导入失败: ' + (e.message || '未知错误'))
    csvImportResult.value = { success: false, message: e.message, errors: [e.message] }
  } finally {
    csvUploading.value = false
  }
}

// 经 NUpload 包装的 CSV 上传处理
function handleCsvUpload({ file }) {
  // Naive UI NUpload 传递的 file 可能是 File 对象或 { file: File } 对象
  const rawFile = file.file || file
  handleCsvFileChange(rawFile)
}

async function handleDownloadTemplate() {
  try {
    const blob = await api.downloadCsvTemplate()
    const url = window.URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url
    a.download = 'vehicle_import_template.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (e) {
    $message.error('CSV模板下载失败: ' + (e.response?.data?.msg || e.message))
  }
}

// ===== 统计信息 =====
const statCards = computed(() => [
  { label: '外部飞书导入', count: dataSourceCounts.value.feishu || 0, icon: 'material-symbols:cloud-done', color: '#2080f0', bg: 'rgba(32,128,240,0.08)' },
  { label: '外部CSV导入', count: dataSourceCounts.value.csv || 0, icon: 'material-symbols:upload-file', color: '#18a058', bg: 'rgba(24,160,88,0.08)' },
  { label: '系统导入', count: dataSourceCounts.value.manual || 0, icon: 'material-symbols:edit-note', color: '#f0a020', bg: 'rgba(240,160,32,0.08)' },
])

</script>

<template>
  <div class="data-source-root vehicle-card">
    <!-- 顶部控制栏：4个容器一排 -->
    <div class="top-bar">
      <!-- 容器1-3：数据统计 -->
      <div v-for="card in statCards" :key="card.label" class="top-item">
        <div class="top-item-icon" :style="{ background: card.bg }">
          <TheIcon :icon="card.icon" :size="18" :style="{ color: card.color }" />
        </div>
        <div class="top-item-body">
          <span class="top-item-title">{{ card.label }}</span>
          <span class="top-item-count">{{ card.count }}</span>
        </div>
      </div>

      <!-- 容器4：自动同步开关（最右侧） -->
      <div class="top-item">
        <div class="top-item-icon" style="background: rgba(32,128,240,0.1)">
          <TheIcon icon="material-symbols:cloud-sync" :size="18" style="color: #2080f0" />
        </div>
        <div class="top-item-body">
          <span class="top-item-title sync-title">车辆管理与飞书多维表格自动同步开关</span>
          <NSwitch :value="autoSyncEnabled" @update:value="handleAutoSyncToggle" size="small" />
        </div>
      </div>
    </div>

    <!-- 数据源卡片列表 -->
    <div class="source-grid">
      <!-- 数据源1：外部飞书导入（预置） -->
      <NCard :bordered="false" class="source-card" :content-style="{ display: 'flex', flexDirection: 'column', flex: 1 }">
        <template #header>
          <div class="source-card-header">
            <div class="source-card-icon" style="background: rgba(32,128,240,0.1)">
              <TheIcon icon="material-symbols:cloud-sync" :size="20" style="color: #2080f0" />
            </div>
            <div>
              <div class="source-card-title">试验管理-车辆管理数据库</div>
              <div class="source-card-subtitle">从预置飞书多维表格导入车辆数据</div>
            </div>
          </div>
        </template>

        <NAlert type="info" class="mb-16">
          <template #header>同步说明</template>
          系统已预置 App ID、App Secret、Base ID 及车辆信息表 ID。
          <br />如果同步失败，请确认：
          <br />1. 多维表格中已添加"试验车辆任务状态小程序"为协作者
          <br />2. 操作路径：右上角 "···" → "更多" → "添加文档应用" → 搜索并添加
          <br />3. 飞书开放平台应用已开启 bitable 权限
        </NAlert>

        <div class="source-action">
          <NButton
            type="primary"
            :loading="syncingSource1"
            size="large"
            @click="handleSyncSource1"
            block
          >
            <template #icon>
              <TheIcon icon="material-symbols:sync" :size="18" />
            </template>
            外部飞书导入
          </NButton>
        </div>
      </NCard>

      <!-- 数据源2：外部飞书导入（用户自定义） -->
      <NCard :bordered="false" class="source-card" :content-style="{ display: 'flex', flexDirection: 'column', flex: 1 }">
        <template #header>
          <div class="source-card-header">
            <div class="source-card-icon" style="background: rgba(240,160,32,0.1)">
              <TheIcon icon="material-symbols:settings-applications" :size="20" style="color: #f0a020" />
            </div>
            <div>
              <div class="source-card-title">外部飞书导入（自定义表格）</div>
              <div class="source-card-subtitle">配置您自己的飞书多维表格，首次设置后自动保存</div>
            </div>
          </div>
        </template>

        <NAlert type="warning" class="mb-16">
          <template #header>⚠️ 授权说明</template>
          请先在目标多维表格中添加应用权限：
          <br />1. 多维表格右上角 "···" → "更多" → "添加文档应用"
          <br />2. 搜索 <b>"试验车辆任务状态小程序"</b> 并添加
          <br />3. 复制表格的 Base ID 和 Table ID 填入下方
        </NAlert>

        <div class="config-form">
          <NInputGroup>
            <NInputGroupLabel style="min-width: 72px">Base ID</NInputGroupLabel>
            <NInput
              v-model:value="userBaseId"
              placeholder="粘贴多维表格 Base ID"
              clearable
            />
          </NInputGroup>
          <NInputGroup>
            <NInputGroupLabel style="min-width: 72px">Table ID</NInputGroupLabel>
            <NInput
              v-model:value="userTableId"
              placeholder="粘贴表格 Table ID"
              clearable
            />
          </NInputGroup>
        </div>

        <div class="source-action">
          <NButton
            type="primary"
            :loading="savingConfig"
            :disabled="!userBaseId || !userTableId"
            size="large"
            @click="handleSaveAndSyncSource2"
            block
          >
            <template #icon>
              <TheIcon icon="material-symbols:save" :size="18" />
            </template>
            保存并同步
          </NButton>
        </div>
      </NCard>

      <!-- 数据源3：外部CSV导入 -->
      <NCard :bordered="false" class="source-card" :content-style="{ display: 'flex', flexDirection: 'column', flex: 1 }">
        <template #header>
          <div class="source-card-header">
            <div class="source-card-icon" style="background: rgba(24,160,88,0.1)">
              <TheIcon icon="material-symbols:upload-file" :size="20" style="color: #18a058" />
            </div>
            <div>
              <div class="source-card-title">外部CSV导入</div>
              <div class="source-card-subtitle">上传 CSV 文件批量导入车辆数据</div>
            </div>
          </div>
        </template>

        <NAlert type="info" class="mb-16">
          <template #header>CSV 导入说明</template>
          支持 UTF-8 / GBK 编码的 .csv 文件。第一行为表头，系统根据车辆 VN 自动去重更新。
          <br />建议先下载模板，按模板格式填写后上传。
        </NAlert>

        <div class="csv-actions">
          <NButton class="mb-16" size="large" @click="handleDownloadTemplate" block>
            <template #icon>
              <TheIcon icon="material-symbols:download" :size="18" />
            </template>
            下载 CSV 导入模板
          </NButton>

          <NUpload
            accept=".csv"
            :max="1"
            :show-file-list="false"
            :custom-request="handleCsvUpload"
          >
            <NButton size="large" block :loading="csvUploading">
              <template #icon>
                <TheIcon icon="material-symbols:upload-file" :size="18" />
              </template>
              {{ csvFileName ? csvFileName : '选择 CSV 文件上传' }}
            </NButton>
          </NUpload>
        </div>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
.data-source-root {
  height: 100%;
  overflow-y: auto;
}

/* 顶部控制栏 — 4个容器一排 */
.top-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.top-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #eef0f4;
}

.top-item-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.top-item-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.top-item-title {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.sync-title {
  white-space: normal;
  line-height: 1.4;
}

.top-item-count {
  font-size: 20px;
  font-weight: 700;
  color: #333;
  line-height: 1;
}

/* 数据源卡片网格：3 个卡片占满宽度 */
.source-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.source-card {
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.source-card :deep(.n-card__content) {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.source-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.source-card-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.source-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.source-card-subtitle {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.source-action {
  margin-top: auto;
  margin-bottom: 4px;
}

/* 配置表单 */
.config-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* CSV 按钮区 */
.csv-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 工具类 */
.mb-16 {
  margin-bottom: 16px;
}

.mt-12 {
  margin-top: 12px;
}
</style>
