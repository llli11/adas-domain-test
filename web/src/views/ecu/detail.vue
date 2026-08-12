<script setup>
import { h, onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NCard,
  NDescriptions,
  NDescriptionsItem,
  NSpin,
  NEmpty,
  NButton,
  NPopconfirm,
  NModal,
  NSelect,
  NDataTable,
  NUpload,
  NInput,
  NTag,
  NDivider,
} from 'naive-ui'
import * as XLSX from 'xlsx'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { useUserStore } from '@/store'

defineOptions({ name: 'ECU详情' })

const ECU_DESC_MAP = {
  ACU: '安全气囊控制器',
  AMP: '外置功放',
  AMP2: '外置功放2',
  AR_HUD: '抬头显示',
  ARP_RL: '后左扶手屏',
  ARP_RR: '后右扶手屏',
  BMS_宁德_BEV10A: '电池管理系统',
  BMS_宁德_PHEV06B: '电池管理系统',
  CDC: '华为影音娱乐系统',
  CMCS: '吸顶屏',
  DCU_FL: '门模块-左前',
  DCU_FR: '门模块-右前',
  DCU_RL: '门模块-左后',
  DCU_RR: '门模块-右后',
  DG: '调光玻璃控制器',
  DKC: '数字钥匙控制器',
  CRF: '冰箱',
  EFP: '电动踏板模块',
  EIL_Logo: '外部指示灯_LOGO',
  EMS: '发动机控制器系统',
  EOPF_EV: '前电机冷却电子油泵软件_EV',
  EOPF_PHEV: '前电机冷却电子油泵软件_PHEV',
  EOPR_EV: '后电子泵软件_EV',
  EOPR_PHEV: '后电子泵软件_PHEV',
  EPB_L_EV: '左电子驻车制动系统_EV',
  EPB_L_PHEV: '左电子驻车制动系统_PHEV',
  EPB_R_EV: '右电子驻车制动系统_EV',
  EPB_R_PHEV: '右电子驻车制动系统_PHEV',
  EPS_EV: '电动助力转向系统_EV',
  EPS_L3: '电动助力转向系统_L3',
  EPS_PHEV: '电动助力转向系统_PHEV',
  ETC: '不停车收费模块',
  FCU: '前行李箱控制模块',
  GL: '前保氛围灯',
  HCM_L1: '左侧大灯模块（高配）',
  HCM_R1: '右侧大灯模块（高配）',
  HSG: '电动压缩机&水加热PTC二合一',
  IC: '仪表屏',
  IL_AD: '智驾状态指示灯',
  IPB_EV: '集成制动控制',
  IPB_L3: '集成制动控制_L3',
  IPB_PHEV: '集成制动控制',
  ISC: '集成悬架控制器（ASC +CDC）',
  ITL: '前顶灯',
  KK: '敲击传感器',
  LBMS: '蓄电池管理模块',
  MCUF_EV: '前电机控制器_EV',
  MCUF_PHEV: '前电机控制器_PHEV',
  MCUR_EV: '后电机控制器_EV',
  MCUR_PHEV: '后电机控制器_PHEV',
  MDC_L3: '智能驾驶域控制单元_L3',
  OBC: '车载充电机',
  ODRC: '避障物检测雷达控制器',
  PNG: '智能电网管理模块',
  POD_FL: '电开门模块-左前',
  POD_FR: '电开门模块-右前',
  POD_RL: '电开门模块-左后',
  POD_RR: '电开门模块-右后',
  POT: '电动尾门模块',
  PS: '副驾屏',
  RBU_L3: '冗余制动控制单元',
  RLLM_Fix: '左后灯光模块-固定侧',
  RLM_Move: '后部灯光模块-移动侧',
  RLS: '雨量光照传感器',
  RRLM_Fix: '右后灯光模块-固定侧',
  RSB_D: '主驾侧可逆式安全带',
  RWS_域磐: '后轮转向控制器_域磐',
  SCCS: '中控屏',
  'SCCS/CS': '中控屏',
  SCURL: '二排左座椅控制器(大四座）',
  SCURR: '二排右座椅控制器(零重力）',
  SCUTR: '座椅控制器-第三排',
  SWM: '转向柱开关总成',
  SWS_L3: '方向盘开关',
  SWS: '方向盘开关',
  T_BOX_L3: '车联网终端_L3',
  TMCF: '前部热管理控制器',
  VCM: '整车控制模块',
  VIU_ML: '座舱左区域控制器',
  VIU_MR: '座舱右区域控制器',
  WCM_FL: '无线充电模块左 NFC',
  WCM_FR: '无线充电模块右',
  WSM_FL1: '按摩模块_左前（腰托）_高配',
  WSM_FR: '按摩模块_右前（腰托）',
  WSM_RL1: '按摩模块_左后（腰托）_高配',
  WSM_RR1: '按摩模块_右后（腰托）_高配',
  WSM2_FL: '按摩模块_左前（座垫）',
  WSM2_FR: '按摩模块_右前（座垫）',
  WSM2_RL: '按摩模块_左后（座垫）',
  WSM2_RR: '按摩模块_右后（座垫）',
}

function getEcuDesc(name) {
  return ECU_DESC_MAP[name] ? `（${ECU_DESC_MAP[name]}）` : ''
}

const userStore = useUserStore()

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const ecuDetail = ref(null)
const remark = ref('')

const compareModalVisible = ref(false)
const targetList = ref([])
const selectedTarget = ref(null)
const targetLoading = ref(false)
const baselineData = ref(null)
const summaryModalVisible = ref(false)
const pendingModalVisible = ref(false)

const historyModalVisible = ref(false)
const historyList = ref([])
const selectedHistory = ref(null)
const historyLoading = ref(false)
const isCurrentVersion = ref(true)

const updateModalVisible = ref(false)
const updateLoading = ref(false)
const updateFile = ref(null)

const onlineUpdateLoading = ref(false)
const onlineUpdateResult = ref(null)
const onlineUpdateConfirmVisible = ref(false)
const onlineUpdateConfirmLoading = ref(false)

const possibleMatchPage = ref({})

const ignoredEcuNames = ref([])

const baselineSelectMap = ref({})  // { ecuName: selectedBaselineName }

function openUpdateModal() {
  updateModalVisible.value = true
  updateFile.value = null
}

function handleUpdateFileChange(options) {
  updateFile.value = { file: options.file.file }
}

