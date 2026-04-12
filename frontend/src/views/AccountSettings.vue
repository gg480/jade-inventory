<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">账户设置</h1>

    <!-- 修改密码 -->
    <div class="card mb-6">
      <h2 class="text-lg font-semibold text-gray-800 mb-4">修改密码</h2>

      <form @submit.prevent="handleChangePassword" class="max-w-md">
        <!-- 当前密码 -->
        <div class="mb-4">
          <label class="form-label">当前密码</label>
          <input
            v-model="currentPassword"
            type="password"
            class="form-input"
            placeholder="请输入当前密码"
            :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': fieldErrors.currentPassword }"
          />
          <p v-if="fieldErrors.currentPassword" class="mt-1 text-xs text-red-600">{{ fieldErrors.currentPassword }}</p>
        </div>

        <!-- 新密码 -->
        <div class="mb-4">
          <label class="form-label">新密码</label>
          <input
            v-model="newPassword"
            type="password"
            class="form-input"
            placeholder="请输入新密码（至少6位）"
            :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': fieldErrors.newPassword }"
          />
          <p v-if="fieldErrors.newPassword" class="mt-1 text-xs text-red-600">{{ fieldErrors.newPassword }}</p>
        </div>

        <!-- 确认新密码 -->
        <div class="mb-4">
          <label class="form-label">确认新密码</label>
          <input
            v-model="confirmPassword"
            type="password"
            class="form-input"
            placeholder="请再次输入新密码"
            :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': fieldErrors.confirmPassword }"
          />
          <p v-if="fieldErrors.confirmPassword" class="mt-1 text-xs text-red-600">{{ fieldErrors.confirmPassword }}</p>
        </div>

        <!-- 操作提示/错误 -->
        <div v-if="submitMsg" class="mb-4 p-3 rounded-lg flex items-start" :class="submitMsgType === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
          <svg v-if="submitMsgType === 'success'" class="h-5 w-5 text-green-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          <svg v-else class="h-5 w-5 text-red-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <p class="ml-3 text-sm" :class="submitMsgType === 'success' ? 'text-green-700' : 'text-red-700'">{{ submitMsg }}</p>
        </div>

        <button
          type="submit"
          class="btn btn-primary"
          :disabled="loading"
        >
          <span v-if="loading" class="inline-block animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></span>
          {{ loading ? '修改中...' : '确认修改' }}
        </button>
      </form>
    </div>

    <!-- 数据库备份 -->
    <div class="card">
      <h2 class="text-lg font-semibold text-gray-800 mb-2">数据库备份</h2>
      <p class="text-sm text-gray-500 mb-4">下载当前数据库的完整备份文件，用于数据迁移或灾难恢复。</p>

      <div class="flex items-center space-x-3">
        <button
          @click="handleBackup"
          class="btn btn-success"
          :disabled="backupLoading"
        >
          <span v-if="backupLoading" class="inline-block animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></span>
          <svg v-else class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          {{ backupLoading ? '下载中...' : '下载数据库备份' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import api from '@/api'

// 修改密码相关
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const submitMsg = ref('')
const submitMsgType = ref('success')
const fieldErrors = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

// 数据库备份相关
const backupLoading = ref(false)

// 处理修改密码
async function handleChangePassword() {
  // 清除之前的错误
  Object.keys(fieldErrors).forEach(key => fieldErrors[key] = '')
  submitMsg.value = ''

  // 前端验证
  let hasError = false
  if (!currentPassword.value) {
    fieldErrors.currentPassword = '请输入当前密码'
    hasError = true
  }
  if (!newPassword.value) {
    fieldErrors.newPassword = '请输入新密码'
    hasError = true
  } else if (newPassword.value.length < 6) {
    fieldErrors.newPassword = '新密码至少需要6位'
    hasError = true
  }
  if (!confirmPassword.value) {
    fieldErrors.confirmPassword = '请确认新密码'
    hasError = true
  } else if (newPassword.value && newPassword.value !== confirmPassword.value) {
    fieldErrors.confirmPassword = '两次输入的密码不一致'
    hasError = true
  }

  if (hasError) return

  loading.value = true
  try {
    await api.auth.changePassword(currentPassword.value, newPassword.value)
    submitMsg.value = '密码修改成功'
    submitMsgType.value = 'success'
    // 清空表单
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (error) {
    submitMsg.value = error.message || '密码修改失败，请重试'
    submitMsgType.value = 'error'
  } finally {
    loading.value = false
  }
}

// 处理数据库备份下载
async function handleBackup() {
  backupLoading.value = true
  try {
    const response = await api.instance.get('/auth/backup-db', {
      responseType: 'blob',
    })

    // 从响应头获取文件名，或使用默认文件名
    const contentDisposition = response.headers?.['content-disposition']
    let filename = `jade-inventory-backup-${new Date().toISOString().slice(0, 10)}.db`
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename\*?=(?:UTF-8'')?(.+)/i)
      if (filenameMatch) {
        filename = decodeURIComponent(filenameMatch[1].replace(/["']/g, ''))
      }
    }

    // 创建下载链接
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('数据库备份失败:', error)
  } finally {
    backupLoading.value = false
  }
}
</script>

<style scoped>
.form-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm;
}

.form-label {
  @apply block text-sm font-medium text-gray-700 mb-1;
}

.btn {
  @apply px-4 py-2 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2;
}

.btn-primary {
  @apply bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500;
}

.btn-success {
  @apply bg-green-600 text-white hover:bg-green-700 focus:ring-green-500;
}

.btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}
</style>
