<template>
  <div style="position: relative;">
    <n-tabs v-model:value="activeTab" type="line" size="medium">
      <!-- ==================== 每日费用 ==================== -->
      <n-tab-pane name="daily" tab="每日费用">
        <n-space :size="8" style="margin-bottom: 12px;">
          <n-date-picker v-model:value="dailyFilterDateRange" type="daterange" placeholder="筛选日期范围" size="small" clearable style="width: 240px" @clear="fetchDailyList(true)" />
          <n-input v-model:value="dailyFilterPerson" placeholder="筛选人员" size="small" clearable style="width: 140px" @keyup.enter="fetchDailyList(true)" @clear="fetchDailyList(true)" />
          <n-input v-model:value="dailyFilterProject" placeholder="筛选项目" size="small" clearable style="width: 140px" @keyup.enter="fetchDailyList(true)" @clear="fetchDailyList(true)" />
          <n-input v-model:value="dailyFilterOrder" placeholder="筛选试验单号" size="small" clearable style="width: 140px" @keyup.enter="fetchDailyList(true)" @clear="fetchDailyList(true)" />
          <n-button size="small" type="primary" @click="fetchDailyList(true)">查询</n-button>
          <n-button size="small" type="info" :loading="autoSyncLoading" @click="doAutoSync">飞书同步</n-button>
        </n-space>
        <div style="margin-bottom: 8px; font-size: 13px; color: #666;">
          共 <b>{{ dailyTotalCount }}</b> 条记录 | 筛选总费用：<b>¥{{ (filteredTotal || 0).toFixed(2) }}</b>
        </div>
        <n-data-table :key="'daily-' + dailyPagination.page + '-' + dailyPagination.pageSize + '-' + dailyFetchVersion" :columns="dailyCols" :data="dailyData" :loading="dailyLoading" size="small" :scroll-x="1600" :max-height="600" remote
          :pagination="dailyPagination" />
      </n-tab-pane>


      <!-- ==================== 供应商单价 ==================== -->
      <n-tab-pane name="supplier" tab="供应商单价">
        <n-card size="small">
          <template #header>供应商单价参考</template>
          <template #header-extra>
            <n-button size="tiny" :type="supplierEditing ? 'primary' : 'default'" @click="supplierEditing = !supplierEditing">{{ supplierEditing ? '完成' : '编辑' }}</n-button>
          </template>
          <template #default>
            <n-space v-if="supplierEditing" :size="6" style="margin-bottom:8px" align="center" wrap>
              <n-text depth="3" style="font-size:12px">新增：</n-text>
              <n-input v-model:value="newSupplierForm.name" placeholder="供应商名" size="tiny" style="width:100px" />
              <n-date-picker v-model:value="newSupplierForm.effective_from" type="date" placeholder="生效开始" size="tiny" clearable style="width:120px" />
              <n-date-picker v-model:value="newSupplierForm.effective_to" type="date" placeholder="生效截止" size="tiny" clearable style="width:120px" />
              <n-input-number v-model:value="newSupplierForm.local" placeholder="武汉/本地单价" size="tiny" :min="0" style="width:110px" />
              <n-input-number v-model:value="newSupplierForm.trip" placeholder="出差单价" size="tiny" :min="0" style="width:110px" />
              <n-select v-model:value="newSupplierForm.unit" size="tiny" style="width:85px" :options="[{label:'元/时',value:'hour'},{label:'元/天',value:'day'}]" />
              <n-button size="tiny" type="success" @click="addSupplierRow">新增</n-button>
            </n-space>
            <n-data-table :columns="supplierCols" :data="supplierData" :loading="supplierLoading" size="small" :bordered="false" :single-line="false" :max-height="400" />
          </template>
        </n-card>
      </n-tab-pane>

    </n-tabs>

    <!-- 飞书同步进度弹窗 -->
    <n-modal v-model:show="showSyncModal" preset="card" title="飞书同步" style="width: 420px;" :mask-closable="false" :closable="syncDone">
      <n-space vertical size="large">
        <n-spin v-if="!syncDone" size="medium" />
        <n-text v-else style="font-size: 16px;">{{ syncMessage }}</n-text>
        <n-text v-if="!syncDone">{{ syncMessage }}</n-text>
        <n-button v-if="syncDone" size="small" type="primary" @click="showSyncModal = false">关闭</n-button>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, h, computed, onMounted, watch } from 'vue'
