<template>
  <div>
    <!-- 筛选栏 -->
    <n-space :size="8" style="margin-bottom: 12px;">
      <n-select v-model:value="filterCategory" :options="categoryOpts" placeholder="类别" size="small" clearable style="width:100px" @update:value="fetchList" />
      <n-select v-model:value="filterSeries" :options="seriesOpts" placeholder="系列" size="small" clearable style="width:130px" @update:value="fetchList" />
      <n-input v-model:value="filterExpenseCode" placeholder="费用号" size="small" clearable style="width:130px" @keyup.enter="fetchList" @clear="fetchList" />
      <n-select v-model:value="usageThreshold" :options="usageOpts" placeholder="使用率" size="small" clearable style="width:110px" @update:value="onUsageChange" />
      <n-button size="small" type="primary" @click="fetchList">查询</n-button>
      <n-button size="small" @click="resetFilter">重置</n-button>
      <n-button size="small" type="info" @click="openCreate">+ 新增费用</n-button>
      <n-button size="small" type="warning" :loading="syncLoading" @click="doSyncFromFeishu">飞书同步</n-button>
    </n-space>

    <!-- 统计卡片 -->
    <n-space :size="12" style="margin-bottom: 12px;" align="stretch">
      <n-card size="small" style="flex:1; text-align:center;"><n-statistic label="费用号总数" :value="tableData.length" /></n-card>
      <n-card size="small" style="flex:1; text-align:center;"><n-statistic label="费用总金额" :value="fmt(totalAmount)" /></n-card>
      <n-card size="small" style="flex:1; text-align:center;"><n-statistic label="已启动金额" :value="fmt(totalStarted)" /></n-card>
      <n-card size="small" style="flex:1; text-align:center;"><n-statistic label="费用启动率" :value="`${overallStartRate}%`" /></n-card>
      <n-card size="small" style="flex:1; text-align:center;"><n-statistic label="费用使用率" :value="`${overallUseRate}%`" /></n-card>
    </n-space>

    <!-- 列表 -->
    <n-data-table :key="dataVersion" :columns="columns" :data="tableData" :loading="loading" :pagination="{ pageSize: 20 }" size="small"
      :row-key="(row) => row.id" :max-height="600" />

    <!-- 详情弹窗 -->
    <n-modal v-model:show="showDetailModal" :title="'费用号 '+(detailRow?.expense_code||'')+' 的试验单'" preset="card" style="width:1100px;">
      <n-data-table :columns="detailColumns" :data="detailData" :loading="detailLoading" :pagination="{ pageSize: 10 }" size="small" :max-height="400" />
      <template #footer><n-button @click="showDetailModal=false">关闭</n-button></template>
    </n-modal>

    <!-- 新增/编辑弹窗 -->
    <n-modal v-model:show="showModal" :title="editing ? '编辑费用号' : '新增费用'" preset="card" style="width:520px;">
      <n-form :model="form" label-placement="left" label-width="100">
        <n-form-item label="系列名称"><n-select v-model:value="form.series_name" :options="seriesFormOpts" placeholder="选择系列" /></n-form-item>
        <n-form-item label="类别"><n-select v-model:value="form.category" :options="categoryFormOpts" placeholder="选择类别" /></n-form-item>
        <n-form-item label="项目名称"><n-input v-model:value="form.project_name" placeholder="输入项目名称" /></n-form-item>
        <n-form-item label="所属预算号"><n-input v-model:value="form.budget_code" placeholder="输入预算号" /></n-form-item>
        <n-form-item label="费用号"><n-input v-model:value="form.expense_code" placeholder="输入费用号" /></n-form-item>
        <n-form-item label="费用总金额"><n-input-number v-model:value="form.total_amount" :min="0" style="width:100%" placeholder="输入金额" /></n-form-item>
        <n-form-item label="负责人"><n-input v-model:value="form.responsible_person" placeholder="输入负责人" /></n-form-item>
        <n-form-item label="是否已结束"><n-switch v-model:value="form.is_used" /></n-form-item>
      </n-form>
      <template #footer><n-space justify="end"><n-button @click="showModal=false">取消</n-button><n-button type="primary" @click="saveExpense">保存</n-button></n-space></template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { NSpace, NSelect, NButton, NCard, NStatistic, NDataTable, NModal, NForm, NFormItem, NInput, NInputNumber, NSwitch } from 'naive-ui'
