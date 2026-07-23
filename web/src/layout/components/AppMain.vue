<template>
  <router-view v-slot="{ Component, route }">
    <KeepAlive :include="keepAliveRouteNames">
      <component
        :is="Component"
        v-if="appStore.reloadFlag"
        :key="appStore.aliveKeys[route.name] || route.fullPath"
      />
    </KeepAlive>
  </router-view>
</template>

<script setup>
import { useAppStore } from '@/store'
import { useRouter } from 'vue-router'
const appStore = useAppStore()
const router = useRouter()
import { onMounted, ref, nextTick } from 'vue'
const allRoutes = router.getRoutes()
const keepAliveRouteNames = computed(() => {
  return allRoutes.filter((route) => route.meta?.keepAlive).map((route) => route.name)
})
</script>
<style>
/* 修复页面容器高度不填充问题 */
.main-content-section {
display: flex !important;
flex-direction: column !important;
}
.main-content-section > * {
flex: 1;
min-height: 0;
}
</style>
