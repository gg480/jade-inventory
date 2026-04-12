<template>
  <div class="flex flex-col sm:flex-row sm:items-center justify-between space-y-3 sm:space-y-0">
    <!-- 左侧：共 X 条 -->
    <div class="text-sm text-gray-700 text-center sm:text-left">
      共 {{ total }} 条
    </div>

    <!-- 右侧：分页控件 -->
    <div class="flex items-center justify-center space-x-2">
      <!-- 上一页 -->
      <button
        type="button"
        @click="goToPrevPage"
        :disabled="page <= 1"
        class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
        :class="{ 'text-gray-400 cursor-not-allowed': page <= 1 }"
      >
        上一页
      </button>

      <!-- 第 N/M 页 -->
      <span class="px-3 py-1 text-sm text-gray-700">
        第 {{ page }} / {{ totalPages }} 页
      </span>

      <!-- 下一页 -->
      <button
        type="button"
        @click="goToNextPage"
        :disabled="page >= totalPages"
        class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
        :class="{ 'text-gray-400 cursor-not-allowed': page >= totalPages }"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: {
    type: Number,
    required: true,
    default: 0
  },
  page: {
    type: Number,
    required: true,
    default: 1
  },
  size: {
    type: Number,
    required: true,
    default: 20
  }
})

const emit = defineEmits(['update:page'])

// 计算总页数
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(props.total / props.size))
})

// 上一页
function goToPrevPage() {
  if (props.page <= 1) return
  emit('update:page', props.page - 1)
}

// 下一页
function goToNextPage() {
  if (props.page >= totalPages.value) return
  emit('update:page', props.page + 1)
}

// 监听total变化，如果当前页码超出范围，自动调整到最后一页
import { watch } from 'vue'
watch(() => props.total, (newTotal) => {
  const maxPage = Math.max(1, Math.ceil(newTotal / props.size))
  if (props.page > maxPage && maxPage > 0) {
    emit('update:page', maxPage)
  }
})
</script>