import expenseApi from '@/api/expense'

const filterCategory = ref(null)
const filterSeries = ref(null)
const filterExpenseCode = ref('')
const usageThreshold = ref(null)
const usageOpts = [{ label:'≥50%', value:50 },{ label:'≥70%', value:70 },{ label:'≥95%', value:95 }]
const allData = ref([])    // 完整数据
const tableData = ref([])
const dataVersion = ref(0) // 表格强制刷新键
const loading = ref(false)
const showModal = ref(false)
const showDetailModal = ref(false)
const detailRow = ref(null)
const detailData = ref([])
const detailLoading = ref(false)
const editing = ref(null)

const form = ref({ series_name: null, category: null, project_name: '', budget_code: '', expense_code: '', total_amount: 0, responsible_person: '', is_used: false })

const categoryOpts = [{ label:'合作',value:'合作'},{ label:'海外',value:'海外'},{ label:'自研',value:'自研' }]
const seriesFormOpts = [{ label:'H37系列',value:'H37'},{ label:'H53系列',value:'H53'},{ label:'H56系列',value:'H56'},{ label:'H77系列',value:'H77'},{ label:'H97系列',value:'H97'},{ label:'ICV系列',value:'ICV'}]
const categoryFormOpts = categoryOpts

function fmt(v) { return v != null ? Number(v).toFixed(2) : '0.00' }

// 从完整系列名提取短系列名
function extractSeries(v) { return v ? (v.split('-')[0] || v.split(' ')[0] || v) : '' }

// 短代码 → 完整系列名映射
const seriesLabelMap = Object.fromEntries(seriesFormOpts.map(o => [o.value, o.label]))
function seriesLabel(short) {
  if (!short) return '-'
  // 尝试匹配已知系列
  for (const [key, label] of Object.entries(seriesLabelMap)) {
    if (short.startsWith(key) || short.includes(key)) return label
  }
  // 尝试从系列名匹配
  const base = short.split('-')[0] || short
  for (const [key, label] of Object.entries(seriesLabelMap)) {
    if (base.startsWith(key) || base.includes(key)) return label
  }
  return short
}

const totalAmount = computed(() => allData.value.reduce((s,r)=>s+Number(r.total_amount||0),0))
const totalStarted = computed(() => allData.value.reduce((s,r)=>s+Number(r.test_orders_total||0),0))
const totalUsed = computed(() => allData.value.reduce((s,r)=>s+Number(r.used_amount||0),0))
const overallStartRate = computed(() => totalAmount.value>0?Math.round(totalStarted.value/totalAmount.value*100*10)/10:0)
const overallUseRate = computed(() => totalAmount.value>0?Math.round(totalUsed.value/totalAmount.value*100*10)/10:0)

