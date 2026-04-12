<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'

const summary = ref(null)
const profitByCategory = ref([])
const profitByChannel = ref([])
const salesTrend = ref([])
const stockAging = ref([])
const batchProfit = ref([])
const loading = ref({
  summary: false,
  category: false,
  channel: false,
  trend: false,
  aging: false,
  batch: false
})

const filters = ref({
  start_date: '',
  end_date: '',
  months: 12,
  min_days: 90
})

// 获取概览数据
async function fetchSummary() {
  loading.value.summary = true
  try {
    summary.value = await api.dashboard.getSummary({ aging_days: filters.value.min_days })
  } catch (error) {
    console.error('获取概览数据失败:', error)
  } finally {
    loading.value.summary = false
  }
}

// 获取按品类利润
async function fetchProfitByCategory() {
  loading.value.category = true
  try {
    const params = {}
    if (filters.value.start_date) params.start_date = filters.value.start_date
    if (filters.value.end_date) params.end_date = filters.value.end_date
    profitByCategory.value = await api.dashboard.getProfitByCategory(params)
  } catch (error) {
    console.error('获取品类利润失败:', error)
  } finally {
    loading.value.category = false
  }
}

// 获取按渠道利润
async function fetchProfitByChannel() {
  loading.value.channel = true
  try {
    const params = {}
    if (filters.value.start_date) params.start_date = filters.value.start_date
    if (filters.value.end_date) params.end_date = filters.value.end_date
    profitByChannel.value = await api.dashboard.getProfitByChannel(params)
  } catch (error) {
    console.error('获取渠道利润失败:', error)
  } finally {
    loading.value.channel = false
  }
}

// 获取销售趋势
async function fetchSalesTrend() {
  loading.value.trend = true
  try {
    salesTrend.value = await api.dashboard.getSalesTrend({ months: filters.value.months })
  } catch (error) {
    console.error('获取销售趋势失败:', error)
  } finally {
    loading.value.trend = false
  }
}

// 获取批次回本看板
async function fetchBatchProfit() {
  loading.value.batch = true
  try {
    batchProfit.value = await api.dashboard.getBatchProfit({}) || []
  } catch (error) {
    console.error('获取批次回本看板失败:', error)
  } finally {
    loading.value.batch = false
  }
}

// 获取压货预警
async function fetchStockAging() {
  loading.value.aging = true
  try {
    const response = await api.dashboard.getStockAging({ min_days: filters.value.min_days })
    // API 返回 { items: [...], total_items, total_value }
    if (response && Array.isArray(response.items)) {
      stockAging.value = response.items
    } else if (Array.isArray(response)) {
      stockAging.value = response
    } else {
      stockAging.value = []
    }
  } catch (error) {
    console.error('获取压货预警失败:', error)
  } finally {
    loading.value.aging = false
  }
}

// 刷新所有数据
function refreshAll() {
  fetchSummary()
  fetchProfitByCategory()
  fetchProfitByChannel()
  fetchSalesTrend()
  fetchStockAging()
  fetchBatchProfit()
}

// 计算品类利润最大值（用于图表）
const categoryMaxProfit = computed(() => {
  if (profitByCategory.value.length === 0) return 0
  return Math.max(...profitByCategory.value.map(item => item.profit))
})

// 计算渠道利润最大值
const channelMaxProfit = computed(() => {
  if (profitByChannel.value.length === 0) return 0
  return Math.max(...profitByChannel.value.map(item => item.profit))
})

// 渠道显示名称
function channelName(channel) {
  const map = {
    store: '门店',
    wechat: '微信',
    ecommerce: '电商'
  }
  return map[channel] || channel
}

// 批次状态
function batchStatusText(s) {
  const map = { new: '未开始', selling: '销售中', paid_back: '已回本', cleared: '清仓完毕' }
  return map[s] || s
}
function batchStatusClass(s) {
  const map = { new: 'bg-gray-100 text-gray-700', selling: 'bg-blue-100 text-blue-800', paid_back: 'bg-green-100 text-green-800', cleared: 'bg-green-100 text-green-800' }
  return map[s] || 'bg-gray-100 text-gray-700'
}

// 导出Excel
function _downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}
async function handleExportSales() {
  try {
    const resp = await api.exportData.sales({ start_date: filters.value.start_date || undefined, end_date: filters.value.end_date || undefined })
    _downloadBlob(resp, `销售导出_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx`)
  } catch (e) { console.error('导出失败:', e) }
}
async function handleExportBatches() {
  try {
    const resp = await api.exportData.batches({})
    _downloadBlob(resp, `批次回本_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx`)
  } catch (e) { console.error('导出失败:', e) }
}

onMounted(() => {
  refreshAll()
})
</script>