import {
  NTabs, NTabPane, NSpace, NDataTable, NButton, NInput,
  NInputNumber, NDatePicker, NCard, NModal, NText, NTag,
  NSelect,
} from 'naive-ui'
import expenseApi from '@/api/expense'

// ==================== 自动从飞书同步 ====================
const autoSyncLoading = ref(false)
const showSyncModal = ref(false)
const syncMessage = ref('正在连接飞书...')
const syncDone = ref(false)
let lastAutoSyncTime = 0
const AUTO_SYNC_COOLDOWN = 30000 // 30秒冷却时间

async function doAutoSync() {
  const now = Date.now()
  if (now - lastAutoSyncTime < AUTO_SYNC_COOLDOWN) return
  lastAutoSyncTime = now
  syncDone.value = false
  autoSyncLoading.value = true
  showSyncModal.value = true
  syncMessage.value = '正在启动飞书同步...'
  try {
    const res = await expenseApi.syncAutoFromFeishu()
    const data = res.data || {}

    // 已有同步在运行 或 新启动了同步 → 进入轮询等待
    if (data.status === 'running' || data.status === 'started') {
      syncMessage.value = data.status === 'started' ? '正在从飞书拉取数据，请稍候...' : '前一次同步仍在进行中，正在等待结果...'
      let pollCount = 0
      let errorCount = 0
      const POLL_INTERVAL = 3000
      const MAX_POLLS = 100
      const MAX_ERRORS = 3 // 连续错误 3 次才放弃，避免偶发网络波动导致失败
      const pollInterval = setInterval(async () => {
        pollCount++
        const elapsed = Math.floor(pollCount * POLL_INTERVAL / 1000)
        syncMessage.value = `正在同步... 已运行 ${elapsed} 秒`
        try {
          const statusRes = await expenseApi.getAutoSyncStatus()
          errorCount = 0 // 成功后重置错误计数
          const sd = statusRes.data || {}
          if (!sd.running) {
            clearInterval(pollInterval)
            syncDone.value = true
            const results = sd.results || {}
            if (results.error) {
              syncMessage.value = `⏰ ${results.error}`
              window.$message?.warning(results.error)
            } else {
              syncMessage.value = '✅ 同步成功'
              window.$message?.success('同步成功')
            }
            await fetchDailyList(true)
            autoSyncLoading.value = false
            return
          }
          if (pollCount >= MAX_POLLS) {
            clearInterval(pollInterval)
            syncDone.value = true
            syncMessage.value = '⏰ 同步超时（超过5分钟），请点击关闭后重试'
            window.$message?.warning('同步超时，请稍后重试')
            autoSyncLoading.value = false
          }
        } catch (e) {
          errorCount++
          console.error('同步状态查询失败(第' + errorCount + '次):', e)
          if (errorCount >= MAX_ERRORS || pollCount >= MAX_POLLS) {
            clearInterval(pollInterval)
            syncDone.value = true
            syncMessage.value = '❌ 同步状态查询失败，请稍后重试'
            autoSyncLoading.value = false
          }
          // 否则继续轮询重试
        }
      }, POLL_INTERVAL)
      return
    }

    // 兼容旧版同步返回
    syncDone.value = true
    const parts = []
    const errors = []
    if (data.expense_code?.success) parts.push(`费用号: +${data.expense_code.created || 0}/~${data.expense_code.updated || 0}`)
    else if (data.expense_code) errors.push(`费用号: ${data.expense_code.message || '失败'}`)
    if (data.test_order?.success) parts.push(`试验单: +${data.test_order.created || 0}/~${data.test_order.updated || 0}`)
    else if (data.test_order) errors.push(`试验单: ${data.test_order.message || '失败'}`)
    if (data.engineer?.success) parts.push(`工程师: +${data.engineer.created || 0}/~${data.engineer.updated || 0}`)
    else if (data.engineer) errors.push(`工程师: ${data.engineer.message || '失败'}`)
    if (data.driver?.success) parts.push(`驾驶员: +${data.driver.created || 0}/~${data.driver.updated || 0}`)
    else if (data.driver) errors.push(`驾驶员: ${data.driver.message || '失败'}`)
    if (data.personnel && !data.personnel.success) errors.push(`人员: ${data.personnel.message || '失败'}`)
    if (data.daily?.success) parts.push('每日费用已完成')
    else if (data.daily) errors.push(`每日费用: ${data.daily.message || '失败'}`)
    if (parts.length > 0) {
      syncMessage.value = `✅ 同步完成: ${parts.join(', ')}`
      window.$message?.success('飞书同步: ' + parts.join(', '))
    }
    if (errors.length > 0) {
      syncMessage.value = `❌ 同步失败: ${errors.join('; ')}`
      window.$message?.error('同步失败: ' + errors.join('; '))
    }
    await fetchDailyList(true)
  } catch (e) {
    console.error('自动同步失败:', e)
    const msg = e?.response?.data?.msg || e?.message || '网络错误'
    syncMessage.value = `❌ 飞书同步失败: ${msg}`
    window.$message?.error('飞书同步失败: ' + msg)
  } finally {
    autoSyncLoading.value = false
    syncDone.value = true
  }
}

