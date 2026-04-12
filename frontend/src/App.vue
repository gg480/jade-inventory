<script setup>
import { useRoute } from 'vue-router'
import AppLayout from './components/AppLayout.vue'
import ToastContainer from './components/ToastContainer.vue'

const route = useRoute()
</script>

<template>
  <AppLayout v-if="!route.meta.noLayout" />
  <router-view v-else />
  <ToastContainer />
</template>
