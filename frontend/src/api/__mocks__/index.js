import { vi } from 'vitest'

const mockApi = {
  sales: {
    createBundleSale: vi.fn(),
    createSale: vi.fn(),
    getSales: vi.fn(),
  },
  customers: {
    getCustomers: vi.fn(),
    createCustomer: vi.fn(),
    updateCustomer: vi.fn(),
  },
  items: {
    getItems: vi.fn(),
    getItem: vi.fn(),
    createItem: vi.fn(),
    updateItem: vi.fn(),
    deleteItem: vi.fn(),
  },
  batches: {
    getBatches: vi.fn(),
    getBatch: vi.fn(),
    createBatch: vi.fn(),
    allocateBatch: vi.fn(),
  },
  dicts: {
    getMaterials: vi.fn(),
    getTypes: vi.fn(),
    getTags: vi.fn(),
    getConfig: vi.fn(),
  },
  dashboard: {
    getDashboardSummary: vi.fn(),
    getBatchProfit: vi.fn(),
    getProfitByCategory: vi.fn(),
    getProfitByChannel: vi.fn(),
    getTrend: vi.fn(),
    getStockAging: vi.fn(),
  },
  metal: {
    getCurrentPrices: vi.fn(),
    updatePrice: vi.fn(),
    getPriceHistory: vi.fn(),
    previewReprice: vi.fn(),
    confirmReprice: vi.fn(),
  },
  suppliers: {
    getSuppliers: vi.fn(),
  },
}

// 默认mock实现
export const setupDefaultMocks = () => {
  // 销售API
  mockApi.sales.createBundleSale.mockResolvedValue({
    code: 0,
    data: {
      id: 1,
      bundle_no: 'b20240412001',
      total_price: 900,
      sale_records: [
        { id: 1, item_id: 1, actual_price: 750 },
        { id: 2, item_id: 2, actual_price: 150 }
      ]
    }
  })

  mockApi.sales.createSale.mockResolvedValue({
    code: 0,
    data: { id: 1, sale_no: 's20240412001' }
  })

  mockApi.sales.getSales.mockResolvedValue({
    code: 0,
    data: { items: [], total: 0, page: 1, size: 20 }
  })

  // 客户API
  mockApi.customers.getCustomers.mockResolvedValue([
    { id: 1, name: '测试客户', phone: '13800138000' },
    { id: 2, name: '另一个客户', wechat: 'wechat123' }
  ])

  // 货品API
  mockApi.items.getItems.mockResolvedValue({
    code: 0,
    data: { items: [], total: 0, page: 1, size: 20 }
  })

  mockApi.items.getItem.mockResolvedValue({
    code: 0,
    data: {
      id: 1,
      sku_code: 'TEST001',
      material_name: '翡翠',
      selling_price: 1000,
      status: 'in_stock'
    }
  })

  // 字典API
  mockApi.dicts.getMaterials.mockResolvedValue([
    { id: 1, name: '翡翠', is_active: true },
    { id: 2, name: '银', is_active: true }
  ])

  mockApi.dicts.getTypes.mockResolvedValue([
    { id: 1, name: '吊坠', material_id: 1, is_active: true },
    { id: 2, name: '项链', material_id: 1, is_active: true }
  ])

  mockApi.dicts.getTags.mockResolvedValue([
    { id: 1, name: '精品', group_name: '品质', is_active: true },
    { id: 2, name: '特价', group_name: '促销', is_active: true }
  ])

  // 仪表板API
  mockApi.dashboard.getDashboardSummary.mockResolvedValue({
    code: 0,
    data: {
      total_items: 100,
      total_value: 500000,
      monthly_sales: 50000,
      profit_margin: 0.3
    }
  })

  return mockApi
}

// 重置所有mocks
export const resetAllMocks = () => {
  Object.values(mockApi).forEach(module => {
    Object.values(module).forEach(mockFn => {
      if (typeof mockFn.mockReset === 'function') {
        mockFn.mockReset()
      }
    })
  })
}

// 创建错误mock
export const setupErrorMocks = (errorCode = 400, errorMessage = '请求失败') => {
  const error = new Error(errorMessage)
  error.code = errorCode
  error.response = { status: errorCode, data: { message: errorMessage } }

  mockApi.sales.createBundleSale.mockRejectedValue(error)
  return error
}

// 导出默认模拟对象
export default mockApi