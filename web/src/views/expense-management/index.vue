<template>
  <div class="expense-mgmt">
    <n-card title="费用管理" size="small">
      <n-tabs v-model:value="activeTab" type="line">
        <n-tab-pane name="dashboard" tab="费用概览">
          <Dashboard />
        </n-tab-pane>
        <n-tab-pane name="daily-record" tab="每日记录">
          <DailyRecord />
        </n-tab-pane>
        <n-tab-pane name="monthly-settlement" tab="月度结算">
          <MonthlySettlement />
        </n-tab-pane>
        <n-tab-pane name="budget-alert" tab="预算预警">
          <BudgetAlert />
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { NCard, NTabs, NTabPane } from 'naive-ui'
import Dashboard from './dashboard/index.vue'
import DailyRecord from './daily-record/index.vue'
import MonthlySettlement from './monthly-settlement/index.vue'
import BudgetAlert from './budget-alert/index.vue'

defineOptions({ name: '费用管理' })
const activeTab = ref('dashboard')
</script>