<template>
  <div>
    <!-- 页面标题和筛选 -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">利润看板</h1>
        <p class="mt-1 text-sm text-gray-600">经营数据分析与压货预警</p>
      </div>
      <div class="mt-4 sm:mt-0 flex space-x-2">
        <div class="flex items-center space-x-2">
          <label class="text-sm text-gray-600">压货阈值:</label>
          <input
            v-model="filters.min_days"
            type="number"
            min="1"
            class="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
          />
          <span class="text-sm text-gray-600">天</span>
        </div>
        <button @click="refreshAll" class="btn btn-primary">
          刷新数据
        </button>
        <button @click="handleExportSales" class="btn btn-secondary ml-2" title="导出销售Excel">
          导出销售
        </button>
        <button @click="handleExportBatches" class="btn btn-secondary ml-2" title="导出批次回本Excel">
          导出批次
        </button>
      </div>
    </div>

    <!-- 概览卡片 -->
    <div v-if="summary" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="card text-center">
        <div class="text-sm text-gray-500">在库货品</div>
        <div class="text-2xl font-bold text-gray-900 mt-1">{{ summary.total_items }}</div>
        <div class="text-xs text-gray-500 mt-1">占用资金 ¥{{ summary.total_stock_value.toFixed(2) }}</div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">本月销售</div>
        <div class="text-2xl font-bold text-jade-600 mt-1">¥{{ summary.month_revenue.toFixed(2) }}</div>
        <div class="text-xs text-gray-500 mt-1">{{ summary.month_sold_count }} 件，毛利 ¥{{ summary.month_profit.toFixed(2) }}</div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">在库货品</div>
        <div class="text-2xl font-bold text-blue-600 mt-1">{{ summary.total_items }}</div>
        <div class="text-xs text-gray-500 mt-1">占用资金 ¥{{ summary.total_stock_value.toFixed(2) }}</div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">本月销售</div>
        <div class="text-2xl font-bold text-red-600 mt-1">{{ summary.month_sold_count }} 件</div>
        <div class="text-xs text-gray-500 mt-1">毛利 ¥{{ summary.month_profit.toFixed(2) }}</div>
      </div>
    </div>

    <!-- 按品类利润 -->
    <div class="card mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900">按品类利润统计</h2>
        <div class="flex space-x-2">
          <input v-model="filters.start_date" type="date" class="text-sm border border-gray-300 rounded px-2 py-1" placeholder="开始日期" />
          <input v-model="filters.end_date" type="date" class="text-sm border border-gray-300 rounded px-2 py-1" placeholder="结束日期" />
          <button @click="fetchProfitByCategory" class="text-sm btn btn-primary px-3 py-1">
            应用
          </button>
        </div>
      </div>

      <div v-if="loading.category" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
      </div>
      <div v-else-if="profitByCategory.length === 0" class="text-center py-8 text-gray-500">
        暂无数据
      </div>
      <div v-else class="space-y-4">
        <div v-for="item in profitByCategory" :key="item.material_id" class="border border-gray-200 rounded-lg p-4">
          <div class="flex items-center justify-between mb-2">
            <div class="font-medium text-gray-900">{{ item.material_name }}</div>
            <div class="text-lg font-bold text-jade-600">¥{{ item.profit.toFixed(2) }}</div>
          </div>
          <div class="flex items-center space-x-4 text-sm text-gray-600">
            <span>销售额: ¥{{ item.revenue.toFixed(2) }}</span>
            <span>成本: ¥{{ item.cost.toFixed(2) }}</span>
            <span>件数: {{ item.sales_count }}</span>
            <span class="font-medium text-blue-600">毛利率: {{ (item.profit_margin * 100).toFixed(1) }}%</span>
          </div>
          <div class="mt-2">
            <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                class="h-full bg-jade-500"
                :style="{ width: `${categoryMaxProfit > 0 ? (item.profit / categoryMaxProfit * 100) : 0}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 按渠道利润和销售趋势 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- 按渠道利润 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">按渠道利润</h2>
        <div v-if="loading.channel" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        </div>
        <div v-else-if="profitByChannel.length === 0" class="text-center py-8 text-gray-500">
          暂无数据
        </div>
        <div v-else class="space-y-4">
          <div v-for="item in profitByChannel" :key="item.channel" class="border border-gray-200 rounded-lg p-4">
            <div class="flex items-center justify-between mb-2">
              <span :class="{
                'px-2 py-1 text-sm rounded-full': true,
                'bg-blue-100 text-blue-800': item.channel === 'store',
                'bg-green-100 text-green-800': item.channel === 'wechat',
                'bg-purple-100 text-purple-800': item.channel === 'ecommerce'
              }">
                {{ channelName(item.channel) }}
              </span>
              <div class="text-lg font-bold text-jade-600">¥{{ item.profit.toFixed(2) }}</div>
            </div>
            <div class="flex items-center space-x-4 text-sm text-gray-600">
              <span>销售额: ¥{{ item.revenue.toFixed(2) }}</span>
              <span>件数: {{ item.sales_count }}</span>
              <span class="font-medium text-blue-600">毛利率: {{ (item.profit_margin * 100).toFixed(1) }}%</span>
            </div>
            <div class="mt-2">
              <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  class="h-full bg-jade-500"
                  :style="{ width: `${channelMaxProfit > 0 ? (item.profit / channelMaxProfit * 100) : 0}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 销售趋势 -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">销售趋势</h2>
          <div class="flex space-x-2">
            <select v-model="filters.months" @change="fetchSalesTrend" class="text-sm border border-gray-300 rounded px-2 py-1">
              <option :value="3">最近3个月</option>
              <option :value="6">最近6个月</option>
              <option :value="12">最近12个月</option>
              <option :value="24">最近24个月</option>
            </select>
          </div>
        </div>
        <div v-if="loading.trend" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        </div>
        <div v-else-if="salesTrend.length === 0" class="text-center py-8 text-gray-500">
          暂无数据
        </div>
        <div v-else class="space-y-3">
          <div v-for="item in salesTrend" :key="item.year_month" class="border border-gray-200 rounded-lg p-3">
            <div class="flex items-center justify-between mb-1">
              <div class="font-medium text-gray-900">{{ item.year_month }}</div>
              <div class="text-sm font-bold text-jade-600">毛利 ¥{{ item.profit.toFixed(2) }}</div>
            </div>
            <div class="flex items-center space-x-4 text-sm text-gray-600">
              <span>销售额: ¥{{ item.revenue.toFixed(2) }}</span>
              <span>销量: {{ item.sales_count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 批次回本看板 -->
    <div class="card mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900">批次回本看板</h2>
      </div>
      <div v-if="loading.batch" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
      </div>
      <div v-else-if="batchProfit.length === 0" class="text-center py-8 text-gray-500">
        暂无批次数据
      </div>
      <div v-else class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>批次编号</th>
              <th>材质</th>
              <th class="text-right">总成本</th>
              <th class="text-right">已售/总数</th>
              <th class="text-right">已回款</th>
              <th class="text-right">利润</th>
              <th class="text-right">回本进度</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="bp in batchProfit" :key="bp.batch_code" class="hover:bg-gray-50">
              <td class="font-mono text-sm">{{ bp.batch_code }}</td>
              <td>{{ bp.material_name }}</td>
              <td class="text-right">¥{{ bp.total_cost.toFixed(2) }}</td>
              <td class="text-right">{{ bp.sold_count }}/{{ bp.quantity }}</td>
              <td class="text-right font-medium">¥{{ bp.revenue.toFixed(2) }}</td>
              <td class="text-right" :class="bp.profit >= 0 ? 'text-green-600' : 'text-red-600'">
                ¥{{ bp.profit.toFixed(2) }}
              </td>
              <td class="text-right">
                <div class="flex items-center justify-end space-x-2">
                  <div class="w-20 bg-gray-200 rounded-full h-2">
                    <div
                      class="h-full rounded-full"
                      :class="bp.payback_rate >= 1 ? 'bg-green-500' : 'bg-blue-500'"
                      :style="{ width: `${Math.min(bp.payback_rate * 100, 100)}%` }"
                    ></div>
                  </div>
                  <span class="text-xs font-medium w-12 text-right">{{ (bp.payback_rate * 100).toFixed(1) }}%</span>
                </div>
              </td>
              <td>
                <span :class="batchStatusClass(bp.status)" class="px-2 py-1 text-xs rounded-full font-medium">
                  {{ batchStatusText(bp.status) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 压货预警 -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900">压货预警</h2>
        <div class="text-sm text-gray-600">
          在库超过 {{ filters.min_days }} 天的货品
        </div>
      </div>

      <div v-if="loading.aging" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
      </div>
      <div v-else-if="stockAging.length === 0" class="text-center py-8 text-gray-500">
        暂无压货，继续保持！
      </div>
      <div v-else>
        <div class="table-container">
          <table class="table">
            <thead>
              <tr>
                <th>货品编号</th>
                <th>材质</th>
                <th>器型</th>
                <th class="text-right">进价</th>
                <th class="text-right">标价</th>
                <th class="text-right">在库天数</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in stockAging" :key="item.item_id" class="hover:bg-red-50">
                <td class="font-mono text-sm">{{ item.sku_code }}</td>
                <td>{{ item.material_name }}</td>
                <td>{{ item.type_name || '-' }}</td>
                <td class="text-right font-medium">¥{{ item.cost_price.toFixed(2) }}</td>
                <td class="text-right">¥{{ item.selling_price.toFixed(2) }}</td>
                <td class="text-right font-bold text-red-600">{{ item.age_days }}天</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-600">
          共 {{ stockAging.length }} 件压货，占用资金 ¥{{ stockAging.reduce((sum, item) => sum + (item.allocated_cost || item.cost_price || 0), 0).toFixed(2) }}
        </div>
      </div>
    </div>
  </div>
</template>