// ==================== Tab ====================
const activeTab = ref('daily')

// ==================== 公共工具函数 ====================
function fmtDate(d) { if (!d) return ''; const dt = new Date(d); const y = dt.getFullYear(); const m = String(dt.getMonth()+1).padStart(2,'0'); const day = String(dt.getDate()).padStart(2,'0'); return `${y}-${m}-${day}` }
function renderTag(val, okVal = '通过') {
  if (val === okVal) return h(NTag, { type: 'success', size: 'small' }, () => okVal)
  if (val === '待审批') return h(NTag, { type: 'warning', size: 'small' }, () => '待审批')
  if (val === '驳回') return h(NTag, { type: 'error', size: 'small' }, () => '驳回')
  return val || '-'
}

// ==================== 供应商单价 ====================
const supplierEditing = ref(false)
const supplierLoading = ref(false)
const supplierData = ref([])
const newSupplierForm = ref({ name: '', local: 0, trip: 0, unit: 'hour', effective_from: null, effective_to: null, contract_no: '', code_local: '', code_trip: '' })

async function fetchSupplierRates() {
  supplierLoading.value = true
  try {
    const r = await expenseApi.getSupplierRateList()
    const list = r.data || []
    supplierData.value = list.map(s => ({
      id: s.id,
      name: s.name,
      local: Number(s.local_rate),
      trip: Number(s.trip_rate),
      unit: s.unit,
      effective_from: s.effective_from,
      effective_to: s.effective_to,
      contract_no: s.contract_no || '',
      code_local: s.code_local || '',
      code_trip: s.code_trip || '',
    }))
  } catch (e) { console.error(e) } finally { supplierLoading.value = false }
}
function supplierPayload(row) {
  return {
    name: row.name,
    local_rate: Number(row.local.toFixed(2)),
    trip_rate: Number(row.trip.toFixed(2)),
    unit: row.unit,
    effective_from: row.effective_from ? fmtDate(row.effective_from) : null,
    effective_to: row.effective_to ? fmtDate(row.effective_to) : null,
    contract_no: row.contract_no || '',
    code_local: row.code_local || '',
    code_trip: row.code_trip || '',
  }
}
async function saveSupplier(row) {
  try {
    if (row.id) {
      await expenseApi.updateSupplierRate({ id: row.id }, supplierPayload(row))
      window.$message?.success('已更新')
    } else {
      await expenseApi.createSupplierRate(supplierPayload(row))
      window.$message?.success('已新增')
      await fetchSupplierRates()
    }
  } catch (e) { console.error(e); window.$message?.error('保存失败') }
}
async function deleteSupplier(row) {
  if (!row.id) { supplierData.value = supplierData.value.filter(s => s !== row); return }
  try { await expenseApi.deleteSupplierRate({ id: row.id }); window.$message?.success('已删除'); await fetchSupplierRates() }
  catch (e) { console.error(e); window.$message?.error('删除失败') }
}
function addSupplierRow() {
  if (!newSupplierForm.value.name) { window.$message?.warning('请输入供应商名称'); return }
  supplierData.value.push({ ...newSupplierForm.value })
  newSupplierForm.value = { name: '', local: 0, trip: 0, unit: 'hour', effective_from: null, effective_to: null, contract_no: '', code_local: '', code_trip: '' }
}
function fmtEffective(fromDate, toDate) {
  const f = fromDate || '—'
  const t = toDate || '至今'
  return `${f} 至 ${t}`
}
const supplierCols = computed(() => [
  { title: '供应商', key: 'name', width: 80 },
  { title: '生效时间段', key: 'effective', width: 220,
    render(row) {
      if (supplierEditing.value) {
        const fromTs = row._fromTs !== undefined ? row._fromTs : (toTs(row.effective_from))
        const toTs_ = row._toTs !== undefined ? row._toTs : (toTs(row.effective_to))
        if (row._fromTs === undefined) row._fromTs = fromTs
        if (row._toTs === undefined) row._toTs = toTs_
        return h('div', { style: 'display:flex;align-items:center;gap:2px' }, [
          h(NDatePicker, { value: row._fromTs, type: 'date', size: 'tiny', clearable: true, style: 'width:88px',
            placeholder: '开始', onUpdateValue: v => { row._fromTs = v; row.effective_from = v ? fmtDate(v) : null } }),
          h('span', { style: 'font-size:11px' }, '至'),
          h(NDatePicker, { value: row._toTs, type: 'date', size: 'tiny', clearable: true, style: 'width:88px',
            placeholder: '截止', onUpdateValue: v => { row._toTs = v; row.effective_to = v ? fmtDate(v) : null } }),
        ])
      }
      const f = row.effective_from || '—'
      const t = row.effective_to || '至今'
      return `${f} 至 ${t}`
    }
  },
  { title: '武汉及周边', key: 'local', width: 180,
    render(row) {
      const label = row.unit === 'day' ? '元/天' : '元/时'
      if (!supplierEditing.value) return `${row.local} ${label}`
      return h('div', { style: 'display:flex;align-items:center;gap:4px' }, [
        h(NInputNumber, { value: row.local, size: 'tiny', min: 0, style: 'width:88px', onUpdateValue: v => { row.local = v } }),
        h(NSelect, { value: row.unit, size: 'tiny', style: 'width:70px', options: [{label:'元/时',value:'hour'},{label:'元/天',value:'day'}], onUpdateValue: v => { row.unit = v } }),
      ])
    }
  },
  { title: '全国(出差)', key: 'trip', width: 140,
    render(row) {
      const label = row.unit === 'day' ? '元/天' : '元/时'
      if (!supplierEditing.value) return `${row.trip} ${label}`
      return h('div', { style: 'display:flex;align-items:center;gap:8px' }, [
        h(NInputNumber, { value: row.trip, size: 'tiny', min: 0, style: 'width:88px', onUpdateValue: v => { row.trip = v } }),
      ])
    }
  },
  { title: '合同号', key: 'contract_no', width: 150, ellipsis: { tooltip: true },
    render(row) {
      if (!supplierEditing.value) return row.contract_no || ''
      return h(NInput, { value: row.contract_no, size: 'tiny', placeholder: '合同号', onUpdateValue: v => { row.contract_no = v } })
    }
  },
  { title: '未出差编号', key: 'code_local', width: 115, ellipsis: { tooltip: true },
    render(row) {
      if (!supplierEditing.value) return row.code_local || ''
      return h(NInput, { value: row.code_local, size: 'tiny', placeholder: '未出差编号', onUpdateValue: v => { row.code_local = v } })
    }
  },
  { title: '出差编号', key: 'code_trip', width: 115, ellipsis: { tooltip: true },
    render(row) {
      if (!supplierEditing.value) return row.code_trip || ''
      return h(NInput, { value: row.code_trip, size: 'tiny', placeholder: '出差编号', onUpdateValue: v => { row.code_trip = v } })
    }
  },
])

