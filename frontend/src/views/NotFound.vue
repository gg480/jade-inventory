<script setup>
</script>

<template>
  <div class="min-h-[60vh] flex items-center justify-center px-4">
    <div class="text-center">
      <!-- 404 大数字 -->
      <div class="text-8xl font-extrabold text-emerald-200 select-none">404</div>

      <!-- 提示信息 -->
      <div class="mt-4">
        <h1 class="text-2xl font-bold text-gray-900">页面不存在</h1>
        <p class="mt-2 text-gray-500">您访问的页面不存在或已被移除，请检查网址是否正确。</p>
      </div>

      <!-- 返回首页按钮 -->
      <div class="mt-8">
        <router-link
          to="/inventory"
          class="inline-flex items-center px-5 py-2.5 rounded-lg text-white bg-emerald-600 hover:bg-emerald-700 transition-colors font-medium text-sm shadow-sm"
        >
          <svg class="mr-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1" />
          </svg>
          返回首页
        </router-link>
      </div>
    </div>
  </div>
</template>
