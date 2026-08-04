import { request } from '@/utils'

export default {
  // 车辆列表
  getVehicleList: (params = {}) => request.get('/vehicle/list', { params }),
  // 车辆详情
  getVehicleById: (params = {}) => request.get('/vehicle/get', { params }),
  // 按VN查询
  getVehicleByVn: (params = {}) => request.get('/vehicle/by-vn', { params }),
  // 新增车辆
  createVehicle: (data = {}) => request.post('/vehicle/create', data),
  // 更新车辆
  updateVehicle: (data = {}) => request.post('/vehicle/update', data),
  // 删除车辆
  deleteVehicle: (params = {}) => request.delete('/vehicle/delete', { params }),
  // 批量删除车辆
  batchDeleteVehicles: (ids = []) => request.delete('/vehicle/batch-delete', { data: { ids } }),
  // 获取字段去重值（下拉联想）
  getFieldValues: (params = {}) => request.get('/vehicle/field-values', { params }),
  // UPSERT批量导入
  upsertVehicle: (data = {}) => request.post('/vehicle/upsert', data),
  // 到期提醒
  getExpiringVehicles: (params = {}) => request.get('/vehicle/alerts/expiring', { params }),
  // 状态地图数据
  getStatusMap: (params = {}) => request.get('/vehicle/status-map', { params }),
  // 飞书同步
  syncFromFeishu: () => request.post('/vehicle/sync/feishu'),
  getSyncStatus: () => request.get('/vehicle/sync/feishu/status'),
  reverseGeocode: (lat, lng) => request.get('/vehicle/reverse-geocode', { params: { lat, lng } }),
  configFeishu: (data = {}) => request.post('/vehicle/sync/feishu/config', data),
  saveFeishuConfig: (data = {}) => request.post('/vehicle/sync/feishu/config/save', data),
  getFeishuConfig: (params = {}) => request.get('/vehicle/sync/feishu/config/get', { params }),
  // CSV导入
  importCsv: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/vehicle/import/csv', formData)
  },
  // CSV模板下载（带认证）
  downloadCsvTemplate: () => request.get('/vehicle/import/template', { responseType: 'blob' }),
}
