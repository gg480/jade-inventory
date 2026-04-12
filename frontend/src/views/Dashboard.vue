<script setup>
import { ref, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import api from '../api'
import toast from '../composables/useToast'

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

// ECharts 实例
const categoryChartRef = ref(null)
const channelChartRef = ref(null)
const trendChartRef = ref(null)
let categoryChart = null
let channelChart = null
let trendChart = null

// 获取概览数据
async function fetchSummary() {
  loading.value.summary = true
  try {
    summary.value = await api.dashboard.getSummary({ aging_days: filters.value.min_days })
  } catch (error) {
    // 静默处理
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
    await nextTick()
    renderCategoryChart()
  } catch (error) {
    // 静默处理
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
    await nextTick()
    renderChannelChart()
  } catch (error) {
    // 静默处理
  } finally {
    loading.value.channel = false
  }
}

// 获取销售趋势
async function fetchSalesTrend() {
  loading.value.trend = true
  try {
    salesTrend.value = await api.dashboard.getSalesTrend({ months: filters.value.months })
    await nextTick()
    renderTrendChart()
  } catch (error) {
    // 静默处理
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
    // 静默处理
  } finally {
    loading.value.batch = false
  }
}

// 获取压货预警
async function fetchStockAging() {
  loading.value.aging = true
  try {
    const response = await api.dashboard.getStockAging({ min_days: filters.value.min_days })
    if (response && Array.isArray(response.items)) {
      stockAging.value = response.items
    } else if (Array.isArray(response)) {
      stockAging.value = response
    } else {
      stockAging.value = []
    }
  } catch (error) {
    // 静默处理
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

// ===================== ECharts 图表 =====================

// 玉器配色方案
const chartColors = ['#059669', '#2563eb', '#9333ea', '#d97706', '#dc2626', '#0891b2', '#4f46e5', '#c026d3', '#65a30d', '#ea580c']

function initCharts() {
  if (categoryChartRef.value) {
    categoryChart = echarts.init(categoryChartRef.value)
  }
  if (channelChartRef.value) {
    channelChart = echarts.init(channelChartRef.value)
  }
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }
}

// 品类利润柱状图
function renderCategoryChart() {
  if (!categoryChart) return
  const data = profitByCategory.value
  if (!data || data.length === 0) {
    categoryChart.clear()
    return
  }

  const sortedData = [...data].sort((a, b) => b.profit - a.profit)
  const names = sortedData.map(d => d.material_name)
  const profits = sortedData.map(d => d.profit)
  const revenues = sortedData.map(d => d.revenue)
  const costs = sortedData.map(d => d.cost)
  const margins = sortedData.map(d => (d.profit_margin * 100).toFixed(1))

  categoryChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(params) {
        const idx = params[0].dataIndex
        const d = sortedData[idx]
        return `<strong>${d.material_name}</strong><br/>` +
          `销售额: ¥${d.revenue.toFixed(2)}<br/>` +
          `成本: ¥${d.cost.toFixed(2)}<br/>` +
          `毛利: ¥${d.profit.toFixed(2)}<br/>` +
          `毛利率: ${(d.profit_margin * 100).toFixed(1)}%<br/>` +
          `件数: ${d.sales_count}`
      }
    },
    grid: { left: 80, right: 40, top: 12, bottom: 20 },
    xAxis: {
      type: 'value',
      axisLabel: { formatter: v => v >= 10000 ? `${(v / 10000).toFixed(1)}万` : v.toFixed(0) }
    },
    yAxis: {
      type: 'category',
      data: names.reverse(),
      axisLabel: { width: 70, overflow: 'truncate' }
    },
    series: [
      {
        name: '利润',
        type: 'bar',
        data: profits.reverse(),
        itemStyle: {
          color: (params) => chartColors[params.dataIndex % chartColors.length],
          borderRadius: [0, 4, 4, 0]
        },
        label: {
          show: true,
          position: 'right',
          formatter: p => `¥${p.value.toFixed(0)}`,
          fontSize: 11
        }
      }
    ]
  }, true)
}

// 渠道利润饼图
function renderChannelChart() {
  if (!channelChart) return
  const data = profitByChannel.value
  if (!data || data.length === 0) {
    channelChart.clear()
    return
  }

  const channelLabelMap = { store: '门店', wechat: '微信', ecommerce: '电商' }
  const pieData = data.map((d, i) => ({
    name: channelLabelMap[d.channel] || d.channel,
    value: Math.round(d.revenue * 100) / 100,
    profit: d.profit,
    profitMargin: d.profit_margin,
    salesCount: d.sales_count,
    itemStyle: { color: chartColors[i % chartColors.length] }
  }))

  channelChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter(p) {
        const d = p.data
        return `<strong>${d.name}</strong><br/>` +
          `销售额: ¥${d.value.toFixed(2)}<br/>` +
          `毛利: ¥${d.profit.toFixed(2)}<br/>` +
          `毛利率: ${(d.profitMargin * 100).toFixed(1)}%<br/>` +
          `件数: ${d.salesCount}`
      }
    },
    legend: {
      bottom: 0,
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { fontSize: 13 }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '42%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: {
        show: true,
        formatter: '{b}\n¥{c}',
        fontSize: 12
      },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.2)' }
      },
      data: pieData
    }]
  }, true)
}

