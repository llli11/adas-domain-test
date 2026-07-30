<script setup>
import { onMounted, ref, h } from 'vue'
import { NCard, NInput, NSelect, NButton, NDataTable, NModal, NForm, NFormItem, NDatePicker, NTag, NInputNumber } from 'naive-ui'
import { useUserStore } from '@/store'
import api from '@/api/tool'

defineOptions({ name: '工具盘点' })

const userStore = useUserStore()

const loading = ref(false)
const showModal = ref(false)
const showCompleteModal = ref(false)
const showEditModal = ref(false)
const inventoryList = ref([])
const currentRow = ref({})

const searchParams = ref({
  task_code: '',
  task_name: '',
  status: null,
})

const statusOptions = [
  { label: '待盘点', value: '待盘点' },
  { label: '进行中', value: '进行中' },
  { label: '已完成', value: '已完成' },
]

const columns = [
  { title: '任务编码', key: 'task_code' },
  { title: '任务名称', key: 'task_name' },
  { title: '盘点日期', key: 'inventory_date' },
  { title: '责任人', key: 'responsible_person' },
  { title: '应盘数量', key: 'total_count' },
  { title: '实盘数量', key: 'actual_count' },
  { title: '差异数量', key: 'diff_count' },
  { title: '差异说明', key: 'diff_explanation', ellipsis: { tooltip: true } },
  {
    title: '状态',
    key: 'status',
    render(row) {
      const statusMap = {
        '待盘点': 'warning',
        '进行中': 'info',
        '已完成': 'success',
      }
      return h(NTag, { type: statusMap[row.status] || 'default' }, { default: () => row.status })
    },
  },
  { title: '完成时间', key: 'complete_time' },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render(row) {
      const buttons = []
      if (row.status !== '已完成') {
        buttons.push(
          h(NButton, { size: 'small', type: 'success', onClick: () => handleComplete(row) }, { default: () => '完成盘点' }),
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
  task_code: '',
  task_name: '',
  inventory_date: null,
  responsible_person: '',
  remark: '',
})

const completeFormValue = ref({
  actual_count: 0,
  diff_explanation: '',
})

const editFormValue = ref({
  actual_count: 0,
  diff_explanation: '',
})

async function fetchInventories() {
  loading.value = true
  try {
    const res = await api.getToolInventoryList(searchParams.value)
    inventoryList.value = res.data || []
  } finally {
    loading.value = false
  }
}

function handleCreate() {
  formValue.value = {
    task_code: `INV${Date.now()}`,
    task_name: '',
    inventory_date: new Date().getTime(),
    responsible_person: '',
    remark: '',
  }
  showModal.value = true
}

async function handleComplete(row) {
  currentRow.value = row
  completeFormValue.value = { actual_count: row.actual_count || 0, diff_explanation: row.diff_explanation || '' }
  showCompleteModal.value = true
}

async function handleCompleteSubmit() {
  await api.completeToolInventory({
    id: currentRow.value.id,
    actual_count: completeFormValue.value.actual_count,
    diff_explanation: completeFormValue.value.diff_explanation,
  })
  showCompleteModal.value = false
  fetchInventories()
}

function handleEdit(row) {
  currentRow.value = row
  editFormValue.value = { actual_count: row.actual_count || 0, diff_explanation: row.diff_explanation || '' }
  showEditModal.value = true
}

async function handleEditSubmit() {
  await api.updateToolInventory({
    id: currentRow.value.id,
    actual_count: editFormValue.value.actual_count,
    diff_explanation: editFormValue.value.diff_explanation,
  })
  showEditModal.value = false
  fetchInventories()
}

async function handleDelete(row) {
  if (confirm('确认删除该盘点任务？')) {
    await api.deleteToolInventory({ id: row.id })
    fetchInventories()
  }
}

async function handleSubmit() {
  const data = {
    ...formValue.value,
    responsible_person: formValue.value.responsible_person || userStore.name,
    inventory_date: new Date(formValue.value.inventory_date).toISOString().split('T')[0],
  }
  await api.createToolInventory(data)
  showModal.value = false
  fetchInventories()
}

onMounted(() => {
  fetchInventories()
})
</script>

<template>
  <div p-15>
    <n-card mb-15>
      <div flex flex-wrap gap-15>
        <div flex items-center>
          <span w-80 flex-shrink-0>任务编码:</span>
          <n-input v-model:value="searchParams.task_code" clearable placeholder="请输入任务编码" style="width: 150px" @keyup.enter="fetchInventories" />
        </div>
        <div flex items-center>
          <span w-80 flex-shrink-0>任务名称:</span>
          <n-input v-model:value="searchParams.task_name" clearable placeholder="请输入任务名称" style="width: 150px" @keyup.enter="fetchInventories" />
        </div>
        <div flex items-center>
          <span w-80 flex-shrink-0>状态:</span>
          <n-select v-model:value="searchParams.status" clearable placeholder="请选择状态" :options="statusOptions" style="width: 150px" />
        </div>
        <n-button type="primary" @click="fetchInventories">搜索</n-button>
        <n-button type="success" @click="handleCreate">创建盘点任务</n-button>
      </div>
    </n-card>

    <n-card title="盘点任务列表">
      <n-data-table :columns="columns" :data="inventoryList" :loading="loading" />
    </n-card>

    <n-modal v-model:show="showModal" title="创建盘点任务" preset="card" style="width: 500px">
      <n-form :model="formValue" label-placement="left" label-width="100">
        <n-form-item label="任务编码" required>
          <n-input v-model:value="formValue.task_code" placeholder="请输入任务编码" />
        </n-form-item>
        <n-form-item label="任务名称" required>
          <n-input v-model:value="formValue.task_name" placeholder="请输入任务名称" />
        </n-form-item>
        <n-form-item label="盘点日期" required>
          <n-date-picker v-model:value="formValue.inventory_date" type="date" style="width: 100%" />
        </n-form-item>
        <n-form-item label="责任人" required>
          <n-input v-model:value="formValue.responsible_person" placeholder="请输入责任人姓名" />
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

    <n-modal v-model:show="showCompleteModal" title="完成盘点" preset="card" style="width: 500px">
      <n-form :model="completeFormValue" label-placement="left" label-width="100">
        <n-form-item label="任务名称">
          <n-tag type="info">{{ currentRow.task_name }}</n-tag>
        </n-form-item>
        <n-form-item label="应盘数量">
          <n-tag type="warning">{{ currentRow.total_count }}</n-tag>
        </n-form-item>
        <n-form-item label="实盘数量" required>
          <n-input-number v-model:value="completeFormValue.actual_count" placeholder="请输入实盘数量" style="width: 100%" :min="0" />
        </n-form-item>
        <n-form-item label="差异说明">
          <n-input v-model:value="completeFormValue.diff_explanation" type="textarea" placeholder="如存在差异请说明原因" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div flex justify-end gap-10>
          <n-button @click="showCompleteModal = false">取消</n-button>
          <n-button type="primary" @click="handleCompleteSubmit">确认完成</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal v-model:show="showEditModal" title="编辑盘点任务" preset="card" style="width: 500px">
      <n-form :model="editFormValue" label-placement="left" label-width="100">
        <n-form-item label="任务名称">
          <n-tag type="info">{{ currentRow.task_name }}</n-tag>
        </n-form-item>
        <n-form-item label="应盘数量">
          <n-tag type="warning">{{ currentRow.total_count }}</n-tag>
        </n-form-item>
        <n-form-item label="实盘数量" required>
          <n-input-number v-model:value="editFormValue.actual_count" placeholder="请输入实盘数量" style="width: 100%" :min="0" />
        </n-form-item>
        <n-form-item label="差异说明">
          <n-input v-model:value="editFormValue.diff_explanation" type="textarea" placeholder="如存在差异请说明原因" />
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
