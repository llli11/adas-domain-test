<template>
  <div class="clock-in-page">
    <div class="form-card">
      <h2 class="form-title">智驾域工程师工作日志收集表</h2>
      <p class="form-subtitle">请如实填写以下信息，带 <span class="required-mark">*</span> 为必填项</p>

      <n-space vertical :size="20">
        <!-- 1. 日期 -->
        <div>
          <div class="field-label"><span>日期</span><span class="required-mark">*</span></div>
          <n-date-picker v-model:value="recordDate" type="date" placeholder="请选择日期" style="width: 100%" size="large" />
        </div>

        <!-- 2. 填写人 -->
        <div>
          <div class="field-label"><span>填写人</span><span class="required-mark">*</span></div>
          <n-select v-model:value="personName" filterable :options="allPersonnelOpts" placeholder="请选择填写人" size="large" :loading="loadingTestOrders" />
        </div>

        <!-- 3. 所在车型项目（自动） -->
        <div>
          <div class="field-label"><span>查询填写人所在车型项目</span></div>
          <n-input :value="autoProjectName" disabled size="large" placeholder="选择填写人后自动带出" />
        </div>

        <!-- 4. 试验需求编号 -->
        <div>
          <div class="field-label"><span>试验需求编号</span><span class="required-mark">*</span></div>
          <n-input v-model:value="requirementCode" placeholder="输入试验需求编号" size="large" />
        </div>

        <!-- 5. 试验版本 -->
        <div>
          <div class="field-label"><span>试验版本</span><span class="required-mark">*</span></div>
          <n-input v-model:value="testVersion" placeholder="输入试验版本号" size="large" />
        </div>

        <!-- 6. 试验任务 -->
        <div>
          <div class="field-label"><span>试验任务</span><span class="required-mark">*</span></div>
          <n-select v-model:value="testTask" :options="testTaskOptions" placeholder="请选择试验任务" size="large" />
        </div>

        <!-- 7. 车辆编号 -->
        <div>
          <div class="field-label"><span>车辆编号</span><span class="required-mark">*</span></div>
          <n-input v-model:value="carNumber" placeholder="有多辆填写格式例：H37B-423#，H37B-456#" size="large" />
        </div>

        <!-- 8&9. 上下班时间 -->
        <n-space :size="16">
          <div style="flex: 1;">
            <div class="field-label"><span>上班时间</span><span class="required-mark">*</span></div>
            <n-time-picker v-model:value="startTime" format="HH:mm" placeholder="请选择" :use12h="false" size="large" style="width: 100%" />
          </div>
          <div style="flex: 1;">
            <div class="field-label"><span>下班时间</span><span class="required-mark">*</span></div>
            <n-time-picker v-model:value="endTime" format="HH:mm" placeholder="请选择" :use12h="false" size="large" style="width: 100%" />
          </div>
        </n-space>

        <!-- 10. 考勤打卡附件 -->
        <div>
          <div class="field-label"><span>考勤打卡附件</span><span class="required-mark">*</span></div>
          <n-upload :action="uploadUrl" :data="{ type: 'clockin' }" :headers="uploadHeaders" accept="image/*,.pdf" @finish="handleAttachmentFinish">
            <n-button>上传文件</n-button>
          </n-upload>
          <span v-if="attachmentUrl" class="upload-done">已上传</span>
        </div>

        <!-- 11. 当天是否加班 -->
        <div>
          <div class="field-label"><span>当天是否加班</span><span class="required-mark">*</span></div>
          <n-select v-model:value="isOvertime" :options="overtimeOptions" placeholder="请选择" size="large" />
        </div>

        <!-- 12. 出差状态 -->
        <div>
          <div class="field-label"><span>出差状态</span><span class="required-mark">*</span></div>
          <n-select v-model:value="travelStatus" :options="travelStatusOptions" placeholder="请选择出差状态" size="large" />
        </div>

        <!-- 13. 工作地点 -->
        <div>
          <div class="field-label"><span>工作地点</span><span class="required-mark">*</span></div>
          <n-input v-model:value="workLocation" placeholder="例武汉，重庆" size="large" />
        </div>

        <!-- 14. 当天工作日时长 -->
        <div>
          <div class="field-label"><span>当天工作日时长(h)</span><span class="required-mark">*</span></div>
          <n-input-number v-model:value="workDuration" :min="0" :step="0.5" placeholder="请输入工作日时长" style="width: 100%" size="large" />
        </div>

        <!-- 15. 当天加班时长 -->
        <div>
          <div class="field-label"><span>当天加班时长(h)</span></div>
          <n-input-number v-model:value="overtimeHours" :min="0" :step="0.5" placeholder="请输入加班时长（选填）" style="width: 100%" size="large" />
        </div>

        <!-- 16. 当天总工时 -->
        <div>
          <div class="field-label"><span>当天总工时(h)</span></div>
          <n-input :value="`${totalHoursVal} 小时`" disabled size="large" />
        </div>

        <!-- 17. 当天工作量 -->
        <div>
          <div class="field-label"><span>当天工作量(次/km)</span></div>
          <n-input v-model:value="workload" placeholder="例，泊车100次，行车400km" size="large" />
        </div>

        <!-- 18. 行泊车发现问题数 -->
        <div>
          <div class="field-label"><span>行泊车发现问题数</span></div>
          <n-input-number v-model:value="problemsFound" :min="0" placeholder="选填" style="width: 100%" size="large" />
        </div>

        <!-- 19. 点检用例数 -->
        <div>
          <div class="field-label"><span>点检用例数</span></div>
          <n-input-number v-model:value="checkCases" :min="0" placeholder="选填" style="width: 100%" size="large" />
        </div>

        <!-- 20. 刷写软件数量 -->
        <div>
          <div class="field-label"><span>整备车辆刷写软件数量</span></div>
          <n-input-number v-model:value="softwareFlashCount" :min="0" placeholder="选填" style="width: 100%" size="large" />
        </div>

        <!-- 21. 问题明细 -->
        <div>
          <div class="field-label"><span>问题明细</span></div>
          <n-input v-model:value="issueDetail" type="textarea" :rows="3" placeholder="如有发现问题请详细描述" size="large" />
        </div>

        <!-- 22. 定位位置 -->
        <div>
          <div class="field-label"><span>定位位置</span></div>
          <n-space vertical :size="8">
            <n-button type="primary" ghost :loading="locating" @click="getLocation" style="width: 100%;">
              <template #icon>
                <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3A8.994 8.994 0 0 0 13 3.06V1h-2v2.06A8.994 8.994 0 0 0 3.06 11H1v2h2.06A8.994 8.994 0 0 0 11 20.94V23h2v-2.06A8.994 8.994 0 0 0 20.94 13H23v-2h-2.06zM12 19c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z"/></svg>
              </template>
              {{ locating ? '获取中...' : '获取实时定位' }}
            </n-button>
            <div v-if="locationCoords" style="color: #333; font-size: 14px;">{{ locationCoords }}</div>
          </n-space>
          <div v-if="locateError" style="color: #e74c3c; font-size: 12px; margin-top: 4px;">{{ locateError }}</div>
        </div>

        <!-- 提交 -->
        <n-button type="primary" block size="large" :loading="submitting" @click="handleSubmit" class="submit-btn">
          提交打卡
        </n-button>
      </n-space>
    </div>
  </div>

  <!-- 成功弹窗 -->
  <n-modal v-model:show="submitted" :mask-closable="false" preset="card" title="提交成功" :bordered="false" closable @close="resetForm">
    <div class="success-content">
      <n-icon size="56" color="#18a058">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
      </n-icon>
      <p class="success-msg">打卡成功！</p>
      <p class="success-desc">您的今日工作日志已提交，等待审批。</p>
      <n-button type="primary" @click="resetForm">继续打卡</n-button>
    </div>
  </n-modal>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { NSpace, NSelect, NInput, NInputNumber, NButton, NDatePicker, NTimePicker, NUpload, NModal, NIcon } from 'naive-ui'
