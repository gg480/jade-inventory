<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  material: {
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
  sub_type: '',
  origin: '',
  cost_per_gram: null,
  sort_order: 0
})

// 表单验证状态
const formErrors = ref({})

// 当visible或material变化时，重置表单数据
watch(() => props.visible, (visible) => {
  if (visible) {
    resetForm()
    if (props.mode === 'edit' && props.material) {
      formData.value = {
        name: props.material.name || '',
        sub_type: props.material.sub_type || '',
        origin: props.material.origin || '',
        cost_per_gram: props.material.cost_per_gram || null,
        sort_order: props.material.sort_order || 0
      }
    }
  }
})

watch(() => props.material, (material) => {
  if (props.mode === 'edit' && material) {
    formData.value = {
      name: material.name || '',
      sub_type: material.sub_type || '',
      origin: material.origin || '',
      cost_per_gram: material.cost_per_gram || null,
      sort_order: material.sort_order || 0
    }
  }
})

function resetForm() {
  formData.value = {
    name: '',
    sub_type: '',
    origin: '',
    cost_per_gram: null,
    sort_order: 0
  }
  formErrors.value = {}
}

function validateForm() {
  const errors = {}
  if (!formData.value.name.trim()) {
    errors.name = '材质名称不能为空'
  }
  if (formData.value.cost_per_gram !== null && formData.value.cost_per_gram < 0) {
    errors.cost_per_gram = '克重单价不能为负数'
  }
  if (formData.value.sort_order < 0) {
    errors.sort_order = '排序权重不能为负数'
  }
  formErrors.value = errors
  return Object.keys(errors).length === 0
}

function handleSubmit() {
  if (!validateForm()) {
    return
  }

  // 提交数据，转换null为undefined
  const submitData = {
    name: formData.value.name.trim(),
    sub_type: formData.value.sub_type.trim() || undefined,
    origin: formData.value.origin.trim() || undefined,
    cost_per_gram: formData.value.cost_per_gram || undefined,
    sort_order: formData.value.sort_order || 0
  }

  emit('submit', submitData)
}

function handleCancel() {
  emit('cancel')
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
      <!-- 模态框头部 -->
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">
          {{ mode === 'add' ? '新增材质' : '编辑材质' }}
        </h3>
        <p v-if="mode === 'edit' && material" class="mt-1 text-sm text-gray-600">
          编辑 {{ material.name }}
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
            <!-- 材质名称 -->
            <div>
              <label class="form-label">材质名称 <span class="text-red-500">*</span></label>
              <input
                v-model="formData.name"
                type="text"
                required
                class="form-input"
                placeholder="如：翡翠"
                :class="{ 'border-red-300': formErrors.name }"
              />
              <p v-if="formErrors.name" class="mt-1 text-xs text-red-600">{{ formErrors.name }}</p>
            </div>

            <!-- 子类 -->
            <div>
              <label class="form-label">子类（可选）</label>
              <input
                v-model="formData.sub_type"
                type="text"
                class="form-input"
                placeholder="如：冰种、糯种"
              />
            </div>

            <!-- 产地 -->
            <div>
              <label class="form-label">产地（可选）</label>
              <input
                v-model="formData.origin"
                type="text"
                class="form-input"
                placeholder="如：缅甸、新疆"
              />
            </div>

            <!-- 克重单价 -->
            <div>
              <label class="form-label">克重单价（¥/克）</label>
              <input
                v-model="formData.cost_per_gram"
                type="number"
                step="0.01"
                min="0"
                class="form-input"
                placeholder="0.00"
                :class="{ 'border-red-300': formErrors.cost_per_gram }"
              />
              <p v-if="formErrors.cost_per_gram" class="mt-1 text-xs text-red-600">{{ formErrors.cost_per_gram }}</p>
              <p class="mt-1 text-xs text-gray-500">贵金属类材质需要填写克重单价</p>
            </div>

            <!-- 排序权重 -->
            <div>
              <label class="form-label">排序权重</label>
              <input
                v-model="formData.sort_order"
                type="number"
                min="0"
                step="1"
                class="form-input"
                :class="{ 'border-red-300': formErrors.sort_order }"
              />
              <p v-if="formErrors.sort_order" class="mt-1 text-xs text-red-600">{{ formErrors.sort_order }}</p>
              <p class="mt-1 text-xs text-gray-500">数字越大显示越靠前，默认为0</p>
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