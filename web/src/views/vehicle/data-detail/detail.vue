<script setup>
import { onMounted, ref, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NButton,
  NTag,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NDatePicker,
  NSpace,
  NPopconfirm,
  NGrid,
  NGridItem,
  NSpin,
  NDivider,
  useMessage,
} from 'naive-ui'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '车辆详情' })

const router = useRouter()
const route = useRoute()
const $message = useMessage()

const vehicleId = ref(null)
const vehicle = ref(null)
const loading = ref(false)
const saving = ref(false)
const isEditing = ref(false)

// 编辑表单
const formRef = ref(null)
const editForm = ref({})

// 枚举选项
const taskStatusOptions = [
  { label: '待命', value: '待命' },
  { label: '任务中', value: '任务中' },
  { label: '故障', value: '故障' },
  { label: '维修', value: '维修' },
  { label: '保养', value: '保养' },
  { label: '报废', value: '报废' },
]

const powerTypeOptions = [
  { label: '纯电', value: '纯电' },
  { label: '混动', value: '混动' },
  { label: '燃油', value: '燃油' },
]

const travelStatusOptions = [
  { label: '在厂', value: '在厂' },
  { label: '出差', value: '出差' },
  { label: '返程', value: '返程' },
]

const statusColorMap = {
  '待命': 'success',
  '任务中': 'info',
  '故障': 'error',
  '维修': 'warning',
  '保养': 'warning',
  '报废': 'default',
}

const travelStatusColorMap = {
  '在厂': 'info',
  '出差': 'warning',
  '返程': 'success',
}

const dataSourceMap = {
  'feishu': '外部飞书导入',
  'csv': '外部CSV导入',
  'manual': '系统导入',
}

// 格式化日期
function fmtDate(date) {
  if (!date) return '-'
  const d = new Date(date)
  return d.toISOString().slice(0, 10)
}

function fmtValue(val) {
  if (val === null || val === undefined || val === '') return '-'
  return val
}

// 加载车辆详情
async function loadVehicle() {
  const id = parseInt(route.params.id)
  if (!id) {
    $message.error('无效的车辆ID')
    return
  }
  vehicleId.value = id
  loading.value = true
  try {
    const res = await api.getVehicleById({ vehicle_id: id })
    vehicle.value = res.data
  } catch (e) {
    console.error('获取车辆详情失败', e)
    $message.error('获取车辆详情失败')
  } finally {
    loading.value = false
  }
}

// 返回列表
function handleBack() {
  router.back()
}

// 进入编辑模式
function handleStartEdit() {
  editForm.value = { ...vehicle.value }
  isEditing.value = true
}

// 取消编辑
function handleCancelEdit() {
  isEditing.value = false
  editForm.value = {}
}

// 保存编辑
async function handleSave() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    const payload = { ...editForm.value }
    // 转换日期
    if (payload.borrow_expire_date && typeof payload.borrow_expire_date === 'number') {
      payload.borrow_expire_date = new Date(payload.borrow_expire_date).toISOString().slice(0, 10)
    }
    if (payload.temp_plate_expire_date && typeof payload.temp_plate_expire_date === 'number') {
      payload.temp_plate_expire_date = new Date(payload.temp_plate_expire_date).toISOString().slice(0, 10)
    }
    if (payload.test_date && typeof payload.test_date === 'number') {
      payload.test_date = new Date(payload.test_date).toISOString().slice(0, 10)
    }

    await api.updateVehicle(payload)
    $message.success('保存成功')
    isEditing.value = false
    vehicle.value = { ...vehicle.value, ...payload }
  } catch (e) {
    $message.error('保存失败: ' + (e.message || '未知错误'))
    console.error(e)
  } finally {
    saving.value = false
  }
}

// 删除车辆
async function handleDelete() {
  try {
    await api.deleteVehicle({ vehicle_id: vehicle.value.id })
    $message.success('删除成功')
    router.back()
  } catch (e) {
    $message.error('删除失败')
    console.error(e)
  }
}

// 字段定义，用于两列布局
const leftFields = [
  { key: 'vn', label: '车辆 VN' },
  { key: 'vehicle_code', label: '车辆编号' },
  { key: 'vehicle_model', label: '车型项目' },
  { key: 'power_type', label: '动力类型' },
  { key: 'color', label: '颜色' },
  { key: 'has_controlled_items', label: '管制物品' },
  { key: 'borrower', label: '借用人' },
  { key: 'borrow_expire_date', label: '借用到期', render: fmtDate },
  { key: 'temp_plate_expire_date', label: '临牌到期', render: fmtDate },
  { key: 'insurance_area', label: '保险区域' },
  { key: 'test_date', label: '试验日期', render: fmtDate },
]

