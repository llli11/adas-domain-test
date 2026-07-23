import { request } from '@/utils';

export default {
  getMapwayList: (params = {}) => request.get('/mapway/list', { params }),
  getMapwayById: (params = {}) => request.get('/mapway/get', { params }),
  createMapway: (data = {}) => request.post('/mapway/create', data),
  updateMapway: (data = {}) => request.post('/mapway/update', data),
  deleteMapway: (params = {}) => request.delete('/mapway/delete', { params }),

  // 新增路线接口
  getRouteDetailList: (params = {}) => request.get('/mapway/route/list', { params }),
  createRouteDetail: (data = {}) => request.post('/mapway/route/create', data),
  updateRouteDetail: (data = {}) => request.post('/mapway/route/update', data),
  deleteRouteDetail: (params = {}) => request.delete('/mapway/route/delete', { params }),
  // 高级检索
  searchRouteDetail: (params = {}) => request.get('/mapway/route/search', { params }),
  filterRoutes: (data = {}, params = {}) => request.post('/mapway/route/filter', data, { params }),
  getRouteImage: (params = {}) => request.get('/mapway/route/image', { params }),
  // 城市拖动
  moveCity: (params = {}) => request.post('/mapway/move_city', null, { params }),
  // 自研项目路线接口
  getSelfDevelopedRouteDetailList: (params = {}) => request.get('/mapway/self-developed/route/list', { params }),
  createSelfDevelopedRouteDetail: (data = {}) => request.post('/mapway/self-developed/route/create', data),
  updateSelfDevelopedRouteDetail: (data = {}) => request.post('/mapway/self-developed/route/update', data),
  deleteSelfDevelopedRouteDetail: (params = {}) => request.delete('/mapway/self-developed/route/delete', { params }),
  searchSelfDevelopedRouteDetail: (params = {}) => request.get('/mapway/self-developed/route/search', { params }),
  getSelfDevelopedRouteImage: (params = {}) => request.get('/mapway/self-developed/route/image', { params }),
};