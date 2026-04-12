<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import api from '../api'
import toast from '../composables/useToast'

// 材质列表
const materials = ref([])
const types = ref([])

// 表单
const form = reactive({
  cost: '',
  material_id: null,
  weight: '',
})

// 定价结果
const recommendation = ref(null)
const materialStats = ref(null)
const typeStats = ref([])
const allMaterialStats = ref([])
const pricingConfig = ref(null)
const loading = ref(false)

// 预设成本档位
const costPresets = [
  { label: '50', value: 50 },
  { label: '100', value: 100 },
  { label: '200', value: 200 },
  { label: '500', value: 500 },
  { label: '1000', value: 1000 },
  { label: '2000', value: 2000 },
  { label: '5000', value: 5000 },
]

// 风险等级样式
function riskClass(level) {
  return {
    low: 'bg-green-50 text-green-700 border-green-200',
    medium: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    high: 'bg-red-50 text-red-700 border-red-200',
  }[level] || 'bg-gray-50 text-gray-700'
}

function riskLabel(level) {
  return { low: '低风险', medium: '中等风险', high: '高风险' }[level] || level
}

function riskIcon(level) {
  if (level === 'low') return '✓'
  if (level === 'medium') return '!'
  return '!!'
}

// 加载材质列表
async function loadMaterials() {
  try {
    const data = await api.dicts.getMaterials(true)
    materials.value = Array.isArray(data) ? data : []
  } catch (err) {
    materials.value = []
  }
}

// 加载全部材质统计
async function loadAllMaterialStats() {
  try {
    const data = await api.pricing.getMaterialStats()
    allMaterialStats.value = Array.isArray(data) ? data : []
  } catch (err) {
    allMaterialStats.value = []
  }
}

// 加载定价配置
async function loadPricingConfig() {
  try {
    const data = await api.pricing.getConfig()
    pricingConfig.value = data
  } catch (err) {
    pricingConfig.value = null
  }
}

// 监听材质变化，加载器型统计
watch(() => form.material_id, async (newVal) => {
  if (newVal) {
    try {
      const data = await api.pricing.getTypeStats(newVal)
      typeStats.value = Array.isArray(data) ? data : []
    } catch (err) {
      typeStats.value = []
    }
  } else {
    typeStats.value = []
  }
})

// 计算定价推荐
async function calculate() {
  if (!form.cost || parseFloat(form.cost) <= 0) {
    toast.warning('请输入有效的成本金额')
    return
  }
  if (!form.material_id) {
    toast.warning('请选择材质')
    return
  }

  loading.value = true
  try {
    const data = await api.pricing.getRecommendation({
      cost: parseFloat(form.cost),
      material_id: form.material_id,
      weight: form.weight ? parseFloat(form.weight) : undefined,
    })
    recommendation.value = data

    // 同时加载该材质的详细统计
    const stats = await api.pricing.getMaterialStats(data.material_id || form.material_id)
    materialStats.value = stats
  } catch (err) {
    toast.error('获取定价推荐失败')
  } finally {
    loading.value = false
  }
}

// 重置
function reset() {
  form.cost = ''
  form.material_id = null
  form.weight = ''
  recommendation.value = null
  materialStats.value = null
  typeStats.value = []
}

// 初始化
onMounted(() => {
  loadMaterials()
  loadAllMaterialStats()
  loadPricingConfig()
})
</script>

