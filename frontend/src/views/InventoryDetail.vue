<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import SaleDialog from '../components/SaleDialog.vue'

const route = useRoute()
const router = useRouter()
const item = ref(null)
const loading = ref(false)
const batchInfo = ref(null)

// 计算属性
const displayCost = computed(() => {
  if (!item.value) return 0
  // 优先使用分摊成本，其次进价
  return item.value.allocated_cost ?? item.value.cost_price ?? 0
})
const displayCostLabel = computed(() => {
  if (!item.value) return '成本'
  return item.value.allocated_cost !== null ? '分摊成本' : '进价'
})
const profit = computed(() => {
  if (!item.value) return 0
  return item.value.selling_price - displayCost.value
})
const profitMargin = computed(() => {
  if (!item.value || item.value.selling_price === 0) return 0
  return (profit.value / item.value.selling_price) * 100
})
const specFields = computed(() => {
  if (!item.value || !item.value.spec) return []
  const spec = item.value.spec
  const fields = []
  if (spec.weight !== null && spec.weight !== undefined) fields.push({ label: '克重', value: `${spec.weight}克` })
  if (spec.metal_weight !== null && spec.metal_weight !== undefined) fields.push({ label: '金属克重', value: `${spec.metal_weight}克` })
  if (spec.size) fields.push({ label: '尺寸', value: spec.size })
  if (spec.bracelet_size) fields.push({ label: '圈口', value: spec.bracelet_size })
  if (spec.bead_count !== null && spec.bead_count !== undefined) fields.push({ label: '粒数', value: `${spec.bead_count}粒` })
  if (spec.bead_diameter) fields.push({ label: '珠子口径', value: spec.bead_diameter })
  if (spec.ring_size) fields.push({ label: '戒指尺寸', value: spec.ring_size })
  return fields
})

// 获取批次详情（用于回本进度）
async function fetchBatch(batchId) {
  try {
    const data = await api.batches.getBatch(batchId)
    batchInfo.value = data
  } catch (error) {
    console.error('获取批次详情失败:', error)
    batchInfo.value = null
  }
}

// 出库相关
const showSaleDialog = ref(false)

// 获取货品详情
async function fetchItem() {
  loading.value = true
  batchInfo.value = null
  try {
    const data = await api.items.getItem(route.params.id)
    item.value = data
    // 如果有关联批次，获取批次详情（用于回本进度）
    if (data.batch_id) {
      await fetchBatch(data.batch_id)
    }
  } catch (error) {
    console.error('获取货品详情失败:', error)
    alert('货品不存在或已删除')
    router.push('/inventory')
  } finally {
    loading.value = false
  }
}

// 删除货品
async function deleteItem() {
  if (!confirm('确定要删除这个货品吗？删除后不可恢复。')) return

  try {
    await api.items.deleteItem(route.params.id)
    alert('删除成功')
    router.push('/inventory')
  } catch (error) {
    alert(`删除失败: ${error.message}`)
  }
}

// 标记为借出
async function markAsLent() {
  if (!confirm('标记为借出？')) return
  try {
    await api.items.updateItem(route.params.id, { status: 'lent_out' })
    alert('已标记为借出')
    fetchItem()
  } catch (error) {
    alert(`操作失败: ${error.message}`)
  }
}

// 标记为已退
async function markAsReturned() {
  if (!confirm('标记为已退？')) return
  try {
    await api.items.updateItem(route.params.id, { status: 'returned' })
    alert('已标记为已退')
    fetchItem()
  } catch (error) {
    alert(`操作失败: ${error.message}`)
  }
}

// 编辑货品
function editItem() {
  router.push(`/inventory/edit/${route.params.id}`)
}

// 打开出库弹窗
function openCheckoutModal() {
  showSaleDialog.value = true
}

// 处理出库成功
function handleSaleSuccess() {
  alert('出库成功！')
  fetchItem() // 刷新详情
}

onMounted(() => {
  fetchItem()
})
</script>

