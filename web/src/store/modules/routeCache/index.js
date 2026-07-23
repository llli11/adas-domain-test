import { defineStore } from 'pinia'
import { ref } from 'vue'
import mapwayApi from '@/api/mapway'

export const useRouteCacheStore = defineStore('routeCache', () => {
  const cooperativeCache = ref({})
  const selfDevelopedCache = ref({})

  function getCooperative(city) {
    return cooperativeCache.value[city] || null
  }

  function getSelfDeveloped(city) {
    return selfDevelopedCache.value[city] || null
  }

  function setCooperative(city, data) {
    cooperativeCache.value[city] = data
  }

  function setSelfDeveloped(city, data) {
    selfDevelopedCache.value[city] = data
  }

  function invalidateCooperative(city) {
    delete cooperativeCache.value[city]
  }

  function invalidateSelfDeveloped(city) {
    delete selfDevelopedCache.value[city]
  }

  async function preloadCooperative(city) {
    if (cooperativeCache.value[city]) return
    try {
      const res = await mapwayApi.getRouteDetailList({ city, page_size: 1000 })
      const data = res.data || []
      data.forEach(g => {
        (g.items || []).forEach(row => {
          row.imageList = null
          row.imageLoading = false
        })
      })
      cooperativeCache.value[city] = data
    } catch (e) {
      console.warn(`预加载合作项目 ${city} 失败:`, e)
    }
  }

  async function preloadSelfDeveloped(city) {
    if (selfDevelopedCache.value[city]) return
    try {
      const res = await mapwayApi.getSelfDevelopedRouteDetailList({ city, page_size: 1000 })
      const data = res.data || []
      data.forEach(g => {
        (g.items || []).forEach(row => {
          row.imageList = null
          row.imageLoading = false
        })
      })
      selfDevelopedCache.value[city] = data
    } catch (e) {
      console.warn(`预加载自研项目 ${city} 失败:`, e)
    }
  }

  async function preloadAllCooperative(cities, delayMs = 500) {
    for (const city of cities) {
      await preloadCooperative(city)
      if (delayMs > 0) await new Promise(r => setTimeout(r, delayMs))
    }
  }

  async function preloadAllSelfDeveloped(cities, delayMs = 500) {
    for (const city of cities) {
      await preloadSelfDeveloped(city)
      if (delayMs > 0) await new Promise(r => setTimeout(r, delayMs))
    }
  }

  return {
    cooperativeCache, selfDevelopedCache,
    getCooperative, getSelfDeveloped,
    setCooperative, setSelfDeveloped,
    invalidateCooperative, invalidateSelfDeveloped,
    preloadCooperative, preloadSelfDeveloped,
    preloadAllCooperative, preloadAllSelfDeveloped,
  }
})