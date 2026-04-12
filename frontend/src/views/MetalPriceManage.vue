<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">贵金属市价管理</h1>

    <!-- 当前市价列表 -->
    <div class="mb-8">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-gray-800">当前市价</h2>
        <div class="text-sm text-gray-500">
          只显示贵金属材质（有克重单价的材质）
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading.currentPrices" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p class="mt-2 text-gray-600">加载中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="currentPrices.length === 0" class="bg-gray-50 rounded-lg p-6 text-center">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2-1.343-2-3-2z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14c-3.314 0-6-1.343-6-3v6c0 1.657 2.686 3 6 3s6-1.343 6-3v-6c0 1.657-2.686 3-6 3z" />
        </svg>
        <p class="mt-2 text-gray-600">暂无贵金属市价记录</p>
        <p class="text-sm text-gray-500 mt-1">请先在材质管理中设置贵金属材质的克重单价</p>
      </div>

      <!-- 有数据时显示 -->
      <div v-else>
        <!-- 表格（桌面） -->
        <div class="hidden md:block overflow-x-auto bg-white rounded-lg shadow">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">材质名称</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">当前单价(元/克)</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">生效日期</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="price in currentPrices" :key="price.material_id">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-gray-900">{{ price.material_name }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-900">¥{{ price.price_per_gram.toFixed(2) }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-900">{{ formatDate(price.effective_date) }}</div>
                  <div class="text-xs text-gray-500">{{ formatTime(price.created_at) }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    @click="openEditModal(price)"
                    class="text-primary-600 hover:text-primary-900 mr-3"
                  >
                    修改
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 卡片（移动端） -->
        <div class="md:hidden space-y-4">
          <div v-for="price in currentPrices" :key="price.material_id" class="bg-white rounded-lg shadow p-4">
            <div class="flex justify-between items-start">
              <div>
                <h3 class="text-sm font-medium text-gray-900">{{ price.material_name }}</h3>
                <p class="mt-1 text-sm text-gray-600">单价：¥{{ price.price_per_gram.toFixed(2) }} 元/克</p>
                <p class="text-xs text-gray-500">生效日期：{{ formatDate(price.effective_date) }}</p>
              </div>
              <button
                @click="openEditModal(price)"
                class="px-3 py-1 bg-primary-50 text-primary-700 text-sm rounded-md hover:bg-primary-100"
              >
                修改
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 修改模态框 -->
    <div v-if="showEditModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">修改{{ editingMaterial?.material_name }}单价</h3>
        </div>

        <div class="px-6 py-4">
          <form @submit.prevent="handleUpdatePrice">
            <!-- 错误提示 -->
            <div v-if="updateError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded">
              <div class="flex items-start">
                <svg class="h-5 w-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
                <p class="ml-3 text-sm text-red-700">{{ updateError }}</p>
              </div>
            </div>

            <div class="space-y-4">
              <!-- 当前单价 -->
              <div>
                <label class="form-label">当前单价</label>
                <div class="text-lg font-semibold text-gray-900">
                  ¥{{ editingMaterial?.price_per_gram?.toFixed(2) }} 元/克
                </div>
                <p class="text-sm text-gray-500 mt-1">生效日期：{{ formatDate(editingMaterial?.effective_date) }}</p>
              </div>

              <!-- 新单价 -->
              <div>
                <label class="form-label">新单价 (¥/克) <span class="text-red-500">*</span></label>
                <input
                  v-model="newPrice"
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  class="form-input"
                  placeholder="0.00"
                  :class="{ 'border-red-300': priceError }"
                />
                <p v-if="priceError" class="mt-1 text-xs text-red-600">{{ priceError }}</p>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                @click="closeEditModal"
                class="btn btn-secondary"
                :disabled="loading.update"
              >
                取消
              </button>
              <button
                type="submit"
                class="btn btn-success"
                :disabled="loading.update"
              >
                <span v-if="loading.update" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
                {{ loading.update ? '保存中...' : '保存并预览调价' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 批量调价预览 -->
    <div v-if="repricePreview" class="mb-8">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-gray-800">批量调价预览</h2>
        <div class="text-sm text-gray-500">
          共 {{ repricePreview.affected_items?.length || 0 }} 件在库货品受影响
        </div>
      </div>

      <div class="bg-white rounded-lg shadow overflow-hidden">
        <div class="px-6 py-4 bg-yellow-50 border-b border-yellow-200">
          <div class="flex items-center">
            <svg class="h-5 w-5 text-yellow-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
            <p class="text-sm text-yellow-800">
              修改 <span class="font-semibold">{{ editingMaterial?.material_name }}</span> 的单价将影响在库货品的零售价。
              请确认以下变更，无误后点击"确认调价"执行。
            </p>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">货品编号</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">货品名称</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">旧售价(元)</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">新售价(元)</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">差价(元)</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="item in repricePreview.affected_items" :key="item.sku_code">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ item.sku_code }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ item.name || '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  ¥{{ item.old_price.toFixed(2) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <span class="font-semibold">¥{{ item.new_price.toFixed(2) }}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <span :class="item.new_price - item.old_price >= 0 ? 'text-green-600' : 'text-red-600'">
                    {{ item.new_price - item.old_price >= 0 ? '+' : '' }}{{ (item.new_price - item.old_price).toFixed(2) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
          <button
            @click="cancelReprice"
            class="btn btn-secondary"
            :disabled="loading.confirm"
          >
            取消调价
          </button>
          <button
            @click="confirmReprice"
            class="btn btn-success"
            :disabled="loading.confirm || !repricePreview?.affected_items?.length"
          >
            <span v-if="loading.confirm" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
            {{ loading.confirm ? '执行中...' : '确认调价' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 市价历史记录 -->
    <div>
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-gray-800">市价历史记录</h2>
        <div class="flex items-center space-x-2">
          <select
            v-model="historyFilter.material_id"
            @change="fetchPriceHistory"
            class="form-input form-input-sm"
          >
            <option value="">所有材质</option>
            <option v-for="price in currentPrices" :key="price.material_id" :value="price.material_id">
              {{ price.material_name }}
            </option>
          </select>
          <select
            v-model="historyFilter.limit"
            @change="fetchPriceHistory"
            class="form-input form-input-sm"
          >
            <option value="10">最近10条</option>
            <option value="20">最近20条</option>
            <option value="50">最近50条</option>
            <option value="100">最近100条</option>
          </select>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading.history" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p class="mt-2 text-gray-600">加载历史记录中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="priceHistory.length === 0" class="bg-gray-50 rounded-lg p-6 text-center">
        <p class="text-gray-600">暂无市价历史记录</p>
      </div>

      <!-- 历史表格 -->
      <div v-else class="bg-white rounded-lg shadow overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">材质名称</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">单价(元/克)</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">生效日期</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">记录时间</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="record in priceHistory" :key="record.id">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ record.material_name }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">¥{{ record.price_per_gram.toFixed(2) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ formatDate(record.effective_date) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ formatDateTime(record.created_at) }}</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import toast from '@/composables/useToast'

// 响应式数据
const currentPrices = ref([])
const priceHistory = ref([])
const showEditModal = ref(false)
const editingMaterial = ref(null)
const newPrice = ref('')
const repricePreview = ref(null)
const updateError = ref('')
const priceError = ref('')

// 加载状态
const loading = ref({
  currentPrices: false,
  history: false,
  update: false,
  confirm: false
})

// 历史记录筛选
const historyFilter = ref({
  material_id: '',
  limit: 20
})

// 初始化加载数据
onMounted(() => {
  fetchCurrentPrices()
  fetchPriceHistory()
})

// 获取当前市价
async function fetchCurrentPrices() {
  loading.value.currentPrices = true
  try {
    const data = await api.metal.getCurrentPrices()
    currentPrices.value = data || []
  } catch (error) {
    console.error('获取当前市价失败:', error)
    currentPrices.value = []
  } finally {
    loading.value.currentPrices = false
  }
}

// 获取市价历史
async function fetchPriceHistory() {
  loading.value.history = true
  try {
    const params = {}
    if (historyFilter.value.material_id) {
      params.material_id = parseInt(historyFilter.value.material_id)
    }
    if (historyFilter.value.limit) {
      params.limit = parseInt(historyFilter.value.limit)
    }

    const data = await api.metal.getPriceHistory(params)
    priceHistory.value = data || []
  } catch (error) {
    console.error('获取市价历史失败:', error)
    priceHistory.value = []
  } finally {
    loading.value.history = false
  }
}

// 打开修改模态框
function openEditModal(price) {
  editingMaterial.value = price
  newPrice.value = (price.price_per_gram + 0.01).toFixed(2) // 默认加0.01元
  updateError.value = ''
  priceError.value = ''
  repricePreview.value = null
  showEditModal.value = true
}

// 关闭修改模态框
function closeEditModal() {
  showEditModal.value = false
  editingMaterial.value = null
  newPrice.value = ''
  updateError.value = ''
  priceError.value = ''
  repricePreview.value = null
}

// 验证新单价
function validateNewPrice() {
  if (!newPrice.value || parseFloat(newPrice.value) <= 0) {
    priceError.value = '请输入有效的单价（大于0）'
    return false
  }

  const newPriceNum = parseFloat(newPrice.value)
  if (editingMaterial.value && Math.abs(newPriceNum - editingMaterial.value.price_per_gram) < 0.01) {
    priceError.value = '新单价与当前单价差异过小（至少0.01元）'
    return false
  }

  priceError.value = ''
  return true
}

// 处理更新单价
async function handleUpdatePrice() {
  if (!validateNewPrice()) {
    return
  }

  loading.value.update = true
  updateError.value = ''

  try {
    const newPriceNum = parseFloat(newPrice.value)

    // 1. 更新市价
    await api.metal.updatePrice(editingMaterial.value.material_id, {
      material_id: editingMaterial.value.material_id,
      price_per_gram: newPriceNum
    })

    // 2. 预览批量调价
    const previewData = await api.metal.previewReprice({
      material_id: editingMaterial.value.material_id,
      new_price_per_gram: newPriceNum
    })

    repricePreview.value = previewData

    // 3. 刷新当前市价
    fetchCurrentPrices()

    // 4. 关闭模态框
    closeEditModal()

  } catch (error) {
    console.error('更新市价失败:', error)
    updateError.value = error.message || '更新市价失败，请重试'
  } finally {
    loading.value.update = false
  }
}

// 确认批量调价
async function confirmReprice() {
  if (!editingMaterial.value || !newPrice.value || !repricePreview.value) {
    return
  }

  loading.value.confirm = true

  try {
    const newPriceNum = parseFloat(newPrice.value)

    // 执行批量调价
    await api.metal.confirmReprice({
      material_id: editingMaterial.value.material_id,
      new_price_per_gram: newPriceNum
    })

    // 刷新数据
    fetchCurrentPrices()
    fetchPriceHistory()

    // 重置状态
    repricePreview.value = null
    editingMaterial.value = null
    newPrice.value = ''

  } catch (error) {
    console.error('批量调价失败:', error)
    toast.error('批量调价失败: ' + (error.message || '请重试'))
  } finally {
    loading.value.confirm = false
  }
}

// 取消批量调价
function cancelReprice() {
  repricePreview.value = null
}

// 日期时间格式化
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

function formatTime(dateTimeStr) {
  if (!dateTimeStr) return ''
  const date = new Date(dateTimeStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatDateTime(dateTimeStr) {
  if (!dateTimeStr) return ''
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.form-label {
  @apply block text-sm font-medium text-gray-700 mb-1;
}

.form-input {
  @apply block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm;
}

.form-input-sm {
  @apply text-sm py-1;
}

.btn {
  @apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2;
}

.btn-secondary {
  @apply bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500;
}

.btn-success {
  @apply bg-green-600 text-white hover:bg-green-700 focus:ring-green-500;
}

.btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}
</style>