const dailyFilterDateRange = ref(null); const dailyFilterPerson = ref(''); const dailyFilterProject = ref(''); const dailyFilterOrder = ref('')
const dailyLoading = ref(false); const dailyData = ref([])
const dailyPagination = reactive({
  page: 1,
  pageSize: 50,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [20, 50, 100, 200],
  onChange: (page) => onDailyPageChange(page),
  onUpdatePageSize: (pageSize) => onDailyPageSizeChange(pageSize),
})
const dailyFetchVersion = ref(0)
const dailyCols = [
  { title: '日期', key: 'record_date', width: 100 },
  { title: '试验需求编号', key: 'test_order_no', width: 110 },
  { title: '供应商', key: 'supplier', width: 80 },
  { title: '人员', key: 'person_name', width: 80 },
  { title: '类型', key: 'person_type', width: 70 },
  { title: '出差状态', key: 'travel_status', width: 75 },
  { title: '正常工时', key: 'normal_hours', width: 80, align: 'center' },
  { title: '加班工时', key: 'overtime_hours', width: 80, align: 'center' },
  { title: '垫付金额', key: 'advance_payment', width: 85, align: 'right', render(r) { return Number(r.advance_payment||0).toFixed(2) } },
  { title: '每日合计', key: 'total_amount', width: 85, align: 'right', render(r) { return Number(r.total_amount||0).toFixed(2) } },
  { title: '单价参考', key: 'rate_ref', width: 85, align: 'center',
    render(r) {
      const sup = r.supplier || ''
      const dateStr = r.record_date || ''
      const trip = r.travel_status === '出差'
      const rates = supplierData.value.filter(s => s.name === sup)
      let rate, unit
      for (const s of rates) {
        const ef = s.effective_from, et = s.effective_to
        if ((!ef || dateStr >= ef) && (!et || dateStr <= et)) {
          rate = trip ? s.trip : s.local; unit = s.unit; break
        }
      }
      if (!rate) rate = trip ? 356 : 290, unit = 'day'
      return `${rate}元/${unit === 'hour' ? '时' : '天'}`
    }
  },
  { title: '审批状态', key: 'approval_status', width: 75, render(r) { return renderTag(r.approval_status) } },
  { title: '数据来源', key: 'source', width: 85, render(r) {
    const isFeishu = r.source === '飞书' || !!r.source_type
    if (isFeishu) return h(NTag, { type: 'info', size: 'small' }, () => '飞书')
    return h(NTag, { type: 'default', size: 'small' }, () => '手动')
  } },
]
const dailyTotalCount = computed(() => dailyPagination.itemCount)
const filteredTotal = ref(0)

