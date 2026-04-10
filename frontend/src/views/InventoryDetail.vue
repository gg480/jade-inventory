<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'

const route = useRoute()
const router = useRouter()
const item = ref(null)
const loading = ref(false)

// 出库相关
const showCheckoutModal = ref(false)
const checkoutForm = ref({
  actual_price: '',
  channel: 'store',
  sale_date: new Date().toISOString().slice(0, 10),
  customer_note: ''
})
const checkoutError = ref('')
const checkoutLoading = ref(false)

// 获取货品详情
async function fetchItem() {
  loading.value = true
  try {
    const data = await api.items.getItem(route.params.id)
    item.value = data
  } catch (error) {
    console.error('获取货品详情失败:', error)
    alert('货品不存在或已删除')
    router.push('/inventory')
  } finally {
    loading.value = false
  }
}

// 删除货品
async function deleteItem() {
  if (!confirm('确定要删除这个货品吗？删除后不可恢复。')) return

  try {
    await api.items.deleteItem(route.params.id)
    alert('删除成功')
    router.push('/inventory')
  } catch (error) {
    alert(`删除失败: ${error.message}`)
  }
}

// 标记为借出
async function markAsLent() {
  if (!confirm('标记为借出？')) return
  try {
    await api.items.updateItem(route.params.id, { status: 'lent_out' })
    alert('已标记为借出')
    fetchItem()
  } catch (error) {
    alert(`操作失败: ${error.message}`)
  }
}

// 标记为已退
async function markAsReturned() {
  if (!confirm('标记为已退？')) return
  try {
    await api.items.updateItem(route.params.id, { status: 'returned' })
    alert('已标记为已退')
    fetchItem()
  } catch (error) {
    alert(`操作失败: ${error.message}`)
  }
}

// 编辑货品
function editItem() {
  router.push(`/inventory/edit/${route.params.id}`)
}

// 打开出库模态框
function openCheckoutModal() {
  checkoutForm.value = {
    actual_price: item.value.selling_price,
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
      item_id: item.value.id,
      actual_price: parseFloat(checkoutForm.value.actual_price),
      channel: checkoutForm.value.channel,
      sale_date: checkoutForm.value.sale_date,
      customer_note: checkoutForm.value.customer_note
    }

    await api.sales.createSale(saleData)
    alert('出库成功！')
    showCheckoutModal.value = false
    fetchItem() // 刷新详情
  } catch (error) {
    checkoutError.value = error.message
  } finally {
    checkoutLoading.value = false
  }
}

// 关闭出库模态框
function closeCheckoutModal() {
  showCheckoutModal.value = false
  checkoutError.value = ''
}

onMounted(() => {
  fetchItem()
})
</script>