<template>
  <div>
    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      <p class="mt-2 text-gray-500">加载中...</p>
    </div>

    <!-- 货品详情 -->
    <div v-else-if="item" class="space-y-6">
      <!-- 头部 -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{{ item.sku_code }}</h1>
          <div class="mt-2 flex items-center space-x-4">
            <span class="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
              {{ item.material_name }}
            </span>
            <span v-if="item.type_name" class="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
              {{ item.type_name }}
            </span>
            <span :class="{
              'px-3 py-1 rounded-full text-sm font-medium': true,
              'bg-green-100 text-green-800': item.status === 'in_stock',
              'bg-blue-100 text-blue-800': item.status === 'lent_out',
              'bg-yellow-100 text-yellow-800': item.status === 'returned',
              'bg-gray-100 text-gray-800': item.status === 'sold'
            }">
              {{ { in_stock: '在库', lent_out: '借出', returned: '已退', sold: '已售' }[item.status] || item.status }}
            </span>
          </div>
        </div>
        <div class="mt-4 sm:mt-0 flex space-x-3">
          <button
            @click="editItem"
            class="btn btn-primary"
          >
            编辑
          </button>
          <button
            v-if="item.status === 'in_stock'"
            @click="openCheckoutModal"
            class="btn btn-success"
          >
            销售出库
          </button>
          <button
            v-if="item.status === 'in_stock'"
            @click="markAsLent"
            class="btn btn-secondary"
          >
            标记为借出
          </button>
          <button
            v-if="item.status === 'lent_out'"
            @click="markAsReturned"
            class="btn btn-secondary"
          >
            标记为已退
          </button>
          <button
            @click="deleteItem"
            class="btn bg-red-600 hover:bg-red-700 text-white"
          >
            删除
          </button>
        </div>
      </div>

      <!-- 基本信息卡片 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- 左侧：基础信息 -->
        <div class="lg:col-span-2">
          <!-- 图片展示 -->
          <div class="card mb-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">图片</h2>
            <div v-if="item.images && item.images.length > 0" class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div v-for="(img, index) in item.images" :key="img.id" class="relative">
                <img
                  :src="`https://picsum.photos/200/200?random=${index}`"
                  :alt="`货品图片 ${index + 1}`"
                  class="w-full h-40 object-cover rounded-lg"
                />
              </div>
            </div>
            <div v-else class="text-center py-8">
              <div class="inline-block p-4 bg-gray-100 rounded-full mb-4">
                <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
              </div>
              <p class="text-gray-500">暂无图片</p>
            </div>
          </div>

          <div class="card">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">基本信息</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="form-label">SKU编号</label>
                <p class="font-mono text-gray-900">{{ item.sku_code }}</p>
              </div>
              <div v-if="item.batch_code">
                <label class="form-label">款号</label>
                <p class="text-gray-900">{{ item.batch_code }}</p>
              </div>
              <div>
                <label class="form-label">材质</label>
                <p class="text-gray-900">{{ item.material_name }}</p>
              </div>
              <div v-if="item.type_name">
                <label class="form-label">器型</label>
                <p class="text-gray-900">{{ item.type_name }}</p>
              </div>
              <div v-if="item.origin">
                <label class="form-label">产地</label>
                <p class="text-gray-900">{{ item.origin }}</p>
              </div>
              <div v-if="item.counter">
                <label class="form-label">柜台</label>
                <p class="text-gray-900">{{ item.counter }}</p>
              </div>
              <div>
                <label class="form-label">在库天数</label>
                <p class="text-gray-900">{{ item.age_days !== null ? `${item.age_days}天` : '-' }}</p>
              </div>
              <div v-if="item.purchase_date">
                <label class="form-label">进货日期</label>
                <p class="text-gray-900">{{ item.purchase_date }}</p>
              </div>
            </div>
          </div>

          <!-- 价格信息卡片 -->
          <div class="card mt-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">价格信息</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="text-center p-4 bg-gray-50 rounded-lg">
                <div class="text-sm text-gray-500">{{ displayCostLabel }}</div>
                <div class="text-2xl font-bold text-gray-900 mt-1">¥{{ displayCost.toFixed(2) }}</div>
              </div>
              <div class="text-center p-4 bg-gray-50 rounded-lg" v-if="item.floor_price">
                <div class="text-sm text-gray-500">底价</div>
                <div class="text-2xl font-bold text-yellow-600 mt-1">¥{{ item.floor_price.toFixed(2) }}</div>
              </div>
              <div class="text-center p-4 bg-gray-50 rounded-lg">
                <div class="text-sm text-gray-500">零售价</div>
                <div class="text-2xl font-bold text-jade-600 mt-1">¥{{ item.selling_price.toFixed(2) }}</div>
              </div>
            </div>
            <div class="mt-4 pt-4 border-t border-gray-200">
              <div class="text-sm text-gray-500">利润空间</div>
              <div class="mt-1 flex items-center">
                <div class="flex-1">
                  <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-jade-500"
                      :style="{ width: `${profitMargin}%` }"
                    ></div>
                  </div>
                </div>
                <div class="ml-4 text-lg font-bold text-jade-600">
                  ¥{{ profit.toFixed(2) }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：其他信息 -->
        <div>
          <!-- 批次信息 -->
          <div v-if="batchInfo" class="card mb-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">批次信息</h2>
            <div class="space-y-3">
              <div>
                <label class="form-label">批次编号</label>
                <p class="text-gray-900">{{ batchInfo.batch_code }}</p>
              </div>
              <div>
                <label class="form-label">回本进度</label>
                <div class="flex items-center">
                  <div class="flex-1">
                    <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        class="h-full bg-green-500"
                        :style="{ width: `${Math.min(batchInfo.payback_rate * 100, 100)}%` }"
                      ></div>
                    </div>
                  </div>
                  <div class="ml-3 text-sm font-medium text-gray-700">
                    {{ (batchInfo.payback_rate * 100).toFixed(1) }}%
                  </div>
                </div>
                <p class="mt-1 text-xs text-gray-500">
                  已回款 ¥{{ batchInfo.revenue.toFixed(2) }} / 总成本 ¥{{ batchInfo.total_cost.toFixed(2) }}
                </p>
              </div>
            </div>
          </div>
          <div class="card">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">规格信息</h2>
            <div class="space-y-4">
              <!-- 动态规格字段 -->
              <div v-for="field in specFields" :key="field.label">
                <label class="form-label">{{ field.label }}</label>
                <p class="text-gray-900">{{ field.value }}</p>
              </div>
              <!-- 证书编号 -->
              <div v-if="item.cert_no">
                <label class="form-label">证书编号</label>
                <p class="text-gray-900 font-mono">{{ item.cert_no }}</p>
              </div>
              <!-- 供货商 -->
              <div v-if="item.supplier_name">
                <label class="form-label">供货商</label>
                <p class="text-gray-900">{{ item.supplier_name }}</p>
              </div>
            </div>
          </div>

          <!-- 标签卡片 -->
          <div class="card mt-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">标签</h2>
            <div v-if="item.tags && item.tags.length > 0" class="flex flex-wrap gap-2">
              <span
                v-for="tag in item.tags"
                :key="tag.id"
                class="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm"
              >
                {{ tag.name }}
              </span>
            </div>
            <p v-else class="text-gray-500 text-sm">暂无标签</p>
          </div>

          <!-- 时间信息 -->
          <div class="card mt-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">时间信息</h2>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">创建时间</span>
                <span class="text-gray-900">{{ new Date(item.created_at).toLocaleString() }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">更新时间</span>
                <span class="text-gray-900">{{ new Date(item.updated_at).toLocaleString() }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 备注信息 -->
      <div v-if="item.notes" class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">备注</h2>
        <p class="text-gray-700 whitespace-pre-line">{{ item.notes }}</p>
      </div>
    </div>

    <!-- 出库弹窗组件 -->
    <SaleDialog
      :item="item"
      :visible="showSaleDialog"
      @close="showSaleDialog = false"
      @success="handleSaleSuccess"
    />
  </div>
</template>