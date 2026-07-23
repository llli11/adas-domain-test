<script setup>
import { onMounted, ref, computed } from 'vue'
import {
  NCard,
  NTag,
  NSpin,
  NEmpty,
  useMessage,
} from 'naive-ui'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '异常状态提醒' })

const $message = useMessage()

// 数据状态
const loading = ref(false)
const tempPlateVehicles = ref([])
const borrowVehicles = ref([])
const faultVehicles = ref([])
const areaMismatchVehicles = ref([])
const allVehicles = ref([])

// 当前子 Tab
const currentTab = ref('temp_plate')

// 子 Tab 定义
const subTabs = [
  { key: 'temp_plate', label: '临牌到期', icon: 'material-symbols:card-text' },
  { key: 'borrow', label: '借用到期', icon: 'material-symbols:handshake' },
  { key: 'abnormal', label: '异常报警', icon: 'material-symbols:warning' },
  { key: 'idle', label: '空置车辆', icon: 'material-symbols:time-to-leave' },
]

// ===== 省份 → 城市映射（用于保险区域校验） =====
const PROVINCE_CITY_MAP = {
  '北京': ['北京'],
  '天津': ['天津'],
  '上海': ['上海'],
  '重庆': ['重庆'],
  '河北': ['石家庄', '唐山', '秦皇岛', '邯郸', '邢台', '保定', '张家口', '承德', '沧州', '廊坊', '衡水'],
  '山西': ['太原', '大同', '阳泉', '长治', '晋城', '朔州', '晋中', '运城', '忻州', '临汾', '吕梁'],
  '内蒙古': ['呼和浩特', '包头', '乌海', '赤峰', '通辽', '鄂尔多斯', '呼伦贝尔', '巴彦淖尔', '乌兰察布'],
  '辽宁': ['沈阳', '大连', '鞍山', '抚顺', '本溪', '丹东', '锦州', '营口', '阜新', '辽阳', '盘锦', '铁岭', '朝阳', '葫芦岛'],
  '吉林': ['长春', '吉林', '四平', '辽源', '通化', '白山', '松原', '白城', '延边'],
  '黑龙江': ['哈尔滨', '齐齐哈尔', '鸡西', '鹤岗', '双鸭山', '大庆', '伊春', '佳木斯', '七台河', '牡丹江', '黑河', '绥化'],
  '江苏': ['南京', '无锡', '徐州', '常州', '苏州', '南通', '连云港', '淮安', '盐城', '扬州', '镇江', '泰州', '宿迁'],
  '浙江': ['杭州', '宁波', '温州', '嘉兴', '湖州', '绍兴', '金华', '衢州', '舟山', '台州', '丽水'],
  '安徽': ['合肥', '芜湖', '蚌埠', '淮南', '马鞍山', '淮北', '铜陵', '安庆', '黄山', '滁州', '阜阳', '宿州', '六安', '亳州', '池州', '宣城'],
  '福建': ['福州', '厦门', '莆田', '三明', '泉州', '漳州', '南平', '龙岩', '宁德'],
  '江西': ['南昌', '景德镇', '萍乡', '九江', '新余', '鹰潭', '赣州', '吉安', '宜春', '抚州', '上饶'],
  '山东': ['济南', '青岛', '淄博', '枣庄', '东营', '烟台', '潍坊', '济宁', '泰安', '威海', '日照', '临沂', '德州', '聊城', '滨州', '菏泽'],
  '河南': ['郑州', '开封', '洛阳', '平顶山', '安阳', '鹤壁', '新乡', '焦作', '濮阳', '许昌', '漯河', '三门峡', '南阳', '商丘', '信阳', '周口', '驻马店'],
  '湖北': ['武汉', '黄石', '十堰', '宜昌', '襄阳', '鄂州', '荆门', '孝感', '荆州', '黄冈', '咸宁', '随州', '恩施'],
  '湖南': ['长沙', '株洲', '湘潭', '衡阳', '邵阳', '岳阳', '常德', '张家界', '益阳', '郴州', '永州', '怀化', '娄底', '湘西'],
  '广东': ['广州', '韶关', '深圳', '珠海', '汕头', '佛山', '江门', '湛江', '茂名', '肇庆', '惠州', '梅州', '汕尾', '河源', '阳江', '清远', '东莞', '中山', '潮州', '揭阳', '云浮'],
  '广西': ['南宁', '柳州', '桂林', '梧州', '北海', '防城港', '钦州', '贵港', '玉林', '百色', '贺州', '河池', '来宾', '崇左'],
  '海南': ['海口', '三亚', '三沙', '儋州'],
  '四川': ['成都', '自贡', '攀枝花', '泸州', '德阳', '绵阳', '广元', '遂宁', '内江', '乐山', '南充', '眉山', '宜宾', '广安', '达州', '雅安', '巴中', '资阳'],
  '贵州': ['贵阳', '六盘水', '遵义', '安顺', '毕节', '铜仁', '黔西南', '黔东南', '黔南'],
  '云南': ['昆明', '曲靖', '玉溪', '保山', '昭通', '丽江', '普洱', '临沧', '楚雄', '红河', '文山', '西双版纳', '大理', '德宏', '怒江', '迪庆'],
  '西藏': ['拉萨', '日喀则', '昌都', '林芝', '山南', '那曲', '阿里'],
  '陕西': ['西安', '铜川', '宝鸡', '咸阳', '渭南', '延安', '汉中', '榆林', '安康', '商洛'],
  '甘肃': ['兰州', '嘉峪关', '金昌', '白银', '天水', '武威', '张掖', '平凉', '酒泉', '庆阳', '定西', '陇南', '临夏', '甘南'],
  '青海': ['西宁', '海东', '海北', '黄南', '海南', '果洛', '玉树', '海西'],
  '宁夏': ['银川', '石嘴山', '吴忠', '固原', '中卫'],
  '新疆': ['乌鲁木齐', '克拉玛依', '吐鲁番', '哈密', '昌吉', '博尔塔拉', '巴音郭楞', '阿克苏', '克孜勒苏', '喀什', '和田', '伊犁', '塔城', '阿勒泰'],
}