function handleUpdate() {
  if (!updateFile.value) {
    window.$message?.warning('请选择HTML文件')
    return
  }
  const vin = route.params.vin
  updateLoading.value = true
  const formData = new FormData()
  formData.append('vin', vin)
  formData.append('file', updateFile.value.file)
api
    .updateECU(formData)
    .then(() => {
      window.$message?.success('更新成功')
      updateModalVisible.value = false
      loadDetail()
      api.addOperationLog({
        operation_type: '更新车辆',
        target_vin: route.params.vin,
        operator: userStore.name || 'system',
      })
    })
    .catch((err) => {
      window.$message?.error(err.message || '更新失败')
    })
    .finally(() => {
      updateLoading.value = false
    })
}

function handleOnlineUpdate() {
  const vin = route.params.vin
  onlineUpdateLoading.value = true
  api
    .onlineUpdateECU(vin)
    .then((res) => {
      updateModalVisible.value = false
      onlineUpdateResult.value = res.data
      onlineUpdateConfirmVisible.value = true
    })
    .catch((err) => {
      window.$message?.error(err.message || '在线更新请求失败')
    })
    .finally(() => {
      onlineUpdateLoading.value = false
    })
}

function handleOnlineUpdateConfirm() {
  if (!onlineUpdateResult.value) return
  const vin = route.params.vin
  onlineUpdateConfirmLoading.value = true
  api
    .confirmOnlineUpdateECU(vin, {
      ecu_data: onlineUpdateResult.value.converted_ecu_data,
      latest_ota_time: onlineUpdateResult.value.latest_ota_time,
    })
    .then(() => {
      window.$message?.success('在线更新成功')
      onlineUpdateConfirmVisible.value = false
      onlineUpdateResult.value = null
      loadDetail()
      api.addOperationLog({
        operation_type: '在线更新',
        target_vin: route.params.vin,
        operator: userStore.name || 'system',
      })
    })
    .catch((err) => {
      window.$message?.error(err.message || '在线更新确认失败')
    })
    .finally(() => {
      onlineUpdateConfirmLoading.value = false
    })
}

function handleOnlineUpdateCancel() {
  onlineUpdateConfirmVisible.value = false
  onlineUpdateResult.value = null
}

function openHistoryModal() {
  historyModalVisible.value = true
  selectedHistory.value = null
  loadHistory()
}

function loadHistory() {
  historyLoading.value = true
  const vin = route.params.vin
  api
    .getECUHistory(vin)
    .then((res) => {
      const historyOptions = (res.data || []).map((item, index) => ({
        label: index === 0 ? formatTime(item.created_at) : formatTime(item.modified_at || item.created_at),
        value: item.id,
      }))
      historyList.value = [{ label: '当前版本', value: 'current' }, ...historyOptions]
    })
    .catch(() => {
      historyList.value = [{ label: '当前版本', value: 'current' }]
    })
    .finally(() => {
      historyLoading.value = false
    })
}

function handleRestore() {
  if (!selectedHistory.value) return
  const vin = route.params.vin
  historyLoading.value = true
  if (selectedHistory.value === 'current') {
    loadDetail()
    isCurrentVersion.value = true
    historyModalVisible.value = false
    window.$message?.success('已切换到当前版本')
    historyLoading.value = false
    return
  }
  api
    .getECUHistoryDetail(vin, selectedHistory.value)
    .then((res) => {
      ecuDetail.value = res.data
      isCurrentVersion.value = false
      historyModalVisible.value = false
      window.$message?.success('已切换到历史版本')
    })
    .catch((err) => {
      window.$message?.error(err.message || '获取历史版本失败')
    })
    .finally(() => {
      historyLoading.value = false
    })
}

function loadTargetList() {
  targetLoading.value = true
  api
    .getTargetList({})
    .then((res) => {
      targetList.value = (res.data || []).map((item) => ({
        label: item.target_name,
        value: item.target_name,
      }))
    })
    .catch(() => {
      targetList.value = []
    })
    .finally(() => {
      targetLoading.value = false
    })
}

function openCompareModal() {
  compareModalVisible.value = true
  selectedTarget.value = null
  loadTargetList()
}

function handleCompare() {
  if (!selectedTarget.value) return

  targetLoading.value = true
  api
    .getTargetDetail(selectedTarget.value)
    .then((res) => {
      baselineData.value = res.data
      possibleMatchPage.value = {}
      compareModalVisible.value = false
      api.addOperationLog({
        operation_type: '对比基线',
        target_vin: route.params.vin,
        target_name: selectedTarget.value,
        operator: userStore.name || 'system',
      })
    })
    .catch(() => {
      window.$message?.error('获取基线数据失败')
    })
    .finally(() => {
      targetLoading.value = false
    })
}

function clearCompare() {
  baselineData.value = null
  summaryModalVisible.value = false
  pendingModalVisible.value = false
  possibleMatchPage.value = {}
}

function currentPage(key) {
  return possibleMatchPage.value[key] ?? 0
}

function goToPage(key, idx) {
  possibleMatchPage.value = { ...possibleMatchPage.value, [key]: idx }
}

function loadIgnoreList() {
  const vin = route.params.vin
  api.getECUIgnoreList(vin).then((res) => {
    ignoredEcuNames.value = (res.data || []).map((item) => item.ecu_name)
  }).catch(() => {})
}

function loadBaselineSelectList() {
  const vin = route.params.vin
  api.getBaselineSelectList(vin).then((res) => {
    const map = {}
    for (const item of (res.data || [])) {
      map[item.ecu_name] = item.selected_baseline_name
    }
    baselineSelectMap.value = map
  }).catch(() => {})
}

function handleSelectBaseline(ecuName, baselineName) {
  const vin = route.params.vin
  api.selectBaseline(vin, { ecu_name: ecuName, baseline_name: baselineName }).then(() => {
    baselineSelectMap.value = { ...baselineSelectMap.value, [ecuName]: baselineName }
    window.$message?.success('已选定基线版本')
  }).catch((err) => {
    window.$message?.error(err.message || '选定失败')
  })
}

function handleDeselectBaseline(ecuName) {
  const vin = route.params.vin
  api.deselectBaseline(vin, { ecu_name: ecuName }).then(() => {
    const newMap = { ...baselineSelectMap.value }
    delete newMap[ecuName]
    baselineSelectMap.value = newMap
    window.$message?.success('已取消选定')
  }).catch((err) => {
    window.$message?.error(err.message || '取消选定失败')
  })
}

