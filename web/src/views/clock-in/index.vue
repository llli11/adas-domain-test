<template>
  <div class="clock-in-page">
    <div class="form-card">
      <h2 class="form-title">智驾域驾驶员工作日志收集表</h2>
      <p class="form-subtitle">带 <span class="required-mark">*</span> 为必填项</p>
      <n-space vertical :size="20">
        <div><div class="field-label"><span>日期</span><span class="required-mark">*</span></div>
          <n-date-picker v-model:value="recordDate" type="date" placeholder="请选择日期" style="width:100%" size="large" /></div>
        <div><div class="field-label"><span>填写人</span><span class="required-mark">*</span></div>
          <n-select v-model:value="personName" filterable :options="allPersonnelOpts" placeholder="请选择填写人" size="large" :loading="loadingTestOrders" /></div>
        <div><div class="field-label"><span>查询填写人所在车型项目</span></div>
          <n-input :value="autoProjectName" disabled size="large" /></div>
        <div><div class="field-label"><span>试验需求编号</span><span class="required-mark">*</span></div>
          <n-input v-model:value="requirementCode" placeholder="输入试验需求编号" size="large" /></div>
        <div><div class="field-label"><span>试验版本</span><span class="required-mark">*</span></div>
          <n-input v-model:value="testVersion" placeholder="输入试验版本号" size="large" /></div>
        <div><div class="field-label"><span>试验任务</span><span class="required-mark">*</span></div>
          <n-select v-model:value="testTask" :options="testTaskOptions" placeholder="请选择试验任务" size="large" /></div>
        <div><div class="field-label"><span>车辆编号</span><span class="required-mark">*</span></div>
          <n-input v-model:value="carNumber" placeholder="例：H37B-423#" size="large" /></div>
        <n-space :size="16">
          <div style="flex:1"><div class="field-label"><span>上班时间</span><span class="required-mark">*</span></div>
            <n-time-picker v-model:value="startTime" format="HH:mm" :use12h="false" size="large" style="width:100%" /></div>
          <div style="flex:1"><div class="field-label"><span>下班时间</span><span class="required-mark">*</span></div>
            <n-time-picker v-model:value="endTime" format="HH:mm" :use12h="false" size="large" style="width:100%" /></div>
        </n-space>

        <!-- 考勤打卡附件 -->
        <div><div class="field-label"><span>考勤打卡附件</span><span class="required-mark">*</span></div>
          <n-upload :action="uploadUrl" :data="{type:'clockin'}" :headers="uploadHeaders" accept="image/*,.pdf" @finish="handleAttachmentFinish">
            <n-button>上传文件</n-button></n-upload>
          <span v-if="attachmentUrl" class="upload-done">已上传</span></div>

        <!-- 垫付费用附件 -->
        <div><div class="field-label"><span>垫付费用附件</span></div>
          <n-upload :action="uploadUrl" :data="{type:'expense'}" :headers="uploadHeaders" accept="image/*,.pdf" @finish="handleExpenseAttachmentFinish">
            <n-button>上传附件</n-button></n-upload>
          <span v-if="expenseAttachmentUrl" class="upload-done">已上传</span></div>

        <div><div class="field-label"><span>当天是否加班</span><span class="required-mark">*</span></div>
          <n-select v-model:value="isOvertime" :options="[{label:'否',value:'否'},{label:'是',value:'是'}]" placeholder="请选择" size="large" /></div>
        <div><div class="field-label"><span>出差状态</span><span class="required-mark">*</span></div>
          <n-select v-model:value="travelStatus" :options="[{label:'出差',value:'出差'},{label:'未出差',value:'未出差'}]" placeholder="请选择" size="large" /></div>
        <div><div class="field-label"><span>工作地点</span><span class="required-mark">*</span></div>
          <n-input v-model:value="workLocation" placeholder="例武汉，重庆" size="large" /></div>

        <!-- 工作日时长（可编辑） -->
        <div><div class="field-label"><span>当天工作日时长(h)</span><span class="required-mark">*</span></div>
          <n-input-number v-model:value="workDuration" :min="0" :step="0.5" placeholder="请输入工作日时长" style="width:100%" size="large" /></div>

        <!-- 加班时长（始终可见） -->
        <div><div class="field-label"><span>当天加班时长(h)</span></div>
          <n-input-number v-model:value="overtimeHours" :min="0" :step="0.5" placeholder="请输入加班时长（选填）" style="width:100%" size="large" /></div>

        <!-- 总工时（自动计算） -->
        <div><div class="field-label"><span>当天总工时(h)</span></div>
          <n-input :value="`${totalHoursVal} 小时`" disabled size="large" /></div>

        <div><div class="field-label"><span>垫付费用总计(元)</span></div>
          <n-input-number v-model:value="dailyAdvanceTotal" :min="0" style="width:100%" size="large" /></div>

        <div><div class="field-label"><span>车辆初始里程</span></div>
          <n-input-number v-model:value="vehicleInitialMileage" :min="0" :step="0.1" style="width:100%" size="large" placeholder="km" /></div>
        <div><div class="field-label"><span>车辆结束里程</span></div>
          <n-input-number v-model:value="vehicleEndMileage" :min="0" :step="0.1" style="width:100%" size="large" placeholder="km" /></div>

        <div><div class="field-label"><span>定位位置</span></div>
          <n-button type="primary" ghost :loading="locating" @click="getLocation" style="width:100%">{{locating?'获取中...':'获取实时定位'}}</n-button>
          <div v-if="locationCoords" style="color:#333;font-size:14px;">{{locationCoords}}</div></div>
        <n-button type="primary" block size="large" :loading="submitting" @click="handleSubmit" class="submit-btn">提交打卡</n-button>
      </n-space>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { NSpace, NSelect, NInput, NInputNumber, NButton, NDatePicker, NTimePicker, NUpload } from 'naive-ui'
