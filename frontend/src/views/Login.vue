<template>
  <!-- 全屏登录页面 -->
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-sky-50 via-emerald-50 to-teal-50 px-4">
    <div class="w-full max-w-sm">
      <!-- 应用标题和图标 -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <svg class="w-9 h-9 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-gray-800">玉器进销存</h1>
        <p class="text-gray-500 mt-1 text-sm">请输入密码登录</p>
      </div>

      <!-- ===== 登录表单 ===== -->
      <div v-if="!showChangePassword" class="bg-white rounded-2xl shadow-lg p-6">
        <form @submit.prevent="handleLogin">
          <!-- 管理密码 -->
          <div class="mb-4">
            <label class="form-label">管理密码</label>
            <div class="relative">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input pr-10"
                placeholder="请输入管理密码"
                autofocus
                @keyup.enter="handleLogin"
              />
              <button
                type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                @click="showPassword = !showPassword"
              >
                <svg v-if="!showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                </svg>
              </button>
            </div>
          </div>

          <!-- 错误提示 -->
          <div v-if="errorMsg" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start">
            <svg class="h-5 w-5 text-red-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
            <p class="ml-3 text-sm text-red-700">{{ errorMsg }}</p>
          </div>

          <!-- 登录按钮 -->
          <button
            type="submit"
            class="btn btn-primary w-full flex items-center justify-center py-2.5 text-base"
            :disabled="loading"
          >
            <span v-if="loading" class="inline-block animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></span>
            {{ loading ? '登录中...' : '登 录' }}
          </button>
        </form>
      </div>

      <!-- ===== 修改密码表单 ===== -->
      <div v-else class="bg-white rounded-2xl shadow-lg p-6">
        <div class="mb-5">
          <h2 class="text-lg font-semibold text-gray-800">首次登录，请修改默认密码</h2>
          <p class="text-sm text-gray-500 mt-1">为了账户安全，请设置新的管理密码</p>
        </div>

        <form @submit.prevent="handleChangePassword">
          <!-- 原密码 -->
          <div class="mb-4">
            <label class="form-label">原密码</label>
            <input
              v-model="oldPassword"
              type="password"
              class="form-input"
              placeholder="请输入原密码"
            />
          </div>

          <!-- 新密码 -->
          <div class="mb-4">
            <label class="form-label">新密码</label>
            <input
              v-model="newPassword"
              type="password"
              class="form-input"
              placeholder="请输入新密码（至少6位）"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': passwordError }"
            />
            <p v-if="passwordError" class="mt-1 text-xs text-red-600">{{ passwordError }}</p>
          </div>

          <!-- 确认新密码 -->
          <div class="mb-4">
            <label class="form-label">确认新密码</label>
            <input
              v-model="confirmPassword"
              type="password"
              class="form-input"
              placeholder="请再次输入新密码"
              :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': confirmError }"
            />
            <p v-if="confirmError" class="mt-1 text-xs text-red-600">{{ confirmError }}</p>
          </div>

          <!-- 错误提示 -->
          <div v-if="changeErrorMsg" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start">
            <svg class="h-5 w-5 text-red-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
            <p class="ml-3 text-sm text-red-700">{{ changeErrorMsg }}</p>
          </div>

          <!-- 修改按钮 -->
          <button
            type="submit"
            class="btn btn-primary w-full flex items-center justify-center py-2.5 text-base"
            :disabled="changeLoading"
          >
            <span v-if="changeLoading" class="inline-block animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></span>
            {{ changeLoading ? '修改中...' : '确认修改' }}
          </button>
        </form>
      </div>

      <!-- 底部信息 -->
      <p class="text-center text-xs text-gray-400 mt-6">玉器店进销存管理系统</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

// ===== 登录相关 =====
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')
const showPassword = ref(false)

// ===== 修改密码相关 =====
const showChangePassword = ref(false)
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const changeLoading = ref(false)
const changeErrorMsg = ref('')
const passwordError = ref('')
const confirmError = ref('')

// 处理登录
async function handleLogin() {
  // 清除之前的错误
  errorMsg.value = ''

  if (!password.value) {
    errorMsg.value = '请输入管理密码'
    return
  }

  loading.value = true
  try {
    const data = await api.auth.login(password.value)

    // 保存token
    localStorage.setItem('token', data.token)

    // 检查是否需要修改密码
    if (data.must_change_password) {
      showChangePassword.value = true
      // 原密码自动填入
      oldPassword.value = password.value
      password.value = ''
    } else {
      // 登录成功，跳转到首页
      router.push('/inventory')
    }
  } catch (error) {
    errorMsg.value = error.message || '登录失败，请检查密码'
  } finally {
    loading.value = false
  }
}

// 处理修改密码
async function handleChangePassword() {
  // 清除之前的错误
  changeErrorMsg.value = ''
  passwordError.value = ''
  confirmError.value = ''

  // 前端验证
  if (!newPassword.value) {
    passwordError.value = '请输入新密码'
    return
  }
  if (newPassword.value.length < 6) {
    passwordError.value = '新密码至少需要6位'
    return
  }
  if (!confirmPassword.value) {
    confirmError.value = '请确认新密码'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    confirmError.value = '两次输入的密码不一致'
    return
  }

  changeLoading.value = true
  try {
    await api.auth.changePassword(oldPassword.value, newPassword.value)
    // 密码修改成功，跳转到首页
    router.push('/inventory')
  } catch (error) {
    changeErrorMsg.value = error.message || '密码修改失败，请重试'
  } finally {
    changeLoading.value = false
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

.btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}
</style>
