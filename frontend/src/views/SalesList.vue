<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const sales = ref([])
const loading = ref(false)
const pagination = ref({
  page: 1,
  size: 20,
  total: 0,
  pages: 0
})

const filters = ref({
  channel: '',
  start_date: '',
  end_date: ''
})

// 获取销售记录
async function fetchSales() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      size: pagination.value.size,
      ...filters.value
    }
    const data = await api.sales.getSales(params)
    sales.value = data.items
    pagination.value = data.pagination
  } catch (error) {
    console.error('获取销售记录失败:', error)
  } finally {
    loading.value = false
  }
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
    end_date: ''
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

// 渠道颜色
function channelColor(channel) {
  const map = {
    store: 'bg-blue-100 text-blue-800',
    wechat: 'bg-green-100 text-green-800',
    ecommerce: 'bg-purple-100 text-purple-800'
  }
  return map[channel] || 'bg-gray-100 text-gray-800'
}

onMounted(() => {
  fetchSales()
})
</script>

<template>
  <div>
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">销售记录</h1>
      <p class="mt-1 text-sm text-gray-600">查看所有销售出库记录和利润统计</p>
    </div>

    <!-- 筛选区域 -->
    <div class="card mb-6">
      <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
        <!-- 渠道筛选 -->
        <div>
          <label class="form-label">销售渠道</label>
          <select v-model="filters.channel" class="form-input">
            <option value="">全部渠道</option>
            <option value="store">门店</option>
            <option value="wechat">微信</option>
            <option value="ecommerce">电商</option>
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

    <!-- 统计摘要 -->
    <div v-if="sales.length > 0" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="card text-center">
        <div class="text-sm text-gray-500">总销售额</div>
        <div class="text-2xl font-bold text-gray-900 mt-1">
          ¥{{ sales.reduce((sum, sale) => sum + sale.actual_price, 0).toFixed(2) }}
        </div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">总毛利</div>
        <div class="text-2xl font-bold text-jade-600 mt-1">
          ¥{{ sales.reduce((sum, sale) => sum + sale.gross_profit, 0).toFixed(2) }}
        </div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">销售件数</div>
        <div class="text-2xl font-bold text-gray-900 mt-1">{{ sales.length }}</div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">平均毛利率</div>
        <div class="text-2xl font-bold text-blue-600 mt-1">
          {{ (sales.reduce((sum, sale) => sum + sale.gross_margin, 0) / sales.length * 100).toFixed(1) }}%
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
      <p class="text-gray-500">还没有任何销售出库记录</p>
    </div>

    <!-- 销售记录列表 -->
    <div v-else>
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th class="w-32">货品编号</th>
              <th>材质</th>
              <th class="w-32">成交日期</th>
              <th class="w-32">渠道</th>
              <th class="w-32 text-right">成交价</th>
              <th class="w-32 text-right">进价</th>
              <th class="w-32 text-right">毛利</th>
              <th class="w-32 text-right">毛利率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sale in sales" :key="sale.id">
              <td class="font-mono text-sm">{{ sale.sku_code }}</td>
              <td>{{ sale.material_name }}</td>
              <td>{{ sale.sale_date }}</td>
              <td>
                <span :class="`px-2 py-1 text-xs rounded-full ${channelColor(sale.channel)}`">
                  {{ channelName(sale.channel) }}
                </span>
              </td>
              <td class="text-right font-medium">¥{{ sale.actual_price.toFixed(2) }}</td>
              <td class="text-right text-gray-600">¥{{ sale.cost_price.toFixed(2) }}</td>
              <td class="text-right font-bold text-jade-600">¥{{ sale.gross_profit.toFixed(2) }}</td>
              <td class="text-right font-bold text-blue-600">{{ (sale.gross_margin * 100).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="flex items-center justify-between mt-6">
        <div class="text-sm text-gray-700">
          显示第 {{ (pagination.page - 1) * pagination.size + 1 }} 到
          {{ Math.min(pagination.page * pagination.size, pagination.total) }} 条，
          共 {{ pagination.total }} 条记录
        </div>
        <div class="flex space-x-2">
          <button
            @click="pagination.page--; fetchSales()"
            :disabled="pagination.page <= 1"
            class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            上一页
          </button>
          <span class="px-3 py-1 text-sm">
            第 {{ pagination.page }} / {{ pagination.pages }} 页
          </span>
          <button
            @click="pagination.page++; fetchSales()"
            :disabled="pagination.page >= pagination.pages"
            class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  </div>
</template>