<template>
  <div class="space-y-4 md:space-y-6">
    <!-- 页面标题 -->
    <div>
      <h1 class="text-xl md:text-2xl font-bold text-gray-900">利润测算定价生成器</h1>
      <p class="text-sm text-gray-500 mt-1">
        结合历史销售数据和珠宝零售逻辑，为新货品提供科学定价参考
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
      <!-- 左侧：输入表单 -->
      <div class="lg:col-span-1 space-y-4">
        <div class="bg-white rounded-lg shadow p-4 md:p-6 space-y-5">
          <h2 class="text-lg font-bold text-gray-900">输入货品信息</h2>

          <!-- 成本 -->
          <div>
            <label class="form-label">进货成本（元） <span class="text-red-500">*</span></label>
            <input
              v-model="form.cost"
              type="number"
              step="0.01"
              min="0.01"
              class="form-input text-lg"
              placeholder="输入成本价"
            />
            <!-- 快捷金额 -->
            <div class="flex flex-wrap gap-2 mt-2">
              <button
                v-for="preset in costPresets"
                :key="preset.value"
                @click="form.cost = preset.value"
                class="px-3 py-1 text-xs rounded-full border transition-colors"
                :class="form.cost == preset.value
                  ? 'bg-emerald-100 border-emerald-300 text-emerald-700'
                  : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'"
              >
                {{ preset.label }}
              </button>
            </div>
          </div>

          <!-- 材质 -->
          <div>
            <label class="form-label">材质分类 <span class="text-red-500">*</span></label>
            <select v-model="form.material_id" class="form-input">
              <option :value="null">请选择材质...</option>
              <option v-for="m in materials" :key="m.id" :value="m.id">
                {{ m.name }}
                <span v-if="m.sub_type">({{ m.sub_type }})</span>
              </option>
            </select>
          </div>

          <!-- 克重（可选） -->
          <div>
            <label class="form-label">克重（克，贵金属用）</label>
            <input
              v-model="form.weight"
              type="number"
              step="0.01"
              min="0"
              class="form-input"
              placeholder="选填，贵金属定价参考"
            />
          </div>

          <!-- 当前配置显示 -->
          <div v-if="pricingConfig" class="bg-gray-50 rounded-lg p-3">
            <p class="text-xs text-gray-500 mb-2">当前系统定价参数</p>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span class="text-gray-500">经营成本率：</span>
                <span class="font-medium">{{ (pricingConfig.operating_cost_rate * 100).toFixed(0) }}%</span>
              </div>
              <div>
                <span class="text-gray-500">上浮比例：</span>
                <span class="font-medium">{{ (pricingConfig.markup_rate * 100).toFixed(0) }}%</span>
              </div>
              <div>
                <span class="text-gray-500">压货天数：</span>
                <span class="font-medium">{{ pricingConfig.aging_threshold_days }}天</span>
              </div>
            </div>
            <p class="text-xs text-gray-400 mt-2">
              可在 字典管理 → 系统配置 中调整
            </p>
          </div>

          <!-- 操作按钮 -->
          <div class="space-y-2">
            <button
              @click="calculate"
              :disabled="loading"
              class="w-full btn btn-primary py-3 font-bold"
            >
              <span v-if="loading" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
              {{ loading ? '计算中...' : '生成定价建议' }}
            </button>
            <button @click="reset" class="w-full btn btn-secondary">重置</button>
          </div>
        </div>
      </div>

      <!-- 中间 + 右侧：结果 -->
      <div class="lg:col-span-2 space-y-4 md:space-y-6">
        <!-- 定价推荐结果 -->
        <div v-if="recommendation" class="space-y-4">
          <!-- 风险评估 -->
          <div
            :class="['rounded-lg border p-4 flex items-center gap-3', riskClass(recommendation.risk_level)]"
          >
            <span class="text-2xl font-bold">{{ riskIcon(recommendation.risk_level) }}</span>
            <div>
              <h3 class="font-bold">{{ riskLabel(recommendation.risk_level) }}</h3>
              <p v-for="factor in recommendation.risk_factors" :key="factor" class="text-sm mt-0.5">
                {{ factor }}
              </p>
              <p v-if="recommendation.risk_factors.length === 0" class="text-sm">
                该品类销售状况良好，定价空间较大
              </p>
            </div>
          </div>

          <!-- 价格区间 -->
          <div class="bg-white rounded-lg shadow p-4 md:p-6">
            <h2 class="text-lg font-bold text-gray-900 mb-4">推荐价格区间</h2>

            <!-- 价格条 -->
            <div class="relative mb-6">
              <!-- 刻度条 -->
              <div class="h-3 bg-gray-100 rounded-full relative">
                <div
                  class="absolute h-3 rounded-full bg-gradient-to-r from-orange-400 via-emerald-400 to-blue-400"
                  :style="{
                    left: '5%',
                    width: '85%'
                  }"
                ></div>
                <!-- 三个标记点 -->
                <div
                  class="absolute top-5 text-center"
                  :style="{ left: 'calc(5% - 20px)', width: '40px' }"
                >
                  <div class="text-xs text-gray-500">保本价</div>
                  <div class="text-sm font-bold text-orange-600">¥{{ recommendation.floor_price?.toFixed(0) }}</div>
                </div>
                <div
                  class="absolute top-5 text-center"
                  style="left: calc(50% - 30px); width: 60px"
                >
                  <div class="text-xs text-gray-500">建议价</div>
                  <div class="text-lg font-bold text-emerald-600">¥{{ recommendation.standard_price?.toFixed(0) }}</div>
                </div>
                <div
                  class="absolute top-5 text-center"
                  :style="{ left: 'calc(85% - 20px)', width: '40px' }"
                >
                  <div class="text-xs text-gray-500">期望价</div>
                  <div class="text-sm font-bold text-blue-600">¥{{ recommendation.high_price?.toFixed(0) }}</div>
                </div>
              </div>
            </div>

            <!-- 详细数据表 -->
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-gray-200">
                    <th class="text-left py-2 px-3 text-gray-500 font-medium">档位</th>
                    <th class="text-right py-2 px-3 text-gray-500 font-medium">售价</th>
                    <th class="text-right py-2 px-3 text-gray-500 font-medium">毛利</th>
                    <th class="text-right py-2 px-3 text-gray-500 font-medium">毛利率</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-b border-gray-100">
                    <td class="py-3 px-3">
                      <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-50 text-orange-700">
                        保守价
                      </span>
                    </td>
                    <td class="py-3 px-3 text-right font-bold text-orange-600">
                      ¥{{ recommendation.low_price?.toFixed(0) }}
                    </td>
                    <td class="py-3 px-3 text-right text-gray-700">
                      ¥{{ (recommendation.low_price - form.cost).toFixed(0) }}
                    </td>
                    <td class="py-3 px-3 text-right text-gray-700">
                      {{ recommendation.low_margin }}%
                    </td>
                  </tr>
                  <tr class="border-b border-gray-100 bg-emerald-50">
                    <td class="py-3 px-3">
                      <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                        建议价
                      </span>
                    </td>
                    <td class="py-3 px-3 text-right font-bold text-emerald-600">
                      ¥{{ recommendation.standard_price?.toFixed(0) }}
                    </td>
                    <td class="py-3 px-3 text-right text-gray-700">
                      ¥{{ (recommendation.standard_price - form.cost).toFixed(0) }}
                    </td>
                    <td class="py-3 px-3 text-right text-gray-700">
                      {{ recommendation.standard_margin }}%
                    </td>
                  </tr>
                  <tr>
                    <td class="py-3 px-3">
                      <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                        期望价
                      </span>
                    </td>
                    <td class="py-3 px-3 text-right font-bold text-blue-600">
                      ¥{{ recommendation.high_price?.toFixed(0) }}
                    </td>
                    <td class="py-3 px-3 text-right text-gray-700">
                      ¥{{ (recommendation.high_price - form.cost).toFixed(0) }}
                    </td>
                    <td class="py-3 px-3 text-right text-gray-700">
                      {{ recommendation.high_margin }}%
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 定价逻辑说明 -->
            <div class="mt-6 space-y-3">
              <h3 class="font-bold text-gray-900">定价逻辑说明</h3>
              <div
                v-for="(logic, idx) in recommendation.pricing_logic"
                :key="idx"
                class="bg-gray-50 rounded-lg p-3"
              >
                <div class="font-medium text-sm text-gray-800">{{ logic.title }}</div>
                <code class="block mt-1 text-xs text-emerald-700 bg-emerald-50 px-2 py-1 rounded">
                  {{ logic.formula }}
                </code>
                <p class="mt-1 text-xs text-gray-500">{{ logic.detail }}</p>
              </div>
            </div>
          </div>

          <!-- 历史参考 -->
          <div
            v-if="recommendation.historical_reference && recommendation.historical_reference.sold_count > 0"
            class="bg-white rounded-lg shadow p-4 md:p-6"
          >
            <h2 class="text-lg font-bold text-gray-900 mb-4">
              历史参考
              <span class="text-sm font-normal text-gray-500 ml-2">
                基于已售 {{ recommendation.historical_reference.sold_count }} 件同类货品
              </span>
            </h2>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="text-center">
                <p class="text-xs text-gray-500">平均售价</p>
                <p class="text-lg font-bold text-gray-900">
                  ¥{{ recommendation.historical_reference.avg_selling_price?.toFixed(0) }}
                </p>
              </div>
              <div class="text-center">
                <p class="text-xs text-gray-500">中位数售价</p>
                <p class="text-lg font-bold text-gray-700">
                  ¥{{ recommendation.historical_reference.median_selling_price?.toFixed(0) }}
                </p>
              </div>
              <div class="text-center">
                <p class="text-xs text-gray-500">平均毛利率</p>
                <p class="text-lg font-bold"
                   :class="recommendation.historical_reference.avg_profit_margin >= 40 ? 'text-emerald-600' : 'text-orange-600'">
                  {{ recommendation.historical_reference.avg_profit_margin }}%
                </p>
              </div>
              <div class="text-center">
                <p class="text-xs text-gray-500">平均周转</p>
                <p class="text-lg font-bold"
                   :class="(recommendation.historical_reference.avg_turnover_days || 0) <= 60 ? 'text-emerald-600' : 'text-red-600'">
                  {{ recommendation.historical_reference.avg_turnover_days }}天
                </p>
              </div>
            </div>
          </div>

          <!-- 器型对比 -->
          <div v-if="typeStats.length > 0" class="bg-white rounded-lg shadow p-4 md:p-6">
            <h2 class="text-lg font-bold text-gray-900 mb-4">器型对比（同材质各款式表现）</h2>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-gray-200">
                    <th class="text-left py-2 px-3 text-gray-500 font-medium">器型</th>
                    <th class="text-right py-2 px-3 text-gray-500 font-medium">已售</th>
                    <th class="text-right py-2 px-3 text-gray-500 font-medium">均价</th>
                    <th class="text-right py-2 px-3 text-gray-500 font-medium">价格范围</th>
                    <th class="text-right py-2 px-3 text-gray-500 font-medium">毛利率</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="ts in typeStats"
                    :key="ts.type_id"
                    class="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td class="py-2.5 px-3 font-medium">{{ ts.type_name }}</td>
                    <td class="py-2.5 px-3 text-right text-gray-600">{{ ts.sold_count }}件</td>
                    <td class="py-2.5 px-3 text-right font-medium">¥{{ ts.avg_price?.toFixed(0) }}</td>
                    <td class="py-2.5 px-3 text-right text-gray-500 text-xs">
                      ¥{{ ts.min_price?.toFixed(0) }} ~ ¥{{ ts.max_price?.toFixed(0) }}
                    </td>
                    <td class="py-2.5 px-3 text-right">
                      <span
                        :class="ts.avg_profit_margin >= 40 ? 'text-emerald-600' : ts.avg_profit_margin >= 25 ? 'text-yellow-600' : 'text-red-600'"
                      >
                        {{ ts.avg_profit_margin }}%
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 未计算时的占位 -->
        <div v-if="!recommendation && !loading" class="bg-white rounded-lg shadow p-8 text-center">
          <svg class="mx-auto h-16 w-16 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <h3 class="mt-4 text-lg font-medium text-gray-700">输入成本和材质后生成定价建议</h3>
          <p class="mt-2 text-sm text-gray-500 max-w-md mx-auto">
            系统会结合历史销售数据、周转速度和珠宝零售逻辑，为你提供多档位定价参考和风险评估
          </p>
        </div>

        <!-- 全材质概览 -->
        <div v-if="allMaterialStats.length > 0" class="bg-white rounded-lg shadow p-4 md:p-6">
          <h2 class="text-lg font-bold text-gray-900 mb-4">各材质销售概览</h2>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200">
                  <th class="text-left py-2 px-3 text-gray-500 font-medium">材质</th>
                  <th class="text-right py-2 px-3 text-gray-500 font-medium">已售</th>
                  <th class="text-right py-2 px-3 text-gray-500 font-medium">均价</th>
                  <th class="text-right py-2 px-3 text-gray-500 font-medium">平均周转</th>
                  <th class="text-right py-2 px-3 text-gray-500 font-medium">毛利率</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="ms in allMaterialStats.filter(s => s.sold_count > 0)"
                  :key="ms.material_id"
                  class="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                  @click="form.material_id = ms.material_id"
                >
                  <td class="py-2.5 px-3 font-medium">{{ ms.material_name }}</td>
                  <td class="py-2.5 px-3 text-right text-gray-600">{{ ms.sold_count }}件</td>
                  <td class="py-2.5 px-3 text-right font-medium">¥{{ ms.avg_selling_price?.toFixed(0) }}</td>
                  <td class="py-2.5 px-3 text-right">
                    <span :class="(ms.avg_turnover_days || 0) <= 60 ? 'text-emerald-600' : 'text-red-600'">
                      {{ ms.avg_turnover_days }}天
                    </span>
                  </td>
                  <td class="py-2.5 px-3 text-right">
                    <span :class="ms.avg_profit_margin >= 40 ? 'text-emerald-600' : ms.avg_profit_margin >= 25 ? 'text-yellow-600' : 'text-red-600'">
                      {{ ms.avg_profit_margin }}%
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
            <p class="mt-2 text-xs text-gray-400">点击材质行可快速选中</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
