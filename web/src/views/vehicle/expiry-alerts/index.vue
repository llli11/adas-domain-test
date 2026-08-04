<script setup>
import { onMounted, ref, computed } from 'vue'
import { NTag, NSpin, NButton, NSelect, useMessage } from 'naive-ui'
import api from '@/api'
import { isAreaMismatch } from '@/utils/cityProvinceMap'

defineOptions({ name: '异常状态提醒' })
const $message = useMessage()
const loading = ref(false)
const allVehicles = ref([])
const currentTab = ref('temp_plate')
const filterDept1 = ref('产品验证中心')
const filterDept2 = ref('智驾域测试')
const filterVehicleCode = ref(null)
const filterBorrower = ref(null)
const filterVn = ref(null)
const filterDriver = ref(null)
const filterTester = ref(null)
const dept1Options = ref([])
const dept2Options = ref([])
const vehicleCodeOptions = ref([])
const borrowerOptions = ref([])
const vnOptions = ref([])
const driverOptions = ref([])
const testerOptions = ref([])
const rawFiltered = computed(() => {
  try {
    let list = allVehicles.value
    if (filterDept1.value) list = list.filter(v => v.dept_l1 === filterDept1.value)
    if (filterDept2.value) list = list.filter(v => v.dept_l2 === filterDept2.value)
    if (filterVehicleCode.value) list = list.filter(v => v.vehicle_code === filterVehicleCode.value)
    if (filterBorrower.value) list = list.filter(v => v.borrower === filterBorrower.value)
    if (filterVn.value) list = list.filter(v => v.vn === filterVn.value)
    if (filterDriver.value) list = list.filter(v => v.driver === filterDriver.value)
    if (filterTester.value) list = list.filter(v => v.tester === filterTester.value)
    return list
  } catch(e) {
    console.error('[expiry] rawFiltered computed error:', e)
    return []
  }
})

const subTabs = [
  { key: 'temp_plate', label: '临牌到期' },
  { key: 'borrow', label: '借用到期' },
  { key: 'abnormal', label: '异常报警' },
  { key: 'utilization', label: '7天利用率' },
  { key: 'idle', label: '空置车辆' },
]

function _daysTo(ds) {
  if (!ds) return null
  const d = new Date(ds); if (isNaN(d.getTime())) return null
  const t = new Date(); t.setHours(0,0,0,0)
  const td = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  return Math.ceil((td - t) / 86400000)
}
function daysColor(d) {
  if (d===null) return '#999'; if (d<0) return '#d03050'; if (d<=7) return '#f97316'; if (d<=14) return '#f0a020'; return '#18a058'
}
function daysText(d) {
  if (d===null) return '--'; if (d<0) return `已过期${Math.abs(d)}天`; if (d===0) return '今天到期'; return `剩余${d}天`
}
function rateColor(r) { if (r==null) return '#999'; return r<=10?'#FF4D4F':r<50?'#FA8C16':'#52C41A' }

const tempPlateAlerts = computed(() => {
  return rawFiltered.value.filter(v => v.temp_plate_expire_date).map(v=>{const d=_daysTo(v.temp_plate_expire_date); return {...v,days:d,color:daysColor(d),label:daysText(d),absDays:d!==null?Math.abs(d):0}}).filter(v=>v.days!==null&&v.days<=30).sort((a,b)=>(a.days??999)-(b.days??999))
})
const borrowAlerts = computed(() => {
  return rawFiltered.value.filter(v => v.borrow_expire_date).map(v=>{const d=_daysTo(v.borrow_expire_date); return {...v,days:d,color:daysColor(d),label:daysText(d),absDays:d!==null?Math.abs(d):0}}).filter(v=>v.days!==null&&v.days<=30).sort((a,b)=>(a.days??999)-(b.days??999))
})
const faultAlerts = computed(() => rawFiltered.value.filter(v => v.task_status==='故障或事故'))
const areaMismatchAlerts = computed(() => rawFiltered.value.filter(v => {const c=(v.test_city||'').replace(/市|省|自治区|特别行政区/g,'').trim();const a=v.temp_plate_area||v.insurance_area||'';return c&&a&&isAreaMismatch(v)}))
const idleAlerts = computed(() => rawFiltered.value.filter(v=>{const t=new Date();t.setHours(0,0,0,0);const tp=v.temp_plate_expire_date?new Date(v.temp_plate_expire_date):null;const bp=v.borrow_expire_date?new Date(v.borrow_expire_date):null;if(tp&&tp<=t)return false;if(bp&&bp<=t)return false;if((v.tester||'').trim()||(v.driver||'').trim())return false;return true}))
const utilizationAlerts = computed(() => rawFiltered.value.filter(v=>v.borrower_7day_rate!=null).map(v=>{const raw=Number(v.borrower_7day_rate);const r=raw<1?raw*100:raw;return {...v,rate:r,color:r<=10?'#FF4D4F':r<50?'#FA8C16':'#52C41A',absDays:r,days:r,label:r<=10?'低利用':r<50?'中利用':'高利用'}}).sort((a,b)=>(a.rate??0)-(b.rate??0)))