const rightFields = [
  { key: 'task_status', label: '任务状态', render: (v) => v ? h(NTag, { type: statusColorMap[v] || 'default', size: 'small', bordered: false, round: true }, { default: () => v }) : '-' },
  { key: 'test_task', label: '试验任务' },
  { key: 'tester', label: '测试人员' },
  { key: 'driver', label: '驾驶人员' },
  { key: 'travel_status', label: '出差状态', render: (v) => v ? h(NTag, { type: travelStatusColorMap[v] || 'default', size: 'small', bordered: false, round: true }, { default: () => v }) : '-' },
  { key: 'test_city', label: '试验城市' },
  { key: 'exit_permit', label: '出门单' },
  { key: 'parking_spot', label: '停车位' },
  { key: 'location_info', label: '位置信息' },
  { key: 'data_source', label: '数据来源', render: (v) => dataSourceMap[v] || v || '-' },
  { key: 'created_at', label: '创建时间', render: fmtDate },
]

onMounted(() => {
  loadVehicle()
})
</script>

<template>
  <NSpin :show="loading" class="wh-full">
    <div v-if="vehicle" class="detail-root">
      <!-- 顶部按钮栏 -->
      <div class="detail-header">
        <div class="header-left">
          <NButton size="small" text @click="handleBack">
            <template #icon>
              <TheIcon icon="material-symbols:arrow-back" :size="18" />
            </template>
            返回
          </NButton>
          <span class="header-title">车辆详情 — {{ vehicle.vn }}</span>
        </div>
        <div class="header-actions" v-if="!isEditing">
          <NButton type="primary" @click="handleStartEdit">
            <template #icon>
              <TheIcon icon="material-symbols:edit" :size="16" />
            </template>
            编辑
          </NButton>
          <NPopconfirm @positive-click="handleDelete">
            <template #trigger>
              <NButton type="error">
                <template #icon>
                  <TheIcon icon="material-symbols:delete-outline" :size="16" />
                </template>
                删除
              </NButton>
            </template>
            确定删除该车辆吗？此操作不可撤销。
          </NPopconfirm>
        </div>
      </div>

      <!-- 查看模式：两列布局 -->
      <div v-if="!isEditing" class="detail-content">
        <div class="info-grid">
          <div
            v-for="field in leftFields"
            :key="field.key"
            class="info-item"
          >
            <span class="info-label">{{ field.label }}</span>
            <span class="info-value">
              {{ field.render ? (typeof field.render === 'function' ? field.render(vehicle[field.key]) : '-') : fmtValue(vehicle[field.key]) }}
            </span>
          </div>
        </div>
        <NDivider vertical style="height: auto" />
        <div class="info-grid">
          <div
            v-for="field in rightFields"
            :key="field.key"
            class="info-item"
          >
            <span class="info-label">{{ field.label }}</span>
            <span class="info-value">
              <component
                v-if="typeof field.render === 'function'"
                :is="() => field.render(vehicle[field.key])"
              />
              <span v-else>{{ fmtValue(vehicle[field.key]) }}</span>
            </span>
          </div>
        </div>
      </div>

      <!-- 编辑模式 -->
      <div v-else class="detail-content">
        <NForm
          ref="formRef"
          label-placement="left"
          label-align="left"
          :label-width="100"
          :model="editForm"
        >
          <NGrid :cols="2" :x-gap="24" :y-gap="0">
            <!-- 左列 -->
            <NGridItem>
              <NFormItem label="车辆 VN" path="vn" :rule="{ required: true, message: '请输入车辆VN', trigger: 'blur' }">
                <NInput v-model:value="editForm.vn" placeholder="唯一标识" />
              </NFormItem>
              <NFormItem label="车辆编号">
                <NInput v-model:value="editForm.vehicle_code" placeholder="车辆编号（车牌号）" />
              </NFormItem>
              <NFormItem label="车型项目">
                <NInput v-model:value="editForm.vehicle_model" placeholder="车型项目" />
              </NFormItem>
              <NFormItem label="动力类型">
                <NSelect v-model:value="editForm.power_type" :options="powerTypeOptions" placeholder="选择动力类型" />
              </NFormItem>
              <NFormItem label="颜色">
                <NInput v-model:value="editForm.color" placeholder="颜色" />
              </NFormItem>
              <NFormItem label="管制物品">
                <NInput v-model:value="editForm.has_controlled_items" placeholder="是否有管制物品" />
              </NFormItem>
              <NFormItem label="借用人">
                <NInput v-model:value="editForm.borrower" placeholder="借用人姓名" />
              </NFormItem>
              <NFormItem label="借用到期">
                <NDatePicker v-model:value="editForm.borrow_expire_date" type="date" placeholder="选择日期" style="width: 100%" value-format="yyyy-MM-dd" />
              </NFormItem>
              <NFormItem label="临牌到期">
                <NDatePicker v-model:value="editForm.temp_plate_expire_date" type="date" placeholder="选择日期" style="width: 100%" value-format="yyyy-MM-dd" />
              </NFormItem>
              <NFormItem label="保险区域">
                <NInput v-model:value="editForm.insurance_area" placeholder="保险区域" />
              </NFormItem>
              <NFormItem label="试验日期">
                <NDatePicker v-model:value="editForm.test_date" type="date" placeholder="选择日期" style="width: 100%" value-format="yyyy-MM-dd" />
              </NFormItem>
            </NGridItem>
            <!-- 右列 -->
            <NGridItem>
              <NFormItem
                label="任务状态"
                path="task_status"
              >
                <NSelect v-model:value="editForm.task_status" :options="taskStatusOptions" placeholder="选择任务状态" />
              </NFormItem>
              <NFormItem label="试验任务">
                <NInput v-model:value="editForm.test_task" placeholder="试验任务名称" />
              </NFormItem>
              <NFormItem label="测试人员">
                <NInput v-model:value="editForm.tester" placeholder="测试人员" />
              </NFormItem>
              <NFormItem label="驾驶人员">
                <NInput v-model:value="editForm.driver" placeholder="驾驶人员" />
              </NFormItem>
              <NFormItem label="出差状态">
                <NSelect v-model:value="editForm.travel_status" :options="travelStatusOptions" placeholder="选择出差状态" />
              </NFormItem>
              <NFormItem label="试验城市">
                <NInput v-model:value="editForm.test_city" placeholder="试验城市" />
              </NFormItem>
              <NFormItem label="出门单">
                <NInput v-model:value="editForm.exit_permit" placeholder="出门单编号" />
              </NFormItem>
              <NFormItem label="停车位">
                <NInput v-model:value="editForm.parking_spot" placeholder="停车位编号" />
              </NFormItem>
              <NFormItem label="位置信息">
                <NInput v-model:value="editForm.location_info" placeholder="详细位置描述" />
              </NFormItem>
              <NFormItem label="数据来源">
                <NInput :value="dataSourceMap[editForm.data_source] || editForm.data_source" readonly />
              </NFormItem>
              <NFormItem label="纬度">
                <NInput v-model:value="editForm.latitude" placeholder="纬度" />
              </NFormItem>
              <NFormItem label="经度">
                <NInput v-model:value="editForm.longitude" placeholder="经度" />
              </NFormItem>
            </NGridItem>
          </NGrid>
        </NForm>

        <div class="edit-actions">
          <NSpace>
            <NButton @click="handleCancelEdit" :disabled="saving">取消</NButton>
            <NButton type="primary" :loading="saving" @click="handleSave">
              <template #icon>
                <TheIcon icon="material-symbols:save" :size="17" />
              </template>
              保存修改
            </NButton>
          </NSpace>
        </div>
      </div>
    </div>
  </NSpin>
</template>

<style scoped>
.detail-root {
  height: 100%;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
}

/* 顶部栏 */
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 17px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 内容区 */
.detail-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  gap: 0;
}

.info-grid {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #f5f5f5;
  transition: background 0.15s;
}

.info-item:hover {
  background: #fafbfc;
}

.info-label {
  width: 100px;
  flex-shrink: 0;
  font-size: 13px;
  color: #999;
  font-weight: 500;
}

.info-value {
  flex: 1;
  font-size: 14px;
  color: #333;
  word-break: break-all;
}

/* 编辑模式 */
.edit-actions {
  padding-top: 20px;
  display: flex;
  justify-content: center;
  border-top: 1px solid #f0f0f0;
  margin-top: 20px;
}

.wh-full {
  width: 100%;
  height: 100%;
}
</style>