function handleIgnoreECU(ecuName) {
  const vin = route.params.vin
  api.ignoreECU(vin, { ecu_name: ecuName }).then(() => {
    ignoredEcuNames.value.push(ecuName)
    window.$message?.success('已忽略')
  }).catch((err) => {
    window.$message?.error(err.message || '忽略失败')
  })
}

function handleRestoreECU(ecuName) {
  const vin = route.params.vin
  api.restoreECUIgnore(vin, { ecu_name: ecuName }).then(() => {
    ignoredEcuNames.value = ignoredEcuNames.value.filter((n) => n !== ecuName)
    window.$message?.success('已恢复')
  }).catch((err) => {
    window.$message?.error(err.message || '恢复失败')
  })
}

function handleResetAll() {
  const vin = route.params.vin
  Promise.all([
    api.resetECUIgnore(vin),
    api.resetBaselineSelect(vin),
  ]).then(() => {
    ignoredEcuNames.value = []
    baselineSelectMap.value = {}
    window.$message?.success('已重置所有')
  }).catch((err) => {
    window.$message?.error(err.message || '重置失败')
  })
}

const hasAnySelection = computed(() => {
  return ignoredEcuNames.value.length > 0 || Object.keys(baselineSelectMap.value).length > 0
})

function formatTime(t) {
  if (!t) return '-'
  const s = String(t)
  return s.length > 19 ? s.slice(0, 19) : s
}

function getSummarySortKey(reason) {
  if (reason === '零件号不一致') return 0
  if (reason === '基线中有可能相关的版本需要人工确认') return 1
  if (reason === '落后') return 2
  if (reason === '一致') return 3
  if (reason === '超前') return 4
  if (reason === '离线') return 5
  if (reason === '忽略') return 6
  if (reason === '基线中有，车辆中未检测到') return 7
  return 8
}

const allSummaryTableData = computed(() => {
  const data = []
  const results = compareResults.value
  const swDid = getDidForDescription('VOYAH SoftwareVersion')
  for (const [ecuName, result] of Object.entries(results)) {
    const ecuItem = ecuInfo.value[ecuName]
    const displayReason = result.reason === '本地无响应' ? '离线' : result.reason
    // 离线且无基线软件版本的不显示
    if (result.reason === '本地无响应' && !result.baselineVersion) continue
    data.push({
      ecu: ecuName,
      currentVersion: ecuItem?.[swDid] || '',
      baselineVersion: result.baselineVersion,
      result: displayReason,
      _sortKey: getSummarySortKey(displayReason),
    })
  }
  for (const pair of filteredPairedEcuList.value) {
    if (pair.ecuName) continue
    if (!pair.baseline) continue
    const baselineVersion = pair.baseline.item[swDid] || ''
    data.push({
      ecu: pair.baseline.name,
      currentVersion: '',
      baselineVersion,
      result: '基线中有，车辆中未检测到',
      _sortKey: getSummarySortKey('基线中有，车辆中未检测到'),
    })
  }
  data.sort((a, b) => a._sortKey - b._sortKey)
  return data
})

const pendingTableData = computed(() => {
  const data = []
  const results = compareResults.value
  for (const [ecuName, result] of Object.entries(results)) {
    if (result.reason === '一致' || result.reason === '超前' || result.reason === '忽略') continue
    if (result.reason === '本地无响应') continue
    const swDid = getDidForDescription('VOYAH SoftwareVersion')
    const ecuItem = ecuInfo.value[ecuName]
    const displayReason = result.reason === '本地无响应' ? '离线' : result.reason
    data.push({
      ecu: ecuName,
      currentVersion: ecuItem?.[swDid] || '',
      baselineVersion: result.baselineVersion,
      result: displayReason,
      _sortKey: getSummarySortKey(displayReason),
    })
  }
  data.sort((a, b) => a._sortKey - b._sortKey)
  return data
})

function openSummaryModal() {
  summaryModalVisible.value = true
}

function openPendingModal() {
  pendingModalVisible.value = true
}

const softwarePkgState = ref({})  // { ecuKey: { status: 'idle'|'found'|'notfound', downloadUrl: '', version: '' } }

async function querySoftwarePackage(ecu, version) {
  const key = ecu
  softwarePkgState.value = { ...softwarePkgState.value, [key]: { status: 'loading', downloadUrl: '', version } }
  try {
    const res = await fetch('https://xuanwu-test.voyah.cn/mgapi/fm-alm/software/info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ package_version: version }),
    })
    const json = await res.json()
    if (json.code === 200 && json.data?.download_url) {
      softwarePkgState.value = { ...softwarePkgState.value, [key]: { status: 'found', downloadUrl: json.data.download_url, version } }
      api.addOperationLog({
        operation_type: '软件包查询',
        target_vin: route.params.vin,
        target_name: version,
        operator: userStore.name || 'system',
      })
    } else {
      softwarePkgState.value = { ...softwarePkgState.value, [key]: { status: 'notfound', downloadUrl: '', version } }
    }
  } catch {
    softwarePkgState.value = { ...softwarePkgState.value, [key]: { status: 'notfound', downloadUrl: '', version } }
  }
}

function downloadPackage(url, version) {
  api.addOperationLog({
    operation_type: '软件包下载',
    target_vin: route.params.vin,
    target_name: version,
    operator: userStore.name || 'system',
  })
  window.open(url, '_blank')
}

const summaryColumns = [
  { title: 'ECU', key: 'ecu' },
  { title: '当前ECU软件版本', key: 'currentVersion' },
  { title: '基线软件版本', key: 'baselineVersion' },
  { title: '软件版本对比结果', key: 'result' },
]

const pendingColumns = [
  { title: 'ECU', key: 'ecu' },
  { title: '当前ECU软件版本', key: 'currentVersion' },
  { title: '基线软件版本', key: 'baselineVersion' },
  { title: '软件版本对比结果', key: 'result' },
  {
    title: '软件包下载',
    key: 'softwarePkg',
    width: 180,
    render: (row) => {
      const state = softwarePkgState.value[row.ecu]
      const version = row.baselineVersion
      if (!version) return h('span', { style: 'color: #999; font-size: 12px' }, '-')
      if (!state) {
        return h('a', {
          style: 'color: #18a058; cursor: pointer; font-size: 13px',
          onClick: () => querySoftwarePackage(row.ecu, version),
        }, '在玄武平台查询')
      }
      if (state.status === 'loading') {
        return h('span', { style: 'color: #999; font-size: 12px' }, '查询中...')
      }
      if (state.status === 'found') {
        return h('a', {
          style: 'color: #18a058; cursor: pointer; font-size: 13px; text-decoration: underline',
          onClick: () => downloadPackage(state.downloadUrl, state.version),
        }, version)
      }
      return h('span', { style: 'color: #999; font-size: 12px' }, '未查询到该软件包')
    },
  },
]

