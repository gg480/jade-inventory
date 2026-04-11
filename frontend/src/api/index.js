import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：可以在这里添加token等
api.interceptors.request.use(
  (config) => {
    // 可以添加认证token等
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理错误
api.interceptors.response.use(
  (response) => {
    // 后端统一格式：{ code: 0, data: ..., message: 'ok' }
    const { code, data, message } = response.data
    if (code === 0) {
      return data
    } else {
      // 业务错误，弹出提示
      const errorMessage = message || '请求失败'
      alert(`错误 ${code}: ${errorMessage}`)
      const error = new Error(errorMessage)
      error.code = code
      return Promise.reject(error)
    }
  },
  (error) => {
    // HTTP错误
    let message = '网络错误，请稍后重试'
    if (error.response) {
      switch (error.response.status) {
        case 400:
          message = '请求参数错误'
          break
        case 401:
          message = '未授权，请登录'
          break
        case 403:
          message = '拒绝访问'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = '服务器错误'
          break
        default:
          message = `请求失败：${error.response.status}`
      }
      // 尝试获取后端错误信息
      if (error.response.data && error.response.data.message) {
        message = error.response.data.message
      }
    } else if (error.request) {
      message = '网络连接失败，请检查网络'
    }

    // 弹出错误提示
    alert(message)

    error.message = message
    return Promise.reject(error)
  }
)

// API模块
const dicts = {
  // 材质
  getMaterials: (includeInactive = false) =>
    api.get('/dicts/materials', { params: { include_inactive: includeInactive } }),
  createMaterial: (data) => api.post('/dicts/materials', data),
  updateMaterial: (id, data) => api.put(`/dicts/materials/${id}`, data),
  deleteMaterial: (id) => api.delete(`/dicts/materials/${id}`),

  // 器型
  getTypes: (materialId, includeInactive = false) =>
    api.get('/dicts/types', { params: { material_id: materialId, include_inactive: includeInactive } }),
  createType: (data) => api.post('/dicts/types', data),
  updateType: (id, data) => api.put(`/dicts/types/${id}`, data),
  deleteType: (id) => api.delete(`/dicts/types/${id}`),

  // 标签
  getTags: (groupName, includeInactive = false) =>
    api.get('/dicts/tags', { params: { group_name: groupName, include_inactive: includeInactive } }),
  createTag: (data) => api.post('/dicts/tags', data),
  updateTag: (id, data) => api.put(`/dicts/tags/${id}`, data),
  deleteTag: (id) => api.delete(`/dicts/tags/${id}`),
}

const items = {
  // 列表
  getItems: (params) => api.get('/items', { params }),
  // 详情
  getItem: (id) => api.get(`/items/${id}`),
  // 单件入库
  createItem: (data) => api.post('/items', data),
  // 批量入库
  createItemsBatch: (data) => api.post('/items/batch', data),
  // 编辑
  updateItem: (id, data) => api.put(`/items/${id}`, data),
  // 删除
  deleteItem: (id) => api.delete(`/items/${id}`),
  // 图片管理
  uploadItemImage: (itemId, formData) => api.post(`/items/${itemId}/images`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteItemImage: (itemId, imageId) => api.delete(`/items/${itemId}/images/${imageId}`),
  setCoverImage: (itemId, imageId) => api.put(`/items/${itemId}/images/${imageId}/cover`),
}

const sales = {
  // 销售列表
  getSales: (params) => api.get('/sales', { params }),
  // 创建销售记录
  createSale: (data) => api.post('/sales', data),
}

const dashboard = {
  // 按品类利润
  getProfitByCategory: (params) => api.get('/dashboard/profit/by-category', { params }),
  // 按渠道利润
  getProfitByChannel: (params) => api.get('/dashboard/profit/by-channel', { params }),
  // 销售趋势
  getSalesTrend: (params) => api.get('/dashboard/trend', { params }),
  // 压货预警
  getStockAging: (params) => api.get('/dashboard/stock-aging', { params }),
  // 概览数据
  getSummary: (params) => api.get('/dashboard/summary', { params }),
}

export default {
  dicts,
  items,
  sales,
  dashboard,
  // 原始axios实例（特殊情况使用）
  instance: api,
}