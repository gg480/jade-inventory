<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { IMAGE_BASE_URL } from '../api'
import toast from '../composables/useToast'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(false)
const labels = ref([])
const selectedIds = ref([])
const selectMode = ref(false)
const printReady = ref(false)

// 从 URL 参数获取预选的货品ID
onMounted(async () => {
  const ids = route.query.ids
  if (ids) {
    selectedIds.value = ids.split(',').map(Number).filter(Boolean)
    if (selectedIds.value.length > 0) {
      await loadLabels()
    }
  }
})

// 加载标签数据
async function loadLabels() {
  if (selectedIds.value.length === 0) {
    toast.warning('请先选择要打印标签的货品')
    return
  }

  loading.value = true
  try {
    const data = await api.labels.getBatchLabels(selectedIds.value)
    labels.value = data
    printReady.value = true
  } catch (err) {
    toast.error('加载标签数据失败')
  } finally {
    loading.value = false
  }
}

// 手动输入SKU加载
async function addBySku() {
  const sku = manualSku.value.trim()
  if (!sku) return
  try {
    const data = await api.labels.lookupBySku(sku)
    // 检查是否已存在
    if (!labels.value.find(l => l.sku_code === sku)) {
      labels.value.push(data)
      printReady.value = true
      toast.success(`已添加 ${data.sku_code}`)
    } else {
      toast.warning('该货品标签已在列表中')
    }
    manualSku.value = ''
  } catch (err) {
    toast.error('未找到该编号的货品')
  }
}

const manualSku = ref('')

// 删除标签
function removeLabel(index) {
  labels.value.splice(index, 1)
  if (labels.value.length === 0) printReady.value = false
}

// 清空所有
function clearAll() {
  labels.value = []
  selectedIds.value = []
  printReady.value = false
}

// 打印
function printLabels() {
  window.print()
}

// 手动添加模式
const showManualAdd = ref(false)
</script>

