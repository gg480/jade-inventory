<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import api from '../api'
import toast from '../composables/useToast'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'success'])

// 表单数据
const form = reactive({
  actual_price: '',
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

// 计算属性：是否为移动端
const isMobile = computed(() => {
  return window.innerWidth < 768 // Tailwind md 断点
})

// 监听 visible 变化，重置表单
watch(() => props.visible, (visible) => {
  if (visible) {
    resetForm()
  }
})

// 重置表单
function resetForm() {
  form.actual_price = props.item.selling_price?.toString() || ''
  form.channel = 'store'
  form.sale_date = new Date().toISOString().slice(0, 10)
  form.customer_id = null
  form.note = ''
  error.value = ''
  loading.value = false
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

// 提交表单
async function submitForm() {
  if (!form.actual_price || parseFloat(form.actual_price) <= 0) {
    toast.warning('请填写有效的成交价')
    return
  }

  error.value = ''
  loading.value = true

  try {
    const saleData = {
      item_id: props.item.id,
      actual_price: parseFloat(form.actual_price),
      channel: form.channel,
      sale_date: form.sale_date,
      customer_id: form.customer_id || undefined,
      note: form.note
    }

    await api.sales.createSale(saleData)
    emit('success')
    closeDialog()
  } catch (err) {
    error.value = err.message || '销售失败'
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
          : 'rounded-lg max-w-md w-full'
      ]"
    >
      <!-- 头部 -->
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">销售</h3>
        <p class="mt-1 text-sm text-gray-600">
          {{ item.sku_code }} - {{ item.material_name }}
          <span v-if="item.name">({{ item.name }})</span>
        </p>
        <p class="mt-1 text-sm text-gray-500">
          零售价：¥{{ item.selling_price?.toFixed(2) || '0.00' }}
          <span v-if="item.cost_price || item.allocated_cost">
            | 成本：¥{{ (item.allocated_cost || item.cost_price || 0).toFixed(2) }}
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

          <div class="space-y-4">
            <!-- 成交价 -->
            <div>
              <label class="form-label">
                成交价（¥） <span class="text-red-500">*</span>
              </label>
              <input
                v-model="form.actual_price"
                type="number"
                step="0.01"
                min="0.01"
                required
                class="form-input"
                placeholder="0.00"
              />
              <p class="mt-1 text-xs text-gray-500">
                标价：¥{{ item.selling_price?.toFixed(2) || '0.00' }}
              </p>
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