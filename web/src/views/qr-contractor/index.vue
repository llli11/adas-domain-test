<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { NTag } from 'naive-ui'

defineOptions({ name: 'QRContractor' })

const route = useRoute()
const token = ref(route.query.token || '')
const API_BASE = '/api/v1'

const staffInfo = ref(null)
const message = ref({ text: '', type: '' })
const activeTab = ref('depart')
const projectOptions = ref([])

// Depart/Return form
const vehicleName = ref('')
const taskType = ref('泊车')

// Work log form
const checkOutTime = ref('18:00')
const checkOutImage = ref('')
const normalHours = ref(8)
const overtimeHours = ref(0)
const workContent = ref('泊车')
const workProjectId = ref(null)
const advancePayment = ref(0)
const advancePaymentImage = ref('')

// Upload state
const checkOutUploading = ref(false)
const checkOutPreview = ref('')
const advancePaymentUploading = ref(false)
const advancePaymentPreview = ref('')

// Leave form
const leaveDate = ref('')
const leaveType = ref('事假')
const leaveReason = ref('')

// Show manual URL input
const showCheckOutUrlInput = ref(false)
const showAdvancePaymentUrlInput = ref(false)

onMounted(() => {
  if (!token.value) {
    message.value = { text: '缺少二维码参数，请重新扫描', type: 'error' }
    return
  }
  loadInfo()
  loadProjects()
})

function showMessage(text, type) {
  message.value = { text, type }
  setTimeout(() => { message.value = { text: '', type: '' } }, 3000)
}

async function request(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    const data = await res.json()
    return data
  } catch (e) {
    console.error('API error:', e)
    return { code: 500, msg: '网络请求失败: ' + e.message, data: null }
  }
}

async function loadInfo() {
  try {
    const res = await request(`${API_BASE}/contractor/qr/info?token=${encodeURIComponent(token.value)}`)
    if (res.code === 200 && res.data) {
      staffInfo.value = res.data
    } else {
      showMessage(res.msg || '加载失败', 'error')
    }
  } catch (e) {
    showMessage('加载人员信息失败', 'error')
  }
}

async function loadProjects() {
  try {
    const res = await request(`${API_BASE}/dept/list`)
    if (res.code === 200 && res.data) {
      projectOptions.value = res.data
    }
  } catch (e) {
    // dept/list requires auth, ignore error silently
  }
}

function switchTab(tab) {
  activeTab.value = tab
}

// 文件上传
async function uploadImage(file, field) {
  const formData = new FormData()
  formData.append('token', token.value)
  formData.append('file', file)

  try {
    const res = await fetch(`${API_BASE}/contractor/qr/upload`, {
      method: 'POST',
      body: formData,
    })
    const data = await res.json()
    if (data.code === 200 && data.data) {
      if (field === 'checkOut') {
        checkOutImage.value = data.data.url
        checkOutPreview.value = data.data.url
      } else {
        advancePaymentImage.value = data.data.url
        advancePaymentPreview.value = data.data.url
      }
      showMessage('图片上传成功', 'success')
    } else {
      showMessage(data.msg || '上传失败', 'error')
    }
  } catch (e) {
    showMessage('上传失败: ' + (e.message || '未知错误'), 'error')
  } finally {
    if (field === 'checkOut') {
      checkOutUploading.value = false
    } else {
      advancePaymentUploading.value = false
    }
  }
}

function handleFileSelect(event, field) {
  const file = event.target.files?.[0]
  if (!file) return
  startUpload(file, field)
  // 重置 input 以允许重复选择同一文件
  event.target.value = ''
}

function handleDrop(event, field) {
  const file = event.dataTransfer?.files?.[0]
  if (!file) return
  startUpload(file, field)
}

function handleDragOver(event) {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'copy'
}

function startUpload(file, field) {
  if (field === 'checkOut') {
    checkOutUploading.value = true
  } else {
    advancePaymentUploading.value = true
  }
  uploadImage(file, field)
}

function removeImage(field) {
  if (field === 'checkOut') {
    checkOutImage.value = ''
    checkOutPreview.value = ''
  } else {
    advancePaymentImage.value = ''
    advancePaymentPreview.value = ''
  }
}

function getImageUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return url
}

async function submitAction(action) {
  if (!vehicleName.value) {
    showMessage('请输入车辆名称', 'error')
    return
  }
  try {
    const endpoint = action === 'depart' ? '/contractor/qr/depart' : '/contractor/qr/return'
    const res = await request(`${API_BASE}${endpoint}`, {
      method: 'POST',
      body: JSON.stringify({
        token: token.value,
        vehicle_name: vehicleName.value,
        task_type: taskType.value,
        action,
      }),
    })
    if (res.code === 200) {
      showMessage(res.msg || '操作成功', 'success')
      loadInfo()
    } else {
      showMessage(res.msg || '操作失败', 'error')
    }
  } catch (e) {
    showMessage('操作失败: ' + (e.message || '未知错误'), 'error')
  }
}

async function submitWorkLog() {
  try {
    const payload = {
      token: token.value,
      check_out_time: checkOutTime.value || null,
      check_out_image: checkOutImage.value || null,
      normal_hours: parseFloat(normalHours.value) || 8,
      overtime_hours: parseFloat(overtimeHours.value) || 0,
      work_content: workContent.value || null,
      project_id: workProjectId.value || null,
      advance_payment: parseFloat(advancePayment.value) || 0,
      advance_payment_image: advancePaymentImage.value || null,
    }
    const res = await request(`${API_BASE}/contractor/qr/worklog`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    if (res.code === 200) {
      showMessage(res.msg || '提交成功', 'success')
    } else {
      showMessage(res.msg || '提交失败', 'error')
    }
  } catch (e) {
    showMessage('提交失败: ' + (e.message || '未知错误'), 'error')
  }
}

async function submitLeave() {
  try {
    const payload = {
      token: token.value,
      leave_date: leaveDate.value || null,
      leave_type: leaveType.value || null,
      reason: leaveReason.value || null,
    }
    const res = await request(`${API_BASE}/contractor/qr/leave`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    if (res.code === 200) {
      showMessage(res.msg || '提交成功', 'success')
    } else {
      showMessage(res.msg || '提交失败', 'error')
    }
  } catch (e) {
    showMessage('提交失败: ' + (e.message || '未知错误'), 'error')
  }
}
</script>

<template>
  <div class="qr-container">
    <h2>外委人员扫码登记</h2>

    <div v-if="message.text" :class="['message', message.type]">
      {{ message.text }}
    </div>

    <div v-if="staffInfo" class="info">
      <p><strong>姓名：</strong>{{ staffInfo.name || '' }}</p>
      <p><strong>属性：</strong>{{ staffInfo.type || '' }}</p>
      <p><strong>公司：</strong>{{ staffInfo.company || '' }}</p>
      <p>
        <strong>当前状态：</strong>
        <NTag :type="staffInfo.task_status === '任务中' ? 'error' : 'success'" size="small">
          {{ staffInfo.task_status || '未知' }}
        </NTag>
      </p>
    </div>
    <div v-else class="info">
      <p>正在加载人员信息...</p>
    </div>

    <div class="tabs">
      <div :class="['tab', { active: activeTab === 'depart' }]" @click="switchTab('depart')">出发/返回</div>
      <div :class="['tab', { active: activeTab === 'worklog' }]" @click="switchTab('worklog')">工作日志</div>
      <div :class="['tab', { active: activeTab === 'leave' }]" @click="switchTab('leave')">请假</div>
    </div>

    <!-- Depart / Return -->
    <div v-show="activeTab === 'depart'" class="section">
      <div class="form-group">
        <label>当前车辆</label>
        <input v-model="vehicleName" type="text" placeholder="请输入车辆名称">
      </div>
      <div class="form-group">
        <label>任务类型</label>
        <select v-model="taskType">
          <option value="泊车">泊车</option>
          <option value="行车">行车</option>
          <option value="LO">LO</option>
          <option value="L1">L1</option>
        </select>
      </div>
      <div class="btn-group">
        <button class="btn-success" @click="submitAction('depart')">出发</button>
        <button class="btn-primary" @click="submitAction('return')">返回</button>
      </div>
    </div>

    <!-- Work Log -->
    <div v-show="activeTab === 'worklog'" class="section">
      <div class="form-group">
        <label>下班时间</label>
        <input v-model="checkOutTime" type="text" placeholder="18:00">
      </div>
      <div class="form-group">
        <label>打卡截图</label>
        <!-- 上传区域 -->
        <div
          v-if="!checkOutPreview"
          class="upload-area"
          :class="{ 'uploading': checkOutUploading }"
          @dragover="handleDragOver"
          @drop="(e) => handleDrop(e, 'checkOut')"
          @click="() => {}"
        >
          <input
            type="file"
            accept="image/*"
            capture="environment"
            class="upload-input"
            @change="(e) => handleFileSelect(e, 'checkOut')"
          >
          <div class="upload-content">
            <span v-if="checkOutUploading" class="upload-spinner"></span>
            <span v-else class="upload-icon">📷</span>
            <span class="upload-text">{{ checkOutUploading ? '上传中...' : '点击拍照/选择照片 或拖入图片' }}</span>
          </div>
        </div>
        <!-- 预览区域 -->
        <div v-else class="preview-area">
          <img :src="getImageUrl(checkOutPreview)" alt="打卡截图预览" class="preview-img">
          <button class="btn-remove" @click="removeImage('checkOut')">✕</button>
        </div>
        <!-- 手动输入URL（兜底） -->
        <div class="url-toggle">
          <a href="javascript:void(0)" @click="showCheckOutUrlInput = !showCheckOutUrlInput">
            {{ showCheckOutUrlInput ? '收起' : '手动输入图片URL' }}
          </a>
        </div>
        <input
          v-show="showCheckOutUrlInput"
          v-model="checkOutImage"
          type="text"
          placeholder="粘贴图片链接"
          class="url-input"
        >
      </div>
      <div class="form-group">
        <label>正常工时</label>
        <input v-model.number="normalHours" type="number" step="0.5">
      </div>
      <div class="form-group">
        <label>加班工时</label>
        <input v-model.number="overtimeHours" type="number" step="0.5">
      </div>
      <div class="form-group">
        <label>工作内容</label>
        <select v-model="workContent">
          <option value="泊车">泊车</option>
          <option value="行车">行车</option>
        </select>
      </div>
      <div class="form-group">
        <label>今日车型项目</label>
        <select v-model="workProjectId">
          <option :value="null">请选择</option>
          <option v-for="p in projectOptions" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
      <div class="form-group">
        <label>垫付费用</label>
        <input v-model.number="advancePayment" type="number" step="0.01">
      </div>
      <div class="form-group">
        <label>垫付证明图片</label>
        <!-- 上传区域 -->
        <div
          v-if="!advancePaymentPreview"
          class="upload-area"
          :class="{ 'uploading': advancePaymentUploading }"
          @dragover="handleDragOver"
          @drop="(e) => handleDrop(e, 'advancePayment')"
        >
          <input
            type="file"
            accept="image/*"
            capture="environment"
            class="upload-input"
            @change="(e) => handleFileSelect(e, 'advancePayment')"
          >
          <div class="upload-content">
            <span v-if="advancePaymentUploading" class="upload-spinner"></span>
            <span v-else class="upload-icon">📷</span>
            <span class="upload-text">{{ advancePaymentUploading ? '上传中...' : '点击拍照/选择照片 或拖入图片' }}</span>
          </div>
        </div>
        <!-- 预览区域 -->
        <div v-else class="preview-area">
          <img :src="getImageUrl(advancePaymentPreview)" alt="垫付证明预览" class="preview-img">
          <button class="btn-remove" @click="removeImage('advancePayment')">✕</button>
        </div>
        <!-- 手动输入URL（兜底） -->
        <div class="url-toggle">
          <a href="javascript:void(0)" @click="showAdvancePaymentUrlInput = !showAdvancePaymentUrlInput">
            {{ showAdvancePaymentUrlInput ? '收起' : '手动输入图片URL' }}
          </a>
        </div>
        <input
          v-show="showAdvancePaymentUrlInput"
          v-model="advancePaymentImage"
          type="text"
          placeholder="粘贴图片链接"
          class="url-input"
        >
      </div>
      <button class="btn-primary" style="width:100%;" @click="submitWorkLog">提交工作日志</button>
    </div>

    <!-- Leave -->
    <div v-show="activeTab === 'leave'" class="section">
      <div class="form-group">
        <label>请假日期</label>
        <input v-model="leaveDate" type="date">
      </div>
      <div class="form-group">
        <label>请假类型</label>
        <select v-model="leaveType">
          <option value="事假">事假</option>
          <option value="病假">病假</option>
          <option value="年假">年假</option>
        </select>
      </div>
      <div class="form-group">
        <label>请假原因</label>
        <input v-model="leaveReason" type="text" placeholder="请输入原因">
      </div>
      <button class="btn-warning" style="width:100%;" @click="submitLeave">提交请假申请</button>
    </div>
  </div>
</template>

<style scoped>
.qr-container { max-width: 480px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
h2 { text-align: center; margin-bottom: 20px; color: #333; }
.info { background: #f0f9ff; border-left: 4px solid #1890ff; padding: 12px; margin-bottom: 20px; border-radius: 4px; }
.info p { margin: 4px 0; color: #555; font-size: 14px; }
.form-group { margin-bottom: 16px; }
label { display: block; margin-bottom: 6px; font-size: 14px; color: #333; font-weight: 500; }
input, select { width: 100%; padding: 10px 12px; border: 1px solid #d9d9d9; border-radius: 6px; font-size: 14px; box-sizing: border-box; }
input:focus, select:focus { outline: none; border-color: #1890ff; }
.btn-group { display: flex; gap: 12px; margin-top: 20px; }
button { flex: 1; padding: 12px; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; transition: opacity 0.2s; }
button:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-primary { background: #1890ff; color: #fff; }
.btn-success { background: #52c41a; color: #fff; }
.btn-warning { background: #faad14; color: #fff; }
.btn-error { background: #ff4d4f; color: #fff; }
.tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.tab { flex: 1; padding: 10px; text-align: center; background: #f0f0f0; border-radius: 6px; cursor: pointer; font-size: 14px; }
.tab.active { background: #1890ff; color: #fff; }
.section { display: block; }
.message { padding: 10px; border-radius: 6px; margin-bottom: 16px; font-size: 14px; }
.message.success { background: #f6ffed; border: 1px solid #b7eb8f; color: #52c41a; }
.message.error { background: #fff2f0; border: 1px solid #ffccc7; color: #ff4d4f; }

/* 文件上传区域 */
.upload-area {
  position: relative;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 20px 12px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s, background 0.3s;
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}
.upload-area:hover,
.upload-area:active {
  border-color: #1890ff;
  background: #f0f9ff;
}
.upload-area.uploading {
  border-color: #1890ff;
  background: #f0f9ff;
  cursor: not-allowed;
}
.upload-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  width: 100%;
  height: 100%;
}
.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  pointer-events: none;
}
.upload-icon {
  font-size: 28px;
}
.upload-text {
  font-size: 12px;
  color: #999;
}
.upload-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e0e0e0;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 预览区域 */
.preview-area {
  position: relative;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  overflow: hidden;
}
.preview-img {
  width: 100%;
  max-height: 200px;
  object-fit: contain;
  display: block;
  background: #f5f5f5;
}
.btn-remove {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(0,0,0,0.5);
  color: #fff;
  border: none;
  font-size: 14px;
  line-height: 24px;
  text-align: center;
  cursor: pointer;
  padding: 0;
  flex: none;
}
.btn-remove:hover {
  background: rgba(255,0,0,0.7);
}

/* URL 手动输入 */
.url-toggle {
  margin-top: 4px;
  text-align: right;
}
.url-toggle a {
  font-size: 12px;
  color: #1890ff;
  text-decoration: none;
}
.url-input {
  margin-top: 6px;
}
</style>
