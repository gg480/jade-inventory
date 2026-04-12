<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 桌面导航栏 (md以上显示) -->
    <nav class="hidden md:flex bg-white shadow-sm border-b border-gray-200">
      <div class="container mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-14">
          <!-- 左侧：Logo -->
          <div class="flex items-center space-x-8">
            <div class="flex-shrink-0">
              <span class="text-xl font-bold text-emerald-600">玉器进销存</span>
            </div>

            <!-- 导航链接 -->
            <div class="flex space-x-6">
              <router-link
                to="/inventory"
                class="px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="{
                  'text-emerald-700 bg-emerald-50': $route.path.startsWith('/inventory'),
                  'text-gray-700 hover:text-emerald-600 hover:bg-gray-50': !$route.path.startsWith('/inventory')
                }"
              >
                库存
              </router-link>
              <router-link
                to="/sales"
                class="px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="{
                  'text-emerald-700 bg-emerald-50': $route.path.startsWith('/sales'),
                  'text-gray-700 hover:text-emerald-600 hover:bg-gray-50': !$route.path.startsWith('/sales')
                }"
              >
                销售
              </router-link>
              <router-link
                to="/dashboard"
                class="px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="{
                  'text-emerald-700 bg-emerald-50': $route.path.startsWith('/dashboard'),
                  'text-gray-700 hover:text-emerald-600 hover:bg-gray-50': !$route.path.startsWith('/dashboard')
                }"
              >
                看板
              </router-link>

              <!-- 设置下拉菜单 -->
              <div class="relative group">
                <button
                  class="px-3 py-2 text-sm font-medium rounded-md transition-colors flex items-center"
                  :class="{
                    'text-emerald-700 bg-emerald-50': $route.path.startsWith('/settings'),
                    'text-gray-700 hover:text-emerald-600 hover:bg-gray-50': !$route.path.startsWith('/settings')
                  }"
                >
                  设置
                  <svg class="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                <div class="absolute left-0 mt-1 w-48 bg-white rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10 border border-gray-200">
                  <router-link
                    to="/settings/dicts"
                    class="block px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 rounded-t-md"
                    :class="{ 'bg-emerald-50 text-emerald-700': $route.path === '/settings/dicts' }"
                  >
                    字典管理
                  </router-link>
                  <router-link
                    to="/settings/metal"
                    class="block px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700"
                    :class="{ 'bg-emerald-50 text-emerald-700': $route.path === '/settings/metal' }"
                  >
                    贵金属市价
                  </router-link>
                  <router-link
                    to="/settings/suppliers"
                    class="block px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 rounded-b-md"
                    :class="{ 'bg-emerald-50 text-emerald-700': $route.path === '/settings/suppliers' }"
                  >
                    供应商管理
                  </router-link>
                </div>
              </div>

              <router-link
                to="/customers"
                class="px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="{
                  'text-emerald-700 bg-emerald-50': $route.path.startsWith('/customers'),
                  'text-gray-700 hover:text-emerald-600 hover:bg-gray-50': !$route.path.startsWith('/customers')
                }"
              >
                客户
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <main class="pb-16 md:pb-0 px-4 py-4">
      <router-view />
    </main>

    <!-- 移动端底部Tab栏 (md以下显示) -->
    <div class="fixed bottom-0 left-0 right-0 md:hidden bg-white border-t border-gray-200 shadow-lg">
      <div class="flex justify-around items-center h-14">
        <router-link
          to="/inventory"
          class="flex-1 flex flex-col items-center justify-center h-full text-xs font-medium transition-colors"
          :class="{
            'text-emerald-600': $route.path.startsWith('/inventory'),
            'text-gray-600': !$route.path.startsWith('/inventory')
          }"
        >
          库存
        </router-link>
        <router-link
          to="/sales"
          class="flex-1 flex flex-col items-center justify-center h-full text-xs font-medium transition-colors"
          :class="{
            'text-emerald-600': $route.path.startsWith('/sales'),
            'text-gray-600': !$route.path.startsWith('/sales')
          }"
        >
          销售
        </router-link>
        <router-link
          to="/dashboard"
          class="flex-1 flex flex-col items-center justify-center h-full text-xs font-medium transition-colors"
          :class="{
            'text-emerald-600': $route.path.startsWith('/dashboard'),
            'text-gray-600': !$route.path.startsWith('/dashboard')
          }"
        >
          看板
        </router-link>
        <router-link
          to="/settings/dicts"
          class="flex-1 flex flex-col items-center justify-center h-full text-xs font-medium transition-colors"
          :class="{
            'text-emerald-600': $route.path.startsWith('/settings'),
            'text-gray-600': !$route.path.startsWith('/settings')
          }"
        >
          设置
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const $route = useRoute()
</script>