<script setup>
import { onMounted, ref, h } from 'vue'
import { NCard, NInput, NSelect, NButton, NDataTable, NModal, NForm, NFormItem, NDatePicker, NTag } from 'naive-ui'
import api from '@/api/tool'

defineOptions({ name: '工具借用' })

const loading = ref(false)
const showModal = ref(false)
const borrowList = ref([])
const availableTools = ref([])

const searchParams = ref({
  tool_code: '',
  tool_name: '',
  borrower_name: '',
  status: null,
  approve_status: null,
})

const statusOptions = [
  { label: '借用中', value: '借用中' },
  { label: '已归还', value: '已归还' },
  { label: '逾期', value: '逾期' },
]

const approveStatusOptions = [
  { label: '待审批', value: '待审批' },
  { label: '已通过', value: '已通过' },
  { label: '已拒绝', value: '已拒绝' },
]

const columns = [
  { title: '工具编码', key: 'tool_code' },
  { title: '工具名称', key: 'tool_name' },
  { title: '借用人', key: 'borrower_name' },
  { title: '借用时间', key: 'borrow_date' },
  { title: '预计归还', key: 'expected_return_date' },
  { title: '实际归还', key: 'actual_return_date' },
  { title: '借用用途', key: 'purpose' },
  {
    title: '借用状态',
    key: 'status',
    render(row) {
      const statusMap = {
        '借用中': 'warning',
        '已归还': 'success',
        '逾期': 'error',
      }
      return h(NTag, { type: statusMap[row.status] || 'default' }, { default: () => row.status })
    },
  },
  {
    title: '审批状态',
    key: 'approve_status',
    render(row) {
      const statusMap = {
        '待审批': 'warning',
        '已通过': 'success',
        '已拒绝': 'error',
      }
      return h(NTag, { type: statusMap[row.approve_status] || 'default' }, { default: () => row.approve_status })
    },
  },
  { title: '审批人', key: 'approver_name' },
  {
    title: '操作',
    key: 'actions',
    render(row) {
      const buttons = []
      if (row.approve_status === '待审批') {
        buttons.push(
          h(NButton, { size: 'small', type: 'success', onClick: () => handleApprove(row, '已通过') }, { default: () => '通过' }),
          h(NButton, { size: 'small', type: 'error', onClick: () => handleApprove(row, '已拒绝') }, { default: () => '拒绝' })
        )
      }
      if (row.status === '借用中' && row.approve_status === '已通过') {
        buttons.push(
          h(NButton, { size: 'small', type: 'warning', onClick: () => handleReturn(row) }, { default: () => '归还' })
        )
      }
      return buttons.length > 0 ? h('div', { class: 'flex gap-2' }, buttons) : '-'
    },
  },
]

const formValue = ref({
  tool_id: null,
  tool_code: '',
  tool_name: '',
  borrower_name: '',
  expected_return_date: null,
  purpose: '',
  remark: '',
})

async function fetchBorrows() {
  loading.value = true
  try {
    const res = await api.getToolBorrowList(searchParams.value)
    borrowList.value = res.data || []
  } finally {
    loading.value = false
  }
}

async function fetchAvailableTools() {
  const res = await api.getToolList({ status: '可用' })
  availableTools.value = (res.data || []).map(t => ({
    label: `${t.tool_code} - ${t.tool_name}`,
    value: t.id,
    tool: t,
  }))
}

function handleCreate() {
  formValue.value = {
    tool_id: null,
    tool_code: '',
    tool_name: '',
    borrower_name: '',
    expected_return_date: null,
    purpose: '',
    remark: '',
  }
  showModal.value = true
}

function handleToolSelect(val) {
  const tool = availableTools.value.find(t => t.value === val)
  if (tool) {
    formValue.value.tool_code = tool.tool.tool_code
    formValue.value.tool_name = tool.tool.tool_name
  }
}

async function handleApprove(row, approveStatus) {
  const user = JSON.parse(localStorage.getItem('userInfo') || '{}')
  await api.approveToolBorrow({
    id: row.id,
    approve_status: approveStatus,
    approver_id: user.id,
    approver_name: user.username,
  })
  fetchBorrows()
}

async function handleReturn(row) {
  if (confirm('确认归还该工具？')) {
    await api.returnToolBorrow({ id: row.id })
    fetchBorrows()
    fetchAvailableTools()
  }
}

async function handleSubmit() {
  const user = JSON.parse(localStorage.getItem('userInfo') || '{}')
  const data = {
    ...formValue.value,
    borrower_id: user.id || 1,
    borrow_date: new Date().toISOString(),
  }
  await api.createToolBorrow(data)
  showModal.value = false
  fetchBorrows()
  fetchAvailableTools()
}

onMounted(() => {
  fetchBorrows()
  fetchAvailableTools()
})
</script>

<template>
  <div p-15>
    <n-card title="搜索条件" mb-15>
      <div flex flex-wrap gap-15>
        <div flex items-center>
          <span w-80 flex-shrink-0>工具编码:</span>
          <n-input v-model:value="searchParams.tool_code" clearable placeholder="请输入工具编码" style="width: 150px" @keyup.enter="fetchBorrows" />
        </div>
        <div flex items-center>
          <span w-80 flex-shrink-0>工具名称:</span>
          <n-input v-model:value="searchParams.tool_name" clearable placeholder="请输入工具名称" style="width: 150px" @keyup.enter="fetchBorrows" />
        </div>
        <div flex items-center>
          <span w-80 flex-shrink-0>借用人:</span>
          <n-input v-model:value="searchParams.borrower_name" clearable placeholder="请输入借用人" style="width: 150px" @keyup.enter="fetchBorrows" />
        </div>
        <div flex items-center>
          <span w-80 flex-shrink-0>借用状态:</span>
          <n-select v-model:value="searchParams.status" clearable placeholder="请选择状态" :options="statusOptions" style="width: 150px" />
        </div>
        <div flex items-center>
          <span w-80 flex-shrink-0>审批状态:</span>
          <n-select v-model:value="searchParams.approve_status" clearable placeholder="请选择状态" :options="approveStatusOptions" style="width: 150px" />
        </div>
        <n-button type="primary" @click="fetchBorrows">搜索</n-button>
        <n-button type="success" @click="handleCreate">申请借用</n-button>
      </div>
    </n-card>

    <n-card title="借用记录">
      <n-data-table :columns="columns" :data="borrowList" :loading="loading" />
    </n-card>

    <n-modal v-model:show="showModal" title="申请借用" preset="card" style="width: 500px">
      <n-form :model="formValue" label-placement="left" label-width="100">
        <n-form-item label="选择工具" required>
          <n-select v-model:value="formValue.tool_id" placeholder="请选择工具" :options="availableTools" @update:value="handleToolSelect" />
        </n-form-item>
        <n-form-item label="借用人" required>
          <n-input v-model:value="formValue.borrower_name" placeholder="请输入借用人姓名" />
        </n-form-item>
        <n-form-item label="预计归还">
          <n-date-picker v-model:value="formValue.expected_return_date" type="datetime" style="width: 100%" />
        </n-form-item>
        <n-form-item label="借用用途">
          <n-input v-model:value="formValue.purpose" placeholder="请输入借用用途" />
        </n-form-item>
        <n-form-item label="备注">
          <n-input v-model:value="formValue.remark" type="textarea" placeholder="请输入备注" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div flex justify-end gap-10>
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleSubmit">确定</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>