const columns = [
  { title:'系列名称', key:'series_name', width:110, render(r){ return seriesLabel(r.series_name) }},
  { title:'类别', key:'category', width:70 },
  { title:'项目名称', key:'project_name', width:170, ellipsis:{tooltip:true} },
  { title:'预算号', key:'budget_code', width:130 },
  { title:'费用号', key:'expense_code', width:130 },
  { title:'负责人', key:'responsible_person', width:90 },
  { title:'是否已结束', key:'is_used', width:90, align:'center', render(r){ return r.is_used ? h('span',{style:{color:'#999'}},'是') : h('span',{style:{color:'#18a058',fontWeight:'600'}},'否') }},
  { title:'费用总金额', key:'total_amount', width:100, align:'right', render(r){ return fmt(r.total_amount) }},
  { title:'已启动金额', key:'test_orders_total', width:100, align:'right', render(r){ return fmt(r.test_orders_total||0) }},
  { title:'已使用金额', key:'test_orders_used', width:100, align:'right', render(r){ return fmt(r.test_orders_used||0) }},
  { title:'已结算金额', key:'test_orders_settled', width:100, align:'right', render(r){ return fmt(r.test_orders_settled||0) }},
  { title:'费用启动率', key:'start_rate', width:95, align:'center', render(r){ return `${r.start_rate||0}%` }},
  { title:'费用使用率', key:'main_usage_rate', width:95, align:'center',
    render(r){ const v=r.main_usage_rate||0; const c=v>=70?'#e74c3c':v>=50?'#f0a020':''; return h('span',{style:{color:c,fontWeight:v>=50?'600':'400'}},`${v}%`) }},
  {
    title:'操作', key:'action', width:160,
    render(row) {
      return h(NSpace,{size:4},()=>[
        h(NButton,{size:'tiny',type:'info',onClick:()=>showDetail(row)},'详情'),
        h(NButton,{size:'tiny',type:'primary',onClick:()=>editRow(row)},'编辑'),
        h(NButton,{size:'tiny',type:'error',ghost:true,onClick:()=>deleteRow(row)},'删除'),
      ])
    }
  },
]

async function fetchList() {
  loading.value=true
  try { const p={}; if(filterCategory.value)p.category=filterCategory.value; if(filterSeries.value)p.project_keyword=filterSeries.value; if(filterExpenseCode.value)p.expense_code=filterExpenseCode.value; const r=await expenseApi.getExpenseCodeList(p); allData.value=r.data||[]; onUsageChange(usageThreshold.value); dataVersion.value++ } catch(e){console.error(e)} finally{loading.value=false}
}
function resetFilter() { filterCategory.value=null; filterSeries.value=null; filterExpenseCode.value=''; usageThreshold.value=null; fetchList() }
function onUsageChange(v) { tableData.value = v ? allData.value.filter(r=>(r.main_usage_rate||0)>=v) : allData.value.slice() }

function openCreate() { editing.value=null; form.value={series_name:null,category:null,project_name:'',budget_code:'',expense_code:'',total_amount:0,responsible_person:'',is_used:false}; showModal.value=true }

function editRow(row) {
  editing.value=row
  // 把当前系列名映射到下拉值
  const curLabel = seriesLabel(row.series_name)
  const match = seriesFormOpts.find(o => o.label === curLabel)
  form.value={
    series_name: match ? match.value : null,
    category: row.category||null,
    project_name: row.project_name||'',
    budget_code: row.budget_code||'',
    expense_code: row.expense_code,
    total_amount: Number(row.total_amount||0),
    responsible_person: row.responsible_person||'',
    is_used: !!row.is_used
  }
  showModal.value=true
}