async function fetchDailyList(reset = false) {
  dailyLoading.value = true
  try {
    if (reset) dailyPagination.page = 1
    const params = { page: dailyPagination.page, page_size: dailyPagination.pageSize }
    if (dailyFilterDateRange.value) {
      const [start, end] = dailyFilterDateRange.value
      if (start) params.record_date_start = typeof start === 'number' ? fmtDate(start) : start
      if (end) params.record_date_end = typeof end === 'number' ? fmtDate(end) : end
    }
    if (dailyFilterPerson.value) params.person_name = dailyFilterPerson.value
    if (dailyFilterProject.value) params.project_name = dailyFilterProject.value
    if (dailyFilterOrder.value) params.test_order_no = dailyFilterOrder.value
    const res = await expenseApi.getDailyRecordList(params)
    dailyData.value = (res.data || []).map(r => ({ ...r }))
    dailyPagination.itemCount = res.total || 0
    filteredTotal.value = res.filtered_total || 0
    dailyFetchVersion.value++
  } catch (e) { console.error(e) } finally {
    dailyLoading.value = false
  }
}

function onDailyPageChange(page) {
  dailyPagination.page = page
  fetchDailyList()
}
function onDailyPageSizeChange(pageSize) {
  dailyPagination.pageSize = pageSize
  dailyPagination.page = 1
  fetchDailyList(true)
}


// ==================== 人员绑定 ====================
const rpFilterOrder = ref('')
const rpFilterPerson = ref('')
const rpFilterSupplier = ref('')
const rpLoading = ref(false); const rpData = ref([])
const rpDataVersion = ref(0)
const rpPg = { pageSize: 10 }
const showRpModal = ref(false); const rpFormRef = ref(null)
const rpEditingId = ref(null)
const rpForm = ref({ test_order_no: '', supplier: '', outsourced_personnel: '', responsible_person: '', requirement_date: null })
const testOrderOpts = ref([])
const testOrdersMap = ref({})

