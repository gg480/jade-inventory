<template>
  <div class="container mx-auto px-4 py-8 max-w-4xl">
    <h1 class="text-2xl font-bold mb-6">通货批次入库</h1>

    <!-- 步骤指示器 -->
    <div class="mb-8">
      <div class="flex items-center">
        <div class="flex items-center">
          <div class="w-8 h-8 rounded-full flex items-center justify-center"
               :class="step === 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'">
            1
          </div>
          <div class="ml-2 font-medium">创建批次</div>
        </div>
        <div class="flex-1 h-1 mx-4 bg-gray-200"></div>
        <div class="flex items-center">
          <div class="w-8 h-8 rounded-full flex items-center justify-center"
               :class="step === 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'">
            2
          </div>
          <div class="ml-2 font-medium">逐件录入</div>
        </div>
      </div>
    </div>

    <!-- 第一步：创建批次 -->
    <div v-if="step === 1">
      <form @submit.prevent="submitBatch" class="bg-white shadow rounded-lg p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- batch_code -->
          <div class="md:col-span-2">
            <label class="block text-sm font-medium mb-1">
              批次编号 <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.batch_code"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="例如：BATCH-2023-001"
            />
          </div>

          <!-- material_id -->
          <div>
            <label class="block text-sm font-medium mb-1">
              材质 <span class="text-red-500">*</span>
            </label>
            <select
              v-model="form.material_id"
              required
              @change="onMaterialChange"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">请选择材质</option>
              <option v-for="material in materials" :key="material.id" :value="material.id">
                {{ material.name }} {{ material.sub_type ? `(${material.sub_type})` : '' }}
              </option>
            </select>
          </div>

          <!-- type_id -->
          <div>
            <label class="block text-sm font-medium mb-1">
              器型（选填）
            </label>
            <select
              v-model="form.type_id"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">请选择器型</option>
              <option v-for="type in types" :key="type.id" :value="type.id">
                {{ type.name }}
              </option>
            </select>
          </div>

          <!-- quantity -->
          <div>
            <label class="block text-sm font-medium mb-1">
              总件数 <span class="text-red-500">*</span>
            </label>
            <input
              v-model.number="form.quantity"
              type="number"
              min="1"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="例如：50"
            />
          </div>

          <!-- total_cost -->
          <div>
            <label class="block text-sm font-medium mb-1">
              批次总价 <span class="text-red-500">*</span>
            </label>
            <input
              v-model.number="form.total_cost"
              type="number"
              step="0.01"
              min="0"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="例如：10000.00"
            />
          </div>

          <!-- cost_alloc_method -->
          <div>
            <label class="block text-sm font-medium mb-1">
              成本分摊方式 <span class="text-red-500">*</span>
            </label>
            <div class="space-y-2">
              <label class="flex items-center">
                <input
                  type="radio"
                  v-model="form.cost_alloc_method"
                  value="equal"
                  class="mr-2"
                  required
                />
                均摊（每件成本相同）
              </label>
              <label class="flex items-center">
                <input
                  type="radio"
                  v-model="form.cost_alloc_method"
                  value="by_weight"
                  class="mr-2"
                />
                按克重分摊
              </label>
              <label class="flex items-center">
                <input
                  type="radio"
                  v-model="form.cost_alloc_method"
                  value="by_price"
                  class="mr-2"
                />
                按售价比例分摊
              </label>
            </div>
          </div>

          <!-- supplier_id -->
          <div>
            <label class="block text-sm font-medium mb-1">
              供应商（选填）
            </label>
            <select
              v-model="form.supplier_id"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">请选择供应商</option>
              <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">
                {{ supplier.name }}
              </option>
            </select>
          </div>

          <!-- purchase_date -->
          <div>
            <label class="block text-sm font-medium mb-1">
              进货日期
            </label>
            <input
              v-model="form.purchase_date"
              type="date"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <!-- notes -->
          <div class="md:col-span-2">
            <label class="block text-sm font-medium mb-1">
              备注
            </label>
            <textarea
              v-model="form.notes"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="批次备注信息"
            ></textarea>
          </div>
        </div>

        <div class="mt-8 flex justify-end">
          <button
            type="submit"
            :disabled="submitting"
            class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ submitting ? '提交中...' : '创建批次并继续' }}
          </button>
        </div>
      </form>
    </div>

    <!-- 第二步：逐件录入 -->
    <div v-if="step === 2">
      <!-- 批次信息栏 -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between">
          <div class="mb-2 md:mb-0">
            <div class="text-lg font-bold text-blue-800">
              批次 <span class="font-bold">{{ form.batch_code }}</span> |
              材质: <span class="font-bold">{{ selectedMaterialName }}</span> |
              已录: <span class="font-bold">{{ itemsAdded }}/{{ form.quantity }}</span> 件
            </div>
            <div class="text-sm text-blue-600 mt-1">
              器型: {{ selectedTypeName || '未指定' }} | 分摊方式: {{ allocMethodLabel }} | 总成本: {{ form.total_cost }} 元
            </div>
          </div>
          <div v-if="itemsAdded >= form.quantity" class="mt-2 md:mt-0">
            <button
              @click="triggerAllocation"
              :disabled="allocating"
              class="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ allocating ? '分摊计算中...' : '触发成本分摊' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 货品录入表单（录够前显示） -->
      <div v-if="itemsAdded < form.quantity && !showAllocationResult">
        <form @submit.prevent="submitItem" class="bg-white shadow rounded-lg p-6 mb-6">
          <h3 class="text-lg font-bold mb-4">录入货品 {{ itemsAdded + 1 }}/{{ form.quantity }}</h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- name -->
            <div>
              <label class="block text-sm font-medium mb-1">
                商品名称（选填）
              </label>
              <input
                v-model="itemForm.name"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="例如：翡翠手镯"
              />
            </div>

            <!-- selling_price -->
            <div>
              <label class="block text-sm font-medium mb-1">
                零售价 <span class="text-red-500">*</span>
              </label>
              <input
                v-model.number="itemForm.selling_price"
                type="number"
                step="0.01"
                min="0"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="例如：1500.00"
              />
            </div>

            <!-- 规格参数动态区域（根据批次器型） -->
            <div v-if="batchSpecFields.length > 0" class="md:col-span-2">
              <h4 class="text-md font-medium mb-3">规格参数</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div v-for="field in batchSpecFields" :key="field.key">
                  <label class="block text-sm font-medium mb-1">
                    {{ field.label }}
                  </label>
                  <input
                    v-model="specForm[field.key]"
                    :type="field.type"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    :placeholder="field.placeholder"
                  />
                </div>
              </div>
            </div>

            <!-- counter -->
            <div>
              <label class="block text-sm font-medium mb-1">
                柜台号（选填）
              </label>
              <input
                v-model.number="itemForm.counter"
                type="number"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="例如：1"
              />
            </div>

            <!-- notes -->
            <div class="md:col-span-2">
              <label class="block text-sm font-medium mb-1">
                备注（选填）
              </label>
              <textarea
                v-model="itemForm.notes"
                rows="2"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="货品备注信息"
              ></textarea>
            </div>
          </div>

          <div class="mt-8 flex justify-end space-x-4">
            <button
              type="button"
              @click="resetItemForm"
              class="px-6 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600 focus:outline-none focus:ring-2 focus:ring-yellow-500"
            >
              重置表单
            </button>
            <button
              type="submit"
              :disabled="submittingItem"
              class="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ submittingItem ? '提交中...' : '添加货品并继续' }}
            </button>
          </div>
        </form>
      </div>

      <!-- 分摊结果展示 -->
      <div v-if="showAllocationResult" class="bg-white shadow rounded-lg p-6 mb-6">
        <h3 class="text-lg font-bold mb-4">成本分摊结果</h3>
        <div v-if="allocationLoading" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p class="mt-2 text-gray-600">正在计算分摊结果...</p>
        </div>
        <div v-else-if="allocationError" class="bg-red-50 border border-red-200 rounded-md p-4">
          <p class="text-red-700">分摊计算失败: {{ allocationError }}</p>
          <button
            @click="loadAllocationResult"
            class="mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            重试
          </button>
        </div>
        <div v-else-if="allocationResult && allocationResult.length > 0">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU编码</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">商品名称</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">售价</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">分摊成本</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">毛利率</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="item in allocationResult" :key="item.id">
                  <td class="px-4 py-3 text-sm">{{ item.sku_code }}</td>
                  <td class="px-4 py-3 text-sm">{{ item.name || '-' }}</td>
                  <td class="px-4 py-3 text-sm">{{ item.selling_price }}</td>
                  <td class="px-4 py-3 text-sm">{{ item.allocated_cost }}</td>
                  <td class="px-4 py-3 text-sm">
                    <span :class="{'text-green-600': item.profit_margin > 0, 'text-red-600': item.profit_margin <= 0}">
                      {{ (item.profit_margin * 100).toFixed(1) }}%
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="mt-6 pt-4 border-t border-gray-200">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span class="text-gray-500">批次总成本:</span>
                <span class="ml-2 font-bold">{{ form.total_cost }} 元</span>
              </div>
              <div>
                <span class="text-gray-500">分摊后总售价:</span>
                <span class="ml-2 font-bold">{{ totalSellingPrice }} 元</span>
              </div>
              <div>
                <span class="text-gray-500">预计总利润:</span>
                <span :class="{'text-green-600': totalProfit > 0, 'text-red-600': totalProfit <= 0}" class="ml-2 font-bold">
                  {{ totalProfit }} 元
                </span>
              </div>
            </div>
          </div>
          <div class="mt-6 flex justify-end">
            <button
              @click="goToBatchesList"
              class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              完成并返回批次列表
            </button>
          </div>
        </div>
        <div v-else class="text-center py-8 text-gray-500">
          暂无分摊结果数据
        </div>
      </div>

      <!-- 录够提示（未触发分摊前） -->
      <div v-if="itemsAdded >= form.quantity && !showAllocationResult" class="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
        <div class="text-green-700 mb-4">
          <svg class="w-12 h-12 mx-auto mb-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 class="text-lg font-bold mb-2">已录入所有 {{ form.quantity }} 件货品</h3>
          <p class="text-sm">请点击上方"触发成本分摊"按钮进行成本分摊计算</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDictStore } from '../store/dict'
