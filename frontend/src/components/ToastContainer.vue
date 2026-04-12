<script setup>
import toast from '../composables/useToast'

// 图标映射
const iconMap = {
  success: 'M5 13l4 4L19 7',
  error: 'M6 18L18 6M6 6l12 12',
  warning: 'M12 9v2m0 4h.01M10.29 3.86l-8.6 14.86A1 1 0 002.56 20h16.88a1 1 0 00.87-1.28l-8.6-14.86a1 1 0 00-1.72 0z',
  info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
}

// 颜色映射
const colorMap = {
  success: {
    bg: 'bg-green-50',
    border: 'border-green-400',
    icon: 'text-green-500',
    text: 'text-green-800',
    progress: 'bg-green-400'
  },
  error: {
    bg: 'bg-red-50',
    border: 'border-red-400',
    icon: 'text-red-500',
    text: 'text-red-800',
    progress: 'bg-red-400'
  },
  warning: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-400',
    icon: 'text-yellow-500',
    text: 'text-yellow-800',
    progress: 'bg-yellow-400'
  },
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-400',
    icon: 'text-blue-500',
    text: 'text-blue-800',
    progress: 'bg-blue-400'
  }
}

function getIcon(type) {
  return iconMap[type] || iconMap.info
}

function getColors(type) {
  return colorMap[type] || colorMap.info
}
</script>

<template>
  <!-- Toast 容器：固定在右上角 -->
  <div class="fixed top-4 right-4 z-[9999] flex flex-col items-end space-y-2 pointer-events-none">
    <transition-group name="toast">
      <div
        v-for="t in toast.list"
        :key="t.id"
        class="pointer-events-auto max-w-sm w-full rounded-lg border shadow-lg overflow-hidden"
        :class="[getColors(t.type).bg, getColors(t.type).border]"
      >
        <div class="flex items-start p-3">
          <!-- 图标 -->
          <div class="flex-shrink-0" :class="getColors(t.type).icon">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getIcon(t.type)" />
            </svg>
          </div>
          <!-- 消息 -->
          <div class="ml-3 flex-1 text-sm font-medium" :class="getColors(t.type).text">
            {{ t.message }}
          </div>
          <!-- 关闭按钮 -->
          <button
            class="ml-3 flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
            @click="toast.list.splice(toast.list.findIndex(x => x.id === t.id), 1)"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
        <!-- 进度条 -->
        <div class="h-0.5" :class="getColors(t.type).progress" style="animation: toast-progress linear forwards" :style="{ animationDuration: t.duration + 'ms' }"></div>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

@keyframes toast-progress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}
</style>
