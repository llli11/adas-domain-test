import axios from 'axios'
import { request } from '@/utils'
import { getToken } from '@/utils'

const downloadRequest = axios.create({
  baseURL: import.meta.env.VITE_BASE_API,
  timeout: 30000,
})
downloadRequest.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.token = token
  return config
})

export default {
  // ==================== 看板统计 ====================
  getExpenseDashboardStats: (params = {}) => request.get('/expense/dashboard/stats', { params }),
  getExpenseDashboardTrend: (params = {}) => request.get('/expense/dashboard/trend', { params }),

  // ==================== 预算预警 ====================
  getBudgetAlertList: (params = {}) => request.get('/expense/alert/list', { params }),

  // ==================== 供应商单价 ====================
  getSupplierRateList: (params = {}) => request.get('/expense/supplier/list', { params }),
  createSupplierRate: (data = {}) => request.post('/expense/supplier/create', data),
  updateSupplierRate: (params = {}, data = {}) => request.post('/expense/supplier/update', data, { params }),
  deleteSupplierRate: (params = {}) => request.delete('/expense/supplier/delete', { params }),

  // ==================== 项目 ====================
  getExpenseProjectList: (params = {}) => request.get('/expense/project/list', { params }),
  createExpenseProject: (data = {}) => request.post('/expense/project/create', data),
  updateExpenseProject: (params = {}, data = {}) => request.post('/expense/project/update', data, { params }),
  deleteExpenseProject: (params = {}) => request.delete('/expense/project/delete', { params }),

  // ==================== 预算号 ====================
  getBudgetCodeList: (params = {}) => request.get('/expense/budget-code/list', { params }),
  createBudgetCode: (data = {}) => request.post('/expense/budget-code/create', data),
  updateBudgetCode: (params = {}, data = {}) => request.post('/expense/budget-code/update', data, { params }),
  deleteBudgetCode: (params = {}) => request.delete('/expense/budget-code/delete', { params }),

  // ==================== 费用号 ====================
  getExpenseCodeList: (params = {}) => request.get('/expense/expense-code/list', { params }),
  createExpenseCode: (data = {}) => request.post('/expense/expense-code/create', data),
  updateExpenseCode: (params = {}, data = {}) => request.post('/expense/expense-code/update', data, { params }),
  deleteExpenseCode: (params = {}) => request.delete('/expense/expense-code/delete', { params }),

  // ==================== 试验单号 ====================
  getTestOrderList: (params = {}) => request.get('/expense/test-order/list', { params }),
  getTestOrderDetail: (params = {}) => request.get('/expense/test-order/detail', { params }),
  createTestOrder: (data = {}) => request.post('/expense/test-order/create', data),
  updateTestOrder: (params = {}, data = {}) => request.post('/expense/test-order/update', data, { params }),
  deleteTestOrder: (params = {}) => request.delete('/expense/test-order/delete', { params }),

  // ==================== 每日费用记录 ====================
  getDailyRecordList: (params = {}) => request.get('/expense/daily-record/list', { params }),
  getFeishuDailyRecord: (params = {}) => request.get('/expense/feishu-daily-record', { params, timeout: 60000 }),
  syncDailyRecords: () => request.post('/expense/daily-record/sync'),
  createDailyRecord: (data = {}) => request.post('/expense/daily-record/create', data),
  updateDailyRecord: (params = {}, data = {}) => request.post('/expense/daily-record/update', data, { params }),
  deleteDailyRecord: (params = {}) => request.delete('/expense/daily-record/delete', { params }),
  importDailyRecord: (data = {}) => request.post('/expense/daily-record/import', data),

  // ==================== 月度结算 ====================
  // 工程师结算
  getEngineerAttendanceQuery: (params = {}) => request.get('/settlement/engineer/query', { params }),
  exportEngineerSettlement: (params = {}) => downloadRequest.get('/settlement/engineer/export', { params, responseType: 'blob' }),
  getMonthlySettlementList: (params = {}) => request.get('/settlement/engineer/list', { params }),
  generateMonthlySettlement: (params = {}) => request.post('/settlement/engineer/generate', {}, { params }),
  updateMonthlySettlement: (params = {}, data = {}) => request.post('/settlement/engineer/update', data, { params }),
  // 驾驶员结算
  getDriverMonthlySettlement: (params = {}) => request.get('/settlement/driver/query', { params }),
  exportDriverSettlement: (params = {}) => downloadRequest.get('/settlement/driver/export', { params, responseType: 'blob' }),

  // 费用确认
  getCostConfirmation: (params = {}) => request.get('/settlement/confirmation/query', { params }),
  updateCostConfirmation: (params = {}) => request.post('/settlement/confirmation/update', null, { params }),

  // ==================== 工程师/驾驶员考勤 ====================
  getEngineerAttendanceList: (params = {}) => request.get('/expense/engineer-attendance/list', { params }),
  createEngineerAttendance: (data = {}) => request.post('/expense/engineer-attendance/create', data),
  updateEngineerAttendance: (params = {}, data = {}) => request.post('/expense/engineer-attendance/update', data, { params }),
  deleteEngineerAttendance: (params = {}) => request.delete('/expense/engineer-attendance/delete', { params }),
  getDriverAttendanceList: (params = {}) => request.get('/expense/driver-attendance/list', { params }),
  createDriverAttendance: (data = {}) => request.post('/expense/driver-attendance/create', data),
  updateDriverAttendance: (params = {}, data = {}) => request.post('/expense/driver-attendance/update', data, { params }),
  deleteDriverAttendance: (params = {}) => request.delete('/expense/driver-attendance/delete', { params }),

  // ==================== 审批待办 ====================
  getPendingApprovalList: (params = {}) => request.get('/expense/pending-approval/list', { params }),
  approveRecord: (params = {}) => request.post('/expense/pending-approval/approve', null, { params }),
  rejectRecord: (params = {}) => request.post('/expense/pending-approval/reject', null, { params }),

  // ==================== 人员绑定 ====================
  getRequirementPersonnelList: (params = {}) => request.get('/expense/requirement-personnel/list', { params }),
  createRequirementPersonnel: (data = {}) => request.post('/expense/requirement-personnel/create', data),
  updateRequirementPersonnel: (params = {}, data = {}) => request.post('/expense/requirement-personnel/update', data, { params }),
  deleteRequirementPersonnel: (params = {}) => request.delete('/expense/requirement-personnel/delete', { params }),



  // ==================== 飞书实时查询（直连飞书 API） ====================
  getFeishuEngineerLog: (params = {}) => request.get('/expense/feishu-engineer-log', { params, timeout: 60000 }),
  getFeishuDriverLog: (params = {}) => request.get('/expense/feishu-driver-log', { params, timeout: 60000 }),

  // ==================== 飞书同步 ====================
  syncFromFeishu: (params = {}) => request.post('/expense/feishu-sync', null, { params, timeout: 600000 }),
  syncPersonnelFromFeishu: () => request.post('/expense/feishu-sync-personnel', {}, { timeout: 600000 }),
  syncAutoFromFeishu: () => request.post('/expense/feishu-auto-sync', {}, { timeout: 600000 }),
  getAutoSyncStatus: () => request.get('/expense/feishu-auto-sync/status'),
  syncExpenseCodeFromFeishu: () => request.post('/expense/feishu-sync-expense-code', {}, { timeout: 120000 }),
  syncTestOrderFromFeishu: () => request.post('/expense/feishu-sync-test-order', {}, { timeout: 120000 }),
  syncFeishuEngineer: () => request.post('/expense/feishu-sync/engineer', {}, { timeout: 600000 }),
  syncFeishuDriver: () => request.post('/expense/feishu-sync/driver', {}, { timeout: 600000 }),
  syncFeishuAll: () => request.post('/expense/feishu-sync/all', {}, { timeout: 600000 }),
}