import api from '../api'

const router = useRouter()
const dictStore = useDictStore()

// 步骤状态
const step = ref(1)
const batchId = ref(null)
const submitting = ref(false)
const submittingItem = ref(false)

// 已添加货品数量
const itemsAdded = ref(0)

// 分摊相关状态
const showAllocationResult = ref(false)
const allocating = ref(false)
const allocationLoading = ref(false)
const allocationError = ref(null)
const allocationResult = ref([])

// 批次表单数据
const form = reactive({
  batch_code: '',
  material_id: '',
  type_id: '',
  quantity: 1,
  total_cost: 0,
  cost_alloc_method: 'equal',
  supplier_id: '',
  purchase_date: new Date().toISOString().split('T')[0],
  notes: ''
})

// 货品表单数据（简化版）
const itemForm = reactive({
  name: '',
  selling_price: '',
  counter: '',
  notes: ''
})

// 规格参数表单
const specForm = reactive({
  weight: '',
  metal_weight: '',
  size: '',
  bracelet_size: '',
  bead_count: '',
  bead_diameter: '',
  ring_size: ''
})

// 批次器型的规格字段配置
const batchSpecFields = ref([])

// 下拉数据
const materials = ref([])
const types = ref([])
const suppliers = ref([])
const tags = ref([])