import expenseApi from '@/api/expense'

defineOptions({ name: '工程师打卡' })

// ==================== 基础字段 ====================
const recordDate = ref(Date.now())
const personName = ref('')
const requirementCode = ref('')
const testVersion = ref('')
const testTask = ref(null)
const carNumber = ref('')
const startTime = ref(null)
const endTime = ref(null)
const attachmentUrl = ref('')
const isOvertime = ref('未加班')
const overtimeHours = ref(0)
const travelStatus = ref(null)
const workLocation = ref('')
const workload = ref('')
const problemsFound = ref(0)
const checkCases = ref(0)
const softwareFlashCount = ref(0)
const issueDetail = ref('')
const locationCoords = ref('')
const locating = ref(false)
const locateError = ref('')
const submitting = ref(false)
const submitted = ref(false)

// ==================== 上传 ====================
const uploadUrl = '/api/v1/expense/attachment/upload-file'
const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { token } : {}
})

function handleAttachmentFinish({ event }) {
  try {
    const r = JSON.parse(event?.target?.response || '{}')
    if (r.data) attachmentUrl.value = r.data.url
  } catch (e) { /* ignore */ }
}

// ==================== 人员数据 ====================
const testOrders = ref([])
const loadingTestOrders = ref(false)

const allPersonnelOpts = computed(() => {
  const seen = new Set()
  const opts = []
  for (const t of testOrders.value) {
    for (const name of (t.personnel_names || [])) {
      if (name === '测试') continue
      if (!seen.has(name)) {
        seen.add(name)
        opts.push({ label: name, value: name })
      }
    }
  }
  return opts
})

