<template>
  <div>
    <n-space :size="8" style="margin-bottom: 12px;">
      <n-input v-model:value="filterOrderNo" placeholder="试验单号" size="small" clearable style="width:150px" @keyup.enter="fetchList" />
      <n-input v-model:value="filterExpenseCode" placeholder="费用号" size="small" clearable style="width:140px" @keyup.enter="fetchList" @clear="fetchList" />
      <n-input v-model:value="filterResponsible" placeholder="责任人" size="small" clearable style="width:100px" @keyup.enter="fetchList" />
      <n-select v-model:value="filterIsUsed" :options="isUsedOpts" placeholder="状态" size="small" clearable style="width:100px" @update:value="applyFilter" />
      <n-select v-model:value="usageThreshold" :options="usageOpts" placeholder="使用率" size="small" clearable style="width:110px" @update:value="applyFilter" />
      <n-button size="small" type="primary" @click="fetchList">查询</n-button>
      <n-button size="small" @click="resetFilter">重置</n-button>
      <n-button size="small" type="info" @click="openCreate">+ 新增试验单</n-button>
      <n-button size="small" type="warning" :loading="syncLoading" @click="doSyncFromFeishu">飞书同步</n-button>
    </n-space>

    <n-space :size="12" style="margin-bottom: 12px;" align="stretch">
      <n-card size="small" style="flex:1; text-align:center;"><n-statistic label="试验单总数" :value="tableData.length" /></n-card>
      <n-card size="small" style="flex:1; text-align:center;"><n-statistic label="试验总金额" :value="fmt(totalPrice)" /></n-card>
      <n-card size="small" style="flex:1; text-align:center;"><n-statistic label="已使用金额" :value="fmt(totalUsed)" /></n-card>
      <n-card size="small" style="flex:1; text-align:center;"><n-statistic label="试验使用率" :value="overallRateStr" /></n-card>
    </n-space>

    <n-data-table :key="dataVersion" :columns="columns" :data="displayData" :loading="loading" :pagination="{ pageSize: 20 }" size="small"
      :row-key="(row) => row.id" :max-height="600" :scroll-x="1620" :single-line="false" />

    <n-modal v-model:show="showModal" :title="editing ? '编辑试验单' : '新增试验单'" preset="card" style="width:660px;">
      <n-form :model="form" label-placement="left" label-width="110">
        <n-form-item label="试验需求单号"><n-input v-model:value="form.test_order_no" placeholder="输入试验需求编号" /></n-form-item>
        <n-form-item label="所属费用号"><n-select v-model:value="form.expense_code_id" :options="expenseCodeOpts" placeholder="选择费用号" filterable :disabled="!!editing" /></n-form-item>
        <n-form-item label="总金额"><n-input-number v-model:value="form.total_price" :min="0" style="width:100%" placeholder="输入总金额" /></n-form-item>
        <n-form-item label="截止到上月已结算"><n-input-number v-model:value="form.settlement_amount" :min="0" style="width:100%" placeholder="输入截止到上月已结算金额" /></n-form-item>
        <n-form-item label="计划开展时间"><n-date-picker v-model:value="form.planned_start_time" value-format="yyyy-MM-dd" type="date" style="width:100%" /></n-form-item>
        <n-form-item label="计划完成时间"><n-date-picker v-model:value="form.planned_end_time" value-format="yyyy-MM-dd" type="date" style="width:100%" /></n-form-item>
        <n-form-item label="实际开展时间"><n-date-picker v-model:value="form.actual_start_time" value-format="yyyy-MM-dd" type="date" style="width:100%" /></n-form-item>
        <n-form-item label="实际完成时间"><n-date-picker v-model:value="form.actual_end_time" value-format="yyyy-MM-dd" type="date" style="width:100%" /></n-form-item>
        <n-form-item label="供应商"><n-input v-model:value="form.supplier" placeholder="输入供应商" /></n-form-item>
        <n-form-item label="委外人数"><n-input-number v-model:value="form.outsourced_count" :min="0" style="width:100%" placeholder="输入委外人数" /></n-form-item>
        <n-form-item label="是否已结束"><n-switch v-model:value="form.is_used" /></n-form-item>
        <n-form-item label="负责人"><n-input v-model:value="form.responsible_person" placeholder="输入负责人" /></n-form-item>
      </n-form>
      <template #footer><n-space justify="end"><n-button @click="showModal=false">取消</n-button><n-button type="primary" @click="saveForm">保存</n-button></n-space></template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { NSpace, NSelect, NButton, NCard, NStatistic, NDataTable, NModal, NForm, NFormItem, NInput, NInputNumber, NDatePicker, NSwitch } from 'naive-ui'
import expenseApi from '@/api/expense'

