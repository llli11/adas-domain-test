<script setup>
import { computed, onMounted, ref } from 'vue'
import { NButton, NCard, NSpace, NTag, NTable, NTh, NTd, NTr } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import api from '@/api'

defineOptions({ name: '状态看板' })

const staffList = ref([])
const projectMap = ref({})

onMounted(() => {
  loadData()
})

async function loadData() {
  const res = await api.getContractorStaffList({ page_size: 999, status: '在职' })
  if (res.data) {
    staffList.value = res.data
  }
  const deptRes = await api.getDepts()
  if (deptRes.data) {
    const map = {}
    deptRes.data.forEach(d => { map[d.id] = d.name })
    projectMap.value = map
  }
}

const projectGroups = computed(() => {
  const groups = {}
  staffList.value.forEach(s => {
    const pid = s.project_id || 0
    if (!groups[pid]) groups[pid] = []
    groups[pid].push(s)
  })
  return groups
})
</script>

<template>
  <CommonPage show-footer title="状态看板">
    <template #action>
      <NButton type="primary" @click="loadData">
        刷新
      </NButton>
    </template>

    <NSpace vertical>
      <NCard v-for="(members, pid) in projectGroups" :key="pid" :title="projectMap[pid] || '未分配项目'">
        <NTable size="small" :bordered="false" :single-line="false">
          <thead>
            <NTr>
              <NTh>姓名</NTh>
              <NTh>属性</NTh>
              <NTh>状态</NTh>
              <NTh>任务</NTh>
              <NTh>车辆</NTh>
            </NTr>
          </thead>
          <tbody>
            <NTr v-for="m in members" :key="m.id">
              <NTd>{{ m.name }}</NTd>
              <NTd>{{ m.type }}</NTd>
              <NTd>
                <NTag :type="m.task_status === '任务中' ? 'error' : 'success'" size="small">{{ m.task_status }}</NTag>
              </NTd>
              <NTd>{{ m.current_task || '-' }}</NTd>
              <NTd>{{ m.current_vehicle || '-' }}</NTd>
            </NTr>
          </tbody>
        </NTable>
      </NCard>
    </NSpace>
  </CommonPage>
</template>
