<script setup>
import SaleList from '../components/SaleList.vue'
</script>

<template>
  <div>
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">销售记录</h1>
      <p class="mt-1 text-sm text-gray-600">查看所有销售出库记录和利润统计</p>
    </div>
    <SaleList />
  </div>
</template>