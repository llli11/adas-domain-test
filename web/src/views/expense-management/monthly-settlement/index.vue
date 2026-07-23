<template>
  <div>
    <n-tabs v-model:value="activeTab" type="line" size="small">
      <n-tab-pane name="driver" tab="驾驶员结算">
        <DriverSettlement />
      </n-tab-pane>
      <n-tab-pane name="engineer" tab="工程师结算">
        <EngineerSettlement />
      </n-tab-pane>
      <n-tab-pane name="confirmation" tab="费用确认">
        <CostConfirmation />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { NTabs, NTabPane } from 'naive-ui'
import DriverSettlement from './DriverSettlement.vue'
import EngineerSettlement from './EngineerSettlement.vue'
import CostConfirmation from './CostConfirmation.vue'

defineOptions({ name: '月度结算' })
const activeTab = ref('driver')
</script>