const onlineUpdateConfirmColumns = [
  { title: 'ECU名称', key: 'ecu_name', width: 120, ellipsis: { tooltip: true } },
  { title: '当前版本时间', key: 'current_db_time', width: 180 },
  { title: '当前版本', key: 'current_version', width: 190, ellipsis: { tooltip: true } },
  { title: 'OTA更新时间', key: 'ota_update_time', width: 180 },
  { title: 'OTA版本', key: 'ota_version', width: 190, ellipsis: { tooltip: true } },
]

const onlineUpdateSkipColumns = [
  { title: 'ECU名称', key: 'ecu_name', width: 120, ellipsis: { tooltip: true } },
  { title: '当前版本时间', key: 'current_db_time', width: 180 },
  { title: '当前版本', key: 'current_version', width: 190, ellipsis: { tooltip: true } },
  { title: 'OTA更新时间', key: 'ota_update_time', width: 180 },
  { title: 'OTA版本', key: 'ota_version', width: 190, ellipsis: { tooltip: true } },
]

const ecuInfo = computed(() => {
  if (!ecuDetail.value?.ecu_info) return {}
  const { _did_map, ...ecus } = ecuDetail.value.ecu_info
  return ecus
})

const didMap = computed(() => {
  if (!ecuDetail.value?.ecu_info?._did_map) return {}
  return ecuDetail.value.ecu_info._did_map
})

const ecuList = computed(() => {
  return Object.keys(ecuInfo.value)
})

const noResponseValues = ['无响应或否定响应', 'ECU Offline', 'ECU 离线', '无响应']

const getDidForDescription = (desc) => {
  const map = didMap.value
  for (const [did, description] of Object.entries(map)) {
    if (description === desc) return did
  }
  return desc
}

const normalizeEcuName = (name) => name?.replace(/\([^)]*\)/g, '').replace(/[-_]/g, '') || ''

const pairedEcuList = computed(() => {
  const list = []
  if (!baselineData.value?.ecu_info) return list

  const baselineEcuInfo = baselineData.value.ecu_info
  const usedBaseline = new Set()

  const byPartNumber = {}
  const swDid = getDidForDescription('VOYAH SoftwareVersion')
  for (const [name, item] of Object.entries(baselineEcuInfo)) {
    if (name === '_did_map') continue
    const v = item[swDid]
    if (v) {
      const pn = v.slice(0, 11)
      ;(byPartNumber[pn] ||= []).push({ name, item })
    }
  }

  for (const [ecuName, ecuItem] of Object.entries(ecuInfo.value)) {
    const v = ecuItem[swDid]
    let baseline = null

    if (v) {
      const pn = v.slice(0, 11)
      const candidates = byPartNumber[pn] || []
      for (const c of candidates) {
        if (!usedBaseline.has(c.name)) {
          baseline = c
          usedBaseline.add(c.name)
          break
        }
      }
    }

    if (!baseline) {
      const nn = normalizeEcuName(ecuName)
      for (const [name, item] of Object.entries(baselineEcuInfo)) {
        if (name === '_did_map') continue
        if (!usedBaseline.has(name) && normalizeEcuName(name) === nn) {
          baseline = { name, item }
          usedBaseline.add(name)
          break
        }
      }
    }

    if (!baseline) {
      const nn = normalizeEcuName(ecuName)
      const possibleBaselines = []
      for (const [name, item] of Object.entries(baselineEcuInfo)) {
        if (name === '_did_map') continue
        if (!usedBaseline.has(name)) {
          const normalizedBaseName = normalizeEcuName(name)
          if (normalizedBaseName.includes(nn)) {
            possibleBaselines.push({ name, item })
            usedBaseline.add(name)
          }
        }
      }
      list.push({
        key: ecuName,
        ecuName,
        ecuItem,
        baseline: null,
        possibleBaselines: possibleBaselines.length > 0 ? possibleBaselines : null,
      })
    } else {
      list.push({
        key: ecuName,
        ecuName,
        ecuItem,
        baseline,
        possibleBaselines: null,
      })
    }
  }

  for (const [name, item] of Object.entries(baselineEcuInfo)) {
    if (name === '_did_map') continue
    if (!usedBaseline.has(name)) {
      list.push({ key: name, ecuName: null, ecuItem: null, baseline: { name, item } })
    }
  }

  return list
})

const filteredPairedEcuList = computed(() => {
  return pairedEcuList.value.filter(pair => !pair.ecuName || !ignoredEcuNames.value.includes(pair.ecuName))
})

