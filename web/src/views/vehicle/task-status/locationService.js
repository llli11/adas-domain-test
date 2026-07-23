/** 车辆定位服务 — 全局单例，组件销毁后持续运行 */
import api from '@/api'

let timer = null
let vehicleId = null
let onUpdate = null  // 回调：通知组件更新 UI

async function reverseGeocode(lat, lng) {
  try {
    const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1&accept-language=zh`)
    const data = await res.json()
    return data.display_name || `${lat.toFixed(6)}, ${lng.toFixed(6)}`
  } catch {
    return `${lat.toFixed(6)}, ${lng.toFixed(6)}`
  }
}

function doUpdate() {
  if (!navigator.geolocation) return
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const lat = pos.coords.latitude
      const lng = pos.coords.longitude
      const addr = await reverseGeocode(lat, lng)
      try {
        await api.updateVehicle({
          id: vehicleId,
          latitude: lat,
          longitude: lng,
          location_info: addr,
        })
      } catch { /* silent */ }
      if (onUpdate) onUpdate({ id: vehicleId, lat, lng, location_info: addr })
    },
    () => {},
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
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
