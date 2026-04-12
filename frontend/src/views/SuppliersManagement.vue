<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">供应商管理</h1>
        <p class="mt-1 text-sm text-gray-600">管理货品供货商信息</p>
      </div>
      <button @click="openAddModal" class="btn btn-success">
        <svg class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        新增供应商
      </button>
    </div>

    <!-- 搜索栏 -->
    <div class="mb-6 card">
      <div class="flex flex-col sm:flex-row gap-4">
        <div class="flex-1">
          <input
            v-model="searchName"
            type="text"
            class="form-input"
            placeholder="按名称搜索..."
            @input="debouncedFetch"
          />
        </div>
        <label class="flex items-center space-x-2">
          <input
            v-model="includeInactive"
            type="checkbox"
            class="h-4 w-4 text-primary-600 rounded"
            @change="fetchSuppliers"
          />
          <span class="text-sm text-gray-700">显示已停用</span>
        </label>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      <p class="mt-4 text-gray-600">加载供应商数据中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="suppliers.length === 0" class="card text-center py-12">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">暂无供应商</h3>
      <p class="mt-1 text-sm text-gray-500">点击"新增供应商"按钮添加第一位供应商。</p>
    </div>

    <!-- 供应商列表 -->
    <div v-else>
      <!-- 桌面表格 -->
      <div class="hidden md:block card overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">名称</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">联系方式</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">备注</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="s in suppliers" :key="s.id" class="hover:bg-gray-50">
              <td class="px-6 py-4">
                <div class="text-sm font-medium text-gray-900">{{ s.name }}</div>
              </td>
              <td class="px-6 py-4 text-sm text-gray-600">{{ s.contact || '-' }}</td>
              <td class="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">{{ s.notes || '-' }}</td>
              <td class="px-6 py-4">
                <span :class="s.is_active ? 'text-green-600' : 'text-gray-400'" class="text-sm">
                  {{ s.is_active ? '启用' : '停用' }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm space-x-3">
                <button @click="openEditModal(s)" class="text-primary-600 hover:text-primary-900">编辑</button>
                <button
                  @click="toggleStatus(s)"
                  :class="s.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'"
                >
                  {{ s.is_active ? '停用' : '启用' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 移动端卡片 -->
      <div class="md:hidden space-y-3">
        <div v-for="s in suppliers" :key="s.id" class="card p-4">
          <div class="flex justify-between items-start">
            <div>
              <h3 class="text-sm font-medium text-gray-900">{{ s.name }}</h3>
              <p v-if="s.contact" class="mt-1 text-xs text-gray-500">{{ s.contact }}</p>
              <p v-if="s.notes" class="mt-1 text-xs text-gray-400 truncate max-w-[200px]">{{ s.notes }}</p>
            </div>
            <span :class="s.is_active ? 'text-green-600' : 'text-gray-400'" class="text-xs">
              {{ s.is_active ? '启用' : '停用' }}
            </span>
          </div>
          <div class="mt-3 flex justify-end space-x-3">
            <button @click="openEditModal(s)" class="text-sm text-primary-600">编辑</button>
            <button
              @click="toggleStatus(s)"
              :class="s.is_active ? 'text-red-600' : 'text-green-600'"
              class="text-sm"
            >
              {{ s.is_active ? '停用' : '启用' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 模态框 -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="fixed inset-0 bg-black/40" @click="closeModal"></div>
      <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          {{ isEdit ? '编辑供应商' : '新增供应商' }}
        </h3>
        <div class="space-y-4">
          <div>
            <label class="form-label">名称 <span class="text-red-500">*</span></label>
            <input v-model="form.name" type="text" class="form-input" placeholder="供应商名称" />
          </div>
          <div>
            <label class="form-label">联系方式</label>
            <input v-model="form.contact" type="text" class="form-input" placeholder="联系人或电话" />
          </div>
          <div>
            <label class="form-label">备注</label>
            <textarea v-model="form.notes" rows="2" class="form-input" placeholder="备注信息"></textarea>
          </div>
        </div>
        <div class="mt-6 flex justify-end space-x-3">
          <button @click="closeModal" class="btn btn-secondary">取消</button>
          <button @click="handleSubmit" :disabled="submitting" class="btn btn-success">
            {{ submitting ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const suppliers = ref([])
const loading = ref(false)
const searchName = ref('')
const includeInactive = ref(false)

// 模态框
const showModal = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const form = ref({ name: '', contact: '', notes: '' })

function debounce(fn, wait) {
  let t
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait) }
}

const debouncedFetch = debounce(() => fetchSuppliers(), 500)

onMounted(() => fetchSuppliers())

async function fetchSuppliers() {
  loading.value = true
  try {
    const params = {}
    if (searchName.value) params.name = searchName.value
    if (includeInactive.value) params.include_inactive = true
    const data = await api.suppliers.getSuppliers(params)
    suppliers.value = data?.items || data || []
  } catch (e) {
    console.error('获取供应商列表失败:', e)
    suppliers.value = []
  } finally {
    loading.value = false
  }
}

function openAddModal() {
  isEdit.value = false
  editingId.value = null
  form.value = { name: '', contact: '', notes: '' }
  showModal.value = true
}

function openEditModal(s) {
  isEdit.value = true
  editingId.value = s.id
  form.value = { name: s.name, contact: s.contact || '', notes: s.notes || '' }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

async function handleSubmit() {
  if (!form.value.name.trim()) {
    alert('请输入供应商名称')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await api.suppliers.updateSupplier(editingId.value, form.value)
    } else {
      await api.suppliers.createSupplier(form.value)
    }
    closeModal()
    await fetchSuppliers()
  } catch (e) {
    console.error('保存供应商失败:', e)
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(s) {
  const newStatus = !s.is_active
  const msg = newStatus ? '确定要启用该供应商吗？' : '确定要停用该供应商吗？'
  if (!confirm(msg)) return
  try {
    await api.suppliers.updateSupplier(s.id, { is_active: newStatus })
    await fetchSuppliers()
  } catch (e) {
    console.error('切换状态失败:', e)
  }
}
</script>

<style scoped>
.form-label { @apply block text-sm font-medium text-gray-700 mb-1; }
.form-input { @apply block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border; }
.btn { @apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2; }
.btn-success { @apply bg-green-600 text-white hover:bg-green-700 focus:ring-green-500; }
.btn-secondary { @apply bg-gray-200 text-gray-700 hover:bg-gray-300 focus:ring-gray-400; }
</style>
