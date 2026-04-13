<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import api from '../api'
import toast from '../composables/useToast'

const props = defineProps({
  items: {
    type: Array,
    required: true,
    default: () => []
  },
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'success'])

// 表单数据
const form = reactive({
  total_price: '',
  alloc_method: 'by_ratio',
  channel: 'store',
  sale_date: new Date().toISOString().slice(0, 10),
  customer_id: null,
  note: ''
})

// 状态
const error = ref('')
const loading = ref(false)
const customers = ref([])
const loadingCustomers = ref(false)

// chain_at_cost: 标记哪些货品是链子（与 items 顺序一一对应）
const chainItems = ref([])

// 计算属性：是否为移动端
const isMobile = computed(() => {
  return window.innerWidth < 768 // Tailwind md 断点
})

// 计算总零售价
const totalRetailPrice = computed(() => {
  return props.items.reduce((sum, item) => sum + (item.selling_price || 0), 0)
})

// 计算分摊预览
const allocationPreview = computed(() => {
  if (!form.total_price || parseFloat(form.total_price) <= 0) {
    return []
  }

  const totalPrice = parseFloat(form.total_price)

  if (form.alloc_method === 'by_ratio') {
    // 按售价比例分摊
    const totalRetail = totalRetailPrice.value
    if (totalRetail <= 0) return []

    return props.items.map(item => {
      const ratio = (item.selling_price || 0) / totalRetail
      return {
        item,
        allocated_price: ratio * totalPrice
      }
    })
  }
  // chain_at_cost 不支持前端预览
  return []
})

// 是否显示分摊预览
const showAllocationPreview = computed(() => {
  return form.alloc_method === 'by_ratio' && form.total_price && parseFloat(form.total_price) > 0
})

// 监听 visible 变化，重置表单
watch(() => props.visible, (visible) => {
  if (visible) {
    resetForm()
  }
})

// 重置表单
function resetForm() {
  form.total_price = ''
  form.alloc_method = 'by_ratio'
  form.channel = 'store'
  form.sale_date = new Date().toISOString().slice(0, 10)
  form.customer_id = null
  form.note = ''
  error.value = ''
  loading.value = false
  // 重置链子标记：全部为 false（非链子）
  chainItems.value = props.items.map(() => false)
}

// 加载客户列表
async function loadCustomers() {
  loadingCustomers.value = true
  try {
    const data = await api.customers.getCustomers({ size: 100 })
    // 处理可能的响应格式：直接数组或分页对象
    if (Array.isArray(data)) {
      customers.value = data
    } else if (data && data.items && Array.isArray(data.items)) {
      customers.value = data.items
    } else {
      console.warn('客户列表响应格式未知:', data)
      customers.value = []
    }
  } catch (err) {
    console.error('加载客户列表失败:', err)
    customers.value = []
  } finally {
    loadingCustomers.value = false
  }
}

// 切换链子标记
function toggleChain(index) {
  chainItems.value[index] = !chainItems.value[index]
}

// 主件数量（未被标记为链子的）
const mainItemCount = computed(() => {
  return chainItems.value.filter(isChain => !isChain).length
})

// 提交表单
async function submitForm() {
  if (!form.total_price || parseFloat(form.total_price) <= 0) {
    toast.warning('请填写有效的套装总价')
    return
  }

  if (props.items.length === 0) {
    toast.warning('请选择至少一件货品')
    return
  }

  // chain_at_cost 校验：至少要有1件主件
  if (form.alloc_method === 'chain_at_cost') {
    if (mainItemCount.value === 0) {
      toast.warning('至少需要保留1件主件（不能全部标记为链子）')
      return
    }
  }

  error.value = ''
  loading.value = true

  try {
    const saleData = {
      item_ids: props.items.map(item => item.id),
      total_price: parseFloat(form.total_price),
      alloc_method: form.alloc_method,
      channel: form.channel,
      sale_date: form.sale_date,
      customer_id: form.customer_id || undefined,
      note: form.note
    }

    // chain_at_cost 时附带 chain_items 数组
    if (form.alloc_method === 'chain_at_cost') {
      saleData.chain_items = chainItems.value
    }

    await api.sales.createBundleSale(saleData)
    emit('success')
    closeDialog()
  } catch (err) {
    error.value = err.message || '套装销售失败'
  } finally {
    loading.value = false
  }
}

