<template>
  <div>
    <n-tabs v-model:value="activeTab" type="line" size="small">
      <n-tab-pane name="expense" tab="费用号看板">
        <ExpenseRateBoard />
      </n-tab-pane>
      <n-tab-pane name="testorder" tab="试验单号看板">
        <TestOrderRateBoard />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { NTabs, NTabPane } from 'naive-ui'
import ExpenseRateBoard from './ExpenseRateBoard.vue'
import TestOrderRateBoard from './TestOrderRateBoard.vue'

defineOptions({ name: '费用概览' })
const activeTab = ref('expense')
</script>