<template>
  <div class="space-y-4">
    <!-- 操作栏 -->
    <div class="flex items-center justify-between flex-wrap gap-3 print-hide">
      <div>
        <h1 class="text-xl md:text-2xl font-bold text-gray-900">标签打印</h1>
        <p class="text-sm text-gray-500 mt-1">
          入库后打印条码标签，贴在货品上，方便后续扫码销售
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="showManualAdd = !showManualAdd"
          class="btn btn-secondary text-sm"
        >
          {{ showManualAdd ? '收起' : '手动添加' }}
        </button>
        <button
          v-if="labels.length > 0"
          @click="clearAll"
          class="btn btn-secondary text-sm"
        >
          清空
        </button>
        <button
          v-if="labels.length > 0"
          @click="printLabels"
          class="btn btn-primary text-sm"
        >
          打印标签 ({{ labels.length }} 件)
        </button>
      </div>
    </div>

    <!-- 使用说明（无数据时显示） -->
    <div v-if="labels.length === 0 && !loading" class="bg-white rounded-lg shadow p-8 text-center print-hide">
      <svg class="mx-auto h-16 w-16 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
      </svg>
      <h3 class="mt-4 text-lg font-medium text-gray-700">标签打印</h3>
      <p class="mt-2 text-sm text-gray-500 max-w-md mx-auto">
        请从库存列表选择货品后打印，或点击「手动添加」输入SKU编号。
        打印的标签包含条码和基本信息，扫码即可快速销售。
      </p>

      <!-- 手动添加表单 -->
      <div v-if="showManualAdd" class="mt-6 max-w-sm mx-auto">
        <div class="flex gap-2">
          <input
            v-model="manualSku"
            @keyup.enter="addBySku"
            type="text"
            class="form-input flex-1"
            placeholder="输入SKU编号，如 FE-20260412-001"
          />
          <button @click="addBySku" class="btn btn-primary whitespace-nowrap">添加</button>
        </div>
      </div>

      <div class="mt-6">
        <button @click="$router.push('/inventory')" class="btn btn-secondary">
          前往库存列表
        </button>
      </div>
    </div>

    <!-- 手动添加（有数据时） -->
    <div v-if="showManualAdd && labels.length > 0" class="bg-white rounded-lg shadow p-4 print-hide">
      <div class="flex gap-2">
        <input
          v-model="manualSku"
          @keyup.enter="addBySku"
          type="text"
          class="form-input flex-1"
          placeholder="输入SKU编号添加标签"
        />
        <button @click="addBySku" class="btn btn-primary whitespace-nowrap">添加</button>
      </div>
    </div>

    <!-- 标签列表预览 -->
    <div v-if="loading" class="text-center py-8 print-hide">
      <span class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></span>
      <p class="mt-2 text-gray-500">加载标签数据中...</p>
    </div>

    <!-- 标签网格（屏幕预览） -->
    <div v-if="labels.length > 0 && !loading" class="print-hide">
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <div
          v-for="(label, index) in labels"
          :key="label.id"
          class="bg-white rounded-lg shadow border border-gray-200 overflow-hidden relative group"
        >
          <!-- 删除按钮 -->
          <button
            @click="removeLabel(index)"
            class="absolute top-2 right-2 z-10 w-6 h-6 bg-red-100 text-red-500 rounded-full hover:bg-red-200 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity print-hide"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <!-- 标签内容 -->
          <div class="p-3">
            <!-- 条码 -->
            <div class="bg-white flex justify-center mb-2">
              <img :src="label.barcode" :alt="label.sku_code" class="h-12 w-auto" />
            </div>
            <!-- 信息 -->
            <p class="text-xs font-mono text-gray-800 font-medium text-center">{{ label.sku_code }}</p>
            <p class="text-xs text-gray-600 text-center truncate">{{ label.material_name }} <span v-if="label.type_name">· {{ label.type_name }}</span></p>
            <p class="text-sm font-bold text-emerald-700 text-center mt-1">¥{{ label.selling_price?.toFixed(0) }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 打印区域（仅打印时显示） -->
    <div v-if="labels.length > 0" class="print-only">
      <div class="label-grid">
        <div
          v-for="label in labels"
          :key="'print-' + label.id"
          class="label-card"
        >
          <!-- 店名 -->
          <div class="label-header">
            <span class="label-shop-name">珠宝玉器</span>
          </div>

          <!-- 条码 -->
          <div class="label-barcode">
            <img :src="label.barcode" :alt="label.sku_code" />
          </div>

          <!-- SKU编号 -->
          <div class="label-sku">{{ label.sku_code }}</div>

          <!-- 信息行 -->
          <div class="label-info">
            <span>{{ label.material_name }}</span>
            <span v-if="label.type_name">· {{ label.type_name }}</span>
          </div>

          <!-- 价格 -->
          <div class="label-price">
            ¥{{ label.selling_price?.toFixed(0) || '---' }}
          </div>

          <!-- 底部信息 -->
          <div class="label-footer">
            <span v-if="label.origin">{{ label.origin }}</span>
            <span v-if="label.cert_no">证书:{{ label.cert_no }}</span>
            <span v-if="label.counter">柜{{ label.counter }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 非打印区域 */
.print-hide {
  display: block;
}

.print-only {
  display: none;
}

/* 打印样式 */
@media print {
  body {
    margin: 0;
    padding: 0;
    background: white;
  }

  .print-hide {
    display: none !important;
  }

  .print-only {
    display: block !important;
  }

  /* 标签网格：每行2个标签 */
  .label-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 2mm;
    padding: 5mm;
  }

  /* 每个标签卡片 */
  .label-card {
    border: 0.5mm solid #333;
    border-radius: 2mm;
    padding: 3mm 4mm;
    text-align: center;
    page-break-inside: avoid;
    font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
    background: white;
    height: 38mm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;
  }

  .label-header {
    text-align: left;
  }

  .label-shop-name {
    font-size: 8pt;
    font-weight: bold;
    color: #333;
    letter-spacing: 2px;
  }

  .label-barcode {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1mm 0;
  }

  .label-barcode img {
    max-height: 18mm;
    width: auto;
    max-width: 100%;
  }

  .label-sku {
    font-size: 7pt;
    font-family: 'Courier New', monospace;
    color: #333;
    letter-spacing: 0.5px;
  }

  .label-info {
    font-size: 6.5pt;
    color: #666;
    margin-top: 0.5mm;
  }

  .label-price {
    font-size: 14pt;
    font-weight: bold;
    color: #d97706;
    margin: 1mm 0;
  }

  .label-footer {
    font-size: 5.5pt;
    color: #999;
    display: flex;
    justify-content: center;
    gap: 3mm;
  }
}

/* 小标签打印模式（可选） */
@media print and (max-width: 210mm) {
  .label-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .label-card {
    height: 35mm;
  }
}
</style>