const counts = computed(() => ({
  temp_plate: tempPlateAlerts.value.length, borrow: borrowAlerts.value.length,
  abnormal: faultAlerts.value.length + areaMismatchAlerts.value.length,
  utilization: utilizationAlerts.value.length, idle: idleAlerts.value.length,
}))

const rateStats = computed(() => {
  const data = rawFiltered.value; let l=0,m=0,h=0,t=0
  data.forEach(v=>{const raw=parseFloat(v.borrower_7day_rate);if(!isNaN(raw)){t++;const r=raw<1?raw*100:raw;if(r<=10)l++;else if(r<50)m++;else h++}})
  return {low:l,mid:m,high:h,total:t}
})

function extractFilterOptions(list) {
  const d1=new Set(),d2=new Set(),vc=new Set(),br=new Set(),vn=new Set(),dr=new Set(),te=new Set()
  list.forEach(v=>{
    if(v.dept_l1)d1.add(v.dept_l1)
    if(v.dept_l2)d2.add(v.dept_l2)
    if(v.vehicle_code)vc.add(v.vehicle_code)
    if(v.borrower)br.add(v.borrower)
    if(v.vn)vn.add(v.vn)
    if(v.driver)dr.add(v.driver)
    if(v.tester)te.add(v.tester)
  })
  dept1Options.value=[...d1].sort().map(v=>({label:v,value:v}))
  dept2Options.value=[...d2].sort().map(v=>({label:v,value:v}))
  vehicleCodeOptions.value=[...vc].sort().map(v=>({label:v,value:v}))
  borrowerOptions.value=[...br].sort().map(v=>({label:v,value:v}))
  vnOptions.value=[...vn].sort().map(v=>({label:v,value:v}))
  driverOptions.value=[...dr].sort().map(v=>({label:v,value:v}))
  testerOptions.value=[...te].sort().map(v=>({label:v,value:v}))
}

async function fetchAlerts() {
  loading.value=true
  try {
    const res=await api.getVehicleList({page:1,page_size:9999})
    allVehicles.value=res.data||[]
    extractFilterOptions(allVehicles.value)
  } catch(e){console.error(e);$message.error('获取数据失败')}
  finally{loading.value=false}
}

onMounted(()=>{
  fetchAlerts()
})
</script>

