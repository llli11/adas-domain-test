import axios from 'axios'
import { request } from '@/utils'
import { getToken } from '@/utils'

// 专用于文件下载的 axios 实例 —— 绕过全局拦截器的 blob 处理
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
  // tool ledger
  getToolList: (params = {}) => request.get('/tool/list', { params }),
  getToolById: (params = {}) => request.get('/tool/get', { params }),
  createTool: (data = {}) => request.post('/tool/create', data),
  updateTool: (params = {}, data = {}) => request.post('/tool/update', data, { params }),
  deleteTool: (params = {}) => request.delete('/tool/delete', { params }),
  batchDeleteTool: () => request.delete('/tool/batch-delete'),
  uploadImage: (data = {}) => request.post('/tool/upload', data),
  exportTool: () => downloadRequest.get('/tool/export', { responseType: 'blob' }),
  importTool: (data = {}) => request.post('/tool/import', data),
  // tool borrow
  getToolBorrowList: (params = {}) => request.get('/tool/borrow/list', { params }),
  getToolBorrowById: (params = {}) => request.get('/tool/borrow/get', { params }),
  createToolBorrow: (data = {}) => request.post('/tool/borrow/create', data),
  approveToolBorrow: (data = {}) => request.post('/tool/borrow/approve', data),
  returnToolBorrow: (params = {}) => request.post('/tool/borrow/return', params),
  // tool inventory
  getToolInventoryList: (params = {}) => request.get('/tool/inventory/list', { params }),
  getToolInventory: (params = {}) => request.get('/tool/inventory/get', { params }),
  createToolInventory: (data = {}) => request.post('/tool/inventory/create', data),
  completeToolInventory: (data = {}) => request.post('/tool/inventory/complete', data),
  updateToolInventory: (data = {}) => request.put('/tool/inventory/update', data),
  deleteToolInventory: (params = {}) => request.delete('/tool/inventory/delete', { params }),
  // tool requirement
  getToolRequirementList: (params = {}) => request.get('/tool/requirement/list', { params }),
  getToolRequirementById: (params = {}) => request.get('/tool/requirement/get', { params }),
  createToolRequirement: (data = {}) => request.post('/tool/requirement/create', data),
  handleToolRequirement: (data = {}) => request.post('/tool/requirement/handle', data),
  updateToolRequirement: (data = {}) => request.put('/tool/requirement/update', data),
  deleteToolRequirement: (params = {}) => request.delete('/tool/requirement/delete', { params }),
}
