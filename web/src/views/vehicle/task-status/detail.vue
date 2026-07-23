<script setup>
import { ref, watch } from 'vue'
import { NForm, NFormItem, NInput, NSelect, NDatePicker, NGrid, NGi, NButton, NDivider, NSpace, useMessage } from 'naive-ui'
import api from '@/api'
import { startLocation, stopLocation, isLocating, getLocatingVehicleId } from './locationService'

const props = defineProps({ visible: Boolean, vehicle: Object })
const emit = defineEmits(['update:visible', 'saved'])
const show = ref(false)
watch(() => props.visible, v => show.value = v)
watch(show, v => emit('update:visible', v))

const $message = useMessage()
const saving = ref(false)
const locating = ref(isLocating())
const form = ref({})

function onLocationUpdate(data) {
  form.value.latitude = data.lat
  form.value.longitude = data.lng
  form.value.location_info = data.location_info
  emit('saved', data)
}

async function handleStartLocation() {
  if (isLocating()) {
    $message.info('定位已在运行中')
    locating.value = true
    return
  }
  if (!navigator.geolocation) {
    $message.error('浏览器不支持定位功能')
    return
  }
  const ok = startLocation(form.value.id, onLocationUpdate)
  if (ok) {
    locating.value = true
  }
}

function handleStopLocation() {
  stopLocation()
  locating.value = false
  $message.info('已停止定位')
}

const statusOpts = ['待开始','空','进行中','已完成','故障或事故'].map(v=>({label:v,value:v}))
const taskOpts = ['城市NCA','高速NCA','泊车测试','L0L1','用列点检','车辆整备','静态测试','内场测试'].map(v=>({label:v,value:v}))
const travelOpts = ['在厂','出差','返程'].map(v=>({label:v,value:v}))

function initForm(v) {
  form.value = {
    id: v?.id, vn: v?.vn||'', vehicle_code: v?.vehicle_code||'', vehicle_model: v?.vehicle_model||'',
    power_type: v?.power_type||'', color: v?.color||'',
    borrower: v?.borrower||'', borrow_expire_date: v?.borrow_expire_date ? new Date(v.borrow_expire_date).getTime() : null,
    temp_plate_expire_date: v?.temp_plate_expire_date ? new Date(v.temp_plate_expire_date).getTime() : null,
    insurance_area: v?.insurance_area||'',
    task_status: v?.task_status||null, test_task: v?.test_task||null,
    tester: v?.tester||'', driver: v?.driver||'', travel_status: v?.travel_status||null,
    test_city: v?.test_city||'', exit_permit: v?.exit_permit||'', parking_spot: v?.parking_spot||'',
    location_info: v?.location_info||'',
    latitude: v?.latitude||null,
    longitude: v?.longitude||null,
  }
  // 恢复定位状态
  locating.value = isLocating() && getLocatingVehicleId() === v?.id
}

watch(() => props.vehicle, v => { if (v) initForm(v) }, { immediate: true })

async function handleSave() {
  saving.value = true
  try {
    const data = { ...form.value }
    if (data.borrow_expire_date) data.borrow_expire_date = new Date(data.borrow_expire_date).toISOString().substring(0,10)
    if (data.temp_plate_expire_date) data.temp_plate_expire_date = new Date(data.temp_plate_expire_date).toISOString().substring(0,10)
    await api.updateVehicle(data)
    $message.success('保存成功')
    emit('saved', data)
    show.value = false
  } catch (e) {
    if (e?.errors) return
    $message.error('保存失败')
  } finally { saving.value = false }
}
</script>

