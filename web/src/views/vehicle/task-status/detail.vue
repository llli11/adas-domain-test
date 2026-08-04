<script setup>
import { ref, watch, computed } from 'vue'
import { NForm, NFormItem, NInput, NSelect, NDatePicker, NGrid, NGi, NButton, NDivider, NSpace, useMessage, NTag } from 'naive-ui'
import api from '@/api'
import { startLocation, stopLocation, isLocating, getLocatingVehicleId, reverseGeocode } from './locationService'
import TheIcon from '@/components/icon/TheIcon.vue'
import { formatRate } from '@/utils/common/common'

const props = defineProps({ visible: Boolean, vehicle: Object })
const emit = defineEmits(['update:visible', 'saved', 'close'])
const show = ref(!!props.visible)
watch(() => props.visible, v => { show.value = v }, { immediate: true })
watch(show, v => emit('update:visible', v))

function handleBack() {
  show.value = false
  emit('close')
}

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
  navigator.permissions?.query({ name: 'geolocation' }).then(perm => {
    if (perm.state === 'denied') $message.warning('定位权限已被拒绝，请在浏览器设置中允许')
  })
  const ok = startLocation(form.value.id, onLocationUpdate)
  if (ok) {
    locating.value = true
    $message.info('正在获取定位…')
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

// 利用率颜色
const rateColor = computed(() => {
  const r = form.value.borrower_7day_rate
  if (r == null) return '#999'
  const n = Number(r)
  if (isNaN(n)) return '#999'
  if (n < 10) return '#FF4D4F'
  if (n < 50) return '#FA8C16'
  return '#52C41A'
})

function initForm(v) {
  form.value = {
    id: v?.id, vn: v?.vn||'', vehicle_code: v?.vehicle_code||'', vehicle_model: v?.vehicle_model||'',
    power_type: v?.power_type||'', color: v?.color||'',
    borrower: v?.borrower||'', borrow_expire_date: v?.borrow_expire_date ? new Date(v.borrow_expire_date).getTime() : null,
    temp_plate_expire_date: v?.temp_plate_expire_date ? new Date(v.temp_plate_expire_date).getTime() : null,
    insurance_area: v?.insurance_area||'',
    temp_plate_area: v?.temp_plate_area||'', 
    borrower_7day_rate: v?.borrower_7day_rate,
    vehicle_status: v?.vehicle_status||'', vehicle_status_note: v?.vehicle_status_note||'',
    key_location: v?.key_location||'', vehicle_manager: v?.vehicle_manager||'',
    borrow_days: v?.borrow_days, vehicle_phase: v?.vehicle_phase||'',
    vehicle_model_config: v?.vehicle_model_config||'',
    temp_plate_info: v?.temp_plate_info||'', temp_plate_insurance_count: v?.temp_plate_insurance_count,
    borrower_account: v?.borrower_account||'', borrower_id: v?.borrower_id||'',
    borrower_phone: v?.borrower_phone||'', borrow_time: v?.borrow_time||'',
    dept_l1: v?.dept_l1||'', dept_l2: v?.dept_l2||'',
    vehicle_manager_id: v?.vehicle_manager_id||'', storage_days: v?.storage_days,
    qr_code: v?.qr_code||'', province: v?.province||'', city: v?.city||'',
    address_detail: v?.address_detail||'', is_monitored: v?.is_monitored||'',
    monitor_method: v?.monitor_method||'', is_first_vin_record: v?.is_first_vin_record||'',
    battery_pack_status: v?.battery_pack_status||'', engine_no: v?.engine_no||'',
    battery_pack_trace: v?.battery_pack_trace||'', front_motor_no: v?.front_motor_no||'',
    rear_motor_no: v?.rear_motor_no||'', battery_pack_part_no: v?.battery_pack_part_no||'',
    battery_pack_rated: v?.battery_pack_rated||'', trial_plan: v?.trial_plan||'',
    trial_plan_id: v?.trial_plan_id||'',
    is_under_modification: v?.is_under_modification||'', feishu_record_id: v?.feishu_record_id||'',
    task_status: v?.task_status||null, test_task: v?.test_task||null,
    tester: v?.tester||'', driver: v?.driver||'', travel_status: v?.travel_status||null,
    test_city: v?.test_city||'', exit_permit: v?.exit_permit||'', parking_spot: v?.parking_spot||'',
    location_info: v?.location_info||'',
    latitude: v?.latitude||null,
    longitude: v?.longitude||null,
    data_source: v?.data_source||'',
    has_controlled_items: v?.has_controlled_items||'',
  }
  locating.value = isLocating() && getLocatingVehicleId() === v?.id
  // 有经纬度时自动逆地理编码显示行政位置
  if (v?.latitude != null && v?.longitude != null) {
    reverseGeocode(v.latitude, v.longitude).then(addr => {
      if (addr) form.value.location_info = addr
    })
  }
}

watch(() => props.vehicle, v => { if (v) initForm(v) }, { immediate: true })

async function handleSave() {
  saving.value = true
  try {
    const data = { ...form.value }
    if (!data.id) { $message.warning('车辆ID无效'); saving.value = false; return }
    if (data.borrow_expire_date) data.borrow_expire_date = new Date(data.borrow_expire_date).toISOString().substring(0,10)
    if (data.temp_plate_expire_date) data.temp_plate_expire_date = new Date(data.temp_plate_expire_date).toISOString().substring(0,10)
    // 有经纬度但没有行政位置时，逆地理编码
    if (data.latitude != null && data.longitude != null && !data.location_info) {
      data.location_info = await reverseGeocode(data.latitude, data.longitude)
    }
    await api.updateVehicle(data)
    $message.success('保存成功')
    emit('saved', data)
    emit('close')
  } catch (e) {
    if (e?.errors) return
    $message.error('保存失败')
  } finally { saving.value = false }
}
</script>

<template>
  <div v-if="show" class="detail-container">
    <div class="detail-panel">
      <div class="detail-hdr">
        <span>{{ form.vehicle_code||form.vn }} — 车辆任务详情</span>
        <NButton size="small" @click="handleBack">✕ 关闭</NButton>
      </div>
      <div class="detail-bd-scroll">
      <div class="detail-bd">
        <NForm :model="form" label-placement="top" size="small">
          <div class="sec-title">✏️ 任务状态信息</div>
          <NGrid :cols="6" :x-gap="6">
            <NGi><NFormItem label="任务状态"><NSelect v-model:value="form.task_status" :options="statusOpts" size="small" /></NFormItem></NGi>
            <NGi><NFormItem label="试验任务"><NSelect v-model:value="form.test_task" :options="taskOpts" size="small" /></NFormItem></NGi>
            <NGi><NFormItem label="测试人员"><NInput v-model:value="form.tester" size="small" /></NFormItem></NGi>
            <NGi><NFormItem label="驾驶人员"><NInput v-model:value="form.driver" size="small" /></NFormItem></NGi>
            <NGi><NFormItem label="出差状态"><NSelect v-model:value="form.travel_status" :options="travelOpts" size="small" /></NFormItem></NGi>
            <NGi><NFormItem label="试验城市"><NInput v-model:value="form.test_city" size="small" /></NFormItem></NGi>
            <NGi><NFormItem label="出门单"><NInput v-model:value="form.exit_permit" size="small" /></NFormItem></NGi>
            <NGi><NFormItem label="停车位"><NInput v-model:value="form.parking_spot" size="small" /></NFormItem></NGi>
            <NGi><NFormItem label="位置信息"><NInput v-model:value="form.location_info" disabled size="small" placeholder="定位自动填充" /></NFormItem></NGi>
            <NGi><NFormItem label="纬度"><NInput :value="form.latitude != null ? form.latitude.toFixed(6) : ''" disabled size="small" placeholder="自动获取" /></NFormItem></NGi>
            <NGi><NFormItem label="经度"><NInput :value="form.longitude != null ? form.longitude.toFixed(6) : ''" disabled size="small" placeholder="自动获取" /></NFormItem></NGi>
            <NGi>
              <NFormItem label="定位">
                <NSpace>
                  <NButton v-if="!locating" type="info" size="small" @click="handleStartLocation">🛰️ 获取定位</NButton>
                  <NButton v-if="locating" type="warning" size="small" @click="handleStopLocation">⏹ 停止</NButton>
                  <span v-if="locating" style="font-size:11px;color:#2080f0">获取中…</span>
                </NSpace>
              </NFormItem>
            </NGi>
          </NGrid>
        </NForm>
      </div>
      <div class="detail-bd-info">
        <NDivider />
        <div class="sec-title">🚗 车辆信息</div>
        <NGrid :cols="6" :x-gap="8">
          <NGi><div class="info-item"><span class="info-lbl">车辆编号</span><span class="info-val">{{ form.vehicle_code||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">车辆VN</span><span class="info-val">{{ form.vn||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">车型项目</span><span class="info-val">{{ form.vehicle_model||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">动力类型</span><span class="info-val">{{ form.power_type||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">颜色</span><span class="info-val">{{ form.color||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">车辆阶段</span><span class="info-val">{{ form.vehicle_phase||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">车型配置</span><span class="info-val">{{ form.vehicle_model_config||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">车辆状态</span><span class="info-val">{{ form.vehicle_status||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">状态备注</span><span class="info-val">{{ form.vehicle_status_note||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">管制物品</span><span class="info-val">{{ form.has_controlled_items||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">借用人</span><span class="info-val">{{ form.borrower||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">借用到期</span><span class="info-val">{{ form.borrow_expire_date ? new Date(form.borrow_expire_date).toISOString().substring(0,10) : '--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">临牌到期</span><span class="info-val">{{ form.temp_plate_expire_date ? new Date(form.temp_plate_expire_date).toISOString().substring(0,10) : '--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">临牌区域</span><span class="info-val">{{ form.temp_plate_area||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">借用天数</span><span class="info-val">{{ form.borrow_days != null ? form.borrow_days : '--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">钥匙位置</span><span class="info-val">{{ form.key_location||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">车管</span><span class="info-val">{{ form.vehicle_manager||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">7日利用率</span><span class="info-val" :style="{color:rateColor,fontWeight:700}">{{ formatRate(form.borrower_7day_rate) }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">所在省</span><span class="info-val">{{ form.province||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">所在市</span><span class="info-val">{{ form.city||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">详细地址</span><span class="info-val">{{ form.address_detail||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">借车人账号</span><span class="info-val">{{ form.borrower_account||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">借车人ID</span><span class="info-val">{{ form.borrower_id||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">电话</span><span class="info-val">{{ form.borrower_phone||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">借车时间</span><span class="info-val">{{ form.borrow_time||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">一级部门</span><span class="info-val">{{ form.dept_l1||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">二级部门</span><span class="info-val">{{ form.dept_l2||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">车管ID</span><span class="info-val">{{ form.vehicle_manager_id||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">在库时长</span><span class="info-val">{{ form.storage_days != null ? form.storage_days : '--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">二维码</span><span class="info-val">{{ form.qr_code||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">是否监控</span><span class="info-val">{{ form.is_monitored||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">监控方式</span><span class="info-val">{{ form.monitor_method||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">临牌信息</span><span class="info-val">{{ form.temp_plate_info||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">办理次数</span><span class="info-val">{{ form.temp_plate_insurance_count != null ? form.temp_plate_insurance_count : '--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">发动机号</span><span class="info-val">{{ form.engine_no||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">前电机号</span><span class="info-val">{{ form.front_motor_no||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">后电机号</span><span class="info-val">{{ form.rear_motor_no||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">电池包状态</span><span class="info-val">{{ form.battery_pack_status||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">电池包额定电量</span><span class="info-val">{{ form.battery_pack_rated||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">试验策划</span><span class="info-val">{{ form.trial_plan||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">试验策划ID</span><span class="info-val">{{ form.trial_plan_id||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">电池包溯源码</span><span class="info-val">{{ form.battery_pack_trace||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">电池包零件号</span><span class="info-val">{{ form.battery_pack_part_no||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">是否VIN最早</span><span class="info-val">{{ form.is_first_vin_record||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">改制中</span><span class="info-val">{{ form.is_under_modification||'--' }}</span></div></NGi>
          <NGi><div class="info-item"><span class="info-lbl">数据来源</span><span class="info-val">{{ form.data_source||'--' }}</span></div></NGi>
        </NGrid>
      </div>
      </div>
      <div class="detail-ft">
        <NSpace>
          <NButton @click="handleBack">取消</NButton>
          <NButton type="primary" :loading="saving" @click="handleSave">保存</NButton>
        </NSpace>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-container { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.detail-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #fff; }
.detail-hdr { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; border-bottom: 1px solid #eee; font-size: 14px; font-weight: 600; background: #fafafa; flex-shrink: 0; }
.detail-bd { padding: 8px 12px 0; }
.detail-bd-info { padding: 0 12px 8px; }
.detail-bd-scroll { flex: 1; overflow-y: auto; min-height: 0; }
.detail-ft { display: flex; justify-content: flex-end; padding: 8px 12px; border-top: 1px solid #eee; background: #fafafa; flex-shrink: 0; }
.sec-title { font-size: 13px; font-weight: 600; color: #333; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 2px solid #2080f0; }

/* 任务状态表单标签 */
.detail-bd :deep(.n-form-item-label) { font-size: 12px; color: #2080f0; font-weight: 500; }

/* 车辆信息展示 */
.info-item { background: #f0f6ff; padding: 5px 8px; border-radius: 4px; margin-bottom: 4px; }
.info-lbl { font-size: 12px; color: #2080f0; display: block; margin-bottom: 1px; }
.info-val { font-size: 14px; color: #1a1a1a; font-weight: 500; }
</style>
