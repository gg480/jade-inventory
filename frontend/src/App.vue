<script setup>
import { ref, computed } from 'vue'
import { RouterView, useRouter } from 'vue-router'

const router = useRouter()
const mobileMenuOpen = ref(false)

// 导航菜单项
const navItems = [
  { name: '库存列表', path: '/inventory', icon: '📦' },
  { name: '入库', path: '/inventory/add', icon: '➕' },
  { name: '销售记录', path: '/sales', icon: '💰' },
  { name: '利润看板', path: '/dashboard', icon: '📊' },
]

// 设置菜单项
const settingsItems = [
  { name: '字典管理', path: '/settings/dicts', icon: '📋' },
  { name: '供货商', path: '/settings/suppliers', icon: '🏢' },
]

// 当前路由
const currentRoute = computed(() => router.currentRoute.value.path)
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-sm border-b border-gray-200">
      <div class="container mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <!-- 左侧：Logo和主导航 -->
          <div class="flex">
            <!-- Logo -->
            <div class="flex-shrink-0 flex items-center">
              <span class="text-xl font-bold text-jade-600">🪷 玉器店进销存</span>
            </div>

            <!-- 桌面导航 -->
            <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
              <router-link
                v-for="item in navItems"
                :key="item.path"
                :to="item.path"
                class="inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="{
                  'text-gray-900 bg-gray-100': currentRoute.startsWith(item.path),
                  'text-gray-500 hover:text-gray-700 hover:bg-gray-50': !currentRoute.startsWith(item.path)
                }"
              >
                <span class="mr-2">{{ item.icon }}</span>
                {{ item.name }}
              </router-link>
            </div>
          </div>

          <!-- 右侧：设置菜单 -->
          <div class="hidden sm:ml-6 sm:flex sm:items-center">
            <div class="relative ml-3">
              <div class="flex space-x-4">
                <router-link
                  v-for="item in settingsItems"
                  :key="item.path"
                  :to="item.path"
                  class="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
                >
                  <span class="mr-2">{{ item.icon }}</span>
                  {{ item.name }}
                </router-link>
              </div>
            </div>
          </div>

          <!-- 移动端菜单按钮 -->
          <div class="flex items-center sm:hidden">
            <button
              @click="mobileMenuOpen = !mobileMenuOpen"
              class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
            >
              <span class="sr-only">打开主菜单</span>
              <!-- 汉堡图标 -->
              <svg
                class="h-6 w-6"
                :class="{ 'hidden': mobileMenuOpen, 'block': !mobileMenuOpen }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
              <!-- 关闭图标 -->
              <svg
                class="h-6 w-6"
                :class="{ 'block': mobileMenuOpen, 'hidden': !mobileMenuOpen }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 移动端菜单（展开时显示） -->
      <div v-show="mobileMenuOpen" class="sm:hidden border-t border-gray-200">
        <div class="pt-2 pb-3 space-y-1">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 text-base font-medium rounded-md transition-colors"
            :class="{
              'bg-primary-50 text-primary-700': currentRoute.startsWith(item.path),
              'text-gray-500 hover:bg-gray-50 hover:text-gray-700': !currentRoute.startsWith(item.path)
            }"
          >
            <span class="mr-3">{{ item.icon }}</span>
            {{ item.name }}
          </router-link>
        </div>
        <div class="pt-4 pb-3 border-t border-gray-200">
          <div class="px-4 space-y-1">
            <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">系统设置</div>
            <router-link
              v-for="item in settingsItems"
              :key="item.path"
              :to="item.path"
              @click="mobileMenuOpen = false"
              class="block px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
            >
              <span class="mr-3">{{ item.icon }}</span>
              {{ item.name }}
            </router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <main class="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 页脚 -->
    <footer class="bg-white border-t border-gray-200 mt-12">
      <div class="container mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="text-center text-gray-500 text-sm">
          <p>玉器店进销存系统 © 2024 | 数据安全存储于本地</p>
          <p class="mt-1">如需帮助，请联系技术支持</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