// 计算属性
const selectedMaterialName = computed(() => {
  const material = materials.value.find(m => m.id == form.material_id)
  return material ? `${material.name}${material.sub_type ? ` (${material.sub_type})` : ''}` : ''
})

const selectedTypeName = computed(() => {
  const type = types.value.find(t => t.id == form.type_id)
  return type ? type.name : ''
})

const allocMethodLabel = computed(() => {
  const labels = {
    equal: '均摊',
    by_weight: '按克重',
    by_price: '按售价比例'
  }
  return labels[form.cost_alloc_method] || form.cost_alloc_method
})

// 计算属性：总售价
const totalSellingPrice = computed(() => {
  if (!allocationResult.value || allocationResult.value.length === 0) return 0
  return allocationResult.value.reduce((sum, item) => sum + (item.selling_price || 0), 0)
})

// 计算属性：总利润
const totalProfit = computed(() => {
  if (!allocationResult.value || allocationResult.value.length === 0) return 0
  const totalAllocatedCost = allocationResult.value.reduce((sum, item) => sum + (item.allocated_cost || 0), 0)
  return totalSellingPrice.value - totalAllocatedCost
})

// 监听材质变化，清空已选择的器型
watch(() => form.material_id, (newMaterialId, oldMaterialId) => {
  if (newMaterialId !== oldMaterialId) {
    form.type_id = ''
  }
})