// 销售趋势折线图
function renderTrendChart() {
  if (!trendChart) return
  const data = salesTrend.value
  if (!data || data.length === 0) {
    trendChart.clear()
    return
  }

  const xData = data.map(d => d.year_month)
  const revenueData = data.map(d => d.revenue)
  const profitData = data.map(d => d.profit)
  const countData = data.map(d => d.sales_count)

  trendChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter(params) {
        const date = params[0].axisValue
        let html = `<strong>${date}</strong><br/>`
        params.forEach(p => {
          if (p.seriesName === '销量') {
            html += `${p.marker} 销量: ${p.value} 件<br/>`
          } else {
            html += `${p.marker} ${p.seriesName}: ¥${p.value.toFixed(2)}<br/>`
          }
        })
        return html
      }
    },
    legend: {
      data: ['销售额', '毛利', '销量'],
      bottom: 0,
      itemWidth: 16,
      itemHeight: 8
    },
    grid: { left: 60, right: 60, top: 16, bottom: 36 },
    xAxis: {
      type: 'category',
      data: xData,
      axisLabel: { fontSize: 11, rotate: xData.length > 12 ? 30 : 0 }
    },
    yAxis: [
      {
        type: 'value',
        name: '金额(¥)',
        axisLabel: { formatter: v => v >= 10000 ? `${(v / 10000).toFixed(1)}万` : v.toFixed(0) }
      },
      {
        type: 'value',
        name: '件数',
        splitLine: { show: false },
        axisLabel: { formatter: v => v.toFixed(0) }
      }
    ],
    series: [
      {
        name: '销售额',
        type: 'line',
        data: revenueData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2, color: '#2563eb' },
        itemStyle: { color: '#2563eb' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(37,99,235,0.15)' },
            { offset: 1, color: 'rgba(37,99,235,0.01)' }
          ])
        }
      },
      {
        name: '毛利',
        type: 'line',
        data: profitData,
        smooth: true,
        symbol: 'diamond',
        symbolSize: 6,
        lineStyle: { width: 2, color: '#059669' },
        itemStyle: { color: '#059669' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(5,150,105,0.15)' },
            { offset: 1, color: 'rgba(5,150,105,0.01)' }
          ])
        }
      },
      {
        name: '销量',
        type: 'bar',
        yAxisIndex: 1,
        data: countData,
        barWidth: 16,
        itemStyle: { color: 'rgba(147,51,234,0.25)', borderRadius: [3, 3, 0, 0] }
      }
    ]
  }, true)
}

// 窗口大小变化时自适应
function handleResize() {
  categoryChart?.resize()
  channelChart?.resize()
  trendChart?.resize()
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
    toast.success('销售数据导出成功')
  } catch (e) {
    // 错误已由拦截器处理
  }
}
async function handleExportBatches() {
  try {
    const resp = await api.exportData.batches({})
    _downloadBlob(resp, `批次回本_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx`)
    toast.success('批次数据导出成功')
  } catch (e) {
    // 错误已由拦截器处理
  }
}

onMounted(() => {
  refreshAll()
  nextTick(() => {
    initCharts()
    // 数据加载完成后渲染图表
    setTimeout(() => {
      renderCategoryChart()
      renderChannelChart()
      renderTrendChart()
    }, 800)
  })
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  categoryChart?.dispose()
  channelChart?.dispose()
  trendChart?.dispose()
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
      <div class="mt-4 sm:mt-0 flex flex-wrap items-center gap-2">
        <div class="flex items-center space-x-1">
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
        <button @click="handleExportSales" class="btn btn-secondary" title="导出销售Excel">
          导出销售
        </button>
        <button @click="handleExportBatches" class="btn btn-secondary" title="导出批次回本Excel">
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
        <div class="text-sm text-gray-500">压货预警</div>
        <div class="text-2xl font-bold text-red-600 mt-1">{{ stockAging.length }}</div>
        <div class="text-xs text-gray-500 mt-1">超过 {{ filters.min_days }} 天未售出</div>
      </div>
      <div class="card text-center">
        <div class="text-sm text-gray-500">批次回本</div>
        <div class="text-2xl font-bold text-green-600 mt-1">{{ batchProfit.filter(b => b.status === 'paid_back' || b.status === 'cleared').length }}</div>
        <div class="text-xs text-gray-500 mt-1">已回本批次</div>
      </div>
    </div>

    <!-- 按品类利润 — ECharts 柱状图 -->
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
      <div v-else ref="categoryChartRef" style="width: 100%; height: 300px;"></div>
    </div>

    <!-- 按渠道利润和销售趋势 — ECharts 双图 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- 按渠道利润 — 饼图 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">按渠道利润</h2>
        <div v-if="loading.channel" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        </div>
        <div v-else-if="profitByChannel.length === 0" class="text-center py-8 text-gray-500">
          暂无数据
        </div>
        <div v-else ref="channelChartRef" style="width: 100%; height: 320px;"></div>
      </div>

      <!-- 销售趋势 — 折线图 -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">销售趋势</h2>
          <select v-model="filters.months" @change="fetchSalesTrend" class="text-sm border border-gray-300 rounded px-2 py-1">
            <option :value="3">最近3个月</option>
            <option :value="6">最近6个月</option>
            <option :value="12">最近12个月</option>
            <option :value="24">最近24个月</option>
          </select>
        </div>
        <div v-if="loading.trend" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        </div>
        <div v-else-if="salesTrend.length === 0" class="text-center py-8 text-gray-500">
          暂无数据
        </div>
        <div v-else ref="trendChartRef" style="width: 100%; height: 320px;"></div>
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
