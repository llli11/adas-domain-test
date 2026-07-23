<script setup>
import { ref, markRaw, onMounted } from 'vue'
import { NTabs, NTabPane, NSpin, useMessage } from 'naive-ui'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import TaskStatus from './task-status/index.vue'
import DataDetail from './data-detail/index.vue'
import ExpiryAlerts from './expiry-alerts/index.vue'
import DataSource from './data-source/index.vue'

const $message = useMessage()
const activeTab = ref('task-status')
const syncing = ref(false)

const tabs = [
  { name: 'task-status', label: '车辆任务状态', icon: 'material-symbols:task-alt', component: markRaw(TaskStatus) },
  { name: 'data-detail', label: '车辆数据详情', icon: 'material-symbols:table-rows', component: markRaw(DataDetail) },
  { name: 'expiry-alerts', label: '异常状态提醒', icon: 'material-symbols:notifications-active', component: markRaw(ExpiryAlerts) },
  { name: 'data-source', label: '数据源管理', icon: 'material-symbols:cloud-sync', component: markRaw(DataSource) },
]

async function autoSyncFromFeishu() {
  if (localStorage.getItem('vehicle_auto_sync_enabled') !== 'true') return
  syncing.value = true
  try {
    const res = await api.syncFromFeishu()
    if (res.data?.success) $message.success(`同步完成: 新增${res.data.created || 0} 更新${res.data.updated || 0}`)
  } catch (e) { console.error(e) }
  finally { syncing.value = false }
}

onMounted(() => autoSyncFromFeishu())
</script>

<template>
  <div class="v-root">
    <div v-if="syncing" class="sync-bar"><NSpin size="small" /> 正在从飞书同步数据...</div>
    <NTabs v-model:value="activeTab" type="card" size="large" :closable="false" class="v-tabs">
      <NTabPane v-for="tab in tabs" :key="tab.name" :name="tab.name">
        <template #tab>
          <div class="tab-label"><TheIcon :icon="tab.icon" :size="16" /> {{ tab.label }}</div>
        </template>
        <div class="tab-inner"><component :is="tab.component" :key="tab.name" /></div>
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped>
.v-root { display: flex; flex-direction: column; height: calc(100vh - 110px); overflow: hidden; }
.sync-bar { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 8px; background: #e8f5e9; color: #2e7d32; font-size: 13px; flex-shrink: 0; }
.v-tabs { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.v-tabs :deep(.n-tabs-nav) { flex-shrink: 0; }
.v-tabs :deep(.n-tabs-content) { flex: 1; min-height: 0; overflow: hidden; }
.v-tabs :deep(.n-tab-pane) { height: 100%; }
.tab-inner { height: 100%; overflow: auto; }
.tab-label { display: flex; align-items: center; gap: 5px; }
</style>