<template>
<div class="ea-root">
  <div class="ea-topbar">
    <NSelect v-model:value="filterDept1" :options="dept1Options" placeholder="一级部门" clearable filterable size="small" style="width:140px" />
    <NSelect v-model:value="filterDept2" :options="dept2Options" placeholder="二级部门" clearable filterable size="small" style="width:140px" />
    <NSelect v-model:value="filterVehicleCode" :options="vehicleCodeOptions" placeholder="车辆编号" clearable filterable size="small" style="width:130px" />
    <NSelect v-model:value="filterVn" :options="vnOptions" placeholder="VIN" clearable filterable size="small" style="width:150px" />
    <NSelect v-model:value="filterBorrower" :options="borrowerOptions" placeholder="借车人" clearable filterable size="small" style="width:110px" />
    <NSelect v-model:value="filterDriver" :options="driverOptions" placeholder="驾驶" clearable filterable size="small" style="width:110px" />
    <NSelect v-model:value="filterTester" :options="testerOptions" placeholder="测试" clearable filterable size="small" style="width:110px" />
    <NButton size="small" @click="filterDept1 = '产品验证中心'; filterDept2 = '智驾域测试'; filterVehicleCode = null; filterVn = null; filterBorrower = null; filterDriver = null; filterTester = null">重置</NButton>
  </div>
  <div class="ea-tabs-bar">
    <div class="ea-tabs">
      <div v-for="t in subTabs" :key="t.key" class="ea-tab" :class="{on:currentTab===t.key}" @click="currentTab=t.key">
        <span>{{ t.label }}</span>
        <span class="ea-tn" :class="counts[t.key]>0?'tn-danger':'tn-ok'">{{ counts[t.key] }}</span>
      </div>
    </div>
    <div class="ea-rate-inline">
      <span class="ea-rate-label">7天利用率</span>
      <span class="ea-r-item r-low">≤10%: <b>{{ rateStats.low }}</b></span>
      <span class="ea-r-item r-mid">10-50%: <b>{{ rateStats.mid }}</b></span>
      <span class="ea-r-item r-high">≥50%: <b>{{ rateStats.high }}</b></span>
      <span class="ea-r-item r-total">总计: <b>{{ rateStats.total }}</b></span>
    </div>
  </div>

  <div class="ea-body">
  <NSpin :show="loading">

    <template v-if="currentTab==='temp_plate'||currentTab==='borrow'||currentTab==='utilization'">
      <div v-if="(currentTab==='temp_plate'?tempPlateAlerts:currentTab==='borrow'?borrowAlerts:utilizationAlerts).length" class="ea-grid">
        <div v-for="(v,i) in (currentTab==='temp_plate'?tempPlateAlerts:currentTab==='borrow'?borrowAlerts:utilizationAlerts)" :key="i" class="ea-card" :style="{borderColor:v.color||'#e0e0e0'}">
          <div class="ea-bar" :style="{background:v.color||'#ccc'}" />
          <div class="ea-bd">
            <div class="ea-rows">
              <div class="ea-p"><span class="ea-l">编号</span><span class="ea-v">{{ v.vehicle_code||v.vn||'--' }}</span></div>
              <div class="ea-p"><span class="ea-l">车型</span><span class="ea-v">{{ v.vehicle_model||'--' }}</span></div>
              <div class="ea-p"><span class="ea-l">驾驶</span><span class="ea-v">{{ v.driver||'--' }}</span></div>
              <div class="ea-p"><span class="ea-l">测试</span><span class="ea-v">{{ v.tester||'--' }}</span></div>
              <div class="ea-p"><span class="ea-l">借车人</span><span class="ea-v">{{ v.borrower||'--' }}</span></div>
              <div class="ea-p"><span class="ea-l">VIN</span><span class="ea-v">{{ v.vn||'--' }}</span></div>
            </div>
            <div v-if="currentTab!=='utilization'" class="ea-info">
              <span class="ea-tt">{{ currentTab==='temp_plate'?'临牌到期':'借用到期' }}</span>
              <span>{{ (currentTab==='temp_plate'?v.temp_plate_expire_date:v.borrow_expire_date)||'--' }}</span>
              <NTag :type="v.days<0?'error':v.days<=7?'warning':'success'" size="tiny" :bordered="false" round>{{ v.label }}</NTag>
            </div>
            <div v-else class="ea-info">
              <span class="ea-tt">利用率</span>
              <span>{{ v.rate.toFixed(1) }}%</span>
              <NTag :type="v.rate<=10?'error':v.rate<50?'warning':'success'" size="tiny" :bordered="false" round>{{ v.label }}</NTag>
            </div>
            <div class="ea-days" :style="{color:v.color||'#999'}"><span class="ea-dn">{{ currentTab==='utilization'?v.rate:v.absDays }}</span><span class="ea-du">{{ currentTab==='utilization'?'%':v.days<0?'天已过期':v.days===0?'到期':'天' }}</span></div>
            <div class="ea-pg"><div class="ea-pgf" :style="{width:(currentTab==='utilization'?Math.min(100,v.rate):Math.max(0,100-(v.days/30)*100))+'%',background:v.color||'#ccc'}" /></div>
          </div>
        </div>
      </div>
      <div v-else class="ea-empty">{{ (filterVehicleCode||filterBorrower||filterVn||filterDriver||filterTester)?'无匹配结果':'暂无提醒数据' }}</div>
    </template>

    <template v-if="currentTab==='abnormal'">
      <div v-if="areaMismatchAlerts.length">
        <div class="ea-st">临牌区域不匹配（{{ areaMismatchAlerts.length }} 辆）</div>
        <div class="ea-grid">
          <div v-for="(v,i) in areaMismatchAlerts" :key="i" class="ea-card" style="border-color:#fa8c16"><div class="ea-bar" style="background:#fa8c16" />
            <div class="ea-bd">
              <div class="ea-rows">
                <div class="ea-p"><span class="ea-l">编号</span><span class="ea-v">{{ v.vehicle_code||v.vn||'--' }}</span></div>
                <div class="ea-p"><span class="ea-l">车型</span><span class="ea-v">{{ v.vehicle_model||'--' }}</span></div>
                <div class="ea-p"><span class="ea-l">驾驶</span><span class="ea-v">{{ v.driver||'--' }}</span></div>
                <div class="ea-p"><span class="ea-l">测试</span><span class="ea-v">{{ v.tester||'--' }}</span></div>
                <div class="ea-p"><span class="ea-l">借车人</span><span class="ea-v">{{ v.borrower||'--' }}</span></div>
                <div class="ea-p"><span class="ea-l">VIN</span><span class="ea-v">{{ v.vn||'--' }}</span></div>
              </div>
              <div class="ea-info"><span class="ea-tt">试验城市</span><span>{{ v.test_city||'--' }}</span></div>
              <div class="ea-info"><span class="ea-tt">临牌区域</span><span style="word-break:break-all">{{ v.temp_plate_area||v.insurance_area||'--' }}</span></div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="faultAlerts.length">
        <div class="ea-st ea-st-red">故障或事故车辆（{{ faultAlerts.length }} 辆）</div>
        <div class="ea-grid">
          <div v-for="(v,i) in faultAlerts" :key="i" class="ea-card" style="border-color:#d03050"><div class="ea-bar" style="background:#d03050" />
            <div class="ea-bd">
              <div class="ea-rows">
                <div class="ea-p"><span class="ea-l">编号</span><span class="ea-v">{{ v.vehicle_code||v.vn||'--' }}</span></div>
                <div class="ea-p"><span class="ea-l">车型</span><span class="ea-v">{{ v.vehicle_model||'--' }}</span></div>
                <div class="ea-p"><span class="ea-l">驾驶</span><span class="ea-v">{{ v.driver||'--' }}</span></div>
                <div class="ea-p"><span class="ea-l">测试</span><span class="ea-v">{{ v.tester||'--' }}</span></div>
                <div class="ea-p"><span class="ea-l">借车人</span><span class="ea-v">{{ v.borrower||'--' }}</span></div>
                <div class="ea-p"><span class="ea-l">VIN</span><span class="ea-v">{{ v.vn||'--' }}</span></div>
              </div>
              <div class="ea-info"><span class="ea-tt">异常</span><span>{{ v.test_task||'--' }}</span><NTag type="error" size="tiny" :bordered="false" round>{{ v.task_status||'故障或事故' }}</NTag></div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="!areaMismatchAlerts.length&&!faultAlerts.length" class="ea-empty">{{ (filterVehicleCode||filterBorrower||filterVn||filterDriver||filterTester)?'无匹配结果':'暂无异常报警' }}</div>
    </template>

    <template v-if="currentTab==='idle'">
      <div v-if="idleAlerts.length" class="ea-grid">
        <div v-for="(v,i) in idleAlerts" :key="i" class="ea-card" style="border-color:#f0a020"><div class="ea-bar" style="background:#f0a020" />
          <div class="ea-bd">
            <div class="ea-rows">
              <div class="ea-p"><span class="ea-l">编号</span><span class="ea-v">{{ v.vehicle_code||v.vn||'--' }}</span></div>
              <div class="ea-p"><span class="ea-l">车型</span><span class="ea-v">{{ v.vehicle_model||'--' }}</span></div>
              <div class="ea-p"><span class="ea-l">驾驶</span><span class="ea-v">{{ v.driver||'--' }}</span></div>
              <div class="ea-p"><span class="ea-l">测试</span><span class="ea-v">{{ v.tester||'--' }}</span></div>
              <div class="ea-p"><span class="ea-l">借车人</span><span class="ea-v">{{ v.borrower||'--' }}</span></div>
              <div class="ea-p"><span class="ea-l">VIN</span><span class="ea-v">{{ v.vn||'--' }}</span></div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="ea-empty">{{ (filterVehicleCode||filterBorrower||filterVn||filterDriver||filterTester)?'无匹配结果':'暂无空置车辆' }}</div>
    </template>

  </NSpin>
  </div>
