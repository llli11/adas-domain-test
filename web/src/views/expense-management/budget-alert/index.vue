<template>
  <div style="padding:15px">

    <n-card title="试验需求预警" size="small" style="margin-bottom:12px">
      <n-data-table :columns="toCols" :data="toAlerts" :loading="loading" size="small" :pagination="{pageSize:10}" :scroll-x="820" :max-height="300" />
    </n-card>

    <n-card title="费用号预警" size="small">
      <n-data-table :columns="ecCols" :data="ecAlerts" :loading="loading" size="small" :pagination="{pageSize:10}" :scroll-x="700" :max-height="300" />
    </n-card>
  </div>
</template>

<script setup>
import { ref, onMounted, h, nextTick } from 'vue'
import { NCard, NDataTable, NTag } from 'naive-ui'
import expenseApi from '@/api/expense'

const loading = ref(false)
const loaded = ref(false)
const toAlerts = ref([])
const ecAlerts = ref([])

const toCols = [
  { title:'试验需求编号', key:'code', width:130 },
  { title:'所属项目', key:'name', width:120, ellipsis:{tooltip:true} },
  { title:'关联费用号', key:'expense_code', width:120 },
  { title:'总金额', key:'total', width:100, align:'right', render(r){ return Number(r.total).toFixed(2) }},
  { title:'已用金额', key:'used', width:100, align:'right', render(r){ return Number(r.used).toFixed(2) }},
  { title:'使用率', key:'rate', width:80, align:'center', render(r){ return r.rate+'%' }},
  { title:'负责人', key:'responsible', width:80 },
  { title:'预警等级', key:'level', width:90, align:'center',
    render(r){ return h(NTag,{type:r.level==='严重'?'error':'warning',size:'small'},()=>r.level) }
  },
]

const ecCols = [
  { title:'费用号', key:'code', width:130 },
  { title:'所属项目', key:'name', width:120, ellipsis:{tooltip:true} },
  { title:'负责人', key:'responsible', width:80 },
  { title:'总金额', key:'total', width:100, align:'right', render(r){ return Number(r.total).toFixed(2) }},
  { title:'已用金额', key:'used', width:100, align:'right', render(r){ return Number(r.used).toFixed(2) }},
  { title:'使用率', key:'rate', width:80, align:'center', render(r){ return r.rate+'%' }},
  { title:'预警等级', key:'level', width:90, align:'center',
    render(r){ return h(NTag,{type:r.level==='严重'?'error':'warning',size:'small'},()=>r.level) }
  },
]

onMounted(async () => {
  await nextTick()
  loading.value = true
  try {
    const r = await expenseApi.getBudgetAlertList()
    toAlerts.value = r.data?.test_order_alerts || []
    ecAlerts.value = r.data?.expense_code_alerts || []
    loaded.value = true
  } catch(e) { console.error('Alert load error:', e) } finally { loading.value = false }
})
</script>
