<script setup>
import { ref, onMounted, watch, computed, onBeforeUnmount } from 'vue'
import api from '../api'
import Pagination from '../components/Pagination.vue'
import toast from '../composables/useToast'
import BundleSaleDialog from '../components/BundleSaleDialog.vue'
import SaleDialog from '../components/SaleDialog.vue'

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
  keyword: '',
  counter: ''
})

// 字典数据
const materials = ref([])
const types = ref([])

// 移动端筛选栏折叠状态
const showFilters = ref(false)

// 入库下拉菜单状态
const showInboundDropdown = ref(false)
const inboundDropdownRef = ref(null)

// 点击外部关闭下拉菜单
function handleClickOutside(event) {
  if (inboundDropdownRef.value && !inboundDropdownRef.value.contains(event.target)) {
    showInboundDropdown.value = false
  }
}

// 监听点击事件
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

// 清理事件监听器
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 选中的货品（用于批量操作）
const selectedItems = ref(new Set())

// 计算选中的货品对象
const selectedItemsData = computed(() => {
  return items.value.filter(item => selectedItems.value.has(item.id))
})

// 出库弹窗相关
const showSaleDialog = ref(false)
const saleItem = ref(null)

// 套装出库相关
const showBundleSaleDialog = ref(false)

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

// 分页变化
function onPageChange(newPage) {
  pagination.value.page = newPage
  fetchItems()
}