const autoProjectName = computed(() => {
  if (!personName.value) return ''
  const t = testOrders.value.find(to => (to.personnel_names || []).includes(personName.value))
  return t?.project_name || ''
})

const autoTestOrderNo = computed(() => {
  if (!personName.value) return ''
  const t = testOrders.value.find(to => (to.personnel_names || []).includes(personName.value))
  return t ? t.test_order_no : ''
})

const autoProjectId = computed(() => {
  if (!personName.value) return null
  const t = testOrders.value.find(to => (to.personnel_names || []).includes(personName.value))
  return t?.project_id || null
})

// ==================== 选项 ====================
const testTaskOptions = [
  { label: '行车', value: '行车' },
  { label: '泊车', value: '泊车' },
  { label: '用例点检', value: '用例点检' },
  { label: '车辆整备', value: '车辆整备' },
]

const travelStatusOptions = [
  { label: '出差', value: '出差' },
  { label: '未出差', value: '未出差' },
]

const overtimeOptions = [
  { label: '未加班', value: '未加班' },
  { label: '加班', value: '加班' },
]

// ==================== 工作时长 ====================
const workDuration = ref(0)

const totalHoursVal = computed(() => {
  return Math.round((workDuration.value + (overtimeHours.value || 0)) * 10) / 10
})

