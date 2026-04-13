<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api, { IMAGE_BASE_URL } from '../api'
import toast from '../composables/useToast'

const router = useRouter()

// 扫码状态
const scanning = ref(false)
const scanningResult = ref('')
const cameraError = ref('')
const manualInput = ref('')
const showManual = ref(false)

// 货品信息
const itemData = ref(null)
const itemLoading = ref(false)

// 销售表单
const saleForm = reactive({
  actual_price: '',
  channel: 'store',
  sale_date: new Date().toISOString().slice(0, 10),
  customer_id: null,
  note: ''
})
const saleLoading = ref(false)
const customers = ref([])

// video/canvas 元素引用
const videoRef = ref(null)
const canvasRef = ref(null)
let stream = null
let animationId = null

// 计算属性
const itemCost = computed(() => {
  if (!itemData.value) return 0
  return itemData.value.cost || 0
})

const profitPreview = computed(() => {
  if (!saleForm.actual_price || !itemCost.value) return null
  const price = parseFloat(saleForm.actual_price)
  const profit = price - itemCost.value
  const margin = itemCost.value > 0 ? (profit / itemCost.value * 100) : 0
  return { profit: profit.toFixed(2), margin: margin.toFixed(1) }
})

// 开始扫描
async function startScan() {
  scanningResult.value = ''
  cameraError.value = ''
  itemData.value = null
  scanning.value = true

  try {
    // 请求摄像头权限
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'environment', // 优先使用后置摄像头
        width: { ideal: 1280 },
        height: { ideal: 720 }
      }
    })

    await nextTick()
    if (videoRef.value) {
      videoRef.value.srcObject = stream
      videoRef.value.play()
      // 开始扫描检测
      requestAnimationFrame(scanFrame)
    }
  } catch (err) {
    cameraError.value = '无法访问摄像头。请检查浏览器权限设置，或使用手动输入。'
    scanning.value = false
    showManual.value = true
  }
}

// 扫描帧处理
async function scanFrame() {
  if (!scanning.value || !videoRef.value || !canvasRef.value) return

  const video = videoRef.value
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')

  if (video.readyState === video.HAVE_ENOUGH_DATA) {
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    ctx.drawImage(video, 0, 0)

    // 使用 BarcodeDetector API（现代浏览器支持）
    if ('BarcodeDetector' in window) {
      try {
        const detector = new BarcodeDetector({
          formats: ['code_128', 'code_39', 'ean_13', 'ean_8', 'upc_a', 'upc_e']
        })
        const barcodes = await detector.detect(canvas)
        if (barcodes.length > 0) {
          const code = barcodes[0].rawValue
          handleScanResult(code)
          return
        }
      } catch (e) {
        // BarcodeDetector 不可用，静默处理
      }
    }
  }

  animationId = requestAnimationFrame(scanFrame)
}

// 处理扫描结果
async function handleScanResult(code) {
  stopScan()
  scanningResult.value = code
  itemLoading.value = true

  try {
    const data = await api.labels.lookupBySku(code)
    itemData.value = data

    // 预填销售价格
    saleForm.actual_price = data.selling_price?.toString() || ''

    // 加载客户列表
    loadCustomers()
  } catch (err) {
    toast.error('未找到该编号的货品')
    itemData.value = null
  } finally {
    itemLoading.value = false
  }
}

// 手动查询
async function manualLookup() {
  const sku = manualInput.value.trim()
  if (!sku) {
    toast.warning('请输入SKU编号')
    return
  }
  handleScanResult(sku)
}

// 停止扫描
function stopScan() {
  scanning.value = false
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
}

// 加载客户列表
async function loadCustomers() {
  try {
    const data = await api.customers.getCustomers({ size: 100 })
    if (Array.isArray(data)) {
      customers.value = data
    } else if (data && data.items) {
      customers.value = data.items
    }
  } catch (err) {
    customers.value = []
  }
}

// 提交销售
async function submitSale() {
  if (!saleForm.actual_price || parseFloat(saleForm.actual_price) <= 0) {
    toast.warning('请填写有效的成交价')
    return
  }

  saleLoading.value = true
  try {
    await api.sales.createSale({
      item_id: itemData.value.id,
      actual_price: parseFloat(saleForm.actual_price),
      channel: saleForm.channel,
      sale_date: saleForm.sale_date,
      customer_id: saleForm.customer_id || undefined,
      note: '扫码销售'
    })

    toast.success(`销售成功！${itemData.value.sku_code}`)
    itemData.value = null
    saleForm.actual_price = ''
    scanningResult.value = ''

    // 自动开始下一次扫描
    startScan()
  } catch (err) {
    toast.error(err.message || '销售失败')
  } finally {
    saleLoading.value = false
  }
}

