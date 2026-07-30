<script setup>
import { onMounted, ref, h } from 'vue'
import { NCard, NInput, NButton, NDataTable, NModal, NForm, NFormItem, NInputNumber, NTag, NDatePicker } from 'naive-ui'
import { useUserStore } from '@/store'
import api from '@/api/tool'

defineOptions({ name: '需求收集' })

const userStore = useUserStore()

const loading = ref(false)
const showModal = ref(false)
const showEditModal = ref(false)
const requirementList = ref([])
const currentRow = ref({})

const searchParams = ref({
  tool_name: '',
  requester_name: '',
  status: null,
})

const statusOptions = [
  { label: '待处理', value: '待处理' },
  { label: '已采购', value: '已采购' },
  { label: '已拒绝', value: '已拒绝' },
]

const columns = [
  { title: '设备名称', key: 'tool_name' },
  { title: '规格型号', key: 'specification' },
  { title: '需求数量', key: 'quantity' },
  { title: '需求人', key: 'requester_name' },
  { title: '需求日期', key: 'request_date' },
  { title: '需求原因', key: 'reason', ellipsis: { tooltip: true } },
  {
    title: '状态',
    key: 'status',
    render(row) {
      const statusMap = {
        '待处理': 'warning',
        '已采购': 'success',
        '已拒绝': 'error',
      }
      return h(NTag, { type: statusMap[row.status] || 'default' }, { default: () => row.status })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    render(row) {
      const buttons = []
      if (row.status === '待处理') {
        buttons.push(
          h(NButton, { size: 'small', type: 'success', onClick: () => handleProcess(row, '已采购') }, { default: () => '采购' }),
          h(NButton, { size: 'small', type: 'error', onClick: () => handleProcess(row, '已拒绝') }, { default: () => '拒绝' }),
        )
      }
      buttons.push(
        h(NButton, { size: 'small', type: 'warning', onClick: () => handleEdit(row) }, { default: () => '编辑' }),
        h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, { default: () => '删除' }),
      )
      return h('div', { class: 'flex flex-wrap gap-2' }, buttons)
    },
  },
]

const formValue = ref({
  tool_name: '',
  specification: '',
  quantity: 1,
  requester_name: '',
  reason: '',
})

const editFormValue = ref({
  tool_name: '',
  specification: '',
  quantity: 1,
  requester_name: '',
  request_date: null,
  reason: '',
})

async function fetchRequirements() {
  loading.value = true
  try {
    const res = await api.getToolRequirementList(searchParams.value)
    requirementList.value = res.data || []
  } finally {
    loading.value = false
  }
}

function handleCreate() {
  formValue.value = {
    tool_name: '',
    tool_type: '',
    specification: '',
    quantity: 1,
    requester_name: '',
    reason: '',
  }
  showModal.value = true
}

async function handleProcess(row, status) {
  await api.handleToolRequirement({
    id: row.id,
    status,
    handler_id: userStore.userId,
    handler_name: userStore.name,
  })
  fetchRequirements()
}

function handleEdit(row) {
  currentRow.value = row
  editFormValue.value = {
    tool_name: row.tool_name,
    specification: row.specification || '',
    quantity: row.quantity,
    requester_name: row.requester_name,
    request_date: row.request_date ? new Date(row.request_date).getTime() : new Date().getTime(),
    reason: row.reason || '',
  }
  showEditModal.value = true
}

async function handleEditSubmit() {
  await api.updateToolRequirement({
    id: currentRow.value.id,
    tool_name: editFormValue.value.tool_name,
    spec_model: editFormValue.value.specification,
    quantity: editFormValue.value.quantity,
    requester_name: editFormValue.value.requester_name,
    requirement_date: new Date(editFormValue.value.request_date).toISOString().split('T')[0],
    reason: editFormValue.value.reason,
  })
  showEditModal.value = false
  fetchRequirements()
}