/** 解析保险区域字符串为省份列表 */
function parseInsuranceProvinces(areaStr) {
  if (!areaStr) return []
  const result = []
  let i = 0
  const known = Object.keys(PROVINCE_CITY_MAP).sort((a, b) => b.length - a.length) // 长名优先
  while (i < areaStr.length) {
    let matched = false
    for (const prov of known) {
      if (areaStr.startsWith(prov, i)) {
        result.push(prov)
        i += prov.length
        matched = true
        break
      }
    }
    if (!matched) i++ // 跳过无法识别的字符
  }
  return result
}

/** 校验试验城市是否在保险省份列表内 */
function isCityInProvinceList(city, provinces) {
  if (!city || provinces.length === 0) return null  // null 表示无法判断
  for (const prov of provinces) {
    const cities = PROVINCE_CITY_MAP[prov]
    if (cities && cities.some(c => city.includes(c) || c.includes(city))) return true
  }
  return false
}

/** 计算保险区域匹配结果 */
function checkInsuranceMatch(vehicle) {
  const provinces = parseInsuranceProvinces(vehicle.insurance_area)
  if (provinces.length === 0) return { matched: null, reason: '无法解析保险区域' }

  // 优先用试验城市
  if (vehicle.test_city) {
    const matched = isCityInProvinceList(vehicle.test_city, provinces)
    if (matched !== null) return { matched, reason: matched ? '匹配' : `城市"${vehicle.test_city}"不在保险区域内` }
  }

  // 用位置信息
  if (vehicle.location_info) {
    const matched = isCityInProvinceList(vehicle.location_info, provinces)
    if (matched !== null) return { matched, reason: matched ? '匹配' : `位置"${vehicle.location_info}"不在保险区域内` }
  }

  return { matched: null, reason: '缺少城市/位置信息，无法判断' }
}

/**
 * 计算到期剩余天数
 */
