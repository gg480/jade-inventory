<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../api'

const items = ref([])
const loading = ref(false)
const pagination = ref({
  page: 1,
  size: 20,
  total: 0,
  pages: 0
})

const filters = ref({
  material_id: null,
  type_id: null,
  status: 'in_stock',
  keyword: ''
})

// 字典数据
const materials = ref([])
const types = ref([])

// 选中的货品（用于批量操作）
const selectedItems = ref(new Set())

// 出库相关
const showCheckoutModal = ref(false)
const checkoutItem = ref(null)
const checkoutForm = ref({
  actual_price: '',
  channel: 'store',
  sale_date: new Date().toISOString().slice(0, 10),
  customer_note: ''
})
const checkoutError = ref('')
const checkoutLoading = ref(false)

// 获取字典数据
async function fetchDicts() {
  try {
    const materialData = await api.dicts.getMaterials()
    materials.value = materialData
  } catch (error) {
    console.error('获取材质数据失败:', error)
  }
}

// 材质改变时获取对应的器型
async function onMaterialChange(materialId) {
  if (!materialId) {
    types.value = []
    filters.value.type_id = null
    return
  }
  try {
    const typeData = await api.dicts.getTypes(materialId)
    types.value = typeData
  } catch (error) {
    console.error('获取器型失败:', error)
    types.value = []
  }
}

// 获取库存列表
async function fetchItems() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      size: pagination.value.size,
      ...filters.value
    }
    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })
    const data = await api.items.getItems(params)
    items.value = data.items
    pagination.value = data.pagination
    // 清空选中状态
    selectedItems.value.clear()
  } catch (error) {
    console.error('获取库存列表失败:', error)
    // 这里可以添加用户提示
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  pagination.value.page = 1
  fetchItems()
}

// 重置筛选
function resetFilters() {
  filters.value = {
    material_id: null,
    type_id: null,
    status: 'in_stock',
    keyword: ''
  }
  types.value = []
  handleSearch()
}

// 切换选中状态
function toggleSelection(itemId) {
  if (selectedItems.value.has(itemId)) {
    selectedItems.value.delete(itemId)
  } else {
    selectedItems.value.add(itemId)
  }
}

// 全选/全不选
function toggleSelectAll() {
  if (selectedItems.value.size === items.value.length) {
    selectedItems.value.clear()
  } else {
    selectedItems.value.clear()
    items.value.forEach(item => selectedItems.value.add(item.id))
  }
}

// 打开出库模态框
function openCheckoutModal(item) {
  checkoutItem.value = item
  checkoutForm.value = {
    actual_price: item.selling_price,
    channel: 'store',
    sale_date: new Date().toISOString().slice(0, 10),
    customer_note: ''
  }
  checkoutError.value = ''
  checkoutLoading.value = false
  showCheckoutModal.value = true
}

// 提交出库
async function submitCheckout() {
  if (!checkoutForm.value.actual_price || parseFloat(checkoutForm.value.actual_price) <= 0) {
    alert('请填写有效的成交价')
    return
  }

  checkoutError.value = ''
  checkoutLoading.value = true

  try {
    const saleData = {
      item_id: checkoutItem.value.id,
      actual_price: parseFloat(checkoutForm.value.actual_price),
      channel: checkoutForm.value.channel,
      sale_date: checkoutForm.value.sale_date,
      customer_note: checkoutForm.value.customer_note
    }

    await api.sales.createSale(saleData)
    alert('出库成功！')
    showCheckoutModal.value = false
    fetchItems() // 刷新列表
  } catch (error) {
    // 错误信息已由API拦截器展示，这里可以设置具体错误状态
    checkoutError.value = error.message
  } finally {
    checkoutLoading.value = false
  }
}

// 删除货品
async function deleteItem(itemId, itemName) {
  if (!confirm(`确定要删除货品 "${itemName}" 吗？删除后不可恢复。`)) return

  try {
    await api.items.deleteItem(itemId)
    alert('删除成功')
    fetchItems() // 刷新列表
  } catch (error) {
    alert(`删除失败: ${error.message}`)
  }
}

// 标记为借出
async function markAsLent(itemId, itemName) {
  if (!confirm(`确定要将货品 "${itemName}" 标记为借出吗？`)) return

  try {
    await api.items.updateItem(itemId, { status: 'lent_out' })
    alert('已标记为借出')
    fetchItems() // 刷新列表
  } catch (error) {
    alert(`操作失败: ${error.message}`)
  }
}

// 批量删除
async function batchDelete() {
  if (selectedItems.value.size === 0) {
    alert('请先选择要删除的货品')
    return
  }

  if (!confirm(`确定要删除选中的 ${selectedItems.value.size} 件货品吗？删除后不可恢复。`)) return

  try {
    const promises = Array.from(selectedItems.value).map(id => api.items.deleteItem(id))
    await Promise.all(promises)
    alert('批量删除成功')
    fetchItems() // 刷新列表
  } catch (error) {
    alert(`批量删除失败: ${error.message}`)
  }
}