import expenseApi from '@/api/expense'
defineOptions({ name: '打卡登记' })

const recordDate = ref(Date.now()); const personName = ref(''); const requirementCode = ref('')
const testVersion = ref(''); const testTask = ref(null); const carNumber = ref('')
const startTime = ref(null); const endTime = ref(null)
const attachmentUrl = ref(''); const expenseAttachmentUrl = ref('')
const isOvertime = ref('否'); const overtimeHours = ref(0); const travelStatus = ref(null)
const workLocation = ref(''); const workDuration = ref(0)
const dailyAdvanceTotal = ref(0); const locationCoords = ref('')
const vehicleInitialMileage = ref(0); const vehicleEndMileage = ref(0)
const locating = ref(false); const submitting = ref(false)

const uploadUrl = '/api/v1/expense/attachment/upload-file'
const uploadHeaders = computed(() => { const t = localStorage.getItem('token'); return t ? { token: t } : {} })

function handleAttachmentFinish({ event }) {
  try { const r = JSON.parse(event?.target?.response || '{}'); if (r.data) attachmentUrl.value = r.data.url } catch (e) {}
}
function handleExpenseAttachmentFinish({ event }) {
  try { const r = JSON.parse(event?.target?.response || '{}'); if (r.data) expenseAttachmentUrl.value = r.data.url } catch (e) {}
}

const testOrders = ref([]); const loadingTestOrders = ref(false)
const allPersonnelOpts = computed(() => {
  const s = new Set(); const o = []
  for (const t of testOrders.value) {
    for (const n of (t.personnel_names || [])) {
      if (n === '测试') continue
      if (!s.has(n)) { s.add(n); o.push({ label: n, value: n }) }
    }
  }
  return o
})
const autoProjectName = computed(() => { if (!personName.value) return ''; const t = testOrders.value.find(to => (to.personnel_names || []).includes(personName.value)); return t?.project_name || '' })
const autoTestOrderNo = computed(() => { if (!personName.value) return ''; const t = testOrders.value.find(to => (to.personnel_names || []).includes(personName.value)); return t ? t.test_order_no : '' })
const testTaskOptions = [{ label: '行车', value: '行车' }, { label: '泊车', value: '泊车' }, { label: '用例点检', value: '用例点检' }, { label: '车辆整备', value: '车辆整备' }]

