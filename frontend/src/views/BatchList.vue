<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import Pagination from '../components/Pagination.vue'

const router = useRouter()

const batches = ref([])
const loading = ref(false)
const pagination = ref({
  page: 1,
  size: 20,
  total: 0,
  pages: 0
})

const filters = ref({
  material_id: null
})

// 字典数据
const materials = ref([])

// 获取字典数据
async function fetchDicts() {
  try {
    const materialData = await api.dicts.getMaterials()
    materials.value = materialData
  } catch (error) {
    console.error('获取材质数据失败:', error)
  }
}

// 获取批次列表
async function fetchBatches() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      size: pagination.value.size
    }
    if (filters.value.material_id) {
      params.material_id = filters.value.material_id
    }
    const data = await api.batches.getBatches(params)
    batches.value = data.items || data
    if (data.pagination) {
      pagination.value = data.pagination
    } else {
      // API may return pagination fields at top level
      pagination.value.total = data.total || batches.value.length
      pagination.value.pages = data.pages || 1
    }
  } catch (error) {
    console.error('获取批次列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  pagination.value.page = 1
  fetchBatches()
}

// 重置筛选
function resetFilters() {
  filters.value.material_id = null
  handleSearch()
}

// 分页变化
function onPageChange(newPage) {
  pagination.value.page = newPage
  fetchBatches()
}

// 分摊方式中文映射
function allocMethodLabel(method) {
  const map = {
    equal: '均摊',
    by_weight: '按克重',
    by_price: '按售价比例'
  }
  return map[method] || method
}

// 回本进度计算
function getPaybackInfo(batch) {
  const soldCount = batch.sold_count || 0
  const quantity = batch.quantity || 1
  const totalCost = batch.total_cost || 0
  const soldRevenue = batch.sold_revenue || batch.revenue || 0

  // 回本率 = 已回款 / 总成本
  const paybackRate = totalCost > 0 ? soldRevenue / totalCost : 0

  // 状态判断
  let status = 'new'
  if (soldCount > 0 && paybackRate < 1) {
    status = 'selling'
  } else if (paybackRate >= 1) {
    status = 'paid_back'
  }

  // 如果有后端返回的 payback_rate 或 status，优先使用
  if (batch.payback_rate !== undefined) {
    const rate = batch.payback_rate
    return { paybackRate: rate, status: batch.status || (rate >= 1 ? 'paid_back' : soldCount > 0 ? 'selling' : 'new') }
  }

  return { paybackRate, status }
}

function statusText(s) {
  const map = { new: '未开始', selling: '销售中', paid_back: '已回本', cleared: '清仓完毕' }
  return map[s] || s
}

function statusClass(s) {
  const map = {
    new: 'bg-gray-100 text-gray-700',
    selling: 'bg-blue-100 text-blue-800',
    paid_back: 'bg-green-100 text-green-800',
    cleared: 'bg-green-100 text-green-800'
  }
  return map[s] || 'bg-gray-100 text-gray-700'
}

// 跳转到该批次下的货品
function goToBatchItems(batch) {
  router.push(`/inventory?batch=${batch.id}`)
}

// 计算库龄（天数）
function calculateAging(purchaseDate) {
  if (!purchaseDate) return null
  const purchase = new Date(purchaseDate)
  if (isNaN(purchase.getTime())) return null
  const today = new Date()
  const diffTime = today - purchase
  return Math.floor(diffTime / (1000 * 60 * 60 * 24))
}

// 统计数据
const totalCost = computed(() => {
  return batches.value.reduce((sum, b) => sum + (b.total_cost || 0), 0)
})
const totalQuantity = computed(() => {
  return batches.value.reduce((sum, b) => sum + (b.quantity || 0), 0)
})
const paidBackCount = computed(() => {
  return batches.value.filter(b => {
    const info = getPaybackInfo(b)
    return info.status === 'paid_back' || info.status === 'cleared'
  }).length
})

onMounted(() => {
  fetchDicts()
  fetchBatches()
})
</script>

<template>
  <div>
    <!-- 页面标题和操作 -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">批次列表</h1>
        <p class="mt-1 text-sm text-gray-600">管理所有通货批次，查看回本进度</p>
      </div>
      <div class="mt-4 sm:mt-0">
        <router-link to="/inventory/batch" class="btn btn-success inline-flex items-center">
          <span class="mr-2">➕</span>
          新建批次
        </router-link>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div v-if="!loading && batches.length > 0" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="card text-center">
        <div class="text-sm text-gray-500">总批次数</div>
        <div class="text-2xl font-bold text-gray-900 mt-1">{{ pagination.total }}</div>
        <div class="text-xs text-gray-500 mt-1">个批次</div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">总件数</div>
        <div class="text-2xl font-bold text-blue-600 mt-1">{{ totalQuantity }}</div>
        <div class="text-xs text-gray-500 mt-1">件货品</div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">总成本</div>
        <div class="text-2xl font-bold text-jade-600 mt-1">¥{{ totalCost.toFixed(2) }}</div>
        <div class="text-xs text-gray-500 mt-1">占用资金</div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">已回本</div>
        <div class="text-2xl font-bold text-green-600 mt-1">{{ paidBackCount }}</div>
        <div class="text-xs text-gray-500 mt-1">个批次</div>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="card mb-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
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

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      <p class="mt-2 text-gray-500">加载中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="batches.length === 0" class="card text-center py-12">
      <div class="text-gray-400 text-5xl mb-4">📦</div>
      <h3 class="text-lg font-medium text-gray-900 mb-1">暂无批次</h3>
      <p class="text-gray-500 mb-6">还没有创建任何批次，点击右上角按钮开始入库</p>
      <router-link to="/inventory/batch" class="btn btn-success">
        创建批次
      </router-link>
    </div>

    <!-- 批次列表 -->
    <div v-else>
      <!-- 桌面端：表格布局（移动端隐藏） -->
      <div class="table-container hidden md:block">
        <table class="table">
          <thead>
            <tr>
              <th class="w-32">批次编号</th>
              <th class="w-24">材质</th>
              <th class="w-24">器型</th>
              <th class="w-20 text-right">数量</th>
              <th class="w-24 text-right">已售/总数</th>
              <th class="w-28 text-right">总成本</th>
              <th class="w-24">分摊方式</th>
              <th class="w-36 text-right">回本进度</th>
              <th>状态</th>
              <th class="w-28">进货日期</th>
              <th class="w-28">供应商</th>
              <th class="w-48 text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="batch in batches"
              :key="batch.id"
              class="hover:bg-gray-50 cursor-pointer"
              @click="goToBatchItems(batch)"
            >
              <td class="font-mono text-sm">{{ batch.batch_code }}</td>
              <td>{{ batch.material?.name || batch.material_name || '-' }}</td>
              <td>{{ batch.type?.name || batch.type_name || '-' }}</td>
              <td class="text-right">{{ batch.quantity }}</td>
              <td class="text-right">
                <span :class="{ 'text-emerald-600 font-medium': batch.sold_count > 0 }">
                  {{ batch.sold_count || 0 }}/{{ batch.quantity }}
                </span>
              </td>
              <td class="text-right font-medium">¥{{ (batch.total_cost || 0).toFixed(2) }}</td>
              <td>
                <span class="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">
                  {{ allocMethodLabel(batch.cost_alloc_method) }}
                </span>
              </td>
              <td class="text-right">
                <div class="flex items-center justify-end space-x-2">
                  <div class="w-20 bg-gray-200 rounded-full h-2">
                    <div
                      class="h-full rounded-full transition-all"
                      :class="getPaybackInfo(batch).paybackRate >= 1 ? 'bg-green-500' : 'bg-blue-500'"
                      :style="{ width: `${Math.min(getPaybackInfo(batch).paybackRate * 100, 100)}%` }"
                    ></div>
                  </div>
                  <span class="text-xs font-medium w-12 text-right">
                    {{ (getPaybackInfo(batch).paybackRate * 100).toFixed(1) }}%
                  </span>
                </div>
              </td>
              <td>
                <span :class="statusClass(getPaybackInfo(batch).status)" class="px-2 py-1 text-xs rounded-full font-medium">
                  {{ statusText(getPaybackInfo(batch).status) }}
                </span>
              </td>
              <td class="text-sm">{{ batch.purchase_date || '-' }}</td>
              <td class="text-sm">{{ batch.supplier?.name || batch.supplier_name || '-' }}</td>
              <td class="text-right">
                <div class="flex items-center justify-end space-x-3">
                  <button
                    class="text-primary-600 hover:text-primary-800 text-sm font-medium"
                    @click.stop="goToBatchItems(batch)"
                    title="查看该批次货品"
                  >
                    查看货品
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
          v-for="batch in batches"
          :key="batch.id"
          class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
          @click="goToBatchItems(batch)"
        >
          <!-- 卡片头部：批次编号和状态 -->
          <div class="flex items-start justify-between mb-3">
            <div>
              <div class="text-sm font-medium text-gray-900">{{ batch.batch_code }}</div>
              <div class="text-xs text-gray-500 mt-1">
                {{ batch.material?.name || batch.material_name || '-' }}
                <span v-if="batch.type?.name || batch.type_name"> · {{ batch.type?.name || batch.type_name }}</span>
              </div>
            </div>
            <span :class="statusClass(getPaybackInfo(batch).status)" class="px-2 py-1 text-xs rounded-full font-medium">
              {{ statusText(getPaybackInfo(batch).status) }}
            </span>
          </div>

          <!-- 回本进度条 -->
          <div class="mb-3">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-500">回本进度</span>
              <span class="text-xs font-medium" :class="getPaybackInfo(batch).paybackRate >= 1 ? 'text-green-600' : 'text-blue-600'">
                {{ (getPaybackInfo(batch).paybackRate * 100).toFixed(1) }}%
              </span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="h-full rounded-full transition-all"
                :class="getPaybackInfo(batch).paybackRate >= 1 ? 'bg-green-500' : 'bg-blue-500'"
                :style="{ width: `${Math.min(getPaybackInfo(batch).paybackRate * 100, 100)}%` }"
              ></div>
            </div>
          </div>

          <!-- 关键信息 -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <div class="text-xs text-gray-500">已售/总数</div>
              <div class="text-sm font-medium text-gray-900">{{ batch.sold_count || 0 }}/{{ batch.quantity }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500">总成本</div>
              <div class="text-sm font-medium text-jade-600">¥{{ (batch.total_cost || 0).toFixed(2) }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500">分摊方式</div>
              <div class="text-sm font-medium text-gray-900">{{ allocMethodLabel(batch.cost_alloc_method) }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500">进货日期</div>
              <div class="text-sm font-medium text-gray-900">{{ batch.purchase_date || '-' }}</div>
            </div>
          </div>

          <!-- 供应商 -->
          <div v-if="batch.supplier?.name || batch.supplier_name" class="mt-2 pt-2 border-t border-gray-100">
            <span class="text-xs text-gray-500">供应商: </span>
            <span class="text-xs text-gray-700">{{ batch.supplier?.name || batch.supplier_name }}</span>
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
  </div>
</template>

<style scoped>
.form-label {
  @apply block text-sm font-medium text-gray-700 mb-1;
}

.form-input {
  @apply block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm;
}

.btn {
  @apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500;
}

.btn-secondary {
  @apply bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500;
}

.btn-success {
  @apply bg-green-600 text-white hover:bg-green-700 focus:ring-green-500;
}
</style>
