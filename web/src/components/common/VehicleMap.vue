<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  markers: { type: Array, default: () => [] },
  height: { type: String, default: '100%' },
  projectColorMap: { type: Object, default: () => ({}) },
})

let map = null
let pendingMarkers = null
const mapContainer = ref(null)

const defaultColor = '#999'

function getColor(item) {
  return props.projectColorMap[item.vehicle_model] || defaultColor
}

function getLabel(item) {
  const project = item.vehicle_model || ''
  const code = item.vehicle_code || item.vn || ''
  return project && code ? `${project} ${code}` : (code || project || '--')
}

function loadLeaflet() {
  return new Promise((resolve) => {
    if (window.L) { resolve(); return }
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css'
    document.head.appendChild(link)
    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js'
    script.onload = () => resolve()
    document.head.appendChild(script)
  })
}

function createMap() {
  if (!mapContainer.value || !window.L) return
  if (map) { map.remove(); map = null }
  const L = window.L
  map = L.map(mapContainer.value, { zoomControl: true })
  L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
    subdomains: ['1','2','3','4'],
    maxZoom: 19,
  }).addTo(map)
  if (pendingMarkers != null) { updateMarkers(pendingMarkers); pendingMarkers = null }
}

function updateMarkers(data) {
  if (!map || !window.L) { pendingMarkers = data || pendingMarkers; return }
  const L = window.L
  const items = data || props.markers
  // 清除已有标记
  map.eachLayer(layer => { if (layer instanceof L.CircleMarker || layer instanceof L.Marker) map.removeLayer(layer) })

  const valid = items.filter(m => m.latitude && m.longitude && !isNaN(Number(m.latitude)) && !isNaN(Number(m.longitude)))
  if (!valid.length) { map.setView([30.59, 114.30], 5); return }

  const bounds = L.latLngBounds([])
  valid.forEach(item => {
    const lat = Number(item.latitude)
    const lng = Number(item.longitude)
    const color = getColor(item)
    const label = getLabel(item)

    const marker = L.circleMarker([lat, lng], {
      radius: 8,
      fillColor: color,
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.85,
    })
    marker.bindTooltip(label, { permanent: true, direction: 'top', offset: [0, -10], className: 'vm-tooltip' })
    marker.on('click', () => {
      L.popup()
        .setLatLng([lat, lng])
        .setContent(`<b>${label}</b><br>状态: ${item.task_status||'未知'}<br>任务: ${item.test_task||'--'}`)
        .openOn(map)
    })
    marker.addTo(map)
    bounds.extend([lat, lng])
  })
  if (bounds.isValid()) {
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 })
  }
}

watch(() => props.markers, (v) => nextTick(() => updateMarkers(v)), { deep: true })

onMounted(async () => {
  await nextTick()
  await loadLeaflet()
  nextTick(createMap)
})

onUnmounted(() => { if (map) { map.remove(); map = null } })
</script>

<template>
  <div ref="mapContainer" class="vm-container" :style="{ height }" />
</template>

<style>
.vm-tooltip {
  font-size: 11px !important;
  font-weight: 700 !important;
  border: 0 !important;
  box-shadow: none !important;
  background: rgba(0,0,0,0.7) !important;
  color: #fff !important;
  padding: 2px 8px !important;
  border-radius: 3px !important;
  white-space: nowrap !important;
}
.vm-tooltip::before { display: none !important; }
</style>

<style scoped>
.vm-container { width: 100%; border-radius: 8px; border: 1px solid #eef0f4; min-height: 200px; }
</style>