function getDaysRemaining(expireDate) {
  if (!expireDate) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const expire = new Date(expireDate)
  return Math.ceil((expire.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
}

function getAlertLevel(diff) {
  if (diff === null) return { type: 'default', color: '#ccc', label: '未知', borderColor: '#e0e0e0' }
  if (diff > 14) return { type: 'success', color: '#18a058', label: '正常', borderColor: '#18a058' }
  if (diff >= 7) return { type: 'warning', color: '#f0a020', label: '即将到期', borderColor: '#f0a020' }
  if (diff >= 1) return { type: 'warning', color: '#f97316', label: '马上到期', borderColor: '#f97316' }
  if (diff === 0) return { type: 'error', color: '#d03050', label: '今天到期', borderColor: '#d03050' }
  return { type: 'error', color: '#d03050', label: '已过期', borderColor: '#d03050' }
}

const tempPlateCount = computed(() => tempPlateVehicles.value.length)
const borrowCount = computed(() => borrowVehicles.value.length)
const abnormalCount = computed(() => areaMismatchAlerts.value.length + faultVehicles.value.length)
const idleCount = computed(() => idleVehicles.value.length)

const tempPlateAlerts = computed(() => {
  return tempPlateVehicles.value.map(v => {
    const diff = getDaysRemaining(v.temp_plate_expire_date)
    return { ...v, daysRemaining: diff, alertLevel: getAlertLevel(diff) }
  }).sort((a, b) => (a.daysRemaining ?? 999) - (b.daysRemaining ?? 999))
})

const borrowAlerts = computed(() => {
  return borrowVehicles.value.map(v => {
    const diff = getDaysRemaining(v.borrow_expire_date)
    return { ...v, daysRemaining: diff, alertLevel: getAlertLevel(diff) }
  }).sort((a, b) => (a.daysRemaining ?? 999) - (b.daysRemaining ?? 999))
})

/** 保险区域不匹配的车辆（带校验结果） */
const areaMismatchAlerts = computed(() => {
  return areaMismatchVehicles.value.map(v => {
    const check = checkInsuranceMatch(v)
    return { ...v, matchCheck: check }
  }).filter(v => v.matchCheck.matched === false)
})

/** 空置车辆：临牌和借用均未过期，且无测试人员和驾驶人员 */
const idleVehicles = computed(() => {
  return allVehicles.value.filter(v => {
    const today = new Date(); today.setHours(0, 0, 0, 0)
    const tempExp = v.temp_plate_expire_date ? new Date(v.temp_plate_expire_date) : null
    const borrowExp = v.borrow_expire_date ? new Date(v.borrow_expire_date) : null
    if (tempExp && tempExp <= today) return false
    if (borrowExp && borrowExp <= today) return false
    if (v.tester && v.tester.trim()) return false
    if (v.driver && v.driver.trim()) return false
    return true
  })
})

/**
 * 加载数据
 */
async function fetchAlerts() {
  loading.value = true
  try {
    const [tempRes, borrowRes, faultRes, allVehiclesRes] = await Promise.all([
      api.getExpiringVehicles({ type: 'temp_plate', page: 1, page_size: 200 }),
      api.getExpiringVehicles({ type: 'borrow', page: 1, page_size: 200 }),
      api.getVehicleList({ task_status: '故障或事故', page: 1, page_size: 200 }),
      api.getVehicleList({ page: 1, page_size: 9999 }),
    ])
    tempPlateVehicles.value = tempRes.data || []
    borrowVehicles.value = borrowRes.data || []
    faultVehicles.value = (faultRes.data?.items || faultRes.data || [])

    // 从全量数据中筛选
    const allList = allVehiclesRes.data?.items || allVehiclesRes.data || []
    allVehicles.value = allList
    areaMismatchVehicles.value = allList.filter(v => v.insurance_area)
  } catch (e) {
    console.error('获取提醒数据失败', e)
    $message.error('获取提醒数据失败')
  } finally {
    loading.value = false
  }
}

const currentAlerts = computed(() => {
  if (currentTab.value === 'temp_plate') return tempPlateAlerts.value
  if (currentTab.value === 'borrow') return borrowAlerts.value
  if (currentTab.value === 'idle') return idleVehicles.value
  return []
})

function getRelativeDaysText(days) {
  if (days === null) return '未知'
  if (days > 0) return `剩余 ${days} 天`
  if (days === 0) return '今天到期'
  return `已过期 ${Math.abs(days)} 天`
}

function getDaysTagType(days) {
  if (days === null) return 'default'
  if (days > 14) return 'success'
  if (days >= 7) return 'warning'
  if (days >= 0) return 'warning'
  return 'error'
}

onMounted(() => {
  fetchAlerts()
})
</script>

<template>
  <div class="expiry-alerts-root">
    <!-- 子 Tab 切换 -->
    <div class="sub-tabs">
      <div
        v-for="tab in subTabs"
        :key="tab.key"
        class="sub-tab-item"
        :class="{ active: currentTab === tab.key }"
        @click="currentTab = tab.key"
      >
        <TheIcon :icon="tab.icon" :size="16" />
        <span>{{ tab.label }}</span>
        <span v-if="tab.key === 'temp_plate'" class="tab-badge" :class="tempPlateCount > 0 ? 'badge-danger' : 'badge-ok'">
          {{ tempPlateCount }}
        </span>
        <span v-if="tab.key === 'borrow'" class="tab-badge" :class="borrowCount > 0 ? 'badge-warn' : 'badge-ok'">
          {{ borrowCount }}
        </span>
        <span v-if="tab.key === 'abnormal'" class="tab-badge" :class="abnormalCount > 0 ? 'badge-danger' : 'badge-ok'">
          {{ abnormalCount }}
        </span>
        <span v-if="tab.key === 'idle'" class="tab-badge" :class="idleCount > 0 ? 'badge-warn' : 'badge-ok'">
          {{ idleCount }}
        </span>
      </div>
    </div>

    <NSpin :show="loading" class="wh-full">

      <!-- ===== 临牌到期 / 借用到期 ===== -->
      <template v-if="currentTab === 'temp_plate' || currentTab === 'borrow'">
        <div v-if="currentAlerts.length > 0" class="alert-grid">
          <div
            v-for="alert in currentAlerts"
            :key="alert.id"
            class="alert-card"
            :style="{ borderColor: alert.alertLevel?.borderColor || '#e0e0e0' }"
          >
            <div class="alert-card-bar" :style="{ background: alert.alertLevel?.color || '#ccc' }"></div>
            <div class="alert-card-content">
              <div class="alert-card-header">
                <div class="alert-card-title">
                  <span class="alert-code">{{ alert.vehicle_code || alert.vn || '--' }}</span>
                  <span v-if="alert.vehicle_model" class="alert-model">{{ alert.vehicle_model }}</span>
                </div>
                <NTag :type="getDaysTagType(alert.daysRemaining ?? null)" size="small" :bordered="false" round>
                  {{ getRelativeDaysText(alert.daysRemaining) }}
                </NTag>
              </div>
              <div class="alert-card-info">
                <div class="alert-info-row" v-if="alert.borrower">
                  <TheIcon icon="material-symbols:person" :size="13" />
                  <span>{{ alert.borrower }}</span>
                </div>
                <div class="alert-info-row" v-if="alert.vn">
                  <TheIcon icon="material-symbols:tag" :size="13" />
                  <span>VN: {{ alert.vn }}</span>
                </div>
                <div class="alert-info-row">
                  <TheIcon icon="material-symbols:calendar-today" :size="13" />
                  <span>
                    {{ currentTab === 'temp_plate'
                      ? `临牌到期: ${alert.temp_plate_expire_date || '-'}`
                      : `借用到期: ${alert.borrow_expire_date || '-'}` }}
                  </span>
                </div>
              </div>
              <div class="alert-days" :style="{ color: alert.alertLevel?.color || '#ccc' }">
                <span v-if="alert.daysRemaining !== null" class="days-number">{{ Math.abs(alert.daysRemaining) }}</span>
                <span v-if="alert.daysRemaining !== null" class="days-unit">
                  {{ alert.daysRemaining > 0 ? '天' : alert.daysRemaining === 0 ? '到期' : '天已过期' }}
                </span>
                <span v-else class="days-number">--</span>
              </div>
              <div v-if="alert.daysRemaining !== null" class="alert-progress">
                <div
                  class="alert-progress-fill"
                  :style="{
                    width: alert.daysRemaining < 0 ? '100%' : Math.min(100, Math.max(0, 100 - (alert.daysRemaining / 30) * 100)) + '%',
                    background: alert.alertLevel?.color || '#f0a020',
                  }"
                ></div>
              </div>
            </div>
          </div>
        </div>
        <NEmpty v-else description="暂无到期提醒数据" class="mt-60" />
      </template>

      <!-- ===== 异常报警 ===== -->
      <template v-if="currentTab === 'abnormal'">
        <!-- 保险区域不匹配 -->
        <div v-if="areaMismatchAlerts.length > 0" class="mb-16">
          <div class="section-label">
            <TheIcon icon="material-symbols:location-off" :size="16" class="mr-4" />
            <span>保险区域不匹配（{{ areaMismatchAlerts.length }} 辆）</span>
          </div>
          <div class="alert-grid">
            <div
              v-for="v in areaMismatchAlerts"
              :key="'area-' + v.id"
              class="alert-card fault-card"
              style="border-color: #d03050"
            >
              <div class="alert-card-bar" style="background: #d03050"></div>
              <div class="alert-card-content">
                <div class="alert-card-header">
                  <div class="alert-card-title">
                    <span class="alert-code">{{ v.vehicle_code || v.vn || '--' }}</span>
                    <span v-if="v.vehicle_model" class="alert-model">{{ v.vehicle_model }}</span>
                  </div>
                  <NTag type="error" size="small" :bordered="false" round>区域不匹配</NTag>
                </div>
                <div class="alert-card-info">
                  <div class="alert-info-row">
                    <TheIcon icon="material-symbols:shield" :size="13" />
                    <span>保险: {{ v.insurance_area }}</span>
                  </div>
                  <div class="alert-info-row" v-if="v.test_city">
                    <TheIcon icon="material-symbols:location-on" :size="13" />
                    <span>城市: {{ v.test_city }}</span>
                  </div>
                  <div class="alert-info-row" v-if="v.borrower">
                    <TheIcon icon="material-symbols:person" :size="13" />
                    <span>{{ v.borrower }}</span>
                  </div>
                </div>
                <div class="alert-days" style="color: #d03050">
                  <span class="days-number">!</span>
                  <span class="days-unit">需处理</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 故障/事故车辆 -->
        <div v-if="faultVehicles.length > 0">
          <div class="section-label">
            <TheIcon icon="material-symbols:warning" :size="16" class="mr-4" />
            <span>故障或事故车辆（{{ faultVehicles.length }} 辆）</span>
          </div>
          <div class="alert-grid">
            <div
              v-for="v in faultVehicles"
              :key="'fault-' + v.id"
              class="alert-card fault-card"
              style="border-color: #d03050"
            >
              <div class="alert-card-bar" style="background: #d03050"></div>
              <div class="alert-card-content">
                <div class="alert-card-header">
                  <div class="alert-card-title">
                    <span class="alert-code">{{ v.vehicle_code || v.vn || '--' }}</span>
                    <span v-if="v.vehicle_model" class="alert-model">{{ v.vehicle_model }}</span>
                  </div>
                  <NTag type="error" size="small" :bordered="false" round>{{ v.task_status || '故障' }}</NTag>
                </div>
                <div class="alert-card-info">
                  <div class="alert-info-row" v-if="v.borrower">
                    <TheIcon icon="material-symbols:person" :size="13" />
                    <span>{{ v.borrower }}</span>
                  </div>
                  <div class="alert-info-row" v-if="v.test_city">
                    <TheIcon icon="material-symbols:location-on" :size="13" />
                    <span>{{ v.test_city }}</span>
                  </div>
                  <div class="alert-info-row" v-if="v.test_task">
                    <TheIcon icon="material-symbols:science" :size="13" />
                    <span>{{ v.test_task }}</span>
                  </div>
                  <div class="alert-info-row" v-if="v.tester || v.driver">
                    <TheIcon icon="material-symbols:group" :size="13" />
                    <span>{{ [v.tester, v.driver].filter(Boolean).join(' / ') }}</span>
                  </div>
                </div>
                <div class="alert-days" style="color: #d03050">
                  <span class="days-number">!</span>
                  <span class="days-unit">需处理</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <NEmpty v-if="areaMismatchAlerts.length === 0 && faultVehicles.length === 0" description="暂无异常报警数据" class="mt-60" />
      </template>

      <!-- ===== 空置车辆 ===== -->
      <template v-if="currentTab === 'idle'">
        <div v-if="idleVehicles.length > 0">
          <div class="section-label" style="color: #f0a020">
            <TheIcon icon="material-symbols:time-to-leave" :size="16" class="mr-4" />
            <span>空置车辆（{{ idleVehicles.length }} 辆）— 临牌借用未过期、无测试和驾驶人员</span>
          </div>
          <div class="alert-grid">
            <div
              v-for="v in idleVehicles"
              :key="'idle-' + v.id"
              class="alert-card"
              style="border-color: #f0a020"
            >
              <div class="alert-card-bar" style="background: #f0a020"></div>
              <div class="alert-card-content">
                <div class="alert-card-header">
                  <div class="alert-card-title">
                    <span class="alert-code">{{ v.vehicle_code || v.vn || '--' }}</span>
                    <span v-if="v.vehicle_model" class="alert-model">{{ v.vehicle_model }}</span>
                  </div>
                  <NTag type="warning" size="small" :bordered="false" round>空置</NTag>
                </div>
                <div class="alert-card-info">
                  <div class="alert-info-row" v-if="v.borrower">
                    <TheIcon icon="material-symbols:person" :size="13" />
                    <span>{{ v.borrower }}</span>
                  </div>
                  <div class="alert-info-row" v-if="v.test_city">
                    <TheIcon icon="material-symbols:location-on" :size="13" />
                    <span>{{ v.test_city }}</span>
                  </div>
                </div>
                <div class="alert-days" style="color: #f0a020">
                  <span class="days-number">-</span>
                  <span class="days-unit">空闲</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <NEmpty v-else description="暂无空置车辆" class="mt-60" />
      </template>

    </NSpin>
  </div>
</template>

<style scoped>
.expiry-alerts-root {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sub-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: #f5f6fa;
  border-radius: 10px;
  margin-bottom: 16px;
  width: fit-content;
  flex-shrink: 0;
}

.sub-tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #666;
  transition: all 0.2s;
  white-space: nowrap;
  user-select: none;
}