// 总工时 = 工作日时长 + 加班时长
const totalHoursVal = computed(() => Math.round((workDuration.value + (overtimeHours.value || 0)) * 10) / 10)

function getLocation() { if (!navigator.geolocation) return; locating.value = true; navigator.geolocation.getCurrentPosition(p => { locationCoords.value = `${p.coords.latitude.toFixed(6)}, ${p.coords.longitude.toFixed(6)}`; locating.value = false }, () => { locating.value = false }, { enableHighAccuracy: true, timeout: 10000 }) }
watch(personName, v => { if (v) requirementCode.value = `XQ-${v}-${Date.now().toString().slice(-6)}` })

function formatTimeStr(val) { if (!val) return null; if (typeof val === 'string') return val; const d = new Date(val); return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}` }

async function handleSubmit() {
  if (!recordDate.value) return warn('请选择日期'); if (!personName.value) return warn('请选择填写人')
  if (!testVersion.value) return warn('请输入试验版本'); if (!testTask.value) return warn('请选择试验任务')
  if (!carNumber.value) return warn('请输入车辆编号'); if (!startTime.value || !endTime.value) return warn('请选择上下班时间')
  if (!attachmentUrl.value) return warn('请上传考勤打卡附件'); if (!travelStatus.value) return warn('请选择出差状态')
  if (!workLocation.value) return warn('请输入工作地点')
  if (!workDuration.value || workDuration.value <= 0) return warn('请输入工作日时长')

  submitting.value = true
  try {
    const ds = new Date(recordDate.value).toISOString().split('T')[0]
    await expenseApi.submitDriverClockIn({
      test_order_no: autoTestOrderNo.value, person_name: personName.value, record_date: ds,
      requirement_code: requirementCode.value, test_version: testVersion.value,
      test_task: testTask.value, car_number: carNumber.value,
      start_time: formatTimeStr(startTime.value), end_time: formatTimeStr(endTime.value),
      is_overtime: isOvertime.value,
      work_duration: workDuration.value,
      overtime_hours: overtimeHours.value || 0,
      total_hours: totalHoursVal.value,
      travel_status: travelStatus.value, work_location: workLocation.value,
      location_coords: locationCoords.value,
      daily_advance_total: dailyAdvanceTotal.value,
      vehicle_initial_mileage: vehicleInitialMileage.value,
      vehicle_end_mileage: vehicleEndMileage.value,
      expense_details: [],
      attachment_url: attachmentUrl.value,
      expense_attachment_url: expenseAttachmentUrl.value,
    })
    window.$message?.success('打卡成功')
  } catch (e) { console.error(e); window.$message?.error('提交失败') } finally { submitting.value = false }
}
function warn(m) { window.$message?.warning(m) }
async function fetchTestOrders() { loadingTestOrders.value = true; try { const r = await expenseApi.getClockInTestOrders(); testOrders.value = r.data || [] } catch (e) { console.error(e) } finally { loadingTestOrders.value = false } }
onMounted(() => fetchTestOrders())
</script>

<style scoped>
.clock-in-page { position:fixed; top:0;left:0;right:0;bottom:0; overflow-y:auto; background:#f5f6f7; padding:20px 0; }
.form-card { max-width:720px; margin:0 auto; background:#fff; border-radius:8px; padding:36px 40px; box-shadow:0 1px 4px rgba(0,0,0,0.06); }
.form-title { font-size:20px; font-weight:600; text-align:center; color:#1a1a1a; }
.form-subtitle { text-align:center; color:#999; font-size:13px; margin:0 0 28px; }
.field-label { margin-bottom:6px; font-size:14px; color:#333; font-weight:500; }
.required-mark { color:#e74c3c; margin-left:2px; }
.upload-done { color:#18a058; font-size:12px; margin-left:8px; }
.submit-btn { margin-top:8px; height:44px; font-size:15px; }
</style>