async function handleDelete(row) {
  if (confirm('确认删除该需求？')) {
    await api.deleteToolRequirement({ id: row.id })
    fetchRequirements()
  }
}

async function handleSubmit() {
  const data = {
    ...formValue.value,
    requester_id: userStore.userId || 1,
    request_date: new Date().toISOString(),
  }
  await api.createToolRequirement(data)
  showModal.value = false
  fetchRequirements()
}

onMounted(() => {
  fetchRequirements()
})
</script>

<template>
  <div p-15>
    <n-card mb-15>
      <div flex flex-wrap gap-15>
        <div flex items-center>
          <span w-80 flex-shrink-0>设备名称:</span>
          <n-input v-model:value="searchParams.tool_name" clearable placeholder="请输入设备名称" style="width: 150px" @keyup.enter="fetchRequirements" />
        </div>
        <div flex items-center>
          <span w-80 flex-shrink-0>需求人:</span>
          <n-input v-model:value="searchParams.requester_name" clearable placeholder="请输入需求人" style="width: 150px" @keyup.enter="fetchRequirements" />
        </div>
        <div flex items-center>
          <span w-80 flex-shrink-0>状态:</span>
          <n-select v-model:value="searchParams.status" clearable placeholder="请选择状态" :options="statusOptions" style="width: 150px" />
        </div>
        <n-button type="primary" @click="fetchRequirements">搜索</n-button>
        <n-button type="success" @click="handleCreate">新增需求</n-button>
      </div>
    </n-card>

    <n-card title="需求列表">
      <n-data-table :columns="columns" :data="requirementList" :loading="loading" />
    </n-card>

    <n-modal v-model:show="showModal" title="新增需求申请" preset="card" style="width: 500px">
      <n-form :model="formValue" label-placement="left" label-width="100">
        <n-form-item label="设备名称" required>
          <n-input v-model:value="formValue.tool_name" placeholder="请输入设备名称" />
        </n-form-item>
        <n-form-item label="设备类型" required>
          <n-input v-model:value="formValue.tool_type" placeholder="请输入设备类型" />
        </n-form-item>
        <n-form-item label="规格型号">
          <n-input v-model:value="formValue.specification" placeholder="请输入规格型号" />
        </n-form-item>
        <n-form-item label="需求数量">
          <n-input-number v-model:value="formValue.quantity" :min="1" style="width: 100%" />
        </n-form-item>
        <n-form-item label="需求人" required>
          <n-input v-model:value="formValue.requester_name" placeholder="请输入需求人姓名" />
        </n-form-item>
        <n-form-item label="需求原因">
          <n-input v-model:value="formValue.reason" type="textarea" placeholder="请输入需求原因" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div flex justify-end gap-10>
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleSubmit">确定</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal v-model:show="showEditModal" title="编辑需求" preset="card" style="width: 500px">
      <n-form :model="editFormValue" label-placement="left" label-width="100">
        <n-form-item label="设备名称" required>
          <n-input v-model:value="editFormValue.tool_name" placeholder="请输入设备名称" />
        </n-form-item>
        <n-form-item label="规格型号">
          <n-input v-model:value="editFormValue.specification" placeholder="请输入规格型号" />
        </n-form-item>
        <n-form-item label="需求数量">
          <n-input-number v-model:value="editFormValue.quantity" :min="1" style="width: 100%" />
        </n-form-item>
        <n-form-item label="需求人" required>
          <n-input v-model:value="editFormValue.requester_name" placeholder="请输入需求人姓名" />
        </n-form-item>
        <n-form-item label="需求日期" required>
          <n-date-picker v-model:value="editFormValue.request_date" type="date" style="width: 100%" />
        </n-form-item>
        <n-form-item label="需求原因">
          <n-input v-model:value="editFormValue.reason" type="textarea" placeholder="请输入需求原因" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div flex justify-end gap-10>
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" @click="handleEditSubmit">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>