const compareResults = computed(() => {
  const results = {}
  if (!baselineData.value?.ecu_info) return results

  const swDid = getDidForDescription('VOYAH SoftwareVersion')

  for (const pair of pairedEcuList.value) {
    const { ecuName, ecuItem, baseline, possibleBaselines } = pair
    if (!ecuName) continue

    // 忽略状态的 ECU 标记为"忽略"
    if (ignoredEcuNames.value.includes(ecuName)) {
      const selectedBaselineName = baselineSelectMap.value[ecuName]
      let selectedVersion = ''
      if (selectedBaselineName && baselineData.value?.ecu_info) {
        const selectedItem = baselineData.value.ecu_info[selectedBaselineName]
        selectedVersion = selectedItem ? (selectedItem[swDid] || '') : ''
      }
      const matchedVersion = baseline ? baseline.item[swDid] : (possibleBaselines?.[0]?.item?.[swDid] || '')
      results[ecuName] = { color: 'gray', baselineVersion: selectedVersion || matchedVersion, reason: '忽略' }
      continue
    }

    const vehicleVersion = ecuItem[swDid]

    // 自身有选定的基线版本
    const selectedBaselineName = baselineSelectMap.value[ecuName]
    let selectedBaselineItem = null
    if (selectedBaselineName && baselineData.value?.ecu_info) {
      selectedBaselineItem = baselineData.value.ecu_info[selectedBaselineName]
    }

    if (noResponseValues.includes(vehicleVersion)) {
      const baselineVersion = selectedBaselineItem
        ? selectedBaselineItem[swDid]
        : (baseline ? baseline.item[swDid] : (possibleBaselines?.[0]?.item?.[swDid] || ''))
      results[ecuName] = { color: 'gray', baselineVersion, reason: '本地无响应' }
      continue
    }

    // 如果有选定基线，用它来对比
    if (selectedBaselineItem) {
      const baselineVersion = selectedBaselineItem[swDid]
      if (vehicleVersion && baselineVersion) {
        const vehiclePartNumber = vehicleVersion.slice(0, 11)
        const baselinePartNumber = baselineVersion.slice(0, 11)
        if (vehiclePartNumber !== baselinePartNumber) {
          results[ecuName] = { color: 'red', baselineVersion, reason: '零件号不一致' }
          continue
        }
        const vehicleLast2 = vehicleVersion.slice(-2)
        const baselineLast2 = baselineVersion.slice(-2)
        const getIndex = (str) => {
          const first = str.charCodeAt(0) - 65
          const second = str.charCodeAt(1) - 65
          return first * 26 + second
        }
        const vehicleIndex = getIndex(vehicleLast2)
        const baselineIndex = getIndex(baselineLast2)
        if (vehicleIndex < baselineIndex) {
          results[ecuName] = { color: 'red', baselineVersion, reason: '落后' }
        } else if (vehicleIndex === baselineIndex) {
          results[ecuName] = { color: 'green', baselineVersion, reason: '一致' }
        } else {
          results[ecuName] = { color: 'yellow', baselineVersion, reason: '超前' }
        }
        continue
      }
    }

    if (!baseline && possibleBaselines && possibleBaselines.length > 0) {
      results[ecuName] = { color: 'red', baselineVersion: '', reason: '基线中有可能相关的版本需要人工确认' }
      continue
    }

    if (!baseline) continue

    const baselineEcuItem = baseline.item
    const baselineVersion = baselineEcuItem[swDid]

    if (!vehicleVersion || !baselineVersion) continue

    const vehiclePartNumber = vehicleVersion.slice(0, 11)
    const baselinePartNumber = baselineVersion.slice(0, 11)

    if (vehiclePartNumber !== baselinePartNumber) {
      results[ecuName] = { color: 'red', baselineVersion, reason: '零件号不一致' }
      continue
    }

    const vehicleLast2 = vehicleVersion.slice(-2)
    const baselineLast2 = baselineVersion.slice(-2)

    const getIndex = (str) => {
      const first = str.charCodeAt(0) - 65
      const second = str.charCodeAt(1) - 65
      return first * 26 + second
    }

    const vehicleIndex = getIndex(vehicleLast2)
    const baselineIndex = getIndex(baselineLast2)

    if (vehicleIndex < baselineIndex) {
      results[ecuName] = { color: 'red', baselineVersion, reason: '落后' }
    } else if (vehicleIndex === baselineIndex) {
      results[ecuName] = { color: 'green', baselineVersion, reason: '一致' }
    } else {
      results[ecuName] = { color: 'yellow', baselineVersion, reason: '超前' }
    }
  }
  return results
})

function loadDetail() {
  const vin = route.params.vin
  if (!vin) {
    router.push('/ecu')
    return
  }

  loading.value = true
  api
    .getECUDetail(vin)
    .then((res) => {
      ecuDetail.value = res.data
      remark.value = res.data?.remark || ''
      loadIgnoreList()
      loadBaselineSelectList()
    })
    .catch(() => {
      ecuDetail.value = null
    })
    .finally(() => {
      loading.value = false
    })
}

function handleRemarkBlur() {
  const vin = route.params.vin
  api.updateECURemark(vin, { remark: remark.value }).catch((err) => {
    window.$message?.error(err.message || '备注保存失败')
  })
}

function goBack() {
  router.push('/ecu')
}

function deleteVehicle() {
  const vin = route.params.vin
  api
    .deleteECU(vin)
    .then(() => {
      window.$message?.success('删除成功')
      router.push('/ecu')
      api.addOperationLog({
        operation_type: '删除车辆',
        target_vin: vin,
        operator: userStore.name || 'system',
      })
    })
    .catch((err) => {
      window.$message?.error(err.message || '删除失败')
    })
}

function downloadBaselineTemplate() {
  if (!ecuDetail.value?.ecu_info) {
    window.$message?.warning('没有ECU数据可导出')
    return
  }

  const workbook = XLSX.utils.book_new()
  const sheetName = '基线版本ECU'
  const worksheet = XLSX.utils.aoa_to_sheet([])

  const allHeaders = new Set(['ECU名'])
  for (const ecuItem of Object.values(ecuInfo.value)) {
    for (const key of Object.keys(ecuItem)) {
      allHeaders.add(didMap.value[key] || key)
    }
  }
  const headers = Array.from(allHeaders)

  const revDidMap = {}
  for (const [did, desc] of Object.entries(didMap.value)) {
    revDidMap[desc] = did
  }
  const data = [headers]
  for (const [ecuName, ecuItem] of Object.entries(ecuInfo.value)) {
    const row = headers.map((h) => {
      if (h === 'ECU名') return ecuName
      const did = revDidMap[h] || h
      return ecuItem[did] || ''
    })
    data.push(row)
  }

  XLSX.utils.sheet_add_aoa(worksheet, data, { origin: 'A1' })

  for (let i = 0; i < headers.length; i++) {
    worksheet['!cols'] = worksheet['!cols'] || []
    worksheet['!cols'][i] = { wch: 25 }
  }

  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName)

  const fileName = `基线模板_${route.params.vin}.xlsx`
  XLSX.writeFile(workbook, fileName)
  window.$message?.success('下载成功')
}

onMounted(() => {
  loadDetail()
})
</script>

