<script setup>
import { onMounted, ref, h } from 'vue'
import { NCard, NInput, NSelect, NButton, NDataTable, NModal, NForm, NFormItem, NDatePicker, NInputNumber, NTag, NSpace, NUpload, NTabs, NTabPane } from 'naive-ui'
import api from '@/api/tool'
import baseApi from '@/api'

defineOptions({ name: '工具台账' })

const loading = ref(false)
const showModal = ref(false)
const modalType = ref('create')
const toolList = ref([])
const currentTool = ref({})
const activeTab = ref('tools')
const importInputRef = ref(null)

const searchParams = ref({
  tool_code: '',
  tool_name: '',
  tool_type: null,
  status: null,
  current_user: '',
})

const toolTypeOptions = [
  { label: '测量工具', value: '测量工具' },
  { label: '维修工具', value: '维修工具' },
  { label: '检测工具', value: '检测工具' },
  { label: '其他', value: '其他' },
]

const statusOptions = [
  { label: '可用', value: '可用' },
  { label: '借出', value: '借出' },
  { label: '维修', value: '维修' },
  { label: '报废', value: '报废' },
]

const columns = [
  { title: '设备编号', key: 'tool_code' },
  { title: '设备名称', key: 'tool_name' },
  { title: '设备类别', key: 'tool_type' },
  { title: '设备数量', key: 'quantity' },
  {
    title: '设备图片',
    key: 'image_url',
    render(row) {
      if (row.image_url) {
        return h('img', { src: row.image_url, style: 'width: 40px; height: 40px; object-fit: cover;' })
      }
      return h('span', '无图片')
    },
  },
  { title: '当前使用者', key: 'current_user' },
  {
    title: '状态',
    key: 'status',
    render(row) {
      const statusMap = {
        '可用': 'success',
        '借出': 'warning',
        '维修': 'info',
        '报废': 'error',
      }
      return h(NTag, { type: statusMap[row.status] || 'default' }, { default: () => row.status || '可用' })
    },
  },
  { title: '备注', key: 'remark', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    render(row) {
      return h('div', { class: 'flex gap-2' }, [
        h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }),
        h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, { default: () => '删除' }),
        h(NButton, { size: 'small', type: 'primary', onClick: () => handleBorrow(row), disabled: !row.is_in_stock }, { default: () => row.is_in_stock ? '借用' : '不可借' }),
      ])
    },
  },
]

const formValue = ref({
  tool_code: '',
  tool_name: '',
  tool_type: '',
  quantity: 1,
  image_url: '',
  current_user: '',
  is_in_stock: true,
  remark: '',
})

async function fetchTools() {
  loading.value = true
  try {
    const res = await api.getToolList(searchParams.value)
    toolList.value = res.data || []
  } finally {
    loading.value = false
  }
}

function handleCreate() {
  modalType.value = 'create'
  formValue.value = {
    tool_code: '',
    tool_name: '',
    tool_type: '',
    quantity: 1,
    image_url: '',
    current_user: '',
    is_in_stock: true,
    remark: '',
  }
  showModal.value = true
}

function handleEdit(row) {
  modalType.value = 'edit'
  currentTool.value = row
  formValue.value = { ...row }
  showModal.value = true
}

const showBorrowModal = ref(false)
const borrowForm = ref({
  borrower_name: '',
  borrow_date: null,
  expected_return_date: null,
  purpose: '',
  approver_id: null,
  approver_name: '',
})

const currentBorrowTool = ref({})
const approverOptions = ref([])

async function fetchApprovers() {
  try {
    const res = await baseApi.getUserList({ page: 1, page_size: 100 })
    const users = res.data || []
    approverOptions.value = users.map(u => ({
      label: u.username,
      value: u.id,
    }))
  } catch (e) {
    approverOptions.value = [{ label: 'admin', value: 1 }]
  }
}

function handleBorrow(row) {
  currentBorrowTool.value = row
  borrowForm.value = {
    borrower_name: '',
    borrow_date: Date.now(),
    expected_return_date: null,
    purpose: '',
    approver_id: null,
    approver_name: '',
  }
  fetchApprovers()
  showBorrowModal.value = true
}

function handleApproverSelect(val) {
  const approver = approverOptions.value.find(a => a.value === val)
  if (approver) {
    borrowForm.value.approver_name = approver.label
  }
}

async function handleBorrowSubmit() {
  if (!borrowForm.value.borrower_name) {
    window.$message?.warning('请输入借用人姓名')
    return
  }
  if (!borrowForm.value.approver_id) {
    window.$message?.warning('请选择审批老师')
    return
  }
  try {
    const user = JSON.parse(localStorage.getItem('userInfo') || '{}')
    await api.createToolBorrow({
      tool_id: currentBorrowTool.value.id,
      tool_code: currentBorrowTool.value.tool_code,
      tool_name: currentBorrowTool.value.tool_name,
      borrower_id: user.id || 1,
      borrower_name: borrowForm.value.borrower_name,
      borrow_date: new Date().toISOString(),
      expected_return_date: borrowForm.value.expected_return_date
        ? new Date(borrowForm.value.expected_return_date).toISOString()
        : null,
      purpose: borrowForm.value.purpose,
      approver_id: borrowForm.value.approver_id,
      approver_name: borrowForm.value.approver_name,
    })
    window.$message?.success('借用申请已提交，请等待审批老师审核')
    showBorrowModal.value = false
    fetchTools()
    fetchBorrows()
  } catch (error) {
    window.$message?.error('提交失败')
  }
}