const filterOrderNo = ref('')
const filterExpenseCode = ref('')
const filterResponsible = ref('')
const filterIsUsed = ref(null)
const usageThreshold = ref(null)
const isUsedOpts = [{ label:'进行中', value:false },{ label:'已结束', value:true }]
const usageOpts = [{ label:'≥50%', value:50 },{ label:'≥70%', value:70 },{ label:'≥95%', value:95 }]
const allData = ref([])
const tableData = ref([])
const dataVersion = ref(0)
const loading = ref(false)
const syncLoading = ref(false)
const showModal = ref(false)
const editing = ref(null)
const expenseCodeOpts = ref([])

const form = ref({
  test_order_no:'', expense_code_id:null, total_price:0, settlement_amount:null,
  planned_start_time:null, planned_end_time:null, actual_start_time:null, actual_end_time:null,
  supplier:'', outsourced_count:0, is_used:false, responsible_person:''
})

const seriesOpts = [{ label:'H37系列',value:'H37'},{ label:'H53系列',value:'H53'},{ label:'H56系列',value:'H56'},{ label:'H66系列',value:'H66'},{ label:'H77系列',value:'H77'},{ label:'H97系列',value:'H97'},{ label:'ICV系列',value:'ICV'}] // 保留（可能别处用）
function fmt(v) { return v != null ? Number(v).toFixed(2) : '0.00' }
function fmtDate(d) { if(!d) return '-'; const s = String(d); return s.length>=10 ? s.slice(0,10) : s }
function fmtDateVal(v) { if(!v) return null; const d = new Date(v); const y = d.getFullYear(); const m = String(d.getMonth()+1).padStart(2,'0'); const day = String(d.getDate()).padStart(2,'0'); return `${y}-${m}-${day}` }

const totalPrice = computed(() => allData.value.reduce((s,r)=>s+Number(r.total_price||0),0))
const totalUsed = computed(() => allData.value.reduce((s,r)=>s+Number(r.used_amount||0),0))
const totalOutsourced = computed(() => allData.value.reduce((s,r)=>s+Number(r.outsourced_count||0),0))
const overallRateStr = computed(() => {
  const p = totalPrice.value; return p>0 ? Math.round(totalUsed.value/p*1000)/10+'%' : '0%'
})

const displayData = computed(() => tableData.value.map(r=>{
  const tp = Number(r.total_price||0); const ua = Number(r.used_amount||0)
  return { ...r, remain: fmt(tp-ua), usageRate: tp>0 ? Math.round(ua/tp*1000)/10 : 0 }
}))

const columns = [
  { title:'试验需求单号', key:'test_order_no', width:130 },
  { title:'预算号', key:'budget_code', width:110 },
  { title:'费用号', key:'expense_code', width:100 },
  { title:'试验金额', key:'total_price', width:95, align:'right', render(r){ return fmt(r.total_price) }},
  { title:'计划开展时间', key:'planned_start_time', width:95, render(r){ return fmtDate(r.planned_start_time) }},
  { title:'计划完成时间', key:'planned_end_time', width:95, render(r){ return fmtDate(r.planned_end_time) }},
  { title:'实际开展时间', key:'actual_start_time', width:95, render(r){ return fmtDate(r.actual_start_time) }},
  { title:'实际完成时间', key:'actual_end_time', width:95, render(r){ return fmtDate(r.actual_end_time) }},
  { title:'供应商', key:'supplier', width:80 },
  { title:'委外人数', key:'outsourced_count', width:70, align:'center' },
  { title:'是否已结束', key:'is_used', width:75, align:'center', render(r){ return r.is_used ? h('span',{style:{color:'#999'}},'是') : h('span',{style:{color:'#18a058',fontWeight:'600'}},'否') }},
  { title:'实时已使用', key:'used_amount', width:90, align:'right', render(r){ return fmt(r.used_amount) }},
  { title:'截止到上月已结算', key:'settlement_amount', width:110, align:'right', render(r){ return fmt(r.settlement_amount) }},
  { title:'剩余金额', key:'remain', width:80, align:'right' },
  { title:'试验使用率', key:'usageRate', width:85, align:'center', render(r){ const v=r.usageRate||0; const c=v>=95?'#e74c3c':v>=70?'#f0a020':''; return h('span',{style:{color:c,fontWeight:v>=50?'600':'400'}},`${v}%`) }},
  { title:'负责人', key:'responsible_person', width:75 },
  { title:'操作', key:'action', width:100, fixed:'right',
    render(row){ return h(NSpace,{size:4},()=>[
      h(NButton,{size:'tiny',type:'primary',onClick:()=>editRow(row)},'编辑'),
      h(NButton,{size:'tiny',type:'error',ghost:true,onClick:()=>deleteRow(row)},'删除'),
    ])}
  },
]

