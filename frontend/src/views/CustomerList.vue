<template>
  <div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">客户管理</h1>
      <button
        @click="openAddModal"
        class="btn btn-success"
      >
        <svg class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        新增客户
      </button>
    </div>

    <!-- 搜索栏 -->
    <div class="mb-6 bg-white p-4 rounded-lg shadow">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="form-label">按姓名搜索</label>
          <input
            v-model="searchParams.name"
            type="text"
            class="form-input"
            placeholder="输入客户姓名"
            @input="debouncedSearch"
          />
        </div>
        <div>
          <label class="form-label">按电话搜索</label>
          <input
            v-model="searchParams.phone"
            type="text"
            class="form-input"
            placeholder="输入客户电话"
            @input="debouncedSearch"
          />
        </div>
        <div>
          <label class="form-label">按微信搜索</label>
          <input
            v-model="searchParams.wechat"
            type="text"
            class="form-input"
            placeholder="输入微信号"
            @input="debouncedSearch"
          />
        </div>
      </div>
      <div class="mt-4 flex justify-between items-center">
        <div class="flex items-center space-x-2">
          <label class="flex items-center">
            <input
              v-model="searchParams.include_inactive"
              type="checkbox"
              class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              @change="fetchCustomers"
            />
            <span class="ml-2 text-sm text-gray-700">显示已停用客户</span>
          </label>
        </div>
        <div class="text-sm text-gray-500">
          共 {{ customers.length }} 位客户
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading.customers" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      <p class="mt-4 text-gray-600">加载客户数据中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="customers.length === 0" class="bg-white rounded-lg shadow p-8 text-center">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">暂无客户</h3>
      <p class="mt-1 text-sm text-gray-500">点击右上角"新增客户"按钮添加第一位客户。</p>
    </div>

    <!-- 客户列表 -->
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <!-- 表格（桌面） -->
      <div class="hidden md:block overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">客户编号</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">姓名</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">电话</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">微信</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">备注</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <template v-for="customer in customers" :key="customer.id">
              <!-- 客户行（可点击展开） -->
              <tr
                @click="toggleCustomerExpanded(customer.id)"
                class="hover:bg-gray-50 cursor-pointer"
                :class="{'bg-gray-50': expandedCustomer === customer.id}"
              >
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-gray-900">{{ customer.customer_code }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div class="text-sm font-medium text-gray-900">{{ customer.name }}</div>
                    <div v-if="!customer.is_active" class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                      已停用
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-900">{{ customer.phone || '-' }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-900">{{ customer.wechat || '-' }}</div>
                </td>
                <td class="px-6 py-4">
                  <div class="text-sm text-gray-900 max-w-xs truncate">{{ customer.notes || '-' }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="customer.is_active ? 'text-green-600' : 'text-gray-500'" class="text-sm">
                    {{ customer.is_active ? '启用' : '停用' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium" @click.stop>
                  <button
                    @click="openEditModal(customer)"
                    class="text-primary-600 hover:text-primary-900 mr-3"
                  >
                    编辑
                  </button>
                  <button
                    @click="toggleCustomerStatus(customer)"
                    :class="customer.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'"
                  >
                    {{ customer.is_active ? '停用' : '启用' }}
                  </button>
                </td>
              </tr>

              <!-- 展开的购买记录 -->
              <tr v-if="expandedCustomer === customer.id">
                <td colspan="7" class="px-6 py-4 bg-gray-50 border-t">
                  <div v-if="loading.details[customer.id]" class="text-center py-4">
                    <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
                    <p class="mt-2 text-sm text-gray-600">加载购买记录中...</p>
                  </div>
                  <div v-else-if="!customerDetails[customer.id]?.purchase_records?.length" class="text-center py-4">
                    <p class="text-sm text-gray-500">该客户暂无购买记录</p>
                  </div>
                  <div v-else>
                    <h4 class="text-sm font-medium text-gray-900 mb-3">购买记录</h4>
                    <div class="overflow-x-auto">
                      <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-100">
                          <tr>
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">销售日期</th>
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">货品编号</th>
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">货品名称</th>
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">成交价(元)</th>
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">毛利(元)</th>
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">销售渠道</th>
                          </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                          <tr v-for="record in customerDetails[customer.id]?.purchase_records" :key="record.id">
                            <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                              {{ formatDate(record.sale_date) }}
                            </td>
                            <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                              {{ record.item_sku }}
                            </td>
                            <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                              {{ record.item_name || '-' }}
                            </td>
                            <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                              ¥{{ record.actual_price.toFixed(2) }}
                            </td>
                            <td class="px-3 py-2 whitespace-nowrap text-sm">
                              <span :class="record.gross_profit >= 0 ? 'text-green-600' : 'text-red-600'">
                                ¥{{ record.gross_profit?.toFixed(2) || '0.00' }}
                              </span>
                            </td>
                            <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                              {{ formatSalesChannel(record.sales_channel) }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- 卡片（移动端） -->
      <div class="md:hidden space-y-4 p-4">
        <div v-for="customer in customers" :key="customer.id" class="bg-gray-50 rounded-lg p-4">
          <!-- 客户卡片头部 -->
          <div @click="toggleCustomerExpanded(customer.id)" class="cursor-pointer">
            <div class="flex justify-between items-start">
              <div>
                <h3 class="text-sm font-medium text-gray-900">{{ customer.name }}</h3>
                <p class="mt-1 text-sm text-gray-600">{{ customer.customer_code }}</p>
                <div class="mt-1 flex flex-wrap gap-2">
                  <span v-if="customer.phone" class="text-xs text-gray-500">电话：{{ customer.phone }}</span>
                  <span v-if="customer.wechat" class="text-xs text-gray-500">微信：{{ customer.wechat }}</span>
                </div>
              </div>
              <div class="flex items-center">
                <span :class="customer.is_active ? 'text-green-600' : 'text-gray-500'" class="text-xs">
                  {{ customer.is_active ? '启用' : '停用' }}
                </span>
                <svg :class="expandedCustomer === customer.id ? 'rotate-180' : ''" class="ml-2 h-5 w-5 text-gray-400 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            <div v-if="customer.notes" class="mt-2 text-sm text-gray-700">
              <p class="truncate">{{ customer.notes }}</p>
            </div>
          </div>

          <!-- 操作按钮（移动端） -->
          <div class="mt-3 flex justify-end space-x-2" @click.stop>
            <button
              @click="openEditModal(customer)"
              class="px-3 py-1 bg-primary-50 text-primary-700 text-sm rounded-md hover:bg-primary-100"
            >
              编辑
            </button>
            <button
              @click="toggleCustomerStatus(customer)"
              :class="customer.is_active ? 'bg-red-50 text-red-700 hover:bg-red-100' : 'bg-green-50 text-green-700 hover:bg-green-100'"
              class="px-3 py-1 text-sm rounded-md"
            >
              {{ customer.is_active ? '停用' : '启用' }}
            </button>
          </div>

          <!-- 展开的购买记录（移动端） -->
          <div v-if="expandedCustomer === customer.id" class="mt-4 pt-4 border-t border-gray-200">
            <div v-if="loading.details[customer.id]" class="text-center py-4">
              <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              <p class="mt-2 text-sm text-gray-600">加载购买记录中...</p>
            </div>
            <div v-else-if="!customerDetails[customer.id]?.purchase_records?.length" class="text-center py-4">
              <p class="text-sm text-gray-500">该客户暂无购买记录</p>
            </div>
            <div v-else>
              <h4 class="text-sm font-medium text-gray-900 mb-3">购买记录</h4>
              <div class="space-y-3">
                <div v-for="record in customerDetails[customer.id]?.purchase_records" :key="record.id" class="bg-white p-3 rounded border border-gray-200">
                  <div class="grid grid-cols-2 gap-2 text-sm">
                    <div class="text-gray-500">销售日期：</div>
                    <div class="text-gray-900">{{ formatDate(record.sale_date) }}</div>
                    <div class="text-gray-500">货品编号：</div>
                    <div class="text-gray-900">{{ record.item_sku }}</div>
                    <div class="text-gray-500">货品名称：</div>
                    <div class="text-gray-900">{{ record.item_name || '-' }}</div>
                    <div class="text-gray-500">成交价：</div>
                    <div class="text-gray-900">¥{{ record.actual_price.toFixed(2) }}</div>
                    <div class="text-gray-500">毛利：</div>
                    <div>
                      <span :class="record.gross_profit >= 0 ? 'text-green-600' : 'text-red-600'">
                        ¥{{ record.gross_profit?.toFixed(2) || '0.00' }}
                      </span>
                    </div>
                    <div class="text-gray-500">销售渠道：</div>
                    <div class="text-gray-900">{{ formatSalesChannel(record.sales_channel) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 客户模态框 -->
    <CustomerModal
      :visible="showCustomerModal"
      :customer="editingCustomer"
      :mode="customerModalMode"
      :loading="customerModalLoading"
      @submit="handleCustomerSubmit"
      @cancel="closeCustomerModal"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import CustomerModal from '@/components/CustomerModal.vue'
import api from '@/api'
// 自定义防抖函数
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// 响应式数据
const customers = ref([])
const customerDetails = ref({}) // { customerId: { purchase_records: [...] } }
const expandedCustomer = ref(null)
const showCustomerModal = ref(false)
const editingCustomer = ref(null)
const customerModalMode = ref('add')
const customerModalLoading = ref(false)

// 搜索参数
const searchParams = ref({
  name: '',
  phone: '',
  wechat: '',
  include_inactive: false
})

// 加载状态
const loading = ref({
  customers: false,
  details: {} // { customerId: boolean }
})

// 初始化加载数据
onMounted(() => {
  fetchCustomers()
})

// 获取客户列表
async function fetchCustomers() {
  loading.value.customers = true
  try {
    const params = {}
    if (searchParams.value.name) params.name = searchParams.value.name
    if (searchParams.value.phone) params.phone = searchParams.value.phone
    if (searchParams.value.wechat) params.wechat = searchParams.value.wechat
    if (searchParams.value.include_inactive) params.include_inactive = true

    const data = await api.customers.getCustomers(params)
    customers.value = data || []
  } catch (error) {
    console.error('获取客户列表失败:', error)
    customers.value = []
  } finally {
    loading.value.customers = false
  }
}

// 防抖搜索
const debouncedSearch = debounce(() => {
  fetchCustomers()
}, 500)

// 切换客户展开状态
async function toggleCustomerExpanded(customerId) {
  if (expandedCustomer.value === customerId) {
    // 如果已经展开，则折叠
    expandedCustomer.value = null
  } else {
    // 展开新客户
    const previousExpanded = expandedCustomer.value
    expandedCustomer.value = customerId

    // 如果之前有其他客户展开，保持其详情缓存
    // 加载新客户的详情（如果尚未加载）
    if (!customerDetails.value[customerId]) {
      await fetchCustomerDetail(customerId)
    }

    // 如果之前有客户展开，可以清空或保留
    // 这里选择保留之前的详情缓存
  }
}

// 获取客户详情（含购买记录）
async function fetchCustomerDetail(customerId) {
  loading.value.details[customerId] = true
  try {
    const data = await api.customers.getCustomerDetail(customerId)
    customerDetails.value[customerId] = data || { purchase_records: [] }
  } catch (error) {
    console.error(`获取客户${customerId}详情失败:`, error)
    customerDetails.value[customerId] = { purchase_records: [] }
  } finally {
    loading.value.details[customerId] = false
  }
}

// 打开新增客户模态框
function openAddModal() {
  editingCustomer.value = null
  customerModalMode.value = 'add'
  showCustomerModal.value = true
}

// 打开编辑客户模态框
function openEditModal(customer) {
  editingCustomer.value = customer
  customerModalMode.value = 'edit'
  showCustomerModal.value = true
}

// 关闭客户模态框
function closeCustomerModal() {
  showCustomerModal.value = false
  editingCustomer.value = null
  customerModalLoading.value = false
}

// 处理客户提交（新增或编辑）
async function handleCustomerSubmit(formData) {
  customerModalLoading.value = true

  try {
    if (customerModalMode.value === 'add') {
      // 新增客户
      await api.customers.createCustomer(formData)
    } else {
      // 编辑客户
      await api.customers.updateCustomer(editingCustomer.value.id, formData)
    }

    // 刷新客户列表
    await fetchCustomers()

    // 如果当前有展开的客户，且编辑的是该客户，刷新详情
    if (expandedCustomer.value && editingCustomer.value && expandedCustomer.value === editingCustomer.value.id) {
      await fetchCustomerDetail(expandedCustomer.value)
    }

    // 关闭模态框
    closeCustomerModal()

  } catch (error) {
    console.error('保存客户失败:', error)
    alert('保存失败: ' + (error.message || '请重试'))
  } finally {
    customerModalLoading.value = false
  }
}

// 切换客户状态（启用/停用）
async function toggleCustomerStatus(customer) {
  const newStatus = !customer.is_active
  const confirmMessage = newStatus ? '确定要启用该客户吗？' : '确定要停用该客户吗？停用后该客户将不会出现在客户列表中。'

  if (!confirm(confirmMessage)) {
    return
  }

  try {
    await api.customers.updateCustomer(customer.id, {
      is_active: newStatus
    })

    // 刷新客户列表
    await fetchCustomers()

    // 如果当前有展开该客户，刷新详情
    if (expandedCustomer.value === customer.id) {
      await fetchCustomerDetail(customer.id)
    }

  } catch (error) {
    console.error('切换客户状态失败:', error)
    alert('操作失败: ' + (error.message || '请重试'))
  }
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 格式化销售渠道
function formatSalesChannel(channel) {
  const channelMap = {
    'in_store': '门店',
    'wechat': '微信',
    'online': '线上',
    'other': '其他'
  }
  return channelMap[channel] || channel
}
</script>

<style scoped>
.form-label {
  @apply block text-sm font-medium text-gray-700 mb-1;
}

.form-input {
  @apply block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm;
}

.btn {
  @apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2;
}

.btn-success {
  @apply bg-green-600 text-white hover:bg-green-700 focus:ring-green-500;
}
</style>