async function handleDelete(row) {
  if (confirm(`确定删除设备 "${row.tool_name}" 吗？`)) {
    await api.deleteTool({ id: row.id })
    fetchTools()
  }
}

function handleBeforeUpload(data) {
  const rawFile = data.file?.file
  if (!rawFile) return false
  const isImage = rawFile.type?.startsWith('image/')
  if (!isImage) {
    window.$message?.error('请上传图片文件')
    return false
  }
  const isLt2M = rawFile.size / 1024 / 1024 < 2
  if (!isLt2M) {
    window.$message?.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

async function customUploadRequest({ file, onFinish, onError }) {
  try {
    console.log('[upload] file obj:', file)
    console.log('[upload] file.file type:', file.file instanceof File, file.file?.type, file.file?.size)
    const formData = new FormData()
    formData.append('file', file.file)
    const res = await api.uploadImage(formData)
    console.log('[upload] response:', res)
    if (res.code === 200) {
      formValue.value.image_url = res.data.url
      window.$message?.success('图片上传成功')
      onFinish()
    } else {
      window.$message?.error(res.msg || '上传失败')
      onError()
    }
  } catch (e) {
    console.error('[upload] error:', e)
    window.$message?.error('上传失败: ' + (e?.message || e?.msg || JSON.stringify(e)))
    onError()
  }
}

async function handleSubmit() {
  if (modalType.value === 'create') {
    await api.createTool(formValue.value)
  } else {
    await api.updateTool({ id: currentTool.value.id }, formValue.value)
  }
  showModal.value = false
  fetchTools()
}

async function handleExport() {
  try {
    const response = await api.exportTool()
    const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'tools.xlsx'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Export error:', error)
    window.$message?.error('导出失败: ' + (error.message || ''))
  }
}

function triggerImport() {
  if (importInputRef.value) {
    importInputRef.value.click()
  }
}

async function handleImport(event) {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    const result = await api.importTool(formData)
    if (result.code === 200) {
      window.$message?.success(result.msg)
    } else {
      window.$message?.error(result.msg || '导入失败')
    }
    fetchTools()
  } catch (error) {
    console.error('Import error:', error)
    window.$message?.error('导入失败: ' + (error.message || ''))
  }

  event.target.value = ''
}

async function handleBatchDelete() {
  if (toolList.value.length === 0) {
    window.$message?.warning('当前没有数据可删除')
    return
  }
  
  if (confirm(`确定要删除所有 ${toolList.value.length} 条设备数据吗？此操作不可撤销！`)) {
    try {
      const result = await api.batchDeleteTool()
      if (result.code === 200) {
        window.$message?.success(result.msg)
        fetchTools()
      } else {
        window.$message?.error(result.msg || '删除失败')
      }
    } catch (error) {
      console.error('Batch delete error:', error)
      window.$message?.error('删除失败: ' + (error.message || ''))
    }
  }
}

const borrowLoading = ref(false)
const borrowList = ref([])

const borrowSearchParams = ref({
  tool_code: '',
  tool_name: '',
  borrower_name: '',
  status: null,
  approve_status: null,
})

const borrowStatusOptions = [
  { label: '借用中', value: '借用中' },
  { label: '已归还', value: '已归还' },
  { label: '逾期', value: '逾期' },
]

const borrowApproveStatusOptions = [
  { label: '待审批', value: '待审批' },
  { label: '已通过', value: '已通过' },
  { label: '已拒绝', value: '已拒绝' },
]

const borrowColumns = [
  { title: '设备编码', key: 'tool_code' },
  { title: '设备名称', key: 'tool_name' },
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

async function fetchBorrows() {
  borrowLoading.value = true
  try {
    const res = await api.getToolBorrowList(borrowSearchParams.value)
    borrowList.value = res.data || []
  } finally {
    borrowLoading.value = false
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
  window.$message?.success(approveStatus === '已通过' ? '已批准借用申请' : '已拒绝借用申请')
  fetchBorrows()
  fetchTools()
}

async function handleReturn(row) {
  if (confirm('确认归还该工具？')) {
    await api.returnToolBorrow({ id: row.id })
    window.$message?.success('工具已归还')
    fetchBorrows()
    fetchTools()
  }
}

function handleTabChange(tab) {
  if (tab === 'tools') {
    fetchTools()
  } else if (tab === 'borrows') {
    fetchBorrows()
  }
}

onMounted(() => {
  fetchTools()
})
</script>

<template>
  <div p-15>
        <n-card title="搜索条件" mb-15>
          <div flex flex-wrap gap-15>
            <div flex items-center>
              <span w-80 flex-shrink-0>设备编号:</span>
              <n-input v-model:value="searchParams.tool_code" clearable placeholder="请输入设备编号" style="width: 150px" @keyup.enter="fetchTools" />
            </div>
            <div flex items-center>
              <span w-80 flex-shrink-0>设备名称:</span>
              <n-input v-model:value="searchParams.tool_name" clearable placeholder="请输入设备名称" style="width: 150px" @keyup.enter="fetchTools" />
            </div>
            <div flex items-center>
              <span w-80 flex-shrink-0>当前使用者:</span>
              <n-input v-model:value="searchParams.current_user" clearable placeholder="请输入当前使用者" style="width: 150px" @keyup.enter="fetchTools" />
            </div>
            <div flex items-center>
              <span w-80 flex-shrink-0>状态:</span>
              <n-select v-model:value="searchParams.status" clearable placeholder="请选择状态" :options="statusOptions" style="width: 150px" />
            </div>
            <n-button type="primary" @click="fetchTools">搜索</n-button>
            <n-button type="success" @click="handleCreate">新增设备</n-button>
            <NSpace>
              <n-button type="info" @click="handleExport">导出Excel</n-button>
              <n-button type="info" @click="triggerImport">导入Excel</n-button>
              <input ref="importInputRef" type="file" accept=".xlsx,.xls" class="hidden" @change="handleImport" />
              <n-button type="error" @click="handleBatchDelete">全部删除</n-button>
            </NSpace>
          </div>
        </n-card>

        <n-card title="设备列表">
          <n-data-table :columns="columns" :data="toolList" :loading="loading" />
        </n-card>

    <n-modal v-model:show="showModal" :title="modalType === 'create' ? '新增设备' : '编辑设备'" preset="card" style="width: 600px">
      <n-form :model="formValue" label-placement="left" label-width="120">
        <div class="grid grid-cols-2 gap-10">
          <div>
            <n-form-item label="设备编号" required>
              <n-input v-model:value="formValue.tool_code" :disabled="modalType === 'edit'" placeholder="请输入设备编号" />
            </n-form-item>
            <n-form-item label="设备名称" required>
              <n-input v-model:value="formValue.tool_name" placeholder="请输入设备名称" />
            </n-form-item>
            <n-form-item label="设备类别" required>
              <n-input v-model:value="formValue.tool_type" placeholder="请输入设备类别" />
            </n-form-item>
            <n-form-item label="设备数量">
              <n-input-number v-model:value="formValue.quantity" :min="1" style="width: 100%" />
            </n-form-item>
          </div>
          <div>
            <n-form-item label="设备图片">
              <n-upload
                :show-file-list="false"
                :custom-request="customUploadRequest"
                :default-file-list="formValue.image_url ? [{ name: '已上传', url: formValue.image_url }] : []"
                @before-upload="handleBeforeUpload"
              >
                <n-button size="small" type="primary">
                  {{ formValue.image_url ? '重新上传' : '点击上传图片' }}
                </n-button>
              </n-upload>
              <div v-if="formValue.image_url" class="mt-2" style="text-align: left">
                <img :src="formValue.image_url" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px; border: 1px solid #eee;" />
              </div>
            </n-form-item>
            <n-form-item label="当前使用者">
              <n-input v-model:value="formValue.current_user" placeholder="请输入当前使用者" />
            </n-form-item>
            <n-form-item label="是否在库">
              <n-select v-model:value="formValue.is_in_stock" :options="[{ label: '是', value: true }, { label: '否', value: false }]" />
            </n-form-item>
          </div>
        </div>
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

    <n-modal v-model:show="showBorrowModal" title="借用申请" preset="card" style="width: 500px">
      <n-form :model="borrowForm" label-placement="left" label-width="100">
        <n-form-item label="借用设备">
          <n-tag type="info">{{ currentBorrowTool.tool_code }} - {{ currentBorrowTool.tool_name }}</n-tag>
        </n-form-item>
        <n-form-item label="借用人" required>
          <n-input v-model:value="borrowForm.borrower_name" placeholder="请输入借用人姓名" />
        </n-form-item>
        <n-form-item label="借用日期" required>
          <n-date-picker v-model:value="borrowForm.borrow_date" type="date" style="width: 100%" />
        </n-form-item>
        <n-form-item label="预计归还日期">
          <n-date-picker v-model:value="borrowForm.expected_return_date" type="date" style="width: 100%" />
        </n-form-item>
        <n-form-item label="借用用途">
          <n-input v-model:value="borrowForm.purpose" type="textarea" placeholder="请输入借用用途" />
        </n-form-item>
        <n-form-item label="审批人" required>
          <n-select
            v-model:value="borrowForm.approver_id"
            placeholder="请选择审批人"
            :options="approverOptions"
            @update:value="handleApproverSelect"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <div flex justify-end gap-10>
          <n-button @click="showBorrowModal = false">取消</n-button>
          <n-button type="primary" @click="handleBorrowSubmit">提交申请</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>