<template>
  <div>
    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      <p class="mt-2 text-gray-500">加载中...</p>
    </div>

    <!-- 货品详情 -->
    <div v-else-if="item" class="space-y-6">
      <!-- 头部 -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{{ item.sku_code }}</h1>
          <div class="mt-2 flex items-center space-x-4">
            <span class="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
              {{ item.material_name }}
            </span>
            <span v-if="item.type_name" class="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
              {{ item.type_name }}
            </span>
            <span :class="{
              'px-3 py-1 rounded-full text-sm font-medium': true,
              'bg-green-100 text-green-800': item.status === 'in_stock',
              'bg-blue-100 text-blue-800': item.status === 'lent_out',
              'bg-yellow-100 text-yellow-800': item.status === 'returned',
              'bg-gray-100 text-gray-800': item.status === 'sold'
            }">
              {{ { in_stock: '在库', lent_out: '借出', returned: '已退', sold: '已售' }[item.status] || item.status }}
            </span>
          </div>
        </div>
        <div class="mt-4 sm:mt-0 flex space-x-3">
          <button
            @click="editItem"
            class="btn btn-primary"
          >
            编辑
          </button>
          <button
            v-if="item.status === 'in_stock'"
            @click="openCheckoutModal"
            class="btn btn-success"
          >
            销售出库
          </button>
          <button
            v-if="item.status === 'in_stock'"
            @click="markAsLent"
            class="btn btn-secondary"
          >
            标记为借出
          </button>
          <button
            v-if="item.status === 'lent_out'"
            @click="markAsReturned"
            class="btn btn-secondary"
          >
            标记为已退
          </button>
          <button
            @click="deleteItem"
            class="btn bg-red-600 hover:bg-red-700 text-white"
          >
            删除
          </button>
        </div>
      </div>

      <!-- 基本信息卡片 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- 左侧：基础信息 -->
        <div class="lg:col-span-2">
          <!-- 图片展示 -->
          <div class="card mb-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">图片</h2>
            <div v-if="item.images && item.images.length > 0" class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div v-for="(img, index) in item.images" :key="img.id" class="relative">
                <img
                  :src="`https://picsum.photos/200/200?random=${index}`"
                  :alt="`货品图片 ${index + 1}`"
                  class="w-full h-40 object-cover rounded-lg"
                />
              </div>
            </div>
            <div v-else class="text-center py-8">
              <div class="inline-block p-4 bg-gray-100 rounded-full mb-4">
                <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
              </div>
              <p class="text-gray-500">暂无图片</p>
            </div>
          </div>

          <div class="card">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">基本信息</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="form-label">SKU编号</label>
                <p class="font-mono text-gray-900">{{ item.sku_code }}</p>
              </div>
              <div v-if="item.batch_code">
                <label class="form-label">款号</label>
                <p class="text-gray-900">{{ item.batch_code }}</p>
              </div>
              <div>
                <label class="form-label">材质</label>
                <p class="text-gray-900">{{ item.material_name }}</p>
              </div>
              <div v-if="item.type_name">
                <label class="form-label">器型</label>
                <p class="text-gray-900">{{ item.type_name }}</p>
              </div>
              <div>
                <label class="form-label">在库天数</label>
                <p class="text-gray-900">{{ item.age_days !== null ? `${item.age_days}天` : '-' }}</p>
              </div>
              <div v-if="item.purchase_date">
                <label class="form-label">进货日期</label>
                <p class="text-gray-900">{{ item.purchase_date }}</p>
              </div>
            </div>
          </div>

          <!-- 价格信息卡片 -->
          <div class="card mt-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">价格信息</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="text-center p-4 bg-gray-50 rounded-lg">
                <div class="text-sm text-gray-500">进货成本</div>
                <div class="text-2xl font-bold text-gray-900 mt-1">¥{{ item.cost_price.toFixed(2) }}</div>
              </div>
              <div class="text-center p-4 bg-gray-50 rounded-lg">
                <div class="text-sm text-gray-500">标价</div>
                <div class="text-2xl font-bold text-jade-600 mt-1">¥{{ item.selling_price.toFixed(2) }}</div>
              </div>
            </div>
            <div class="mt-4 pt-4 border-t border-gray-200">
              <div class="text-sm text-gray-500">利润空间</div>
              <div class="mt-1 flex items-center">
                <div class="flex-1">
                  <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-jade-500"
                      :style="{ width: `${(item.selling_price - item.cost_price) / item.selling_price * 100}%` }"
                    ></div>
                  </div>
                </div>
                <div class="ml-4 text-lg font-bold text-jade-600">
                  ¥{{ (item.selling_price - item.cost_price).toFixed(2) }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：其他信息 -->
        <div>
          <div class="card">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">规格信息</h2>
            <div class="space-y-4">
              <div v-if="item.weight">
                <label class="form-label">克重</label>
                <p class="text-gray-900">{{ item.weight }}克</p>
              </div>
              <div v-if="item.size">
                <label class="form-label">尺寸</label>
                <p class="text-gray-900">{{ item.size }}</p>
              </div>
              <div v-if="item.cert_no">
                <label class="form-label">证书编号</label>
                <p class="text-gray-900 font-mono">{{ item.cert_no }}</p>
              </div>
              <div v-if="item.supplier_name">
                <label class="form-label">供货商</label>
                <p class="text-gray-900">{{ item.supplier_name }}</p>
              </div>
            </div>
          </div>

          <!-- 标签卡片 -->
          <div class="card mt-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">标签</h2>
            <div v-if="item.tags && item.tags.length > 0" class="flex flex-wrap gap-2">
              <span
                v-for="tag in item.tags"
                :key="tag.id"
                class="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm"
              >
                {{ tag.name }}
              </span>
            </div>
            <p v-else class="text-gray-500 text-sm">暂无标签</p>
          </div>

          <!-- 时间信息 -->
          <div class="card mt-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">时间信息</h2>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">创建时间</span>
                <span class="text-gray-900">{{ new Date(item.created_at).toLocaleString() }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">更新时间</span>
                <span class="text-gray-900">{{ new Date(item.updated_at).toLocaleString() }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 备注信息 -->
      <div v-if="item.notes" class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">备注</h2>
        <p class="text-gray-700 whitespace-pre-line">{{ item.notes }}</p>
      </div>
    </div>

    <!-- 出库模态框 -->
    <div v-if="showCheckoutModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">销售出库</h3>
          <p class="mt-1 text-sm text-gray-600">{{ item?.sku_code }} - {{ item?.material_name }}</p>
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
                  标价：¥{{ item?.selling_price.toFixed(2) }}，
                  进价：¥{{ item?.cost_price.toFixed(2) }}
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
                @click="closeCheckoutModal"
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