<template>
  <div class="ecu-detail-page">
    <NCard :bordered="false" class="detail-card">
      <template #header>
        <div class="header">
          <NButton text @click="goBack">
            <TheIcon icon="arrow-left" :size="20" class="mr-5" />
            返回
          </NButton>
          <span class="title">ECU详情 - {{ route.params.vin }}</span>
          <div class="header-actions">
            <NButton v-if="baselineData" quaternary @click="clearCompare">
              <TheIcon icon="material-symbols:close" :size="16" class="mr-5" />
              清除对比
            </NButton>
            <NButton
              v-if="baselineData"
              quaternary
              type="info"
              @click="openSummaryModal"
            >
              <TheIcon icon="material-symbols:summarize" :size="16" class="mr-5" />
              汇总结果
            </NButton>
            <NButton
              v-if="baselineData"
              quaternary
              type="warning"
              @click="openPendingModal"
            >
              <TheIcon icon="material-symbols:pending-actions" :size="16" class="mr-5" />
              等待处理
            </NButton>
            <NButton type="primary" quaternary @click="openCompareModal">
              <TheIcon icon="material-symbols:compare-arrows" :size="16" class="mr-5" />
              对比基线
            </NButton>
            <NButton v-if="hasAnySelection" quaternary type="warning" @click="handleResetAll">
              <TheIcon icon="material-symbols:restart-alt" :size="16" class="mr-5" />
              重置所有
            </NButton>
            <NButton quaternary type="success" @click="downloadBaselineTemplate">
              <TheIcon icon="material-symbols:download" :size="16" class="mr-5" />
              下载基线模板
            </NButton>
            <NButton quaternary @click="openHistoryModal">
              <TheIcon icon="material-symbols:history" :size="18" />
            </NButton>
            <NButton quaternary type="warning" @click="openUpdateModal">
              <TheIcon icon="material-symbols:refresh" :size="18" />
            </NButton>
            <NPopconfirm @positive-click="deleteVehicle">
              <template #trigger>
                <NButton quaternary type="error">
                  <TheIcon icon="material-symbols:delete-outline" :size="18" />
                </NButton>
              </template>
              确定要删除该车辆吗？此操作不可恢复。
            </NPopconfirm>
          </div>
        </div>
      </template>

      <NSpin :show="loading">
        <template v-if="ecuDetail">
          <NCard title="数据详情" size="small" style="margin-bottom: 16px">
            <div class="info-tags">
              <div class="info-tag-item">
                <span class="tag-label">VIN</span>
                <span class="tag-value">{{ ecuDetail.vin }}</span>
              </div>
              <div class="info-tag-item">
                <span class="tag-label">车型</span>
                <span class="tag-value">{{ ecuDetail.vehicle_model || '-' }}</span>
              </div>
              <div class="info-tag-item">
                <span class="tag-label">编号</span>
                <span class="tag-value">{{ ecuDetail.vehicle_no || '-' }}</span>
              </div>
              <div class="info-tag-item">
                <span class="tag-label">使用人</span>
                <span class="tag-value">{{ ecuDetail.user_name || '-' }}</span>
              </div>
              <div class="info-tag-item">
                <span class="tag-label">创建时间</span>
                <span class="tag-value">{{ formatTime(ecuDetail.created_at) }}</span>
              </div>
              <div class="info-tag-item">
                <span class="tag-label">更新时间</span>
                <span class="tag-value">{{ isCurrentVersion ? formatTime(ecuDetail.updated_at) : '-' }}</span>
              </div>
              <div class="info-tag-item">
                <span class="tag-label">修改时间</span>
                <span class="tag-value">{{ isCurrentVersion ? formatTime(ecuDetail.modified_at) : '-' }}</span>
              </div>
              <div class="info-tag-item">
                <span class="tag-label">数据来源</span>
                <span class="tag-value">{{ ecuDetail.data_source || '-' }}</span>
              </div>
            </div>
          </NCard>

          <NCard title="备注信息" size="small" style="margin-bottom: 16px">
            <NInput
              v-model:value="remark"
              type="textarea"
              placeholder="请输入备注信息"
              :rows="3"
              @blur="handleRemarkBlur"
            />
          </NCard>

          <template v-if="baselineData">
            <div class="compare-layout">
              <div class="compare-header-row">
                <div class="compare-header-cell">车辆ECU</div>
                <div class="compare-header-cell">基线ECU ({{ baselineData.target_name || baselineData.name || '' }})</div>
              </div>
              <div v-for="pair in filteredPairedEcuList" :key="pair.key" class="compare-row">
                <div class="compare-row-cell">
                  <NCard
                    v-if="pair.ecuName"
                    size="small"
                    class="ecu-card"
                    :class="{
                      red: compareResults[pair.ecuName]?.color === 'red' && (!pair.possibleBaselines || pair.possibleBaselines.length === 0),
                      green: compareResults[pair.ecuName]?.color === 'green',
                      yellow: compareResults[pair.ecuName]?.color === 'yellow',
                      gray: compareResults[pair.ecuName]?.color === 'gray',
                      'possible-match': !pair.baseline && pair.possibleBaselines && pair.possibleBaselines.length > 0,
                      ignored: ignoredEcuNames.includes(pair.ecuName),
                    }"
                  >
                    <template #header>
                      <span :class="{ 'line-through': ignoredEcuNames.includes(pair.ecuName) }">{{ pair.ecuName }}{{ getEcuDesc(pair.ecuName) }}</span>
                    </template>
                    <template #header-extra>
                      <NButton v-if="ignoredEcuNames.includes(pair.ecuName)" size="tiny" @click.stop="handleRestoreECU(pair.ecuName)">恢复</NButton>
                      <NButton v-else size="tiny" @click.stop="handleIgnoreECU(pair.ecuName)">忽略</NButton>
                    </template>
                    <div class="ecu-info-list">
                      <div v-for="(value, key) in pair.ecuItem" :key="key" class="info-item">
                        <span class="info-label">{{ didMap[key] || key }}</span>
                        <span class="info-value">
                          {{ value || '-' }}
                          <template v-if="key === getDidForDescription('VOYAH SoftwareVersion') && compareResults[pair.ecuName]">
                            <span class="compare-info">
                              <template v-if="compareResults[pair.ecuName].baselineVersion">
                                (基线: {{ compareResults[pair.ecuName].baselineVersion }} -
                                {{ compareResults[pair.ecuName].reason }})
                              </template>
                              <template v-else>
                                ({{ compareResults[pair.ecuName].reason }})
                              </template>
                            </span>
                          </template>
                        </span>
                      </div>
                      <div v-if="!pair.baseline && (!pair.possibleBaselines || pair.possibleBaselines.length === 0)" class="info-item">
                        <span class="info-label">匹配状态</span>
                        <span class="info-value unmatched">基线中未匹配到该ECU</span>
                      </div>
                    </div>
                  </NCard>
                </div>
                <div class="compare-row-cell">
                  <template v-if="pair.baseline">
                    <NCard
                      size="small"
                      class="ecu-card"
                      :class="pair.ecuName ? {
                        red: compareResults[pair.ecuName]?.color === 'red',
                        green: compareResults[pair.ecuName]?.color === 'green',
                        yellow: compareResults[pair.ecuName]?.color === 'yellow',
                        gray: compareResults[pair.ecuName]?.color === 'gray',
                      } : {}"
                    >
                      <template #header>{{ pair.baseline.name }}{{ getEcuDesc(pair.baseline.name) }}</template>
                      <div class="ecu-info-list">
                        <div v-for="(value, key) in pair.baseline.item" :key="key" class="info-item">
                          <span class="info-label">{{ didMap[key] || key }}</span>
                          <span class="info-value">{{ value || '-' }}</span>
                        </div>
                        <div v-if="!pair.ecuName" class="info-item">
                          <span class="info-label">匹配状态</span>
                          <span class="info-value unmatched">基线中有，车辆中未检测到</span>
                        </div>
                      </div>
                    </NCard>
                  </template>
                  <template v-else-if="pair.possibleBaselines && pair.possibleBaselines.length > 0">
                    <div class="possible-baseline-wrapper">
                      <div class="possible-baseline-item">
                        <NCard
                          size="small"
                          class="ecu-card possible-match"
                          :class="{
                            selected: baselineSelectMap[pair.ecuName] === pair.possibleBaselines[currentPage(pair.key)].name,
                          }"
                        >
                          <template #header>
                            <span>{{ pair.possibleBaselines[currentPage(pair.key)].name }}{{ getEcuDesc(pair.possibleBaselines[currentPage(pair.key)].name) }}</span>
                            <span v-if="baselineSelectMap[pair.ecuName] === pair.possibleBaselines[currentPage(pair.key)].name" class="selected-tag">已选定</span>
                          </template>
                          <template #header-extra>
                            <NButton
                              v-if="baselineSelectMap[pair.ecuName] === pair.possibleBaselines[currentPage(pair.key)].name"
                              size="tiny"
                              type="warning"
                              @click.stop="handleDeselectBaseline(pair.ecuName)"
                            >取消选定</NButton>
                            <NButton
                              v-else
                              size="tiny"
                              type="primary"
                              @click.stop="handleSelectBaseline(pair.ecuName, pair.possibleBaselines[currentPage(pair.key)].name)"
                            >选定</NButton>
                          </template>
                          <div class="ecu-info-list">
                            <div v-for="(value, key) in pair.possibleBaselines[currentPage(pair.key)].item" :key="key" class="info-item">
                              <span class="info-label">{{ didMap[key] || key }}</span>
                              <span class="info-value">{{ value || '-' }}</span>
                            </div>
                            <div class="info-item">
                              <span class="info-label">匹配状态</span>
                              <span class="info-value unmatched">基线中有可能相关的版本需要人工确认</span>
                            </div>
                          </div>
                        </NCard>
                        <div class="possible-match-nav">
                          <div
                            v-for="(pb, idx) in pair.possibleBaselines"
                            :key="'dot-' + idx"
                            class="nav-dot"
                            :class="{ active: currentPage(pair.key) === idx }"
                            @click="goToPage(pair.key, idx)"
                          />
                        </div>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="ecu-sections">
            <div v-for="ecuName in ecuList" :key="ecuName" class="ecu-section">
              <NCard
                size="small"
                class="ecu-card"
                :class="{
                  red: compareResults[ecuName]?.color === 'red',
                  green: compareResults[ecuName]?.color === 'green',
                  yellow: compareResults[ecuName]?.color === 'yellow',
                  gray: compareResults[ecuName]?.color === 'gray',
                  ignored: ignoredEcuNames.includes(ecuName),
                }"
              >
                <template #header>
                  <span :class="{ 'line-through': ignoredEcuNames.includes(ecuName) }">{{ ecuName }}{{ getEcuDesc(ecuName) }}</span>
                </template>
                <template #header-extra>
                  <NButton v-if="ignoredEcuNames.includes(ecuName)" size="tiny" @click.stop="handleRestoreECU(ecuName)">恢复</NButton>
                  <NButton v-else size="tiny" @click.stop="handleIgnoreECU(ecuName)">忽略</NButton>
                </template>
                <div class="ecu-info-list">
                  <div v-for="(value, key) in ecuInfo[ecuName]" :key="key" class="info-item">
                    <span class="info-label">{{ didMap[key] || key }}</span>
                    <span class="info-value">
                      {{ value || '-' }}
                      <template
                        v-if="key === getDidForDescription('VOYAH SoftwareVersion') && compareResults[ecuName]"
                      >
                        <span class="compare-info">
                          (基线: {{ compareResults[ecuName].baselineVersion }} -
                          {{ compareResults[ecuName].reason }})
                        </span>
                      </template>
                    </span>
                  </div>
                </div>
              </NCard>
            </div>
          </div>
        </template>
        <NEmpty v-else-if="!loading" description="未找到数据" />
      </NSpin>
    </NCard>

    <NModal
      v-model:show="compareModalVisible"
      preset="card"
      title="选择基线版本"
      style="width: 400px; z-index: 1001"
      :mask-closable="true"
    >
      <div style="margin-bottom: 16px">
        <div style="margin-bottom: 8px; color: #666; font-size: 14px">基线版本</div>
        <NSelect
          v-model:value="selectedTarget"
          :options="targetList"
          filterable
          placeholder="搜索或选择基线版本"
          :loading="targetLoading"
          clearable
        />
      </div>
      <template #footer>
        <div style="display: flex; justify-content: flex-end">
          <NButton @click="compareModalVisible = false">取消</NButton>
          <NButton
            type="primary"
            style="margin-left: 12px"
            :loading="targetLoading"
            :disabled="!selectedTarget"
            @click="handleCompare"
          >
            确定
          </NButton>
        </div>
      </template>
    </NModal>

    <NModal
      v-model:show="summaryModalVisible"
      preset="card"
      title="汇总结果"
      style="width: 800px; z-index: 1001"
      :mask-closable="true"
    >
      <NDataTable
        :columns="summaryColumns"
        :data="allSummaryTableData"
        :bordered="false"
        size="small"
      />
    </NModal>

    <NModal
      v-model:show="pendingModalVisible"
      preset="card"
      title="等待处理"
      style="width: 900px; z-index: 1001"
      :mask-closable="true"
    >
      <NDataTable
        :columns="pendingColumns"
        :data="pendingTableData"
        :bordered="false"
        size="small"
      />
    </NModal>

    <NModal
      v-model:show="historyModalVisible"
      preset="card"
      title="历史版本"
      style="width: 400px; z-index: 1001"
      :mask-closable="true"
    >
      <div style="margin-bottom: 16px">
        <div style="margin-bottom: 8px; color: #666; font-size: 14px">选择历史版本</div>
        <NSelect
          v-model:value="selectedHistory"
          :options="historyList"
          filterable
          placeholder="选择历史版本"
          :loading="historyLoading"
          clearable
        />
      </div>
      <template #footer>
        <div style="display: flex; justify-content: flex-end">
          <NButton @click="historyModalVisible = false">取消</NButton>
          <NButton
            type="primary"
            style="margin-left: 12px"
            :loading="historyLoading"
            :disabled="!selectedHistory"
            @click="handleRestore"
          >
            确定
          </NButton>
        </div>
      </template>
    </NModal>

    <NModal
      v-model:show="updateModalVisible"
      title="更新ECU信息"
      preset="card"
      style="width: 500px"
      :mask-closable="true"
    >
      <NForm label-placement="left" label-width="80px">
        <NFormItem label="VIN">
          <NInput v-model:value="route.params.vin" disabled />
        </NFormItem>
        <NFormItem label="文件" required>
          <NUpload
            accept=".html,.htm"
            :max="1"
            :custom-request="handleUpdateFileChange"
          >
            <NButton>点击上传HTML文件</NButton>
          </NUpload>
        </NFormItem>
      </NForm>
      <template #footer>
        <div style="display: flex; justify-content: flex-end">
          <NButton type="info" :loading="onlineUpdateLoading" disabled @click="handleOnlineUpdate">在线更新</NButton>
          <NButton style="margin-left: 12px" @click="updateModalVisible = false">取消</NButton>
          <NButton type="primary" style="margin-left: 12px" :loading="updateLoading" @click="handleUpdate">
            确认
          </NButton>
        </div>
      </template>
    </NModal>

    <NModal
      v-model:show="onlineUpdateConfirmVisible"
      title="在线更新确认"
      preset="card"
      style="width: 1100px; z-index: 1001"
      :mask-closable="false"
    >
      <template v-if="onlineUpdateResult">
        <div style="margin-bottom: 16px">
          <div style="display: flex; gap: 16px; margin-bottom: 12px">
            <NTag type="success" size="large">待更新: {{ onlineUpdateResult.total_updated }} 个ECU</NTag>
            <NTag type="default" size="large">已跳过: {{ onlineUpdateResult.total_skipped }} 个ECU</NTag>
          </div>
          <NDivider />
          <div style="font-size: 14px; color: #666; margin-bottom: 8px">
            以下ECU的 OTA_UPDATE_T 晚于数据库记录的更新时间，将被更新：
          </div>
          <NDataTable
            v-if="onlineUpdateResult.updated_ecus.length > 0"
            :columns="onlineUpdateConfirmColumns"
            :data="onlineUpdateResult.updated_ecus"
            :bordered="false"
            size="small"
          />
          <div v-else style="color: #999; padding: 24px 0; text-align: center">没有需要更新的ECU</div>
          <NDivider />
          <div style="font-size: 14px; color: #666; margin-bottom: 8px">
            以下ECU的 OTA_UPDATE_T 早于或等于数据库记录的更新时间，将被跳过：
          </div>
          <NDataTable
            v-if="onlineUpdateResult.skipped_ecus.length > 0"
            :columns="onlineUpdateSkipColumns"
            :data="onlineUpdateResult.skipped_ecus"
            :bordered="false"
            size="small"
          />
          <div style="margin-top: 12px; color: #999; font-size: 13px">
            确认后，updated_at 将更新为: {{ onlineUpdateResult.latest_ota_time || '无' }}
          </div>
          <div style="color: #999; font-size: 13px">
            data_source 将从 "{{ onlineUpdateResult.current_data_source }}" 改为 "ota_online"
          </div>
        </div>
      </template>
      <template #footer>
        <div style="display: flex; justify-content: flex-end">
          <NButton @click="handleOnlineUpdateCancel">取消</NButton>
          <NButton type="primary" style="margin-left: 12px" :loading="onlineUpdateConfirmLoading" @click="handleOnlineUpdateConfirm">
            确认更新
          </NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.ecu-detail-page {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.detail-card {
  min-height: 100%;
}

.info-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.info-tag-item {
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 6px;
  min-width: 120px;
}

.tag-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.tag-value {
  font-size: 14px;
  color: #333;
  word-break: break-all;
}

.header {
  display: flex;
  align-items: center;
  flex: 1;
}

.header-actions {
  margin-left: auto;
}

.title {
  margin-left: 12px;
  font-size: 16px;
  font-weight: 500;
}

.ecu-sections {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.compare-layout {
  margin-top: 16px;
}

.compare-header-row {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.compare-header-cell {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
  padding: 8px 12px;
  background: #f0f0f0;
  border-radius: 6px;
  text-align: center;
}

.compare-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.compare-row-cell {
  flex: 1;
  min-width: 0;
}

.possible-baseline-wrapper {
  display: flex;
}

.possible-baseline-item {
  flex: 1;
  min-width: 0;
}

.possible-match-nav {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
}

.nav-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d9d9d9;
  cursor: pointer;
  transition: background 0.2s;
}

.nav-dot.active {
  background: #1890ff;
}

.nav-dot:hover {
  background: #91d5ff;
}

.ecu-section {
  width: calc(50% - 8px);
}

.ecu-card {
  border-radius: 8px;
}

:deep(.ecu-card.red) {
  background-color: #ffccc7 !important;
}

:deep(.ecu-card.green) {
  background-color: #b7eb8f !important;
}

:deep(.ecu-card.yellow) {
  background-color: #e6f7ff !important;
}

:deep(.ecu-card.gray) {
  background-color: #d9d9d9 !important;
}

:deep(.ecu-card.possible-match) {
  background-color: #fff566 !important;
}

.ecu-info-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  align-items: center;
}

.info-label {
  flex: 0 0 200px;
  color: #666;
  font-size: 13px;
}

.info-value {
  flex: 1;
  color: #333;
  font-size: 13px;
  word-break: break-all;
}

.compare-info {
  margin-left: 8px;
  color: #666;
  font-size: 12px;
}

.info-value.unmatched {
  color: #e74c3c;
  font-weight: 500;
}

.mr-5 {
  margin-right: 5px;
}

:deep(.n-data-table-td) {
  white-space: nowrap !important;
}

.ignored :deep(.n-card-header) {
  opacity: 0.6;
}

.line-through {
  text-decoration: line-through;
}

:deep(.ecu-card.ignored) .info-item {
  text-decoration: line-through;
  opacity: 0.6;
}

.ecu-card.selected {
  border-color: #18a058;
  box-shadow: 0 0 0 1px #18a058;
}

.selected-tag {
  font-size: 12px;
  color: #18a058;
  margin-left: 8px;
  font-weight: 400;
}
</style>