const rpCols = [
  { title: '试验需求编号', key: 'test_order_no', width: 160 },
  { title: '供应商', key: 'supplier', width: 90 },
  { title: '委外人员', key: 'outsourced_personnel', width: 200, ellipsis: { tooltip: true } },
  { title: '负责人', key: 'responsible_person', width: 100 },
  { title: '操作', key: 'action', width: 130,
    render(row) {
      return h(NSpace, { size: 4, wrap: true, wrapItem: false }, () => [
        h(NButton, { size: 'tiny', type: 'warning', onClick: () => editRp(row) }, '编辑'),
        h(NButton, { size: 'tiny', type: 'error', onClick: () => deleteRp(row) }, '删除'),
      ])
    }
  },
]

async function loadTestOrders() {
  try {
    const r = await expenseApi.getTestOrderList({})
    const items = r.data || []
    const map = {}
    const opts = items.map(item => {
      map[item.test_order_no] = {
        responsible_person: item.responsible_person || '',
        supplier: item.supplier || '',
      }
      return { label: item.test_order_no, value: item.test_order_no }
    })
    testOrdersMap.value = map
    testOrderOpts.value = opts
  } catch (e) { console.error(e) }
}

function onRpOrderChange(val) {
  const info = testOrdersMap.value[val]
  if (info) {
    rpForm.value.responsible_person = info.responsible_person || ''
    rpForm.value.supplier = info.supplier || ''
  }
}

async function fetchRpList() {
  rpLoading.value = true
  try {
    const params = { has_outsourced: 'true' }
    if (rpFilterOrder.value) params.test_order_no = rpFilterOrder.value
    if (rpFilterPerson.value) params.outsourced_personnel = rpFilterPerson.value
    if (rpFilterSupplier.value) params.supplier = rpFilterSupplier.value
    const res = await expenseApi.getRequirementPersonnelList(params)
    rpData.value = res.data || []; rpDataVersion.value++
  } catch (e) { console.error(e) } finally { rpLoading.value = false }
}


function toTs(dateStr) {
  if (!dateStr) return null
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return null
  return d.getTime()
}
function openRpAddModal() {
  rpEditingId.value = null
  rpForm.value = { test_order_no: '', supplier: '', outsourced_personnel: '', responsible_person: '', requirement_date: null }
  showRpModal.value = true
  loadTestOrders()
}
function editRp(row) {
  rpEditingId.value = row.id
  rpForm.value = {
    test_order_no: row.test_order_no,
    supplier: row.supplier || '',
    outsourced_personnel: row.outsourced_personnel || '',
    responsible_person: row.responsible_person || '',
    requirement_date: toTs(row.requirement_date),
  }
  showRpModal.value = true
  loadTestOrders()
}
async function submitRp() {
  if (!rpForm.value.test_order_no) { window.$message?.warning('请选择试验需求编号'); return }
  const payload = { ...rpForm.value, requirement_date: fmtDate(rpForm.value.requirement_date) }
  try {
    if (rpEditingId.value) {
      await expenseApi.updateRequirementPersonnel({ id: rpEditingId.value }, payload)
    } else {
      await expenseApi.createRequirementPersonnel(payload)
    }
    window.$message?.success(rpEditingId.value ? '更新成功' : '创建成功')
    showRpModal.value = false
    await fetchRpList()
  } catch (e) { console.error(e); window.$message?.error('操作失败') }
}
async function deleteRp(row) {
  try {
    await expenseApi.deleteRequirementPersonnel({ id: row.id })
    window.$message?.success('删除成功')
    await fetchRpList()
  } catch (e) { console.error(e); window.$message?.error('删除失败') }
}

// ==================== Tab 切换自动加载 + 自动同步 ====================
watch(activeTab, (tab) => {
  if (tab === 'daily') fetchDailyList(true)
})

// 默认查询最近 30 天
function setDefaultDailyDateRange() {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  dailyFilterDateRange.value = [start.getTime(), end.getTime()]
}

// ==================== 初始化 ====================
onMounted(() => {
  fetchSupplierRates()
  setDefaultDailyDateRange()
  fetchDailyList(true)
})
</script>