// 批量借出
async function batchLendOut() {
  if (selectedItems.value.size === 0) {
    alert('请先选择要借出的货品')
    return
  }

  if (!confirm(`确定要将选中的 ${selectedItems.value.size} 件货品标记为借出吗？`)) return

  try {
    const promises = Array.from(selectedItems.value).map(id =>
      api.items.updateItem(id, { status: 'lent_out' })
    )
    await Promise.all(promises)
    alert('批量借出成功')
    fetchItems() // 刷新列表
  } catch (error) {
    alert(`批量借出失败: ${error.message}`)
  }
}

// 监听材质变化
watch(() => filters.value.material_id, (newMaterialId) => {
  onMaterialChange(newMaterialId)
})

onMounted(() => {
  fetchDicts()
  fetchItems()
})
</script>

<template>
  <div>
    <!-- 页面标题和操作 -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">库存列表</h1>
        <p class="mt-1 text-sm text-gray-600">管理所有在库货品，支持筛选和搜索</p>
      </div>
      <div class="mt-4 sm:mt-0">
        <router-link
          to="/inventory/add"
          class="btn btn-success inline-flex items-center"
        >
          <span class="mr-2">➕</span>
          入库新货品
        </router-link>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div v-if="!loading && items.length > 0" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="card text-center">
        <div class="text-sm text-gray-500">总库存</div>
        <div class="text-2xl font-bold text-gray-900 mt-1">{{ pagination.total }}</div>
        <div class="text-xs text-gray-500 mt-1">件货品</div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">在库中</div>
        <div class="text-2xl font-bold text-green-600 mt-1">
          {{ items.filter(item => item.status === 'in_stock').length }}
        </div>
        <div class="text-xs text-gray-500 mt-1">可销售</div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">借出中</div>
        <div class="text-2xl font-bold text-blue-600 mt-1">
          {{ items.filter(item => item.status === 'lent_out').length }}
        </div>
        <div class="text-xs text-gray-500 mt-1">待售货品</div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">库存价值</div>
        <div class="text-2xl font-bold text-jade-600 mt-1">
          ¥{{ items.reduce((sum, item) => sum + item.cost_price, 0).toFixed(2) }}
        </div>
        <div class="text-xs text-gray-500 mt-1">按进价计算</div>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="card mb-6">
      <div class="grid grid-cols-1 md:grid-cols-6 gap-4">
        <!-- 关键词搜索 -->
        <div>
          <label class="form-label">关键词搜索</label>
          <input
            v-model="filters.keyword"
            type="text"
            placeholder="编号/款号/证书/备注"
            class="form-input"
            @keyup.enter="handleSearch"
          />
        </div>

        <!-- 材质筛选 -->
        <div>
          <label class="form-label">材质</label>
          <select v-model="filters.material_id" class="form-input">
            <option value="">全部材质</option>
            <option v-for="material in materials" :key="material.id" :value="material.id">
              {{ material.name }}
            </option>
          </select>
        </div>

        <!-- 器型筛选 -->
        <div>
          <label class="form-label">器型</label>
          <select v-model="filters.type_id" class="form-input" :disabled="!filters.material_id">
            <option value="">全部器型</option>
            <option v-for="type in types" :key="type.id" :value="type.id">
              {{ type.name }}
            </option>
          </select>
        </div>

        <!-- 状态筛选 -->
        <div>
          <label class="form-label">状态</label>
          <select v-model="filters.status" class="form-input">
            <option value="">全部</option>
            <option value="in_stock">在库</option>
            <option value="lent_out">借出</option>
            <option value="returned">已退</option>
            <option value="sold">已售</option>
          </select>
        </div>

        <!-- 操作按钮 -->
        <div class="flex flex-col sm:flex-row sm:items-end space-y-2 sm:space-y-0 sm:space-x-2">
          <button @click="handleSearch" class="btn btn-primary flex-1">
            搜索
          </button>
          <button @click="resetFilters" class="btn btn-secondary flex-1">
            重置
          </button>
        </div>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="items.length > 0 && !loading" class="card mb-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between">
        <div class="flex items-center space-x-4 mb-3 sm:mb-0">
          <label class="inline-flex items-center">
            <input
              type="checkbox"
              :checked="selectedItems.size === items.length && items.length > 0"
              @change="toggleSelectAll"
              class="h-4 w-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
            />
            <span class="ml-2 text-sm text-gray-700">全选</span>
          </label>
          <div class="text-sm text-gray-600">
            已选中 {{ selectedItems.size }} 件货品
          </div>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-if="selectedItems.size > 0"
            @click="batchLendOut"
            class="btn btn-secondary text-sm flex-1 sm:flex-none"
          >
            批量借出
          </button>
          <button
            v-if="selectedItems.size > 0"
            @click="batchDelete"
            class="btn bg-red-600 hover:bg-red-700 text-white text-sm flex-1 sm:flex-none"
          >
            批量删除
          </button>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      <p class="mt-2 text-gray-500">加载中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="items.length === 0" class="card text-center py-12">
      <div class="text-gray-400 text-5xl mb-4">📦</div>
      <h3 class="text-lg font-medium text-gray-900 mb-1">暂无货品</h3>
      <p class="text-gray-500 mb-6">还没有入库任何货品，点击右上角按钮开始入库</p>
      <router-link to="/inventory/add" class="btn btn-success">
        开始入库
      </router-link>
    </div>

    <!-- 库存列表 -->
    <div v-else>
      <!-- 桌面端：表格布局（移动端隐藏） -->
      <div class="table-container hidden md:block">
        <table class="table">
          <thead>
            <tr>
              <th class="w-10">
                <input
                  type="checkbox"
                  :checked="selectedItems.size === items.length && items.length > 0"
                  @change="toggleSelectAll"
                  class="h-4 w-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
                />
              </th>
              <th class="w-32">编号</th>
              <th>材质</th>
              <th>器型</th>
              <th class="w-24 text-right">进价</th>
              <th class="w-24 text-right">售价</th>
              <th class="w-24">状态</th>
              <th class="w-32">在库天数</th>
              <th class="w-48 text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td>
                <input
                  type="checkbox"
                  :checked="selectedItems.has(item.id)"
                  @change="toggleSelection(item.id)"
                  class="h-4 w-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
                />
              </td>
              <td class="font-mono text-sm">{{ item.sku_code }}</td>
              <td>{{ item.material_name }}</td>
              <td>{{ item.type_name || '-' }}</td>
              <td class="text-right font-medium">¥{{ item.cost_price.toFixed(2) }}</td>
              <td class="text-right font-medium text-jade-600">¥{{ item.selling_price.toFixed(2) }}</td>
              <td>
                <span :class="{
                  'px-2 py-1 text-xs rounded-full': true,
                  'bg-green-100 text-green-800': item.status === 'in_stock',
                  'bg-blue-100 text-blue-800': item.status === 'lent_out',
                  'bg-yellow-100 text-yellow-800': item.status === 'returned',
                  'bg-gray-100 text-gray-800': item.status === 'sold'
                }">
                  {{
                    { in_stock: '在库', lent_out: '借出', returned: '已退', sold: '已售' }[item.status] || item.status
                  }}
                </span>
              </td>
              <td>
                <span v-if="item.age_days !== null" class="text-gray-600">
                  {{ item.age_days }}天
                </span>
                <span v-else class="text-gray-400">-</span>
              </td>
              <td class="text-right">
                <div class="flex items-center justify-end space-x-3">
                  <router-link
                    :to="`/inventory/${item.id}`"
                    class="text-primary-600 hover:text-primary-800 text-sm font-medium"
                    title="查看详情"
                  >
                    详情
                  </router-link>
                  <button
                    v-if="item.status === 'in_stock'"
                    @click="openCheckoutModal(item)"
                    class="text-jade-600 hover:text-jade-800 text-sm font-medium"
                    title="销售出库"
                  >
                    出库
                  </button>
                  <button
                    v-if="item.status === 'in_stock'"
                    @click="markAsLent(item.id, item.sku_code)"
                    class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    title="标记为借出"
                  >
                    借出
                  </button>
                  <button
                    @click="deleteItem(item.id, item.sku_code)"
                    class="text-red-600 hover:text-red-800 text-sm font-medium"
                    title="删除货品"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 移动端：卡片式布局（桌面端隐藏） -->
      <div class="block md:hidden space-y-4">
        <div
          v-for="item in items"
          :key="item.id"
          class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
        >
          <!-- 卡片头部：编号和选择框 -->
          <div class="flex items-start justify-between mb-3">
            <div class="font-mono text-sm font-medium text-gray-900">{{ item.sku_code }}</div>
            <input
              type="checkbox"
              :checked="selectedItems.has(item.id)"
              @change="toggleSelection(item.id)"
              class="h-4 w-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
            />
          </div>

          <!-- 基本信息 -->
          <div class="grid grid-cols-2 gap-3 mb-3">
            <div>
              <div class="text-xs text-gray-500">材质</div>
              <div class="text-sm font-medium text-gray-900">{{ item.material_name }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500">器型</div>
              <div class="text-sm text-gray-900">{{ item.type_name || '-' }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500">进价</div>
              <div class="text-sm font-medium text-gray-900">¥{{ item.cost_price.toFixed(2) }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500">售价</div>
              <div class="text-sm font-medium text-jade-600">¥{{ item.selling_price.toFixed(2) }}</div>
            </div>
          </div>

          <!-- 状态和库龄 -->
          <div class="flex items-center justify-between mb-3">
            <div>
              <span :class="{
                'px-2 py-1 text-xs rounded-full': true,
                'bg-green-100 text-green-800': item.status === 'in_stock',
                'bg-blue-100 text-blue-800': item.status === 'lent_out',
                'bg-yellow-100 text-yellow-800': item.status === 'returned',
                'bg-gray-100 text-gray-800': item.status === 'sold'
              }">
                {{
                  { in_stock: '在库', lent_out: '借出', returned: '已退', sold: '已售' }[item.status] || item.status
                }}
              </span>
            </div>
            <div class="text-xs text-gray-600">
              在库{{ item.age_days !== null ? `${item.age_days}天` : '-' }}
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex justify-between pt-3 border-t border-gray-100">
            <router-link
              :to="`/inventory/${item.id}`"
              class="text-primary-600 hover:text-primary-800 text-sm font-medium"
            >
              详情
            </router-link>
            <div class="flex space-x-3">
              <button
                v-if="item.status === 'in_stock'"
                @click="openCheckoutModal(item)"
                class="text-jade-600 hover:text-jade-800 text-sm font-medium"
              >
                出库
              </button>
              <button
                v-if="item.status === 'in_stock'"
                @click="markAsLent(item.id, item.sku_code)"
                class="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                借出
              </button>
              <button
                @click="deleteItem(item.id, item.sku_code)"
                class="text-red-600 hover:text-red-800 text-sm font-medium"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between mt-6 space-y-3 sm:space-y-0">
        <div class="text-sm text-gray-700 text-center sm:text-left">
          显示第 {{ (pagination.page - 1) * pagination.size + 1 }} 到
          {{ Math.min(pagination.page * pagination.size, pagination.total) }} 条，
          共 {{ pagination.total }} 条记录
        </div>
        <div class="flex items-center justify-center space-x-2">
          <button
            @click="pagination.page--; fetchItems()"
            :disabled="pagination.page <= 1"
            class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            上一页
          </button>
          <span class="px-3 py-1 text-sm">
            第 {{ pagination.page }} / {{ pagination.pages }} 页
          </span>
          <button
            @click="pagination.page++; fetchItems()"
            :disabled="pagination.page >= pagination.pages"
            class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- 出库模态框 -->
    <div v-if="showCheckoutModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">销售出库</h3>
          <p class="mt-1 text-sm text-gray-600">{{ checkoutItem?.sku_code }} - {{ checkoutItem?.material_name }}</p>
        </div>
        <div class="px-6 py-4">
          <form @submit.prevent="submitCheckout">
            <!-- 错误提示 -->
            <div v-if="checkoutError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded">
              <div class="flex items-start">
                <div class="flex-shrink-0">
                  <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div class="ml-3">
                  <p class="text-sm text-red-700">{{ checkoutError }}</p>
                </div>
              </div>
            </div>
            <div class="space-y-4">
              <!-- 成交价 -->
              <div>
                <label class="form-label">成交价（元） <span class="text-red-500">*</span></label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">¥</span>
                  <input
                    v-model="checkoutForm.actual_price"
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    class="form-input pl-8"
                  />
                </div>
                <p class="mt-1 text-xs text-gray-500">
                  标价：¥{{ checkoutItem?.selling_price.toFixed(2) }}，
                  进价：¥{{ checkoutItem?.cost_price.toFixed(2) }}
                </p>
              </div>

              <!-- 销售渠道 -->
              <div>
                <label class="form-label">销售渠道</label>
                <select v-model="checkoutForm.channel" class="form-input">
                  <option value="store">门店</option>
                  <option value="wechat">微信</option>
                  <option value="ecommerce">电商</option>
                </select>
              </div>

              <!-- 成交日期 -->
              <div>
                <label class="form-label">成交日期</label>
                <input
                  v-model="checkoutForm.sale_date"
                  type="date"
                  class="form-input"
                />
              </div>

              <!-- 客户/交易备注 -->
              <div>
                <label class="form-label">客户/交易备注（可选）</label>
                <textarea
                  v-model="checkoutForm.customer_note"
                  rows="2"
                  class="form-input"
                  placeholder="可填写客户信息、交易备注等"
                ></textarea>
              </div>
            </div>

            <div class="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                @click="showCheckoutModal = false"
                class="btn btn-secondary"
              >
                取消
              </button>
              <button
                type="submit"
                class="btn btn-success"
                :disabled="checkoutLoading"
              >
                <span v-if="checkoutLoading" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
                {{ checkoutLoading ? '处理中...' : '确认出库' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>