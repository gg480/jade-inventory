<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  type: {
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

// 所有可用的规格字段选项
const specFieldOptions = [
  { value: 'weight', label: '重量 (克)' },
  { value: 'size', label: '尺寸 (长/宽/高)' },
  { value: 'bracelet_size', label: '圈口 (手镯)' },
  { value: 'bead_count', label: '粒数 (珠串)' },
  { value: 'bead_diameter', label: '珠子口径 (mm)' },
  { value: 'ring_size', label: '戒指尺寸' },
  { value: 'metal_weight', label: '金属重量 (贵金属)' }
]

// 表单数据
const formData = ref({
  name: '',
  spec_fields: [],
  sort_order: 0
})

// 表单验证状态
const formErrors = ref({})

// 当visible或type变化时，重置表单数据
watch(() => props.visible, (visible) => {
  if (visible) {
    resetForm()
    if (props.mode === 'edit' && props.type) {
      loadTypeData(props.type)
    }
  }
})

watch(() => props.type, (type) => {
  if (props.mode === 'edit' && type) {
    loadTypeData(type)
  }
})

function loadTypeData(type) {
  // 解析spec_fields JSON字符串
  let specFieldsArray = []
  if (type.spec_fields) {
    try {
      specFieldsArray = JSON.parse(type.spec_fields)
    } catch (e) {
      console.error('解析spec_fields失败:', e)
      specFieldsArray = []
    }
  }

  formData.value = {
    name: type.name || '',
    spec_fields: specFieldsArray,
    sort_order: type.sort_order || 0
  }
}

function resetForm() {
  formData.value = {
    name: '',
    spec_fields: [],
    sort_order: 0
  }
  formErrors.value = {}
}

function validateForm() {
  const errors = {}
  if (!formData.value.name.trim()) {
    errors.name = '器型名称不能为空'
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

  // 提交数据，转换spec_fields为JSON字符串
  const submitData = {
    name: formData.value.name.trim(),
    spec_fields: formData.value.spec_fields.length > 0
      ? JSON.stringify(formData.value.spec_fields)
      : undefined,
    sort_order: formData.value.sort_order || 0
  }

  emit('submit', submitData)
}

function handleCancel() {
  emit('cancel')
}

// 切换规格字段选择
function toggleSpecField(value) {
  const index = formData.value.spec_fields.indexOf(value)
  if (index > -1) {
    formData.value.spec_fields.splice(index, 1)
  } else {
    formData.value.spec_fields.push(value)
  }
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
      <!-- 模态框头部 -->
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">
          {{ mode === 'add' ? '新增器型' : '编辑器型' }}
        </h3>
        <p v-if="mode === 'edit' && type" class="mt-1 text-sm text-gray-600">
          编辑 {{ type.name }}
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
            <!-- 器型名称 -->
            <div>
              <label class="form-label">器型名称 <span class="text-red-500">*</span></label>
              <input
                v-model="formData.name"
                type="text"
                required
                class="form-input"
                placeholder="如：手镯、吊坠、戒指"
                :class="{ 'border-red-300': formErrors.name }"
              />
              <p v-if="formErrors.name" class="mt-1 text-xs text-red-600">{{ formErrors.name }}</p>
            </div>

            <!-- 规格字段选择 -->
            <div>
              <label class="form-label">规格字段（多选）</label>
              <p class="text-sm text-gray-500 mb-2">选择该器型需要填写的规格参数</p>
              <div class="grid grid-cols-2 gap-2">
                <div
                  v-for="option in specFieldOptions"
                  :key="option.value"
                  class="flex items-center"
                >
                  <input
                    type="checkbox"
                    :id="`spec-${option.value}`"
                    :value="option.value"
                    :checked="formData.spec_fields.includes(option.value)"
                    @change="toggleSpecField(option.value)"
                    class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label :for="`spec-${option.value}`" class="ml-2 text-sm text-gray-700">
                    {{ option.label }}
                  </label>
                </div>
              </div>
              <p v-if="formData.spec_fields.length > 0" class="mt-2 text-xs text-gray-500">
                已选择：{{ formData.spec_fields.map(f => specFieldOptions.find(o => o.value === f)?.label).join(', ') }}
              </p>
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