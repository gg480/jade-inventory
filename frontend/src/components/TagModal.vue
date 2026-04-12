<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  tag: {
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
  },
  existingGroups: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['submit', 'cancel'])

// 标准分组选项（参考PRD.md）
const standardGroups = [
  { value: '种水', label: '种水' },
  { value: '颜色', label: '颜色' },
  { value: '工艺', label: '工艺' },
  { value: '题材', label: '题材' }
]

// 表单数据
const formData = ref({
  name: '',
  group_name: '',
  description: ''
})

// 是否使用自定义分组
const useCustomGroup = ref(false)
const customGroupName = ref('')

// 表单验证状态
const formErrors = ref({})

// 当visible或tag变化时，重置表单数据
watch(() => props.visible, (visible) => {
  if (visible) {
    resetForm()
    if (props.mode === 'edit' && props.tag) {
      loadTagData(props.tag)
    }
  }
})

watch(() => props.tag, (tag) => {
  if (props.mode === 'edit' && tag) {
    loadTagData(tag)
  }
})

function loadTagData(tag) {
  formData.value = {
    name: tag.name || '',
    group_name: tag.group_name || '',
    description: tag.description || ''
  }

  // 如果分组不在现有分组中，启用自定义分组
  if (tag.group_name && !props.existingGroups.includes(tag.group_name)) {
    useCustomGroup.value = true
    customGroupName.value = tag.group_name
  } else {
    useCustomGroup.value = false
    customGroupName.value = ''
  }
}

function resetForm() {
  formData.value = {
    name: '',
    group_name: '',
    description: ''
  }
  useCustomGroup.value = false
  customGroupName.value = ''
  formErrors.value = {}
}

function validateForm() {
  const errors = {}
  if (!formData.value.name.trim()) {
    errors.name = '标签名称不能为空'
  }

  // 验证分组
  const finalGroupName = getFinalGroupName()
  if (!finalGroupName.trim()) {
    errors.group = '请选择或输入分组名称'
  }

  formErrors.value = errors
  return Object.keys(errors).length === 0
}

function getFinalGroupName() {
  if (useCustomGroup.value) {
    return customGroupName.value.trim()
  }
  return formData.value.group_name
}

function handleSubmit() {
  if (!validateForm()) {
    return
  }

  const finalGroupName = getFinalGroupName()

  // 提交数据
  const submitData = {
    name: formData.value.name.trim(),
    group_name: finalGroupName || undefined,
    description: formData.value.description.trim() || undefined
  }

  emit('submit', submitData)
}

function handleCancel() {
  emit('cancel')
}

// 切换分组模式
function toggleGroupMode() {
  useCustomGroup.value = !useCustomGroup.value
  if (!useCustomGroup.value) {
    customGroupName.value = ''
  } else {
    formData.value.group_name = ''
  }
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
      <!-- 模态框头部 -->
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">
          {{ mode === 'add' ? '新增标签' : '编辑标签' }}
        </h3>
        <p v-if="mode === 'edit' && tag" class="mt-1 text-sm text-gray-600">
          编辑 {{ tag.name }}
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
                  <li v-for="(error, key) in formErrors" :key="key">{{ error }}</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <!-- 标签名称 -->
            <div>
              <label class="form-label">标签名称 <span class="text-red-500">*</span></label>
              <input
                v-model="formData.name"
                type="text"
                required
                class="form-input"
                placeholder="如：冰种、飘花、雕花"
                :class="{ 'border-red-300': formErrors.name }"
              />
              <p v-if="formErrors.name" class="mt-1 text-xs text-red-600">{{ formErrors.name }}</p>
            </div>

            <!-- 分组选择 -->
            <div>
              <label class="form-label">所属分组 <span class="text-red-500">*</span></label>

              <!-- 使用现有分组或自定义分组 -->
              <div class="mb-3">
                <div class="flex items-center space-x-4">
                  <div class="flex items-center">
                    <input
                      type="radio"
                      id="group-existing"
                      :checked="!useCustomGroup"
                      @change="toggleGroupMode"
                      class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                    />
                    <label for="group-existing" class="ml-2 text-sm text-gray-700">
                      选择现有分组
                    </label>
                  </div>
                  <div class="flex items-center">
                    <input
                      type="radio"
                      id="group-custom"
                      :checked="useCustomGroup"
                      @change="toggleGroupMode"
                      class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                    />
                    <label for="group-custom" class="ml-2 text-sm text-gray-700">
                      输入新分组
                    </label>
                  </div>
                </div>
              </div>

              <!-- 现有分组下拉 -->
              <div v-if="!useCustomGroup">
                <select
                  v-model="formData.group_name"
                  class="form-input"
                  :class="{ 'border-red-300': formErrors.group }"
                >
                  <option value="">请选择分组</option>
                  <!-- 标准分组 -->
                  <optgroup label="标准分组">
                    <option v-for="group in standardGroups" :key="group.value" :value="group.value">
                      {{ group.label }}
                    </option>
                  </optgroup>
                  <!-- 已有分组（排除标准分组） -->
                  <optgroup v-if="existingGroups.filter(g => !standardGroups.map(sg => sg.value).includes(g)).length > 0" label="已有分组">
                    <option v-for="group in existingGroups.filter(g => !standardGroups.map(sg => sg.value).includes(g))" :key="group" :value="group">
                      {{ group }}
                    </option>
                  </optgroup>
                </select>
              </div>

              <!-- 自定义分组输入 -->
              <div v-else>
                <input
                  v-model="customGroupName"
                  type="text"
                  class="form-input"
                  placeholder="输入新的分组名称"
                  :class="{ 'border-red-300': formErrors.group }"
                />
              </div>

              <p v-if="formErrors.group" class="mt-1 text-xs text-red-600">{{ formErrors.group }}</p>
            </div>

            <!-- 描述 -->
            <div>
              <label class="form-label">描述（可选）</label>
              <textarea
                v-model="formData.description"
                rows="3"
                class="form-input"
                placeholder="标签描述"
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