// ==================== 定位 ====================
function getLocation() {
  if (!navigator.geolocation) { locateError.value = '您的浏览器不支持定位功能'; return }
  locating.value = true
  locateError.value = ''
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const { latitude, longitude } = pos.coords
      locationCoords.value = `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
      locating.value = false
    },
    (err) => {
      locating.value = false
      switch (err.code) {
        case err.PERMISSION_DENIED: locateError.value = '请允许定位权限后重试'; break
        case err.POSITION_UNAVAILABLE: locateError.value = '无法获取位置信息'; break
        case err.TIMEOUT: locateError.value = '获取定位超时，请重试'; break
        default: locateError.value = '定位失败，请重试'
      }
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
  )
}

// ==================== 自动填充 ====================
watch(personName, (val) => {
  if (val) requirementCode.value = `XQ-${val}-${Date.now().toString().slice(-6)}`
})

// ==================== 重置 ====================
function resetForm() {
  submitted.value = false
  recordDate.value = Date.now()
  personName.value = ''
  requirementCode.value = ''
  testVersion.value = ''
  testTask.value = null
  carNumber.value = ''
  startTime.value = null
  endTime.value = null
  attachmentUrl.value = ''
  isOvertime.value = '未加班'
  overtimeHours.value = 0
  workDuration.value = 0
  travelStatus.value = null
  workLocation.value = ''
  workload.value = ''
  problemsFound.value = 0
  checkCases.value = 0
  softwareFlashCount.value = 0
  issueDetail.value = ''
  locationCoords.value = ''
  locateError.value = ''
}

// ==================== 加载 ====================
async function fetchTestOrders() {
  loadingTestOrders.value = true
  try {
    const res = await expenseApi.getClockInTestOrders()
    testOrders.value = res.data || []
  } catch (e) { console.error('加载人员列表失败:', e) }
  finally { loadingTestOrders.value = false }
}

// ==================== 提交 ====================
function formatTimeStr(val) {
  if (!val) return null
  if (typeof val === 'string') return val
  const d = new Date(val)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function handleSubmit() {
  if (!recordDate.value) return warn('请选择日期')
  if (!personName.value) return warn('请选择填写人')
  if (!requirementCode.value) return warn('请输入试验需求编号')
  if (!testVersion.value) return warn('请输入试验版本')
  if (!testTask.value) return warn('请选择试验任务')
  if (!carNumber.value) return warn('请输入车辆编号')
  if (!startTime.value || !endTime.value) return warn('请选择上下班时间')
  if (!attachmentUrl.value) return warn('请上传考勤打卡附件')
  if (!travelStatus.value) return warn('请选择出差状态')
  if (!workLocation.value) return warn('请输入工作地点')
  if (!workDuration.value || workDuration.value <= 0) return warn('请输入工作日时长')

  submitting.value = true
  try {
    const dateStr = new Date(recordDate.value).toISOString().split('T')[0]
    await expenseApi.engineerClockInSubmit({
      project_id: autoProjectId.value || 1,
      test_order_no: autoTestOrderNo.value || '',
      record_date: dateStr,
      person_name: personName.value,
      test_task: testTask.value,
      car_number: carNumber.value,
      start_time: formatTimeStr(startTime.value),
      end_time: formatTimeStr(endTime.value),
      is_overtime: isOvertime.value === '加班',
      overtime_hours: overtimeHours.value || 0,
      work_duration: workDuration.value,
      total_hours: totalHoursVal.value,
      travel_status: travelStatus.value,
      work_location: workLocation.value,
      location_coords: locationCoords.value,
      workload: workload.value,
      problems_found: problemsFound.value,
      check_cases: checkCases.value,
      software_flash_count: softwareFlashCount.value,
      issue_detail: issueDetail.value,
      test_version: testVersion.value,
    })
    submitted.value = true
    window.$message?.success('打卡成功')
  } catch (e) {
    console.error('提交失败:', e)
    window.$message?.error('提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

function warn(msg) { window.$message?.warning(msg) }

onMounted(() => { fetchTestOrders() })
</script>

<style scoped>
.clock-in-page {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  overflow-y: auto;
  background: #f5f6f7;
  padding: 20px 0;
}

.form-card {
  max-width: 720px;
  margin: 0 auto;
  background: #fff;
  border-radius: 8px;
  padding: 36px 40px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.form-title { font-size: 20px; font-weight: 600; margin: 0 0 4px 0; text-align: center; color: #1a1a1a; }

.form-subtitle { text-align: center; color: #999; font-size: 13px; margin: 0 0 28px 0; }

.field-label { margin-bottom: 6px; font-size: 14px; color: #333; font-weight: 500; }

.required-mark { color: #e74c3c; margin-left: 2px; }

.upload-done { color: #18a058; font-size: 12px; margin-left: 8px; }

.submit-btn { margin-top: 8px; height: 44px; font-size: 15px; }

.success-content { text-align: center; padding: 20px 0; }

.success-msg { font-size: 17px; font-weight: 500; margin: 12px 0 4px; }

.success-desc { color: #999; font-size: 13px; margin-bottom: 20px; }

:deep(.n-input__input-el),
:deep(.n-date-picker__input input),
:deep(.n-time-picker__input input),
:deep(.n-base-selection-label),
:deep(.n-base-selection-input__content) {
  color: #333 !important;
}

:deep(.n-input__placeholder),
:deep(.n-base-selection-placeholder__content) {
  color: #999 !important;
}

:deep(.n-input-number .n-input__input-el) {
  color: #333 !important;
  text-align: right;
}
</style>

<style>
html, body { overflow: auto !important; height: auto !important; }

.n-base-select-menu .n-base-select-option__content,
.n-base-select-menu .n-base-select-option {
  color: #333 !important;
  background: #fff !important;
}

.n-base-select-menu .n-base-select-option:hover {
  background: #f0f5ff !important;
}

.n-base-select-menu .n-base-select-option.n-base-select-option--selected .n-base-select-option__content {
  color: #2080f0 !important;
}

.n-base-selection .n-base-selection-label,
.n-base-selection .n-base-selection-label__content,
.n-base-selection .n-base-selection-input__content,
.n-base-selection .n-base-selection-label__render-label > span {
  color: #333 !important;
}
</style>