async function loadExpenseCodeOpts() { try { const r=await expenseApi.getExpenseCodeList(); expenseCodeOpts.value=(r.data||[]).map(e=>({label:e.expense_code+' - '+e.project_name,value:e.id})) } catch(e){} }

async function doSyncFromFeishu() {
  syncLoading.value = true
  try {
    const r = await expenseApi.syncTestOrderFromFeishu()
    const data = r.data || {}
    if (data.success) {
      window.$message?.success(data.message || '同步完成')
      fetchList()
    } else {
      window.$message?.warning(data.message || '同步失败')
    }
  } catch (e) {
    window.$message?.error('同步请求失败')
  } finally {
    syncLoading.value = false
  }
}

async function fetchList() {
  loading.value=true
  try {
    const p={}; if(filterOrderNo.value) p.test_order_no=filterOrderNo.value; if(filterResponsible.value) p.responsible_person=filterResponsible.value; if(filterExpenseCode.value) p.expense_code=filterExpenseCode.value
    const r=await expenseApi.getTestOrderList(p); allData.value=r.data||[]; applyFilter(); dataVersion.value++
  } catch(e){console.error(e)} finally{loading.value=false}
}

function resetFilter() { filterOrderNo.value=''; filterExpenseCode.value=''; filterResponsible.value=''; filterIsUsed.value=null; usageThreshold.value=null; fetchList() }

function applyFilter() {
  let d=[...allData.value]
  if(filterIsUsed.value!==null) d=d.filter(r=>!!r.is_used===filterIsUsed.value)
  if(usageThreshold.value) { const t=usageThreshold.value; d=d.filter(r=>{ const tp=Number(r.total_price||0); return tp>0&&(Number(r.used_amount||0)/tp*100)>=t }) }
  tableData.value=d
}

function openCreate() { editing.value=null; loadExpenseCodeOpts(); form.value={test_order_no:'',expense_code_id:null,total_price:0,settlement_amount:null,planned_start_time:null,planned_end_time:null,actual_start_time:null,actual_end_time:null,supplier:'',outsourced_count:0,is_used:false,responsible_person:''}; showModal.value=true }

function editRow(row) {
  editing.value=row
  form.value={
    test_order_no:row.test_order_no, expense_code_id:row.expense_code_id||null,
    total_price:Number(row.total_price||0), settlement_amount:row.settlement_amount!=null?Number(row.settlement_amount):null,
    planned_start_time:fmtDate(row.planned_start_time)=== '-' ? null : new Date(fmtDate(row.planned_start_time)).getTime(),
    planned_end_time:fmtDate(row.planned_end_time)=== '-' ? null : new Date(fmtDate(row.planned_end_time)).getTime(),
    actual_start_time:fmtDate(row.actual_start_time)=== '-' ? null : new Date(fmtDate(row.actual_start_time)).getTime(),
    actual_end_time:fmtDate(row.actual_end_time)=== '-' ? null : new Date(fmtDate(row.actual_end_time)).getTime(),
    supplier:row.supplier||'', outsourced_count:Number(row.outsourced_count||0),
    is_used:!!row.is_used, responsible_person:row.responsible_person||''
  }; showModal.value=true
}

async function saveForm() {
  if(!form.value.test_order_no) return window.$message?.warning('请输入试验需求编号')
  try {
    const payload = {
      test_order_no:form.value.test_order_no, total_price:form.value.total_price, settlement_amount:form.value.settlement_amount,
      planned_start_time:fmtDateVal(form.value.planned_start_time),
      planned_end_time:fmtDateVal(form.value.planned_end_time),
      actual_start_time:fmtDateVal(form.value.actual_start_time),
      actual_end_time:fmtDateVal(form.value.actual_end_time),
      supplier:form.value.supplier||'', outsourced_count:form.value.outsourced_count,
      is_used:form.value.is_used, responsible_person:form.value.responsible_person||'',
    }
    if(!editing.value) { if(!form.value.expense_code_id) return window.$message?.warning('请选择费用号'); payload.expense_code_id=form.value.expense_code_id }
    if(editing.value) await expenseApi.updateTestOrder({ id:editing.value.id }, payload)
    else await expenseApi.createTestOrder(payload)
    window.$message?.success('保存成功'); showModal.value=false; await fetchList()
  } catch(e){console.error(e); window.$message?.error('保存失败')}
}

async function deleteRow(row) {
  if(!confirm(`确定删除试验单 ${row.test_order_no}？`)) return
  try { await expenseApi.deleteTestOrder({ id:row.id }); window.$message?.success('已删除'); fetchList() }
  catch(e){console.error(e); window.$message?.error('删除失败')}
}

onMounted(()=>{ fetchList(); loadExpenseCodeOpts() })
</script>