// 重置筛选
function resetFilters() {
  filters.value = {
    material_id: null,
    type_id: null,
    status: 'in_stock',
    keyword: '',
    counter: ''
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

// 打开出库弹窗
function openSaleDialog(item) {
  saleItem.value = item
  showSaleDialog.value = true
}

// 出库成功回调
function handleSaleSuccess() {
  toast.success('出库成功！')
  showSaleDialog.value = false
  fetchItems()
}

// 删除货品
async function deleteItem(itemId, itemName) {
  if (!confirm(`确定要删除货品 "${itemName}" 吗？删除后不可恢复。`)) return

  try {
    await api.items.deleteItem(itemId)
    toast.success('删除成功')
    fetchItems() // 刷新列表
  } catch (error) {
    toast.error(`删除失败: ${error.message}`)
  }
}

// 标记为借出
async function markAsLent(itemId, itemName) {
  if (!confirm(`确定要将货品 "${itemName}" 标记为借出吗？`)) return

  try {
    await api.items.updateItem(itemId, { status: 'lent_out' })
    toast.success('已标记为借出')
    fetchItems() // 刷新列表
  } catch (error) {
    toast.error(`操作失败: ${error.message}`)
  }
}

// 批量删除
async function batchDelete() {
  if (selectedItems.value.size === 0) {
    toast.warning('请先选择要删除的货品')
    return
  }

  if (!confirm(`确定要删除选中的 ${selectedItems.value.size} 件货品吗？删除后不可恢复。`)) return

  try {
    const promises = Array.from(selectedItems.value).map(id => api.items.deleteItem(id))
    await Promise.all(promises)
    toast.success('批量删除成功')
    fetchItems() // 刷新列表
  } catch (error) {
    toast.error(`批量删除失败: ${error.message}`)
  }
}

// 打开套装出库对话框
function openBundleSaleDialog() {
  if (selectedItems.value.size < 2) {
    toast.warning('请至少选择2件货品进行套装出库')
    return
  }

  // 检查所有选中货品是否都在库
  const notInStockItems = selectedItemsData.value.filter(item => item.status !== 'in_stock')
  if (notInStockItems.length > 0) {
    toast.warning(`以下货品不在库，无法出库：${notInStockItems.map(item => item.sku_code).join(', ')}`)
    return
  }

  showBundleSaleDialog.value = true
}

// 处理套装出库成功
function handleBundleSaleSuccess() {
  toast.success('套装出库成功！')
  fetchItems() // 刷新列表
  showBundleSaleDialog.value = false
}

// 批量借出
async function batchLendOut() {
  if (selectedItems.value.size === 0) {
    toast.warning('请先选择要借出的货品')
    return
  }

  if (!confirm(`确定要将选中的 ${selectedItems.value.size} 件货品标记为借出吗？`)) return

  try {
    const promises = Array.from(selectedItems.value).map(id =>
      api.items.updateItem(id, { status: 'lent_out' })
    )
    await Promise.all(promises)
    toast.success('批量借出成功')
    fetchItems() // 刷新列表
  } catch (error) {
    toast.error(`批量借出失败: ${error.message}`)
  }
}

// 批量打印标签
function batchPrintLabels() {
  const ids = Array.from(selectedItems.value).join(',')
  window.open(`/labels?ids=${ids}`, '_blank')
}

// 导出库存Excel
async function handleExportInventory() {
  try {
    const params = {}
    if (filters.value.material_id) params.material_id = filters.value.material_id
    if (filters.value.type_id) params.type_id = filters.value.type_id
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.keyword) params.keyword = filters.value.keyword
    if (filters.value.counter) params.counter = filters.value.counter
    const resp = await api.exportData.inventory(params)
    const url = URL.createObjectURL(resp)
    const a = document.createElement('a')
    a.href = url
    a.download = `库存导出_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('导出失败:', e)
  }
}

// 计算库龄（天数）
function calculateAging(purchaseDate) {
  if (!purchaseDate) return null
  const purchase = new Date(purchaseDate)
  // 检查日期是否有效
  if (isNaN(purchase.getTime())) return null
  const today = new Date()
  const diffTime = today - purchase
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  return diffDays
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
      <div class="mt-4 sm:mt-0 flex gap-2">
        <button @click="handleExportInventory" class="btn btn-secondary" title="导出库存Excel">
          导出
        </button>
        <!-- 入库下拉菜单 -->
        <div class="relative inline-block text-left" ref="inboundDropdownRef">
          <button
            type="button"
            class="btn btn-success inline-flex items-center"
            @click.stop="showInboundDropdown = !showInboundDropdown"
          >
            <span class="mr-2">➕</span>
            入库
            <svg class="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <div
            v-if="showInboundDropdown"
            class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200"
          >
            <router-link
              to="/inventory/add"
              class="block px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 rounded-t-md"
              @click.stop="showInboundDropdown = false"
            >
              高货入库
            </router-link>
            <router-link
              to="/inventory/batch"
              class="block px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 rounded-b-md"
              @click.stop="showInboundDropdown = false"
            >
              通货入库
            </router-link>
          </div>
        </div>
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
      <!-- 移动端筛选栏标题和切换按钮 -->
      <div class="md:hidden flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
        <h3 class="text-lg font-medium text-gray-900">筛选条件</h3>
        <button
          @click="showFilters = !showFilters"
          class="flex items-center text-sm text-emerald-600 hover:text-emerald-800"
        >
          <span>{{ showFilters ? '收起筛选' : '展开筛选' }}</span>
          <svg
            class="ml-1 w-4 h-4 transform transition-transform"
            :class="{ 'rotate-180': showFilters }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      <!-- 筛选表单 -->
      <div :class="{ 'hidden md:block': !showFilters }">
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

          <!-- 柜台筛选 -->
          <div>
            <label class="form-label">柜台编号</label>
            <input
              v-model="filters.counter"
              type="number"
              placeholder="请输入柜台号"
              class="form-input"
              min="1"
              @keyup.enter="handleSearch"
            />
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
            v-if="selectedItems.size >= 2"
            @click="openBundleSaleDialog"
            class="btn btn-success text-sm flex-1 sm:flex-none"
          >
            套装出库
          </button>
          <button
            v-if="selectedItems.size > 0"
            @click="batchPrintLabels"
            class="btn btn-secondary text-sm flex-1 sm:flex-none"
          >
            打印标签
          </button>
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
              <th class="w-40">名称</th>
              <th class="w-24">材质</th>
              <th class="w-24">器型</th>
              <th class="w-24 text-right">成本</th>
              <th class="w-24 text-right">售价</th>
              <th class="w-24">状态</th>
              <th class="w-24">库龄</th>
              <th class="w-24">柜台</th>
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
              <td>{{ item.name || item.sku_code }}</td>
              <td>{{ item.material_name }}</td>
              <td>{{ item.type_name || '-' }}</td>
              <td class="text-right font-medium">¥{{ item.cost_price.toFixed(2) }}</td>
              <td class="text-right font-medium text-jade-600">¥{{ item.selling_price.toFixed(2) }}</td>
              <td>
                <span :class="{
                  'px-2 py-1 text-xs rounded-full': true,
                  'bg-green-100 text-green-800': item.status === 'in_stock',
                  'bg-blue-100 text-blue-800': item.status === 'lent_out',
                  'bg-red-100 text-red-800': item.status === 'returned',
                  'bg-gray-100 text-gray-800': item.status === 'sold'
                }">
                  {{
                    { in_stock: '在库', lent_out: '借出', returned: '已退', sold: '已售' }[item.status] || item.status
                  }}
                </span>
              </td>
              <td>
                <span v-if="item.purchase_date" :class="{'text-red-600': calculateAging(item.purchase_date) > 90, 'text-gray-600': calculateAging(item.purchase_date) !== null}">
                  {{ calculateAging(item.purchase_date) !== null ? calculateAging(item.purchase_date) + '天' : '-' }}
                </span>
                <span v-else class="text-gray-400">-</span>
              </td>
              <td>{{ item.counter || '-' }}</td>
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
                    @click="openSaleDialog(item)"
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
          class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
          @click="$router.push(`/inventory/${item.id}`)"
        >
          <!-- 卡片头部：名称和状态 -->
          <div class="flex items-start justify-between mb-3">
            <div>
              <div class="text-sm font-medium text-gray-900">{{ item.name || item.sku_code }}</div>
              <div class="text-xs text-gray-500 mt-1">{{ item.sku_code }}</div>
            </div>
            <span :class="{
              'px-2 py-1 text-xs rounded-full': true,
              'bg-green-100 text-green-800': item.status === 'in_stock',
              'bg-blue-100 text-blue-800': item.status === 'lent_out',
              'bg-red-100 text-red-800': item.status === 'returned',
              'bg-gray-100 text-gray-800': item.status === 'sold'
            }">
              {{
                { in_stock: '在库', lent_out: '借出', returned: '已退', sold: '已售' }[item.status] || item.status
              }}
            </span>
          </div>

          <!-- 材质和售价 -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <div class="text-xs text-gray-500">材质</div>
              <div class="text-sm font-medium text-gray-900">{{ item.material_name }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500">售价</div>
              <div class="text-sm font-medium text-jade-600">¥{{ item.selling_price.toFixed(2) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页组件 -->
      <Pagination
        :total="pagination.total"
        :page="pagination.page"
        :size="pagination.size"
        @update:page="onPageChange"
        class="mt-6"
      />
    </div>

    <!-- 单件出库弹窗 -->
    <SaleDialog
      v-if="saleItem"
      :item="saleItem"
      :visible="showSaleDialog"
      @close="showSaleDialog = false"
      @success="handleSaleSuccess"
    />

    <!-- 套装出库弹窗组件 -->
    <BundleSaleDialog
      :items="selectedItemsData"
      :visible="showBundleSaleDialog"
      @close="showBundleSaleDialog = false"
      @success="handleBundleSaleSuccess"
    />
  </div>
</template>