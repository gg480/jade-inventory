<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'
import Pagination from './Pagination.vue'

// 数据
const sales = ref([])
const loading = ref(false)
const pagination = ref({
  page: 1,
  size: 20,
  total: 0,
  pages: 0
})

// 筛选条件
const filters = ref({
  channel: '',
  start_date: '',
  end_date: '',
  customer_id: ''
})

// 客户列表（用于下拉）
const customers = ref([])
const customerLoading = ref(false)

// 获取客户列表
async function fetchCustomers() {
  customerLoading.value = true
  try {
    const data = await api.customers.getCustomers({ page: 1, size: 500 })
    customers.value = data.items || data
  } catch (error) {
    console.error('获取客户列表失败:', error)
  } finally {
    customerLoading.value = false
  }
}

// 获取销售记录
async function fetchSales() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      size: pagination.value.size,
      ...filters.value
    }
    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })
    const data = await api.sales.getSales(params)
    sales.value = data.items
    pagination.value = data.pagination
  } catch (error) {
    console.error('获取销售记录失败:', error)
  } finally {
    loading.value = false
  }
}

// 分页变化
function onPageChange(newPage) {
  pagination.value.page = newPage
  fetchSales()
}

// 搜索
function handleSearch() {
  pagination.value.page = 1
  fetchSales()
}

// 重置筛选
function resetFilters() {
  filters.value = {
    channel: '',
    start_date: '',
    end_date: '',
    customer_id: ''
  }
  handleSearch()
}

// 渠道显示名称
function channelName(channel) {
  const map = {
    store: '门店',
    wechat: '微信',
    ecommerce: '电商'
  }
  return map[channel] || channel
}

// 毛利颜色
function profitColor(profit) {
  return profit >= 0 ? 'text-green-600' : 'text-red-600'
}

// 移动端检测
const isMobile = computed(() => window.innerWidth < 768)

// 初始化
onMounted(() => {
  fetchCustomers()
  fetchSales()
})
</script>

<template>
  <div>
    <!-- 筛选区域 -->
    <div class="card mb-6">
      <div class="grid grid-cols-1 md:grid-cols-6 gap-4">
        <!-- 渠道筛选 -->
        <div>
          <label class="form-label">销售渠道</label>
          <select v-model="filters.channel" class="form-input">
            <option value="">全部渠道</option>
            <option value="store">门店</option>
            <option value="wechat">微信</option>
          </select>
        </div>

        <!-- 日期范围 -->
        <div>
          <label class="form-label">开始日期</label>
          <input v-model="filters.start_date" type="date" class="form-input" />
        </div>
        <div>
          <label class="form-label">结束日期</label>
          <input v-model="filters.end_date" type="date" class="form-input" />
        </div>

        <!-- 客户筛选 -->
        <div>
          <label class="form-label">客户</label>
          <select v-model="filters.customer_id" class="form-input" :disabled="customerLoading">
            <option value="">全部客户</option>
            <option v-for="customer in customers" :key="customer.id" :value="customer.id">
              {{ customer.name }}
            </option>
          </select>
        </div>

        <!-- 操作按钮 -->
        <div class="flex items-end space-x-2">
          <button @click="handleSearch" class="btn btn-primary flex-1">
            搜索
          </button>
          <button @click="resetFilters" class="btn btn-secondary">
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
    <div v-else-if="sales.length === 0" class="card text-center py-12">
      <div class="text-gray-400 text-5xl mb-4">💰</div>
      <h3 class="text-lg font-medium text-gray-900 mb-1">暂无销售记录</h3>
      <p class="text-gray-500">暂无符合条件的销售记录</p>
    </div>

    <!-- 销售记录列表 -->
    <div v-else>
      <!-- 桌面端表格 (md以上显示) -->
      <div class="hidden md:block">
        <div class="table-container">
          <table class="table">
            <thead>
              <tr>
                <th class="w-32">销售单号</th>
                <th class="w-32">货品编号</th>
                <th>名称</th>
                <th class="w-32 text-right">成交价</th>
                <th class="w-32 text-right">成本</th>
                <th class="w-32 text-right">毛利</th>
                <th class="w-32">渠道</th>
                <th class="w-32">日期</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="sale in sales" :key="sale.id">
                <td class="font-mono text-sm">{{ sale.sale_no }}</td>
                <td class="font-mono text-sm">{{ sale.item_sku }}</td>
                <td>{{ sale.item_name }}</td>
                <td class="text-right font-medium">¥{{ sale.actual_price.toFixed(2) }}</td>
                <td class="text-right text-gray-600">¥{{ sale.cost?.toFixed(2) || '0.00' }}</td>
                <td class="text-right font-bold" :class="profitColor(sale.gross_profit)">
                  ¥{{ sale.gross_profit.toFixed(2) }}
                </td>
                <td>
                  <span :class="`px-2 py-1 text-xs rounded-full ${sale.channel === 'store' ? 'bg-blue-100 text-blue-800' : sale.channel === 'wechat' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`">
                    {{ channelName(sale.channel) }}
                  </span>
                </td>
                <td>{{ sale.sale_date }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 移动端卡片 (md以下显示) -->
      <div class="md:hidden space-y-4">
        <div v-for="sale in sales" :key="sale.id" class="card p-4">
          <div class="flex justify-between items-start mb-2">
            <div>
              <h3 class="font-medium text-gray-900">{{ sale.item_name }}</h3>
              <p class="text-sm text-gray-500">{{ sale.sale_date }}</p>
            </div>
            <span :class="`px-2 py-1 text-xs rounded-full ${sale.channel === 'store' ? 'bg-blue-100 text-blue-800' : sale.channel === 'wechat' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`">
              {{ channelName(sale.channel) }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-4 mt-4">
            <div>
              <div class="text-sm text-gray-500">成交价</div>
              <div class="font-medium">¥{{ sale.actual_price.toFixed(2) }}</div>
            </div>
            <div>
              <div class="text-sm text-gray-500">毛利</div>
              <div class="font-bold" :class="profitColor(sale.gross_profit)">
                ¥{{ sale.gross_profit.toFixed(2) }}
              </div>
            </div>
          </div>
          <div class="mt-2 text-xs text-gray-400">
            货品编号: {{ sale.item_sku }} | 销售单号: {{ sale.sale_no }}
          </div>
        </div>
      </div>

      <!-- 分页 -->
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
/* 表格样式 */
.table-container {
  @apply overflow-x-auto border border-gray-200 rounded-lg;
}
.table {
  @apply min-w-full divide-y divide-gray-200;
}
.table thead {
  @apply bg-gray-50;
}
.table th {
  @apply px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider;
}
.table tbody {
  @apply bg-white divide-y divide-gray-200;
}
.table td {
  @apply px-4 py-3 whitespace-nowrap text-sm;
}
/* 卡片样式 */
.card {
  @apply bg-white rounded-lg border border-gray-200 shadow-sm;
}
/* 表单样式 */
.form-label {
  @apply block text-sm font-medium text-gray-700 mb-1;
}
.form-input {
  @apply block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-primary-500;
}
/* 按钮样式 */
.btn {
  @apply inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2;
}
.btn-primary {
  @apply bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500;
}
.btn-secondary {
  @apply bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-gray-500;
}
</style>