// 监听批次器型变化，更新规格字段
watch(() => form.type_id, async (newTypeId, oldTypeId) => {
  if (newTypeId !== oldTypeId) {
    await updateBatchSpecFields(newTypeId)
  }
})

// 加载下拉数据
async function loadSelectData() {
  try {
    // 加载材质
    materials.value = await dictStore.loadMaterials()

    // 加载标签
    tags.value = await dictStore.loadTags()

    // 加载供应商
    const supplierData = await api.suppliers.getSuppliers()
    suppliers.value = supplierData

    // 设置默认日期为今天
    if (!form.purchase_date) {
      form.purchase_date = new Date().toISOString().split('T')[0]
    }
  } catch (error) {
    console.error('加载下拉数据失败:', error)
    alert('加载数据失败，请刷新页面重试')
  }
}

// 材质变化时加载器型
async function onMaterialChange() {
  const materialId = form.material_id
  if (!materialId) {
    types.value = []
    batchSpecFields.value = []
    return
  }
  try {
    types.value = await dictStore.loadTypesByMaterial(materialId)
    // 如果批次已选择器型，更新规格字段
    if (form.type_id) {
      await updateBatchSpecFields(form.type_id)
    }
  } catch (error) {
    console.error('加载器型失败:', error)
    types.value = []
    batchSpecFields.value = []
  }
}

// 更新批次器型的规格字段
async function updateBatchSpecFields(typeId) {
  if (!typeId) {
    batchSpecFields.value = []
    return
  }
  const type = types.value.find(t => t.id == typeId)
  if (!type || !type.spec_fields) {
    batchSpecFields.value = []
    return
  }
  try {
    const specConfig = JSON.parse(type.spec_fields)
    const fieldDefinitions = {
      weight: { label: '克重(g)', type: 'number', placeholder: '例如：10.5' },
      metal_weight: { label: '金属克重(g)', type: 'number', placeholder: '例如：5.2' },
      size: { label: '尺寸', type: 'text', placeholder: '例如：长宽高' },
      bracelet_size: { label: '圈口', type: 'text', placeholder: '例如：56' },
      bead_count: { label: '粒数', type: 'number', placeholder: '例如：108' },
      bead_diameter: { label: '珠子口径', type: 'text', placeholder: '例如：8mm' },
      ring_size: { label: '戒指尺寸', type: 'text', placeholder: '例如：12号' }
    }
    const fields = []
    for (const key in specConfig) {
      if (specConfig[key] && fieldDefinitions[key]) {
        fields.push({
          key,
          ...fieldDefinitions[key]
        })
      }
    }
    batchSpecFields.value = fields
  } catch (error) {
    console.error('解析规格字段失败:', error)
    batchSpecFields.value = []
  }
}

// 提交批次
async function submitBatch() {
  submitting.value = true
  try {
    // 构造请求数据
    const data = {
      batch_code: form.batch_code,
      material_id: parseInt(form.material_id),
      quantity: parseInt(form.quantity),
      total_cost: parseFloat(form.total_cost),
      cost_alloc_method: form.cost_alloc_method,
      purchase_date: form.purchase_date || null,
      notes: form.notes || null
    }

    // 可选字段
    if (form.type_id) {
      data.type_id = parseInt(form.type_id)
    }
    if (form.supplier_id) {
      data.supplier_id = parseInt(form.supplier_id)
    }

    // 调用API
    const response = await api.batches.createBatch(data)

    // 保存批次ID，进入第二步
    batchId.value = response.id || response
    step.value = 2

    // 如果批次有器型，更新规格字段
    if (form.type_id) {
      await updateBatchSpecFields(form.type_id)
    }

  } catch (error) {
    console.error('创建批次失败:', error)
    alert(`创建批次失败: ${error.message || '请检查输入数据'}`)
  } finally {
    submitting.value = false
  }
}

