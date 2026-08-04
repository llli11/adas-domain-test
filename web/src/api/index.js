import { request } from '@/utils'

export default {
  login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  // users
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  // role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // menus
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),
  // apis
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),
  // depts
  getDepts: (params = {}) => request.get('/dept/list', { params }),
  createDept: (data = {}) => request.post('/dept/create', data),
  updateDept: (data = {}) => request.post('/dept/update', data),
  deleteDept: (params = {}) => request.delete('/dept/delete', { params }),
  // auditlog
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),
  // ==================== contractor staff =============
  getContractorStaffList: (params = {}) => request.get('/contractor/staff/list', { params }),
  getContractorStaffById: (params = {}) => request.get('/contractor/staff/get', { params }),
  createContractorStaff: (data = {}) => request.post('/contractor/staff/create', data),
  updateContractorStaff: (data = {}) => request.post('/contractor/staff/update', data),
  deleteContractorStaff: (params = {}) => request.delete('/contractor/staff/delete', { params }),
  resignContractorStaff: (data = {}) => request.post('/contractor/staff/resign', data),
  getContractorStaffDashboard: (params = {}) => request.get('/contractor/staff/dashboard', { params }),
  generateContractorStaffQRToken: (data = {}) => request.post('/contractor/staff/qr_token', data),
  // ==================== contractor requirement ====================
  getContractorRequirementList: (params = {}) => request.get('/contractor/requirement/list', { params }),
  createContractorRequirement: (data = {}) => request.post('/contractor/requirement/create', data),
  updateContractorRequirement: (data = {}) => request.post('/contractor/requirement/update', data),
  deleteContractorRequirement: (params = {}) => request.delete('/contractor/requirement/delete', { params }),
  approveContractorRequirement: (data = {}) => request.post('/contractor/requirement/approve', data),
  // ==================== contractor transfer ====================
  getContractorTransferList: (params = {}) => request.get('/contractor/transfer/list', { params }),
  createContractorTransfer: (data = {}) => request.post('/contractor/transfer/apply', data),
  updateContractorTransfer: (data = {}) => request.post('/contractor/transfer/update', data),
  deleteContractorTransfer: (params = {}) => request.delete('/contractor/transfer/delete', { params }),
  confirmContractorTransfer: (data = {}) => request.post('/contractor/transfer/confirm', data),
  // ==================== contractor vehicle status ====================
  getContractorVehicleStatusList: (params = {}) => request.get('/contractor/vehicle_status/list', { params }),
  // ==================== contractor work log ====================
  getContractorWorkLogList: (params = {}) => request.get('/contractor/worklog/list', { params }),
  createContractorWorkLog: (data = {}) => request.post('/contractor/worklog/create', data),
  updateContractorWorkLog: (data = {}) => request.post('/contractor/worklog/update', data),
  deleteContractorWorkLog: (params = {}) => request.delete('/contractor/worklog/delete', { params }),
  confirmContractorWorkLog: (data = {}) => request.post('/contractor/worklog/confirm', data),
  batchNotifyContractorWorkLog: (data = {}) => request.post('/contractor/worklog/batch_notify', data),
  // ==================== contractor leave ====================
  getContractorLeaveList: (params = {}) => request.get('/contractor/leave/list', { params }),
  createContractorLeave: (data = {}) => request.post('/contractor/leave/create', data),
  updateContractorLeave: (data = {}) => request.post('/contractor/leave/update', data),
  deleteContractorLeave: (params = {}) => request.delete('/contractor/leave/delete', { params }),
  approveContractorLeave: (data = {}) => request.post('/contractor/leave/approve', data),
  // ==================== contractor evaluation ====================
  getContractorEvaluationList: (params = {}) => request.get('/contractor/evaluation/list', { params }),
  rateContractorEvaluation: (data = {}) => request.post('/contractor/evaluation/rate', data),
  generateContractorEvaluation: (data = {}) => request.post('/contractor/evaluation/generate', data),
  updateContractorEvaluation: (data = {}) => request.post('/contractor/evaluation/update', data),
  deleteContractorEvaluation: (params = {}) => request.delete('/contractor/evaluation/delete', { params }),
  // ==================== contractor QR (public) ====================
  getContractorQRInfo: (params = {}) => request.get('/contractor/qr/info', { params, noNeedToken: true }),
  submitContractorQRDepart: (data = {}) => request.post('/contractor/qr/depart', data, { noNeedToken: true }),
  submitContractorQRReturn: (data = {}) => request.post('/contractor/qr/return', data, { noNeedToken: true }),
  submitContractorQRWorkLog: (data = {}) => request.post('/contractor/qr/worklog', data, { noNeedToken: true }),
  submitContractorQRLeave: (data = {}) => request.post('/contractor/qr/leave', data, { noNeedToken: true }),
  // ==================== contractor attendance/performance/resignation (legacy) ====================
  getContractorAttendanceList: (params = {}) => request.get('/contractor/attendance/list', { params }),
  createContractorAttendance: (data = {}) => request.post('/contractor/attendance/create', data),
  batchContractorAttendance: (data = {}) => request.post('/contractor/attendance/batch', data),
  updateContractorAttendance: (data = {}) => request.post('/contractor/attendance/update', data),
  deleteContractorAttendance: (params = {}) => request.delete('/contractor/attendance/delete', { params }),
  getContractorPerformanceList: (params = {}) => request.get('/contractor/performance/list', { params }),
  createContractorPerformance: (data = {}) => request.post('/contractor/performance/create', data),
  updateContractorPerformance: (data = {}) => request.post('/contractor/performance/update', data),
  deleteContractorPerformance: (params = {}) => request.delete('/contractor/performance/delete', { params }),
  getContractorResignationList: (params = {}) => request.get('/contractor/resignation/list', { params }),
  createContractorResignation: (data = {}) => request.post('/contractor/resignation/create', data),
  approveContractorResignation: (data = {}) => request.post('/contractor/resignation/approve', data),
  updateContractorResignation: (data = {}) => request.post('/contractor/resignation/update', data),
  deleteContractorResignation: (params = {}) => request.delete('/contractor/resignation/delete', { params }),
    // vehicles
  getVehicleList: (params = {}) => request.get('/vehicle/list', { params }),
  getVehicleById: (params = {}) => request.get('/vehicle/get', { params }),
  getVehicleByVn: (params = {}) => request.get('/vehicle/by-vn', { params }),
  createVehicle: (data = {}) => request.post('/vehicle/create', data),
  updateVehicle: (data = {}) => request.post('/vehicle/update', data),
  deleteVehicle: (params = {}) => request.delete('/vehicle/delete', { params }),
  batchDeleteVehicles: (ids = []) => request.delete('/vehicle/batch-delete', { data: { ids } }),
  getFieldValues: (params = {}) => request.get('/vehicle/field-values', { params }),
  upsertVehicle: (data = {}) => request.post('/vehicle/upsert', data),
  getExpiringVehicles: (params = {}) => request.get('/vehicle/alerts/expiring', { params }),
  getStatusMap: (params = {}) => request.get('/vehicle/status-map', { params }),
  syncFromFeishu: (data = {}) => request.post('/vehicle/sync/feishu', data),
  getSyncStatus: () => request.get('/vehicle/sync/feishu/status'),
  reverseGeocode: (lat, lng) => request.get('/vehicle/reverse-geocode', { params: { lat, lng } }),
  configFeishu: (data = {}) => request.post('/vehicle/sync/feishu/config', data),
  healthCheckFeishu: () => request.get('/vehicle/sync/feishu/health'),
  importCsv: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return request.post('/vehicle/import/csv', formData)
    },
  downloadCsvTemplate: () => request.get('/vehicle/import/template', { responseType: 'blob' }),
  // 用户飞书配置
  saveFeishuConfig: (data = {}) => request.post('/vehicle/sync/feishu/config/save', data),
  getFeishuConfig: (params = {}) => request.get('/vehicle/sync/feishu/config/get', { params }),
    // ECU
  getECUList: (params = {}) => request.get('/ecu/list', { params }),
  getECUDetail: (vin) => request.get(`/ecu/detail/${vin}`),
  updateECU: (formData) => request.post('/ecu/update', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  deleteECU: (vin) => request.delete(`/ecu/delete/${vin}`),
  getECUHistory: (vin) => request.get(`/ecu/history/${vin}`),
  getECUHistoryDetail: (vin, historyId) => request.get(`/ecu/history/${vin}/${historyId}`),
  restoreECUVersion: (vin, historyId) => request.post(`/ecu/restore/${vin}/${historyId}`, {}),
  updateECURemark: (vin, data) => request.post(`/ecu/remark/${vin}`, data),
  // 基线管理
  getTargetList: (params = {}) => request.get('/ecu/target/list', { params }),
  getTargetDetail: (target_name) => request.get(`/ecu/target/detail/${target_name}`),
  updateTarget: (formData) => request.post('/ecu/target/update', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  deleteTarget: (target_name) => request.delete(`/ecu/target/delete/${target_name}`),
  // ECU忽略
  ignoreECU: (vin, data) => request.post(`/ecu/ignore/${vin}`, data),
  restoreECUIgnore: (vin, data) => request.post(`/ecu/ignore/${vin}/restore`, data),
  getECUIgnoreList: (vin) => request.get(`/ecu/ignore/${vin}`),
  resetECUIgnore: (vin) => request.post(`/ecu/ignore/${vin}/reset`, {}),
  // 基线选定
  selectBaseline: (vin, data) => request.post(`/ecu/baseline-select/${vin}`, data),
  deselectBaseline: (vin, data) => request.post(`/ecu/baseline-select/${vin}/deselect`, data),
  getBaselineSelectList: (vin) => request.get(`/ecu/baseline-select/${vin}`),
  resetBaselineSelect: (vin) => request.post(`/ecu/baseline-select/${vin}/reset`, {}),
  // 操作记录
  addOperationLog: (data = {}) => request.post('/ecu/log', data),
  getOperationStats: () => request.get('/ecu/log/stats'),
  getOperationChart: (params = {}) => request.get('/ecu/log/chart', { params }),
  getOperationLogList: (params = {}) => request.get('/ecu/log/list', { params }),
  getLogOperators: () => request.get('/ecu/log/operators'),
  // 在线更新ECU
  onlineUpdateECU: (vin) => request.post(`/ecu/online-update/${vin}`, {}, { timeout: 130000 }),
  confirmOnlineUpdateECU: (vin, data) => request.post(`/ecu/online-update/confirm/${vin}`, data),
}