// 返回
function goBack() {
  stopScan()
  router.push('/sales')
}

// 组件卸载时停止摄像头
onUnmounted(() => {
  stopScan()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 页面头部 -->
    <div class="bg-emerald-600 text-white px-4 py-3 flex items-center gap-3">
      <button @click="goBack" class="p-1 hover:bg-emerald-700 rounded">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div>
        <h1 class="text-lg font-bold">扫码销售</h1>
        <p class="text-xs text-emerald-100">扫描条码快速记录销售</p>
      </div>
    </div>

    <!-- 扫码区域 -->
    <div v-if="scanning" class="relative bg-black mx-4 mt-4 rounded-xl overflow-hidden" style="aspect-ratio: 4/3;">
      <video ref="videoRef" class="w-full h-full object-cover" playsinline muted></video>
      <canvas ref="canvasRef" class="hidden"></canvas>

      <!-- 扫描框 -->
      <div class="absolute inset-0 flex items-center justify-center">
        <div class="w-64 h-32 border-2 border-white rounded-lg relative">
          <div class="absolute left-0 top-0 w-6 h-6 border-l-3 border-t-3 border-emerald-400 rounded-tl-md"></div>
          <div class="absolute right-0 top-0 w-6 h-6 border-r-3 border-t-3 border-emerald-400 rounded-tr-md"></div>
          <div class="absolute left-0 bottom-0 w-6 h-6 border-l-3 border-b-3 border-emerald-400 rounded-bl-md"></div>
          <div class="absolute right-0 bottom-0 w-6 h-6 border-r-3 border-b-3 border-emerald-400 rounded-br-md"></div>
          <!-- 扫描线 -->
          <div class="absolute top-0 left-2 right-2 h-0.5 bg-emerald-400 animate-scan-line"></div>
        </div>
      </div>

      <!-- 提示文字 -->
      <div class="absolute bottom-4 left-0 right-0 text-center">
        <span class="bg-black bg-opacity-60 text-white text-sm px-4 py-2 rounded-full">
          将条码对准框内
        </span>
      </div>
    </div>

    <!-- 摄像头错误 -->
    <div v-if="cameraError" class="mx-4 mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <p class="text-sm text-yellow-700">{{ cameraError }}</p>
    </div>

    <!-- 手动输入 -->
    <div class="mx-4 mt-4">
      <div class="flex gap-2">
        <input
          v-model="manualInput"
          @keyup.enter="manualLookup"
          type="text"
          class="form-input flex-1"
          placeholder="手动输入SKU编号..."
        />
        <button
          @click="manualLookup"
          class="btn btn-primary whitespace-nowrap"
          :disabled="itemLoading"
        >
          {{ itemLoading ? '查询中...' : '查询' }}
        </button>
      </div>
    </div>

    <!-- 扫描结果 -->
    <div v-if="itemLoading" class="mx-4 mt-6 text-center">
      <span class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></span>
      <p class="mt-2 text-gray-500 text-sm">查询货品信息...</p>
    </div>

    <!-- 货品信息 + 销售表单 -->
    <div v-if="itemData && !itemLoading" class="mx-4 mt-4 space-y-4">
      <!-- 货品卡片 -->
      <div class="bg-white rounded-xl shadow p-4">
        <div class="flex items-start gap-3">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <span class="text-xs font-mono bg-emerald-50 text-emerald-700 px-2 py-1 rounded">
                {{ itemData.sku_code }}
              </span>
              <span
                :class="[
                  'text-xs px-2 py-0.5 rounded-full',
                  itemData.status === 'in_stock' ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'
                ]"
              >
                {{ itemData.status === 'in_stock' ? '在库' : '已售' }}
              </span>
            </div>
            <h2 class="mt-2 text-lg font-bold text-gray-900">
              {{ itemData.material_name }}
              <span v-if="itemData.type_name"> · {{ itemData.type_name }}</span>
            </h2>
            <p v-if="itemData.name" class="text-sm text-gray-500">{{ itemData.name }}</p>
          </div>
        </div>

        <!-- 价格信息 -->
        <div class="mt-3 grid grid-cols-3 gap-2">
          <div class="bg-gray-50 rounded-lg p-2 text-center">
            <p class="text-xs text-gray-500">成本</p>
            <p class="text-sm font-bold text-gray-700">¥{{ itemCost.toFixed(0) }}</p>
          </div>
          <div class="bg-gray-50 rounded-lg p-2 text-center">
            <p class="text-xs text-gray-500">标价</p>
            <p class="text-sm font-bold text-gray-700">¥{{ itemData.selling_price?.toFixed(0) }}</p>
          </div>
          <div class="bg-gray-50 rounded-lg p-2 text-center">
            <p class="text-xs text-gray-500">底价</p>
            <p class="text-sm font-bold text-orange-600">¥{{ itemData.floor_price?.toFixed(0) || '---' }}</p>
          </div>
        </div>
      </div>

      <!-- 已售出提示 -->
      <div v-if="itemData.status !== 'in_stock'" class="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
        <svg class="mx-auto h-8 w-8 text-red-400" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        <p class="mt-2 text-sm text-red-700 font-medium">该货品已售出</p>
        <button @click="startScan" class="mt-3 btn btn-primary text-sm">继续扫码</button>
      </div>

      <!-- 销售表单 -->
      <div v-if="itemData.status === 'in_stock'" class="bg-white rounded-xl shadow p-4">
        <h3 class="text-lg font-bold text-gray-900 mb-4">记录销售</h3>

        <div class="space-y-4">
          <!-- 成交价 -->
          <div>
            <label class="form-label">成交价 <span class="text-red-500">*</span></label>
            <input
              v-model="saleForm.actual_price"
              type="number"
              step="0.01"
              min="0.01"
              class="form-input text-lg font-bold"
              placeholder="0.00"
            />
            <!-- 毛利预览 -->
            <div v-if="profitPreview" class="mt-2 flex items-center gap-2 text-sm">
              <span :class="parseFloat(profitPreview.profit) >= 0 ? 'text-green-600' : 'text-red-600'">
                {{ parseFloat(profitPreview.profit) >= 0 ? '+' : '' }}¥{{ profitPreview.profit }}
              </span>
              <span class="text-gray-400">|</span>
              <span :class="parseFloat(profitPreview.margin) >= 0 ? 'text-green-600' : 'text-red-600'">
                毛利率 {{ profitPreview.margin }}%
              </span>
            </div>
          </div>

          <!-- 销售渠道 -->
          <div>
            <label class="form-label">渠道</label>
            <div class="flex gap-3">
              <button
                @click="saleForm.channel = 'store'"
                :class="[
                  'flex-1 py-2 rounded-lg text-sm font-medium transition-colors',
                  saleForm.channel === 'store'
                    ? 'bg-emerald-100 text-emerald-700 border-2 border-emerald-300'
                    : 'bg-gray-50 text-gray-600 border-2 border-transparent'
                ]"
              >
                门店
              </button>
              <button
                @click="saleForm.channel = 'wechat'"
                :class="[
                  'flex-1 py-2 rounded-lg text-sm font-medium transition-colors',
                  saleForm.channel === 'wechat'
                    ? 'bg-emerald-100 text-emerald-700 border-2 border-emerald-300'
                    : 'bg-gray-50 text-gray-600 border-2 border-transparent'
                ]"
              >
                微信
              </button>
            </div>
          </div>

          <!-- 日期 -->
          <div>
            <label class="form-label">日期</label>
            <input v-model="saleForm.sale_date" type="date" class="form-input" />
          </div>

          <!-- 客户（可选） -->
          <div>
            <label class="form-label">客户（可选）</label>
            <select v-model="saleForm.customer_id" class="form-input">
              <option :value="null">不选择客户</option>
              <option v-for="c in customers" :key="c.id" :value="c.id">
                {{ c.name }} <span v-if="c.phone">({{ c.phone }})</span>
              </option>
            </select>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="mt-6 space-y-3">
          <button
            @click="submitSale"
            :disabled="saleLoading"
            class="w-full btn btn-success py-3 text-base font-bold"
          >
            <span v-if="saleLoading" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
            {{ saleLoading ? '处理中...' : '确认销售' }}
          </button>
          <button
            @click="startScan"
            class="w-full btn btn-secondary"
          >
            继续扫码
          </button>
        </div>
      </div>
    </div>

    <!-- 初始状态（未扫描） -->
    <div v-if="!scanning && !itemData && !itemLoading && !cameraError" class="mx-4 mt-8 text-center">
      <svg class="mx-auto h-20 w-20 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
      </svg>
      <p class="mt-4 text-gray-500">点击下方按钮开始扫描条码</p>
      <button @click="startScan" class="mt-4 btn btn-primary text-lg px-8 py-3">
        开始扫码
      </button>
      <p class="mt-3 text-xs text-gray-400">或手动输入SKU编号查询</p>
    </div>
  </div>
</template>

<style scoped>
@keyframes scan-line {
  0%, 100% { top: 0; }
  50% { top: calc(100% - 2px); }
}

.animate-scan-line {
  animation: scan-line 2s ease-in-out infinite;
}
</style>
