import axios from 'axios'
import toast from '../composables/useToast'

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
    const responseData = response.data

    // 情况1：后端直接返回列表（字典接口）
    if (Array.isArray(responseData)) {
      return responseData
    }

    // 情况2：后端返回 { code, data, message } 格式
    if (responseData && typeof responseData === 'object' && 'code' in responseData) {
      const { code, data, message } = responseData
      if (code === 0) {
        return data
      } else {
        // 业务错误，弹出提示
        const errorMessage = message || '请求失败'
        toast.error(`${errorMessage}`)
        const error = new Error(errorMessage)
        error.code = code
        return Promise.reject(error)
      }
    }

    // 情况3：其他格式直接返回
    return responseData
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
    toast.error(message)

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

  // 系统配置
  getConfig: () => api.get('/config'),
  updateConfig: (key, value) => api.put(`/config/${key}`, { value }),
}

const batches = {
  // 批次列表
  getBatches: (params) => api.get('/batches', { params }),
  // 批次详情
  getBatch: (id) => api.get(`/batches/${id}`),
  // 创建批次
  createBatch: (data) => api.post('/batches', data),
  // 触发成本分摊
  allocateBatch: (id) => api.post(`/batches/${id}/allocate`),
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
  // 创建套装销售
  createBundleSale: (data) => api.post('/sales/bundle', data),
}

const customers = {
  // 客户列表
  getCustomers: (params) => api.get('/customers/', { params }),
  // 创建客户
  createCustomer: (data) => api.post('/customers/', data),
  // 编辑客户
  updateCustomer: (id, data) => api.put(`/customers/${id}`, data),
  // 获取客户详情（含购买记录）
  getCustomerDetail: (id) => api.get(`/customers/${id}`),
}

const suppliers = {
  // 供应商列表
  getSuppliers: (params) => api.get('/suppliers/', { params }),
  // 新增供应商
  createSupplier: (data) => api.post('/suppliers/', data),
  // 编辑供应商
  updateSupplier: (id, data) => api.put(`/suppliers/${id}`, data),
}

const dashboard = {
  // 概览数据
  getDashboardSummary: (params) => api.get('/dashboard/summary', { params }),
  // 批次利润分析
  getBatchProfit: (params) => api.get('/dashboard/batch-profit', { params }),
  // 按品类利润
  getProfitByCategory: (params) => api.get('/dashboard/profit/by-category', { params }),
  // 按渠道利润
  getProfitByChannel: (params) => api.get('/dashboard/profit/by-channel', { params }),
  // 销售趋势
  getTrend: (params) => api.get('/dashboard/trend', { params }),
  // 压货预警
  getStockAging: (params) => api.get('/dashboard/stock-aging', { params }),
  // 兼容别名
  getSummary: (params) => api.get('/dashboard/summary', { params }),
  getSalesTrend: (params) => api.get('/dashboard/trend', { params }),
}

const exportData = {
  // 导出库存
  inventory: (params) => api.get('/export/inventory', { params, responseType: 'blob' }),
  // 导出销售
  sales: (params) => api.get('/export/sales', { params, responseType: 'blob' }),
  // 导出批次回本
  batches: (params) => api.get('/export/batches', { params, responseType: 'blob' }),
}

const metal = {
  // 获取当前市价（只显示有 cost_per_gram 的材质）
  getCurrentPrices: () => api.get('/metal-prices'),
  // 更新贵金属市价
  updatePrice: (material_id, data) => api.put(`/metal-prices/${material_id}`, data),
  // 获取历史记录
  getPriceHistory: (params) => api.get('/metal-prices/history', { params }),
  // 预览批量调价
  previewReprice: (data) => api.post('/metal-prices/reprice', data),
  // 确认批量调价
  confirmReprice: (data) => api.post('/metal-prices/reprice/confirm', data),
  // 向后兼容的别名
  getMetalPrices: (params) => api.get('/metal-prices/history', { params }), // 历史记录
  updateMetalPrice: (data) => api.post('/metal-prices', data), // 旧版本，不推荐
}

// 图片URL前缀
export const IMAGE_BASE_URL = '/data/images'

export default {
  dicts,
  batches,
  items,
  sales,
  customers,
  suppliers,
  dashboard,
  metal,
  exportData,
  IMAGE_BASE_URL,
  // 原始axios实例（特殊情况使用）
  instance: api,
}