// 关闭弹窗
function closeDialog() {
  emit('close')
}

// 点击背景关闭
function handleBackdropClick(e) {
  if (e.target === e.currentTarget) {
    closeDialog()
  }
}

// 初始化
onMounted(() => {
  loadCustomers()
})
</script>

<template>
  <!-- 遮罩层 -->
  <div
    v-if="visible"
    class="fixed inset-0 z-50"
    :class="isMobile ? 'bg-black bg-opacity-50' : 'bg-gray-500 bg-opacity-75 flex items-center justify-center p-4'"
    @click="handleBackdropClick"
  >
    <!-- 弹窗内容 -->
    <div
      :class="[
        'bg-white shadow-xl',
        isMobile
          ? 'fixed inset-x-0 bottom-0 rounded-t-2xl max-h-[90vh] overflow-y-auto'
          : 'rounded-lg max-w-lg w-full'  // 稍宽一些，因为要显示货品列表
      ]"
    >
      <!-- 头部 -->
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">套装销售</h3>
        <p class="mt-1 text-sm text-gray-600">
          已选 {{ items.length }} 件货品
          <span v-if="totalRetailPrice > 0">
            | 总标价：¥{{ totalRetailPrice.toFixed(2) }}
          </span>
        </p>
      </div>

      <!-- 表单内容 -->
      <div class="px-6 py-4">
        <form @submit.prevent="submitForm">
          <!-- 错误提示 -->
          <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded">
            <div class="flex items-start">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-sm text-red-700">{{ error }}</p>
              </div>
            </div>
          </div>

          <!-- 已选货品列表 -->
          <div class="mb-6">
            <label class="form-label">已选货品</label>
            <div class="space-y-2 max-h-48 overflow-y-auto border border-gray-200 rounded-md p-3">
              <div v-for="(item, index) in items" :key="item.id" class="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                <div class="flex items-center flex-1">
                  <!-- chain_at_cost 勾选框 -->
                  <input
                    v-if="form.alloc_method === 'chain_at_cost'"
                    type="checkbox"
                    :checked="chainItems[index]"
                    @change="toggleChain(index)"
                    class="h-4 w-4 text-amber-600 rounded border-gray-300 focus:ring-amber-500 mr-2 flex-shrink-0"
                    title="标记为链子/绳子类"
                  />
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-gray-900">
                      {{ item.sku_code }}
                      <span v-if="form.alloc_method === 'chain_at_cost' && chainItems[index]" class="ml-1 px-1.5 py-0.5 text-xs rounded bg-amber-100 text-amber-700">链子</span>
                    </div>
                    <div class="text-xs text-gray-500">{{ item.material_name }} <span v-if="item.name">({{ item.name }})</span></div>
                  </div>
                </div>
                <div class="text-sm text-gray-700 ml-4">
                  ¥{{ (item.selling_price || 0).toFixed(2) }}
                </div>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <!-- 套装总价 -->
            <div>
              <label class="form-label">
                套装总价（¥） <span class="text-red-500">*</span>
              </label>
              <input
                v-model="form.total_price"
                type="number"
                step="0.01"
                min="0.01"
                required
                class="form-input"
                placeholder="0.00"
              />
              <p class="mt-1 text-xs text-gray-500">
                总标价：¥{{ totalRetailPrice.toFixed(2) }}
              </p>
            </div>

            <!-- 分摊方式 -->
            <div>
              <label class="form-label">分摊方式</label>
              <div class="space-y-2">
                <label class="inline-flex items-center">
                  <input
                    v-model="form.alloc_method"
                    type="radio"
                    value="by_ratio"
                    class="form-radio text-primary-600"
                  />
                  <span class="ml-2">按售价比例分摊</span>
                </label>
                <label class="inline-flex items-center">
                  <input
                    v-model="form.alloc_method"
                    type="radio"
                    value="chain_at_cost"
                    class="form-radio text-primary-600"
                  />
                  <span class="ml-2">链子按原价，剩余给主件</span>
                </label>
              </div>
              <p class="mt-1 text-xs text-gray-500" v-if="form.alloc_method === 'by_ratio'">
                各件成交价 = (该件售价 / 总售价) × 套装总价
              </p>
              <p class="mt-1 text-xs text-gray-500" v-if="form.alloc_method === 'chain_at_cost'">
                链子/绳子类货品按原价计入，剩余金额全部分配给主件。请在上方货品列表中勾选链子。
              </p>
              <!-- chain_at_cost 校验提示 -->
              <p v-if="form.alloc_method === 'chain_at_cost' && mainItemCount === 0" class="mt-1 text-xs text-red-600">
                至少需要保留1件主件（不能全部标记为链子）
              </p>
            </div>

            <!-- 分摊预览 -->
            <div v-if="form.total_price && parseFloat(form.total_price) > 0">
              <label class="form-label">分摊预览</label>
              <div v-if="showAllocationPreview" class="space-y-2 max-h-48 overflow-y-auto border border-gray-200 rounded-md p-3">
                <div v-for="preview in allocationPreview" :key="preview.item.id" class="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                  <div class="flex-1">
                    <div class="text-sm font-medium text-gray-900">{{ preview.item.sku_code }}</div>
                    <div class="text-xs text-gray-500">标价：¥{{ (preview.item.selling_price || 0).toFixed(2) }}</div>
                  </div>
                  <div class="text-sm font-semibold text-jade-600 ml-4">
                    ¥{{ preview.allocated_price.toFixed(2) }}
                  </div>
                </div>
              </div>
              <div v-else-if="form.alloc_method === 'chain_at_cost'" class="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                <p class="text-sm text-yellow-700">
                  <strong>链子按原价分摊：</strong>链子/绳子类货品将按原价计算，剩余金额全部分配给主件。具体分摊结果将在提交后由系统计算。
                </p>
              </div>
            </div>

            <!-- 销售渠道 -->
            <div>
              <label class="form-label">销售渠道</label>
              <div class="flex space-x-4">
                <label class="inline-flex items-center">
                  <input
                    v-model="form.channel"
                    type="radio"
                    value="store"
                    class="form-radio text-primary-600"
                  />
                  <span class="ml-2">门店</span>
                </label>
                <label class="inline-flex items-center">
                  <input
                    v-model="form.channel"
                    type="radio"
                    value="wechat"
                    class="form-radio text-primary-600"
                  />
                  <span class="ml-2">微信</span>
                </label>
              </div>
            </div>

            <!-- 成交日期 -->
            <div>
              <label class="form-label">成交日期</label>
              <input
                v-model="form.sale_date"
                type="date"
                class="form-input"
                required
              />
            </div>

            <!-- 客户选择 -->
            <div>
              <label class="form-label">客户（可选）</label>
              <select
                v-model="form.customer_id"
                class="form-input"
                :disabled="loadingCustomers"
              >
                <option :value="null">请选择客户...</option>
                <option v-for="customer in customers" :key="customer.id" :value="customer.id">
                  {{ customer.name }}
                  <span v-if="customer.phone">({{ customer.phone }})</span>
                </option>
              </select>
              <p v-if="loadingCustomers" class="mt-1 text-xs text-gray-500">加载客户列表中...</p>
            </div>

            <!-- 备注 -->
            <div>
              <label class="form-label">备注（可选）</label>
              <textarea
                v-model="form.note"
                rows="2"
                class="form-input"
                placeholder="可填写交易备注、客户信息等"
              ></textarea>
            </div>
          </div>

          <!-- 按钮组 -->
          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              @click="closeDialog"
              class="btn btn-secondary"
              :disabled="loading"
            >
              取消
            </button>
            <button
              type="submit"
              class="btn btn-success"
              :disabled="loading"
            >
              <span v-if="loading" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
              {{ loading ? '处理中...' : '确认销售' }}
            </button>
          </div>
        </form>
      </div>
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