.sub-tab-item:hover { color: #333; background: #edf0f5; }
.sub-tab-item.active { background: #fff; color: #2080f0; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08); }

.tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 700;
}

.badge-danger { background: #fde8e8; color: #d03050; }
.badge-warn { background: #fef3e6; color: #e6a620; }
.badge-ok { background: #e8f5e9; color: #18a058; }

.alert-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 12px;
  overflow-y: auto;
  flex: 1;
  align-content: start;
}

.alert-card {
  display: flex;
  background: #fff;
  border-radius: 10px;
  border: 1.5px solid #e0e0e0;
  overflow: hidden;
  transition: all 0.2s;
}

.alert-card:hover { box-shadow: 0 3px 12px rgba(0, 0, 0, 0.06); transform: translateY(-1px); }
.alert-card-bar { width: 4px; flex-shrink: 0; }

.alert-card-content {
  flex: 1;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.alert-card-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.alert-card-title { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.alert-code { font-weight: 700; font-size: 14px; color: #333; }
.alert-model { font-size: 12px; color: #999; }

.alert-card-info { display: flex; flex-direction: column; gap: 3px; }
.alert-info-row { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #777; }

.alert-days { display: flex; align-items: baseline; gap: 2px; }
.days-number { font-size: 28px; font-weight: 800; line-height: 1; }
.days-unit { font-size: 12px; font-weight: 600; }

.alert-progress { height: 4px; background: #f0f0f0; border-radius: 2px; overflow: hidden; }
.alert-progress-fill { height: 100%; border-radius: 2px; transition: width 0.4s ease; }

.fault-card { border-color: #d03050 !important; }
.fault-card .alert-card-bar { background: #d03050; }

.section-label {
  display: flex;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: #d03050;
  margin-bottom: 12px;
}

.mb-16 { margin-bottom: 16px; }
.mr-4 { margin-right: 4px; }
.mt-60 { margin-top: 60px; }
.wh-full { height: 100%; }
</style>
