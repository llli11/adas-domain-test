<script setup>
import { onMounted, onActivated, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NButton,
  NCard,
  NInput,
  NSpace,
  NModal,
  NForm,
  NFormItem,
  NUpload,
  NSpin,
  useMessage,
  NAlert,
} from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { useUserStore } from '@/store'

defineOptions({ name: '基线列表' })

const userStore = useUserStore()

const router = useRouter()
const route = useRoute()
const message = useMessage()

const searchName = ref('')
const targetList = ref([])
const loading = ref(false)

const updateModalVisible = ref(false)
const updateLoading = ref(false)
const updateForm = ref({
  target_name: '',
  file: null,
})

// 监听路由变化，刷新数据
watch(() => route.fullPath, () => {
  handleSearch()
})

// 每次页面激活时都刷新数据
onActivated(() => {
  handleSearch()
})

function handleSearch() {
  loading.value = true
  api
    .getTargetList({ search: searchName.value || undefined })
    .then((res) => {
      console.log('API response:', res)
      targetList.value = res.data || []
    })
    .catch((err) => {
      console.error('API error:', err)
      message.error(err.message || '获取数据失败')
    })
    .finally(() => {
      loading.value = false
    })
}

function handleClickCard(target_name) {
  router.push(`/ecu/target/detail/${target_name}`)
}

function showUpdateModal() {
  updateModalVisible.value = true
}

function handleUpdate() {
  if (!updateForm.value.target_name) {
    message.warning('请输入基线版本名称')
    return
  }
  if (!updateForm.value.file) {
    message.warning('请上传Excel文件')
    return
  }

  updateLoading.value = true
  const formData = new FormData()
  formData.append('target_name', updateForm.value.target_name)
  formData.append('file', updateForm.value.file)

  api
    .updateTarget(formData)
    .then((res) => {
      message.success('创建成功')
      const name = updateForm.value.target_name
      updateModalVisible.value = false
      updateForm.value = { target_name: '', file: null }
      handleSearch()
      api.addOperationLog({
        operation_type: '新建基线',
        target_name: name,
        operator: userStore.name || 'system',
      })
    })
    .catch((err) => {
      message.error(err.message || '创建失败')
    })
    .finally(() => {
      updateLoading.value = false
    })
}

function handleFileChange(options) {
  updateForm.value.file = options.file.file
}

async function downloadTemplate() {
  try {
    const response = await fetch('/api/v1/ecu/target/template', {
      headers: { 'token': localStorage.getItem('token') || '' }
    })
    
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = '基线版本模板.xlsx'
      a.click()
      window.URL.revokeObjectURL(url)
      message.success('模板下载成功')
    } else {
      const data = await response.json()
      message.error(data.msg || '模板生成失败')
    }
  } catch (err) {
    message.error('模板下载失败')
  }
}

onMounted(() => {
  handleSearch()
})
</script>

<template>
  <div class="target-page">
    <NCard :bordered="false" class="target-card">
      <div class="toolbar">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <NSpace>
            <NInput
              v-model:value="searchName"
              placeholder="搜索基线版本名称"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
<NButton type="primary" @click="handleSearch">
              <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />
              搜索
            </NButton>
          </NSpace>
          <NSpace>
            <NButton type="info" @click="downloadTemplate">
              <TheIcon icon="material-symbols:download" :size="16" class="mr-5" />
              下载模板
            </NButton>
            <NButton type="success" @click="showUpdateModal">
              <TheIcon icon="material-symbols:add" :size="16" class="mr-5" />
              新建基线
            </NButton>
          </NSpace>
        </div>
      </div>

      <div class="target-grid">
        <NCard
          v-for="item in targetList"
          :key="item.id"
          class="target-box"
          hoverable
          @click="handleClickCard(item.target_name)"
        >
          <div class="name-label">{{ item.target_name }}</div>
        </NCard>
      </div>
      <div v-if="targetList.length === 0 && !loading" class="empty-tip">
        <div>暂无基线数据</div>
      </div>
    </NCard>

    <NModal
      v-model:show="updateModalVisible"
      title="新建基线版本"
      preset="card"
      style="width: 500px"
      :mask-closable="false"
    >
      <NAlert type="info" style="margin-bottom: 16px">
        Excel模板格式：第一列为ECU名，第二列为VOYAH SoftwareVersion，其他列可选
      </NAlert>
      <NForm label-placement="left" label-width="120px">
        <NFormItem label="基线版本名称" required>
          <NInput v-model:value="updateForm.target_name" placeholder="请输入基线版本名称" />
        </NFormItem>
        <NFormItem label="上传Excel" required>
          <NUpload
            accept=".xlsx,.xls"
            :max="1"
            :custom-request="handleFileChange"
          >
            <NButton>点击上传Excel文件</NButton>
          </NUpload>
        </NFormItem>
      </NForm>
      <template #footer>
        <div style="display: flex; justify-content: flex-end">
          <NButton @click="updateModalVisible = false">取消</NButton>
          <NButton type="primary" style="margin-left: 16px" :loading="updateLoading" @click="handleUpdate">
            确认
          </NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.target-page {
  padding: 16px;
}

.target-card {
  min-height: calc(100vh - 100px);
}

.toolbar {
  margin-bottom: 16px;
}

.target-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.target-box {
  cursor: pointer;
  transition: all 0.3s;
}

.target-box:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.name-label {
  text-align: center;
  font-size: 16px;
  font-weight: 500;
  padding: 20px 0;
}

.empty-tip {
  grid-column: 1 / -1;
  text-align: center;
  color: #999;
  padding: 40px 0;
}
</style>