</div>
</template>

<style scoped>
.ea-root { height:100%; display:flex; flex-direction:column; overflow:hidden; padding:12px 16px; }
.ea-topbar { display:flex; align-items:center; gap:10px; padding:8px 0 6px; flex-shrink:0; }
.ea-tabs-bar { display:flex; align-items:center; padding:0 0 8px; flex-shrink:0; }
.ea-rate-inline { display:flex; align-items:center; gap:8px; margin-left:auto; flex-shrink:0; }
.ea-rate-label { font-size:12px; color:#666; font-weight:500; }
.ea-r-item { font-size:12px; padding:3px 10px; border-radius:6px; font-weight:600; }
.r-low { background:#FFF1F0; color:#FF4D4F; } .r-mid { background:#FFF7E6; color:#FA8C16; }
.r-high { background:#F6FFED; color:#52C41A; } .r-total { background:#F5F5F5; color:#333; }

.ea-tabs { display:flex; gap:2px; flex-shrink:0; }
.ea-tab { display:flex; align-items:center; gap:5px; padding:7px 16px; border-radius:6px 6px 0 0; cursor:pointer; font-size:13px; font-weight:500; color:#7a8599; white-space:nowrap; border-bottom:2px solid transparent; transition: all 0.15s; }
.ea-tab:hover { color:#2080f0; background:#f0f6ff; }
.ea-tab.on { color:#2080f0; background:#f0f6ff; border-bottom-color:#2080f0; font-weight:600; }
.ea-tn { min-width:20px; height:20px; padding:0 6px; border-radius:10px; font-size:12px; font-weight:700; display:inline-flex; align-items:center; justify-content:center; }
.tn-danger { background:#fff0f0; color:#d03050; } .tn-ok { background:#edf7ed; color:#18a058; }

.ea-body { flex:1; min-height:0; overflow-y:auto; }
.ea-body :deep(.n-spin-container) { overflow:visible!important; }

.ea-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:10px; }
.ea-card { display:flex; background:#fff; border-radius:10px; border:1.5px solid #e0e0e0; overflow:hidden; }
.ea-bar { width:4px; flex-shrink:0; }
.ea-bd { flex:1; padding:10px 8px 10px 12px; display:flex; flex-direction:column; gap:6px; min-width:0; }
.ea-rows { display:flex; flex-direction:column; gap:4px; }
.ea-p { display:flex; align-items:center; gap:6px; }
.ea-l { font-size:11px; color:#1a1a2e; font-weight:700; min-width:40px; flex-shrink:0; }
.ea-v { font-size:13px; color:#333; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ea-info { display:flex; align-items:center; gap:4px; font-size:12px; color:#555; }
.ea-tt { font-size:12px; color:#1a1a2e; font-weight:700; }
.ea-days { display:flex; align-items:baseline; gap:2px; }
.ea-dn { font-size:26px; font-weight:800; line-height:1; }
.ea-du { font-size:11px; font-weight:600; }
.ea-pg { height:4px; background:#f0f0f0; border-radius:2px; overflow:hidden; }
.ea-pgf { height:100%; border-radius:2px; }
.ea-st { font-size:13px; font-weight:600; color:#fa8c16; margin:14px 0 10px; }
.ea-st-red { color:#d03050; }
.ea-empty { text-align:center; padding:30px 0; color:#999; font-size:11px; }
</style>
