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
            <div class="flex space-x-1">
              <!-- 库存管理 下拉菜单 -->
              <div class="relative group">
                <button
                  class="px-3 py-2 text-sm font-medium rounded-md transition-colors flex items-center"
                  :class="{
                    'text-emerald-700 bg-emerald-50': $route.path.startsWith('/inventory') || $route.path.startsWith('/batches'),
                    'text-gray-700 hover:text-emerald-600 hover:bg-gray-50': !$route.path.startsWith('/inventory') && !$route.path.startsWith('/batches')
                  }"
                >
                  库存管理
                  <svg class="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                <div class="absolute left-0 mt-1 w-48 bg-white rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10 border border-gray-200">
                  <router-link
                    to="/inventory"
                    class="block px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 rounded-t-md"
                    :class="{ 'bg-emerald-50 text-emerald-700': $route.path === '/inventory' }"
                  >
                    库存列表
                  </router-link>
                  <router-link
                    to="/batches"
                    class="block px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700"
                    :class="{ 'bg-emerald-50 text-emerald-700': $route.path === '/batches' }"
                  >
                    批次列表
                  </router-link>
                  <router-link
                    to="/inventory/add"
                    class="block px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 rounded-b-md"
                    :class="{ 'bg-emerald-50 text-emerald-700': $route.path === '/inventory/add' }"
                  >
                    新增入库
                  </router-link>
                </div>
              </div>

              <router-link
                to="/sales"
                class="px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="{
                  'text-emerald-700 bg-emerald-50': $route.path.startsWith('/sales') || $route.path === '/scan',
                  'text-gray-700 hover:text-emerald-600 hover:bg-gray-50': !$route.path.startsWith('/sales') && $route.path !== '/scan'
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
              <router-link
                to="/pricing"
                class="px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="{
                  'text-emerald-700 bg-emerald-50': $route.path === '/pricing',
                  'text-gray-700 hover:text-emerald-600 hover:bg-gray-50': $route.path !== '/pricing'
                }"
              >
                定价
              </router-link>

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

              <!-- 设置下拉菜单 -->
              <div class="relative group">
                <button
                  class="px-3 py-2 text-sm font-medium rounded-md transition-colors flex items-center"
                  :class="{
                    'text-emerald-700 bg-emerald-50': $route.path.startsWith('/settings') || $route.path === '/labels',
                    'text-gray-700 hover:text-emerald-600 hover:bg-gray-50': !$route.path.startsWith('/settings') && $route.path !== '/labels'
                  }"
                >
                  工具
                  <svg class="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                <div class="absolute left-0 mt-1 w-48 bg-white rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10 border border-gray-200">
                  <router-link
                    to="/scan"
                    class="block px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 rounded-t-md"
                    :class="{ 'bg-emerald-50 text-emerald-700': $route.path === '/scan' }"
                  >
                    扫码出库
                  </router-link>
                  <router-link
                    to="/labels"
                    class="block px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700"
                    :class="{ 'bg-emerald-50 text-emerald-700': $route.path === '/labels' }"
                  >
                    标签打印
                  </router-link>
                  <router-link
                    to="/settings/dicts"
                    class="block px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700"
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
    <div class="fixed bottom-0 left-0 right-0 md:hidden bg-white border-t border-gray-200 shadow-lg safe-area-bottom">
      <div class="flex items-center h-14">
        <!-- 库存 -->
        <router-link
          to="/inventory"
          class="flex-1 flex flex-col items-center justify-center h-full text-[10px] font-medium transition-colors gap-0.5"
          :class="{
            'text-emerald-600': $route.path.startsWith('/inventory') || $route.path.startsWith('/batches'),
            'text-gray-500': !$route.path.startsWith('/inventory') && !$route.path.startsWith('/batches')
          }"
        >
          <!-- 库存图标: 箱子/包裹 -->
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          <span>库存</span>
        </router-link>

        <!-- 销售 -->
        <router-link
          to="/sales"
          class="flex-1 flex flex-col items-center justify-center h-full text-[10px] font-medium transition-colors gap-0.5"
          :class="{
            'text-emerald-600': $route.path.startsWith('/sales') || $route.path === '/scan',
            'text-gray-500': !$route.path.startsWith('/sales') && $route.path !== '/scan'
          }"
        >
          <!-- 销售图标: 购物车 -->
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" />
          </svg>
          <span>销售</span>
        </router-link>

        <!-- 扫码（突出按钮） -->
        <router-link
          to="/scan"
          class="flex-1 flex flex-col items-center justify-center h-full text-[10px] font-medium transition-colors gap-0.5"
          :class="{
            'text-emerald-600': $route.path === '/scan',
            'text-gray-500': $route.path !== '/scan'
          }"
        >
          <!-- 扫码图标: 条码扫描 -->
          <div class="w-10 h-10 -mt-4 bg-emerald-600 rounded-full flex items-center justify-center shadow-lg">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
            </svg>
          </div>
          <span class="-mt-1">扫码</span>
        </router-link>

        <!-- 看板 -->
        <router-link
          to="/dashboard"
          class="flex-1 flex flex-col items-center justify-center h-full text-[10px] font-medium transition-colors gap-0.5"
          :class="{
            'text-emerald-600': $route.path.startsWith('/dashboard'),
            'text-gray-500': !$route.path.startsWith('/dashboard')
          }"
        >
          <!-- 看板图标: 柱状图 -->
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <span>看板</span>
        </router-link>

        <!-- 批次 -->
        <router-link
          to="/batches"
          class="flex-1 flex flex-col items-center justify-center h-full text-[10px] font-medium transition-colors gap-0.5"
          :class="{
            'text-emerald-600': $route.path.startsWith('/batches'),
            'text-gray-500': !$route.path.startsWith('/batches')
          }"
        >
          <!-- 批次图标: 层叠 -->
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <span>批次</span>
        </router-link>

        <!-- 客户 -->
        <router-link
          to="/customers"
          class="flex-1 flex flex-col items-center justify-center h-full text-[10px] font-medium transition-colors gap-0.5"
          :class="{
            'text-emerald-600': $route.path.startsWith('/customers'),
            'text-gray-500': !$route.path.startsWith('/customers')
          }"
        >
          <!-- 客户图标: 用户组 -->
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <span>客户</span>
        </router-link>

        <!-- 设置 -->
        <router-link
          to="/settings/dicts"
          class="flex-1 flex flex-col items-center justify-center h-full text-[10px] font-medium transition-colors gap-0.5"
          :class="{
            'text-emerald-600': $route.path.startsWith('/settings'),
            'text-gray-500': !$route.path.startsWith('/settings')
          }"
        >
          <!-- 设置图标: 齿轮 -->
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span>设置</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const $route = useRoute()
</script>

<style scoped>
/* iOS 安全区域适配 */
.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
</style>