<template>
  <div v-if="show" class="detail-overlay">
    <div class="detail-panel">
      <div class="detail-hdr">
        <span>{{ form.vehicle_code||form.vn }} — 车辆任务详情</span>
        <NButton size="small" @click="show = false">✕ 关闭</NButton>
      </div>
      <div class="detail-bd">
        <NForm :model="form" label-placement="top" size="small">
          <div class="sec-title">基础信息</div>
          <NGrid :cols="3" :x-gap="12">
            <NGi><NFormItem label="车辆VN"><NInput :value="form.vn" disabled /></NFormItem></NGi>
            <NGi><NFormItem label="车辆编号"><NInput :value="form.vehicle_code" disabled /></NFormItem></NGi>
            <NGi><NFormItem label="车型项目"><NInput :value="form.vehicle_model" disabled /></NFormItem></NGi>
            <NGi><NFormItem label="动力类型"><NInput :value="form.power_type" disabled /></NFormItem></NGi>
            <NGi><NFormItem label="颜色"><NInput :value="form.color" disabled /></NFormItem></NGi>
            <NGi><NFormItem label="借用人"><NInput :value="form.borrower" disabled /></NFormItem></NGi>
            <NGi><NFormItem label="借用到期"><NDatePicker :value="form.borrow_expire_date" disabled type="date" /></NFormItem></NGi>
            <NGi><NFormItem label="临牌到期"><NDatePicker :value="form.temp_plate_expire_date" disabled type="date" /></NFormItem></NGi>
            <NGi><NFormItem label="保险区域"><NInput :value="form.insurance_area" disabled /></NFormItem></NGi>
          </NGrid>
          <NDivider />
          <div class="sec-title">任务状态信息</div>
          <NGrid :cols="3" :x-gap="12">
            <NGi><NFormItem label="任务状态"><NSelect v-model:value="form.task_status" :options="statusOpts" /></NFormItem></NGi>
            <NGi><NFormItem label="试验任务"><NSelect v-model:value="form.test_task" :options="taskOpts" /></NFormItem></NGi>
            <NGi><NFormItem label="测试人员"><NInput v-model:value="form.tester" /></NFormItem></NGi>
            <NGi><NFormItem label="驾驶人员"><NInput v-model:value="form.driver" /></NFormItem></NGi>
            <NGi><NFormItem label="出差状态"><NSelect v-model:value="form.travel_status" :options="travelOpts" /></NFormItem></NGi>
            <NGi><NFormItem label="试验城市"><NInput v-model:value="form.test_city" /></NFormItem></NGi>
            <NGi><NFormItem label="位置信息"><NInput v-model:value="form.location_info" disabled placeholder="获取定位后自动填充地址" /></NFormItem></NGi>
            <NGi><NFormItem label="纬度"><NInput :value="form.latitude != null ? form.latitude.toFixed(6) : ''" disabled placeholder="自动获取" /></NFormItem></NGi>
            <NGi><NFormItem label="经度"><NInput :value="form.longitude != null ? form.longitude.toFixed(6) : ''" disabled placeholder="自动获取" /></NFormItem></NGi>
            <NGi><NFormItem label="出门单"><NInput v-model:value="form.exit_permit" /></NFormItem></NGi>
            <NGi><NFormItem label="停车位"><NInput v-model:value="form.parking_spot" /></NFormItem></NGi>
          </NGrid>
        </NForm>
      </div>
      <div class="loc-bar">
        <NButton v-if="!locating" type="info" @click="handleStartLocation">🛰️ 获取定位</NButton>
        <NButton v-if="locating" type="warning" @click="handleStopLocation">⏹ 停止定位</NButton>
        <span v-if="locating" style="font-size:12px;color:#2080f0">持续获取中…</span>
      </div>
      <div class="detail-ft">
        <NSpace>
          <NButton @click="show = false">取消</NButton>
          <NButton type="primary" :loading="saving" @click="handleSave">保存</NButton>
        </NSpace>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-overlay { position: absolute; top: 0; left: 0; bottom: 0; width: 52%; background: #fff; z-index: 10; display: flex; flex-direction: column; overflow: hidden; }
.detail-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.detail-hdr { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; border-bottom: 1px solid #eee; font-size: 15px; font-weight: 600; background: #fafafa; flex-shrink: 0; }
.detail-bd { flex: 1; overflow-y: auto; padding: 20px; }
.detail-ft { display: flex; justify-content: flex-end; padding: 12px 20px; border-top: 1px solid #eee; background: #fafafa; flex-shrink: 0; }
.sec-title { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 12px; padding-bottom: 6px; border-bottom: 2px solid #2080f0; }
.loc-bar { display: flex; align-items: center; gap: 10px; padding: 10px 0; margin: 4px 0; }
</style>