async function saveExpense() {
  if(!form.value.expense_code) return window.$message?.warning('请输入费用号')
  try {
    if (editing.value) {
      const payload = { expense_code: form.value.expense_code, total_amount: form.value.total_amount, responsible_person: form.value.responsible_person || '', is_used: form.value.is_used }
      await expenseApi.updateExpenseCode({ id: editing.value.id }, payload)
    } else {
      // 新建
      if(!form.value.project_name) return window.$message?.warning('请输入项目名称')
      if(!form.value.budget_code) return window.$message?.warning('请输入预算号')
      const opt = seriesFormOpts.find(o => o.value === form.value.series_name)
      const seriesFull = opt ? opt.label : (form.value.series_name||'')
      let projectId = null
      const pList = await expenseApi.getExpenseProjectList({ project_name: form.value.project_name })
      const existP = (pList.data||[]).find(p => p.project_name === form.value.project_name)
      if (existP) projectId = existP.id
      else {
        await expenseApi.createExpenseProject({ series_name: seriesFull, category: form.value.category||'', project_name: form.value.project_name })
        const pList2 = await expenseApi.getExpenseProjectList({ project_name: form.value.project_name })
        const np = (pList2.data||[]).find(p => p.project_name === form.value.project_name)
        projectId = np ? np.id : null
      }
      if (!projectId) return window.$message?.error('创建项目失败')
      let budgetId = null
      const bList = await expenseApi.getBudgetCodeList({ project_id: projectId })
      const existB = (bList.data||[]).find(b => b.budget_code === form.value.budget_code)
      if (existB) budgetId = existB.id
      else {
        await expenseApi.createBudgetCode({ project_id: projectId, budget_code: form.value.budget_code })
        const bList2 = await expenseApi.getBudgetCodeList({ project_id: projectId })
        const nb = (bList2.data||[]).find(b => b.budget_code === form.value.budget_code)
        budgetId = nb ? nb.id : null
      }
      if (!budgetId) return window.$message?.error('创建预算号失败')
      await expenseApi.createExpenseCode({ budget_id: budgetId, expense_code: form.value.expense_code, total_amount: form.value.total_amount, responsible_person: form.value.responsible_person, is_used: form.value.is_used })
    }
    window.$message?.success('保存成功'); showModal.value=false; await fetchList()
  } catch(e){console.error(e); window.$message?.error('保存失败')}
}

async function deleteRow(row) {
  if(!confirm(`确定删除费用号 ${row.expense_code}？`)) return
  try { await expenseApi.deleteExpenseCode({id:row.id}); window.$message?.success('已删除'); fetchList() }
  catch(e){console.error(e); window.$message?.error('删除失败')}
}

const detailColumns = [
  { title:'试验需求单号', key:'test_order_no', width:140 },
  { title:'预算号', key:'budget_code', width:120 },
  { title:'费用号', key:'expense_code', width:120 },
  { title:'试验金额', key:'total_price', width:100, align:'right', render(r){ return fmt(r.total_price) }},
  { title:'已使用金额', key:'used_amount', width:110, align:'right', render(r){ return fmt(r.used_amount) }},
  { title:'计划开展时间', key:'planned_start_time', width:110, render(r){ return (r.planned_start_time||'').toString().slice(0,10)||'-' }},
  { title:'计划完成时间', key:'planned_end_time', width:110, render(r){ return (r.planned_end_time||'').toString().slice(0,10)||'-' }},
  { title:'实际开展时间', key:'actual_start_time', width:110, render(r){ return (r.actual_start_time||'').toString().slice(0,10)||'-' }},
  { title:'实际完成时间', key:'actual_end_time', width:110, render(r){ return (r.actual_end_time||'').toString().slice(0,10)||'-' }},
  { title:'供应商', key:'supplier', width:90 },
  { title:'委外人数', key:'outsourced_count', width:80, align:'center' },
  { title:'是否已结束', key:'is_used', width:90, align:'center', render(r){ return r.is_used ? h('span',{style:{color:'#999'}},'是') : h('span',{style:{color:'#18a058',fontWeight:'600'}},'否') }},
  { title:'负责人', key:'responsible_person', width:80 },
]

async function showDetail(row) {
  detailRow.value = row
  detailLoading.value = true
  showDetailModal.value = true
  try {
    const r = await expenseApi.getTestOrderList({ expense_code_id: row.id })
    detailData.value = r.data || []
  } catch(e){ console.error(e) }
  finally { detailLoading.value = false }
}

const syncLoading = ref(false)
async function doSyncFromFeishu() {
  syncLoading.value = true
  try {
    await expenseApi.syncExpenseCodeFromFeishu()
    await expenseApi.syncTestOrderFromFeishu()
    window.$message?.success('飞书同步完成')
    await fetchList()
  } catch(e) { console.error(e); window.$message?.error('同步失败') } finally { syncLoading.value = false }
}

onMounted(()=>{fetchList()})
</script>
