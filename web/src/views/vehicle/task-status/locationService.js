/** 车辆定位服务 — 全局单例，组件销毁后持续运行 */
import api from '@/api'

let timer = null
let vehicleId = null
let onUpdate = null  // 回调：通知组件更新 UI

export function reverseGeocode(lat, lng) {
  return _reverseGeocode(lat, lng)
}

async function _reverseGeocode(lat, lng) {
  // 方案1：后端代理
  try {
    const res = await api.reverseGeocode(lat, lng)
    const addr = res?.data?.address || ''
    if (addr) return addr
  } catch (e) {
    console.warn('[Location] 后端逆地理编码失败:', e?.message || e)
  }
  // 方案2：直连 Nominatim
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 5000)
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1&accept-language=zh`,
      { signal: controller.signal }
    )
    clearTimeout(timeout)
    const data = await res.json()
    return data.display_name || ''
  } catch (e) {
    console.warn('[Location] 直连逆地理编码失败:', e?.message || e)
  }
  // 方案3：兜底 — 格式化的经纬度
  return `(${lat.toFixed(4)}, ${lng.toFixed(4)})`
}

function doUpdate() {
  if (!navigator.geolocation) return
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const lat = pos.coords.latitude
      const lng = pos.coords.longitude
      const addr = await _reverseGeocode(lat, lng)
      const payload = { id: vehicleId, latitude: lat, longitude: lng, location_info: addr }
      if (!vehicleId) { console.warn('[Location] 车辆ID无效'); return }
      try {
        const res = await api.updateVehicle(payload)
        console.log('[Location] 已保存', { lat, lng, addr, res })
      } catch (e) {
        console.warn('[Location] API保存失败:', e.response?.data || e.message)
      }
      if (onUpdate) onUpdate({ id: vehicleId, lat, lng, location_info: addr })
    },
    () => { console.warn('[Location] 定位失败，请检查浏览器定位权限') },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
  )
}

export function isLocating() {
  return timer !== null
}

export function getLocatingVehicleId() {
  return vehicleId
}

export function startLocation(id, updateCallback) {
  if (!navigator.geolocation) return false
  if (!id) { console.warn('[Location] 车辆ID为空'); return false }
  vehicleId = id
  onUpdate = updateCallback
  doUpdate()
  timer = setInterval(doUpdate, 10000)
  return true
}

export function stopLocation() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  vehicleId = null
  onUpdate = null
}

// 关闭标签页时清理
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', stopLocation)
}