// 提交货品
async function submitItem() {
  submittingItem.value = true
  try {
    // 构造规格数据（基于批次器型）
    const specData = {}
    batchSpecFields.value.forEach(field => {
      const value = specForm[field.key]
      if (value !== '' && value !== null) {
        specData[field.key] = field.type === 'number' ? parseFloat(value) : value
      }
    })

    // 自动生成SKU（批次ID + 序号）
    const itemNumber = itemsAdded.value + 1
    const skuCode = `${form.batch_code}-${itemNumber.toString().padStart(3, '0')}`

    // 默认商品名称
    const defaultName = itemForm.name || `${selectedMaterialName.value} ${selectedTypeName.value || '货品'}`

    // 构造货品数据（简化版）
    const data = {
      sku_code: skuCode,
      batch_id: batchId.value,
      batch_code: form.batch_code,
      material_id: parseInt(form.material_id),
      selling_price: parseFloat(itemForm.selling_price),
      notes: itemForm.notes || null,
      spec: Object.keys(specData).length > 0 ? specData : null
    }

    // 可选字段
    if (defaultName) data.name = defaultName
    if (itemForm.counter) data.counter = parseInt(itemForm.counter)
    // 批次器型传递给货品
    if (form.type_id) data.type_id = parseInt(form.type_id)

    // 调用API
    await api.items.createItem(data)

    // 更新计数，重置表单
    itemsAdded.value++
    resetItemForm()

    // 成功提示（不再询问是否完成，录够后会显示触发分摊按钮）
    alert(`货品添加成功！已录入 ${itemsAdded.value}/${form.quantity} 件。`)

  } catch (error) {
    console.error('添加货品失败:', error)
    alert(`添加货品失败: ${error.message || '请检查输入数据'}`)
  } finally {
    submittingItem.value = false
  }
}

// 重置货品表单
function resetItemForm() {
  itemForm.name = ''
  itemForm.selling_price = ''
  itemForm.counter = ''
  itemForm.notes = ''
  // 清空规格表单（基于批次器型）
  batchSpecFields.value.forEach(field => {
    specForm[field.key] = ''
  })
}

// 触发成本分摊
async function triggerAllocation() {
  if (!confirm('确定触发成本分摊计算吗？分摊后无法撤销。')) {
    return
  }

  allocating.value = true
  try {
    // 调用分摊API
    await api.batches.allocateBatch(batchId.value)

    // 显示结果区域
    showAllocationResult.value = true

    // 加载分摊结果
    await loadAllocationResult()

  } catch (error) {
    console.error('触发成本分摊失败:', error)
    alert(`成本分摊失败: ${error.message || '请稍后重试'}`)
  } finally {
    allocating.value = false
  }
}

// 加载分摊结果
async function loadAllocationResult() {
  allocationLoading.value = true
  allocationError.value = null
  try {
    // 获取批次详情，包含分摊后的货品信息
    const batchDetail = await api.batches.getBatch(batchId.value)

    // 获取该批次的所有货品
    const itemsResponse = await api.items.getItems({ batch_id: batchId.value })

    // 计算毛利率
    allocationResult.value = itemsResponse.map(item => {
      const profitMargin = item.allocated_cost && item.selling_price
        ? (item.selling_price - item.allocated_cost) / item.selling_price
        : 0
      return {
        ...item,
        profit_margin: profitMargin
      }
    })

  } catch (error) {
    console.error('加载分摊结果失败:', error)
    allocationError.value = error.message || '加载失败'
  } finally {
    allocationLoading.value = false
  }
}

// 返回批次列表
function goToBatchesList() {
  router.push('/batches')
}

// 初始化
onMounted(() => {
  loadSelectData()
})
</script>