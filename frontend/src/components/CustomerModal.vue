<template>
  <div v-if="visible" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
      <!-- 模态框头部 -->
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">
          {{ mode === 'add' ? '新增客户' : '编辑客户' }}
        </h3>
        <p v-if="mode === 'edit' && customer" class="mt-1 text-sm text-gray-600">
          编辑 {{ customer.name }}
        </p>
      </div>

      <!-- 表单内容 -->
      <div class="px-6 py-4">
        <form @submit.prevent="handleSubmit">
          <!-- 错误提示 -->
          <div v-if="Object.keys(formErrors).length > 0" class="mb-4 p-3 bg-red-50 border border-red-200 rounded">
            <div class="flex items-start">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-sm text-red-700">请修正以下错误：</p>
                <ul class="mt-1 text-sm text-red-700 list-disc list-inside">
                  <li v-for="error in Object.values(formErrors)" :key="error">{{ error }}</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <!-- 客户姓名 -->
            <div>
              <label class="form-label">姓名 <span class="text-red-500">*</span></label>
              <input
                v-model="formData.name"
                type="text"
                required
                class="form-input"
                placeholder="如：张三"
                :class="{ 'border-red-300': formErrors.name }"
              />
              <p v-if="formErrors.name" class="mt-1 text-xs text-red-600">{{ formErrors.name }}</p>
            </div>

            <!-- 电话 -->
            <div>
              <label class="form-label">电话（可选）</label>
              <input
                v-model="formData.phone"
                type="tel"
                class="form-input"
                placeholder="如：13800138000"
              />
            </div>

            <!-- 微信 -->
            <div>
              <label class="form-label">微信（可选）</label>
              <input
                v-model="formData.wechat"
                type="text"
                class="form-input"
                placeholder="如：wechat123"
              />
            </div>

            <!-- 备注 -->
            <div>
              <label class="form-label">备注（可选）</label>
              <textarea
                v-model="formData.notes"
                rows="3"
                class="form-input"
                placeholder="如：熟客、喜欢翡翠、常买吊坠"
              />
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              @click="handleCancel"
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
              {{ loading ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  customer: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'add', // 'add' or 'edit'
    validator: (value) => ['add', 'edit'].includes(value)
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit', 'cancel'])

// 表单数据
const formData = ref({
  name: '',
  phone: '',
  wechat: '',
  notes: ''
})

// 表单验证状态
const formErrors = ref({})

// 当visible或customer变化时，重置表单数据
watch(() => props.visible, (visible) => {
  if (visible) {
    resetForm()
    if (props.mode === 'edit' && props.customer) {
      formData.value = {
        name: props.customer.name || '',
        phone: props.customer.phone || '',
        wechat: props.customer.wechat || '',
        notes: props.customer.notes || ''
      }
    }
  }
})

watch(() => props.customer, (customer) => {
  if (props.mode === 'edit' && customer) {
    formData.value = {
      name: customer.name || '',
      phone: customer.phone || '',
      wechat: customer.wechat || '',
      notes: customer.notes || ''
    }
  }
})

function resetForm() {
  formData.value = {
    name: '',
    phone: '',
    wechat: '',
    notes: ''
  }
  formErrors.value = {}
}

function validateForm() {
  const errors = {}
  if (!formData.value.name.trim()) {
    errors.name = '客户姓名不能为空'
  }
  formErrors.value = errors
  return Object.keys(errors).length === 0
}

function handleSubmit() {
  if (!validateForm()) {
    return
  }

  // 提交数据，转换空字符串为undefined
  const submitData = {
    name: formData.value.name.trim(),
    phone: formData.value.phone.trim() || undefined,
    wechat: formData.value.wechat.trim() || undefined,
    notes: formData.value.notes.trim() || undefined
  }

  emit('submit', submitData)
}

function handleCancel() {
  emit('cancel')
}
</script>

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