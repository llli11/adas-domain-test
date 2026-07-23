import request from '@/utils/request'

const reqWrap = async (apiPromise) => {
  const res = await apiPromise
  if (res.code !== 200) {
    throw new Error(res.msg || '请求失败')
  }
  return res
}

export default {
  // 项目类型
  getProjectTypes() {
    return reqWrap(request.get('/version_index/project-type/list'))
  },
  addProjectType(data) {
    return reqWrap(request.post('/version_index/project-type/add', data))
  },
  deleteProjectType(id) {
    return reqWrap(request.delete(`/version_index/project-type/delete/${id}`))
  },

  // 车型
  getCarModels() {
    return reqWrap(request.get('/version_index/car-model/list'))
  },
  addCarModel(data) {
    return reqWrap(request.post('/version_index/car-model/add', data))
  },
  deleteCarModel(id) {
    return reqWrap(request.delete(`/version_index/car-model/delete/${id}`))
  },

  // 版本号
  getVersionCodes() {
    return reqWrap(request.get('/version_index/version-code/list'))
  },
  addVersionCode(data) {
    return reqWrap(request.post('/version_index/version-code/add', data))
  },
  deleteVersionCode(id) {
    return reqWrap(request.delete(`/version_index/version-code/delete/${id}`))
  },

  // 指标大类
  getIndexCategories() {
    return reqWrap(request.get('/version_index/index-category/list'))
  },
  addIndexCategory(data) {
    return reqWrap(request.post('/version_index/index-category/add', data))
  },
  deleteIndexCategory(id) {
    return reqWrap(request.delete(`/version_index/index-category/delete/${id}`))
  },

  // 指标子项（携带大类ID关联）
  getIndexSubItems(categoryId) {
    return reqWrap(request.get(`/version_index/index-sub/list?category_id=${categoryId}`))
  },
  addIndexSubItem(data) {
    return reqWrap(request.post('/version_index/index-sub/add', data))
  },
  deleteIndexSubItem(id) {
    return reqWrap(request.delete(`/version_index/index-sub/delete/${id}`))
  },

  // 具体指标
  getIndexItems(subId) {
    return reqWrap(request.get(`/version_index/index-item/list?sub_id=${subId}`))
  },
  addIndexItem(data) {
    return reqWrap(request.post('/version_index/index-item/add', data))
  },
  deleteIndexItem(id) {
    return reqWrap(request.delete(`/version_index/index-item/delete/${id}`))
  },

  // 保存指标数据
  saveVersionData(data) {
    return reqWrap(request.post('/version_index/data/save', data))
  },
  getSavedData(params) {
    return reqWrap(request.get('/version_index/data/list', { params }))
  }
}