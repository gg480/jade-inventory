<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useDictStore } from '../store/dict'
import toast from '../composables/useToast'

const props = defineProps({
  id: { type: String, default: null }
})

const router = useRouter()
const dictStore = useDictStore()
const mode = ref('single') // 'single' 或 'batch'
const isEditMode = computed(() => !!props.id)
const loading = ref(false)
const loadingItem = ref(false)



// 单件入库表单
const singleForm = reactive({
  sku_code: '',
  name: '',
  batch_code: '',
  material_id: null,
  type_id: null,
  tag_ids: [],
  cost_price: '',
  selling_price: '',
  floor_price: '',
  origin: '',
  counter: '',
  cert_no: '',
  notes: '',
  supplier_id: null,
  purchase_date: ''
})

// 规格参数表单（根据器型动态显示）
const specForm = reactive({
  weight: '',
  metal_weight: '',
  size: '',
  bracelet_size: '',
  bead_count: '',
  bead_diameter: '',
  ring_size: ''
})

// 批量入库表单
const batchForm = reactive({
  batch_code: '',
  material_id: null,
  type_id: null,
  tag_ids: [],
  quantity: 1,
  cost_price: '',
  selling_price: '',
  sku_prefix: 'ITEM',
  weight: '',
  size: '',
  supplier_id: null,
  purchase_date: ''
})

// 当前模式的材质ID（计算属性）
const currentMaterialId = computed(() => {
  return mode.value === 'single' ? singleForm.material_id : batchForm.material_id
})

// 监听当前材质ID变化
watch(currentMaterialId, (newMaterialId, oldMaterialId) => {
  // 如果材质ID发生变化，更新器型列表
  if (newMaterialId !== oldMaterialId) {
    updateTypesByMaterial(newMaterialId, true) // 材质变化时清空已选择的器型
  }
})

// 监听器型变化，更新规格字段
watch(() => mode.value === 'single' ? singleForm.type_id : batchForm.type_id, (newTypeId) => {
  updateSpecFields(newTypeId)
})

// 监听模式切换，清空规格字段
watch(mode, (newMode) => {
  if (specFields) specFields.value = []
  if (specForm) {
    Object.keys(specForm).forEach(key => {
      specForm[key] = ''
    })
  }
})

// 字典数据
const materials = dictStore.materials // ref
const types = ref([])
const tags = dictStore.tags // ref
const suppliers = ref([])

// 规格字段配置
const specFields = ref([])
const showSpecFields = computed(() => specFields.value.length > 0)

// 获取字典数据（使用缓存）
async function fetchDicts() {
  try {
    // 获取材质（带缓存）
    const materialsData = await dictStore.loadMaterials()
    // 获取标签（带缓存）
    const tagsData = await dictStore.loadTags()
    // 获取供应商
    const suppliersData = await api.suppliers.getSuppliers()
    suppliers.value = suppliersData
    return { materialsData, tagsData, suppliersData }
  } catch (error) {
    console.error('获取字典数据失败:', error)
    toast.error(`加载字典数据失败: ${error.message}，请确保后端服务正在运行，然后刷新页面。`)
    throw error // 重新抛出错误，让上层处理
  }
}

// 加载货品数据（编辑模式）
async function loadItem() {
  if (!isEditMode.value) return
  loadingItem.value = true
  try {
    const item = await api.items.getItem(props.id)
    // 填充单件表单
    singleForm.sku_code = item.sku_code
    singleForm.name = item.name || ''
    singleForm.batch_code = item.batch_code || ''
    singleForm.material_id = item.material_id
    singleForm.type_id = item.type_id || null
    singleForm.tag_ids = item.tags.map(tag => tag.id)
    singleForm.cost_price = item.cost_price.toString()
    singleForm.selling_price = item.selling_price.toString()
    singleForm.floor_price = item.floor_price ? item.floor_price.toString() : ''
    singleForm.origin = item.origin || ''
    singleForm.counter = item.counter ? item.counter.toString() : ''
    singleForm.cert_no = item.cert_no || ''
    singleForm.notes = item.notes || ''
    singleForm.supplier_id = item.supplier_id || null
    singleForm.purchase_date = item.purchase_date || ''

    // 加载规格数据
    if (item.spec) {
      specForm.weight = item.spec.weight ? item.spec.weight.toString() : ''
      specForm.metal_weight = item.spec.metal_weight ? item.spec.metal_weight.toString() : ''
      specForm.size = item.spec.size || ''
      specForm.bracelet_size = item.spec.bracelet_size || ''
      specForm.bead_count = item.spec.bead_count ? item.spec.bead_count.toString() : ''
      specForm.bead_diameter = item.spec.bead_diameter || ''
      specForm.ring_size = item.spec.ring_size || ''
    }

    // 根据材质ID加载器型列表
    if (item.material_id) {
      await updateTypesByMaterial(item.material_id, false)
      // 设置规格字段配置
      if (item.type_id) {
        updateSpecFields(item.type_id)
      }
    }
  } catch (error) {
    toast.error(`加载货品失败: ${error.message}`)
    router.push('/inventory')
  } finally {
    loadingItem.value = false
  }
}

// 根据材质ID更新器型列表（使用缓存）
async function updateTypesByMaterial(materialId, shouldClearType = true) {
  // 防御性检查：确保mode已初始化
  if (!mode) {
    console.warn('mode not initialized yet')
    return []
  }

  // 如果需要，清除当前表单的器型选择
  if (shouldClearType) {
    if (mode.value === 'single') {
      if (singleForm) singleForm.type_id = null
    } else {
      if (batchForm) batchForm.type_id = null
    }
  }

  if (!materialId) {
    types.value = []
    return []
  }
  try {
    const typeData = await dictStore.loadTypesByMaterial(materialId)
    types.value = typeData
    return typeData
  } catch (error) {
    console.error('获取器型失败:', error)
    types.value = []
    return []
  }
}

// 更新规格字段配置
function updateSpecFields(typeId) {
  if (!typeId) {
    specFields.value = []
    // 清空规格表单
    if (specForm) {
      Object.keys(specForm).forEach(key => {
        specForm[key] = ''
      })
    }
    return
  }

  if (!types.value) {
    specFields.value = []
    return
  }

  const type = types.value.find(t => t.id === typeId)
  if (!type || !type.spec_fields) {
    specFields.value = []
    return
  }

  try {
    // 解析spec_fields JSON字符串
    const fields = JSON.parse(type.spec_fields)
    specFields.value = Array.isArray(fields) ? fields : []

    // 如果规格字段配置变更，可以重置已有值（可选）
    // 这里不清空，保留用户可能已填写的数据
  } catch (error) {
    console.error('解析规格字段失败:', error, type.spec_fields)
    specFields.value = []
  }
}

// 提交单件入库（或编辑）
async function submitSingle() {
  if (!validateSingleForm()) return

  loading.value = true
  try {
    // 构建规格对象，只包含非空值
    const specData = {}
    if (specForm.weight.trim()) specData.weight = parseFloat(specForm.weight)
    if (specForm.metal_weight.trim()) specData.metal_weight = parseFloat(specForm.metal_weight)
    if (specForm.size.trim()) specData.size = specForm.size
    if (specForm.bracelet_size.trim()) specData.bracelet_size = specForm.bracelet_size
    if (specForm.bead_count.trim()) specData.bead_count = parseInt(specForm.bead_count)
    if (specForm.bead_diameter.trim()) specData.bead_diameter = specForm.bead_diameter
    if (specForm.ring_size.trim()) specData.ring_size = specForm.ring_size

    const formData = {
      // 编辑模式下不传 sku_code（后端不允许修改）
      ...(isEditMode.value ? {} : { sku_code: singleForm.sku_code }),
      name: singleForm.name || null,
      batch_code: singleForm.batch_code || null,
      material_id: singleForm.material_id ? parseInt(singleForm.material_id) : null,
      type_id: singleForm.type_id ? parseInt(singleForm.type_id) : null,
      tag_ids: singleForm.tag_ids.map(id => parseInt(id)),
      cost_price: parseFloat(singleForm.cost_price),
      selling_price: parseFloat(singleForm.selling_price),
      floor_price: singleForm.floor_price ? parseFloat(singleForm.floor_price) : null,
      origin: singleForm.origin || null,
      counter: singleForm.counter ? parseInt(singleForm.counter) : null,
      cert_no: singleForm.cert_no || null,
      notes: singleForm.notes || null,
      supplier_id: singleForm.supplier_id ? parseInt(singleForm.supplier_id) : null,
      purchase_date: singleForm.purchase_date || null
    }

    // 如果有规格数据，添加到表单
    if (Object.keys(specData).length > 0) {
      formData.spec = specData
    }

    if (isEditMode.value) {
      await api.items.updateItem(props.id, formData)
      toast.success('编辑成功！')
      router.push('/inventory')
    } else {
      await api.items.createItem(formData)
      toast.success('入库成功！')

      // 询问用户下一步操作
      const continueAdd = confirm('入库成功！\n\n点击"确定"继续入库，点击"取消"查看库存列表。')
      if (continueAdd) {
        // 重置表单，保留SKU和进货日期
        const currentSku = singleForm.sku_code
        const currentDate = singleForm.purchase_date
        Object.keys(singleForm).forEach(key => {
          if (key === 'sku_code') {
            // 生成新的SKU
            generateSku()
          } else if (key === 'purchase_date') {
            // 保持当前日期
            singleForm[key] = currentDate
          } else if (key === 'material_id') {
            // 清空材质，触发器型清空
            singleForm[key] = null
          } else if (key === 'tag_ids') {
            singleForm[key] = []
          } else if (typeof singleForm[key] === 'string') {
            singleForm[key] = ''
          } else {
            singleForm[key] = null
          }
        })

        // 清空规格表单
        Object.keys(specForm).forEach(key => {
          specForm[key] = ''
        })

        // 清空规格字段配置
        specFields.value = []

        // 清空器型选择
        singleForm.type_id = null
        types.value = []
      } else {
        router.push('/inventory')
      }
    }
  } catch (error) {
    toast.error(`${isEditMode.value ? '编辑' : '入库'}失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

// 提交批量入库
async function submitBatch() {
  if (!validateBatchForm()) return

  loading.value = true
  try {
    const formData = {
      ...batchForm,
      cost_price: parseFloat(batchForm.cost_price),
      selling_price: parseFloat(batchForm.selling_price),
      tag_ids: batchForm.tag_ids.map(id => parseInt(id)),
      material_id: batchForm.material_id ? parseInt(batchForm.material_id) : null,
      type_id: batchForm.type_id ? parseInt(batchForm.type_id) : null,
      supplier_id: batchForm.supplier_id ? parseInt(batchForm.supplier_id) : null,
      weight: batchForm.weight ? parseFloat(batchForm.weight) : null,
      quantity: parseInt(batchForm.quantity),
      purchase_date: batchForm.purchase_date || null
    }

    await api.items.createItemsBatch(formData)
    toast.success(`批量入库成功！已创建 ${batchForm.quantity} 件货品`)
    router.push('/inventory')
  } catch (error) {
    toast.error(`批量入库失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

// 表单验证
function validateSingleForm() {
  if (!singleForm.sku_code.trim()) {
    toast.warning('请填写SKU编号')
    return false
  }
  if (!singleForm.material_id) {
    toast.warning('请选择材质')
    return false
  }
  if (!singleForm.cost_price || parseFloat(singleForm.cost_price) <= 0) {
    toast.warning('请填写有效的进价')
    return false
  }
  if (!singleForm.selling_price || parseFloat(singleForm.selling_price) <= 0) {
    toast.warning('请填写有效的售价')
    return false
  }
  return true
}

function validateBatchForm() {
  if (!batchForm.batch_code.trim()) {
    toast.warning('请填写款号')
    return false
  }
  if (!batchForm.material_id) {
    toast.warning('请选择材质')
    return false
  }
  if (!batchForm.cost_price || parseFloat(batchForm.cost_price) <= 0) {
    toast.warning('请填写有效的进价')
    return false
  }
  if (!batchForm.selling_price || parseFloat(batchForm.selling_price) <= 0) {
    toast.warning('请填写有效的售价')
    return false
  }
  if (!batchForm.quantity || parseInt(batchForm.quantity) < 1) {
    toast.warning('请填写有效的数量')
    return false
  }
  return true
}

// 自动生成SKU编号（示例）
function generateSku() {
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0')
  singleForm.sku_code = `ITEM-${date}-${random}`
}

// 计算标签分组
const tagGroups = computed(() => {
  const groups = {}
  const tagList = tags.value // tags是计算属性，使用.value获取数组
  if (!tagList || !Array.isArray(tagList)) {
    return groups
  }
  tagList.forEach(tag => {
    const groupName = tag.group_name || '其他'
    if (!groups[groupName]) {
      groups[groupName] = []
    }
    groups[groupName].push(tag)
  })
  return groups
})

onMounted(async () => {
  try {
    await fetchDicts()
    // 设置默认值（非编辑模式）
    if (!isEditMode.value) {
      // 自动生成SKU
      generateSku()
      // 设置进货日期为今天
      singleForm.purchase_date = new Date().toISOString().split('T')[0]
    }
    if (isEditMode.value) {
      mode.value = 'single' // 编辑模式固定为单件
      await loadItem()
    }
  } catch (error) {
    console.error('组件初始化失败:', error)
  }
})
</script>

<template>
  <div>
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">{{ isEditMode ? '编辑货品' : '入库表单' }}</h1>
      <p class="mt-1 text-sm text-gray-600">{{ isEditMode ? '编辑货品信息' : '支持单件入库和同款批量入库' }}</p>
    </div>

    <!-- 模式切换 -->
    <div v-if="!isEditMode" class="card mb-6">
      <div class="flex border-b border-gray-200">
        <button
          @click="mode = 'single'"
          class="px-4 py-3 text-sm font-medium border-b-2 transition-colors"
          :class="mode === 'single' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
        >
          📦 单件入库（高货）
        </button>
        <button
          @click="mode = 'batch'"
          class="ml-8 px-4 py-3 text-sm font-medium border-b-2 transition-colors"
          :class="mode === 'batch' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
        >
          📦📦 批量入库（通货）
        </button>
      </div>
    </div>

    <!-- 单件入库表单 -->
    <div v-if="mode === 'single'" class="card">
      <form @submit.prevent="submitSingle">
        <div class="space-y-6">
          <!-- 基础信息 -->
          <div>
            <h3 class="text-lg font-medium text-gray-900 mb-4">基础信息</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- SKU编号 -->
              <div>
                <label class="form-label">SKU编号 <span class="text-red-500">*</span></label>
                <div class="flex space-x-2">
                  <input
                    v-model="singleForm.sku_code"
                    type="text"
                    placeholder="如 FC-20240315-001"
                    class="form-input flex-1"
                    :readonly="isEditMode"
                    :class="{ 'bg-gray-100 cursor-not-allowed': isEditMode }"
                    required
                  />
                  <button
                    v-if="!isEditMode"
                    type="button"
                    @click="generateSku"
                    class="btn btn-secondary whitespace-nowrap"
                  >
                    自动生成
                  </button>
                </div>
                <p class="mt-1 text-xs text-gray-500">唯一编号，不可重复{{ isEditMode ? '（不可修改）' : '' }}</p>
              </div>

              <!-- 款号 -->
              <div>
                <label class="form-label">款号</label>
                <input
                  v-model="singleForm.batch_code"
                  type="text"
                  placeholder="同款商品共用（通货填写）"
                  class="form-input"
                />
              </div>

              <!-- 商品名称 -->
              <div class="md:col-span-2">
                <label class="form-label">商品名称</label>
                <input
                  v-model="singleForm.name"
                  type="text"
                  placeholder="输入商品名称"
                  class="form-input"
                />
              </div>
            </div>
          </div>

          <!-- 分类信息 -->
          <div>
            <h3 class="text-lg font-medium text-gray-900 mb-4">分类信息</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- 材质 -->
              <div>
                <label class="form-label">材质 <span class="text-red-500">*</span></label>
                <select
                  v-model="singleForm.material_id"
                  class="form-input"
                  required
                >
                  <option value="">请选择材质</option>
                  <option v-for="material in materials" :key="material.id" :value="material.id">
                    {{ material.name }}
                  </option>
                </select>
              </div>

              <!-- 器型 -->
              <div>
                <label class="form-label">器型</label>
                <select v-model="singleForm.type_id" class="form-input" :disabled="!singleForm.material_id">
                  <option value="">请选择器型</option>
                  <option v-for="type in types" :key="type.id" :value="type.id">
                    {{ type.name }}
                  </option>
                </select>
              </div>
            </div>

            <!-- 标签 -->
            <div class="mt-4">
              <label class="form-label">标签（可选）</label>
              <div class="space-y-3">
                <div v-for="(groupTags, groupName) in tagGroups" :key="groupName" class="border border-gray-200 rounded-lg p-3">
                  <div class="text-sm font-medium text-gray-700 mb-2">{{ groupName }}</div>
                  <div class="flex flex-wrap gap-2">
                    <label
                      v-for="tag in groupTags"
                      :key="tag.id"
                      class="inline-flex items-center px-3 py-1.5 border rounded-full cursor-pointer transition-colors"
                      :class="singleForm.tag_ids.includes(tag.id) ? 'bg-primary-50 border-primary-200 text-primary-700' : 'border-gray-200 text-gray-700 hover:bg-gray-50'"
                    >
                      <input
                        type="checkbox"
                        :value="tag.id"
                        v-model="singleForm.tag_ids"
                        class="sr-only"
                      />
                      {{ tag.name }}
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 规格参数（动态显示） -->
          <div v-if="showSpecFields">
            <h3 class="text-lg font-medium text-gray-900 mb-4">规格参数</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- weight 克重(g) -->
              <div v-if="specFields.includes('weight')">
                <label class="form-label">克重(g)</label>
                <input
                  v-model="specForm.weight"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  class="form-input"
                />
              </div>

              <!-- metal_weight 金属克重(g) -->
              <div v-if="specFields.includes('metal_weight')">
                <label class="form-label">金属克重(g)</label>
                <input
                  v-model="specForm.metal_weight"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  class="form-input"
                />
              </div>

              <!-- size 尺寸 -->
              <div v-if="specFields.includes('size')">
                <label class="form-label">尺寸</label>
                <input
                  v-model="specForm.size"
                  type="text"
                  placeholder="如：长50mm宽20mm"
                  class="form-input"
                />
              </div>

              <!-- bracelet_size 圈口 -->
              <div v-if="specFields.includes('bracelet_size')">
                <label class="form-label">圈口</label>
                <input
                  v-model="specForm.bracelet_size"
                  type="text"
                  placeholder="如：52mm"
                  class="form-input"
                />
              </div>

              <!-- bead_count 粒数 -->
              <div v-if="specFields.includes('bead_count')">
                <label class="form-label">粒数</label>
                <input
                  v-model="specForm.bead_count"
                  type="number"
                  min="1"
                  placeholder="如：108"
                  class="form-input"
                />
              </div>

              <!-- bead_diameter 珠子口径 -->
              <div v-if="specFields.includes('bead_diameter')">
                <label class="form-label">珠子口径</label>
                <input
                  v-model="specForm.bead_diameter"
                  type="text"
                  placeholder="如：8mm"
                  class="form-input"
                />
              </div>

              <!-- ring_size 戒指尺寸 -->
              <div v-if="specFields.includes('ring_size')">
                <label class="form-label">戒指尺寸</label>
                <input
                  v-model="specForm.ring_size"
                  type="text"
                  placeholder="如：15号"
                  class="form-input"
                />
              </div>
            </div>
          </div>

          <!-- 价格信息 -->
          <div>
            <h3 class="text-lg font-medium text-gray-900 mb-4">价格信息 <span class="text-red-500">*</span></h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="form-label">进货成本（¥）</label>
                <input
                  v-model="singleForm.cost_price"
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0.00"
                  class="form-input"
                  required
                />
              </div>
              <div>
                <label class="form-label">标价（¥）</label>
                <input
                  v-model="singleForm.selling_price"
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0.00"
                  class="form-input"
                  required
                />
              </div>

              <!-- 底价 -->
              <div class="md:col-span-2">
                <label class="form-label">底价（¥）</label>
                <input
                  v-model="singleForm.floor_price"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  class="form-input"
                />
                <p class="mt-1 text-xs text-gray-500">选填，低于此价不出售</p>
              </div>
            </div>
          </div>

          <!-- 其他信息 -->
          <div>
            <h3 class="text-lg font-medium text-gray-900 mb-4">其他信息</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="form-label">证书编号</label>
                <input v-model="singleForm.cert_no" type="text" class="form-input" />
              </div>
              <div>
                <label class="form-label">进货日期</label>
                <input v-model="singleForm.purchase_date" type="date" class="form-input" />
              </div>

              <!-- 产地 -->
              <div>
                <label class="form-label">产地</label>
                <input v-model="singleForm.origin" type="text" placeholder="如：缅甸、新疆" class="form-input" />
              </div>

              <!-- 柜台号 -->
              <div>
                <label class="form-label">柜台号</label>
                <input v-model="singleForm.counter" type="number" min="1" placeholder="如：1" class="form-input" />
              </div>
            </div>

            <!-- 供应商 -->
            <div class="mt-4">
              <label class="form-label">供应商</label>
              <select v-model="singleForm.supplier_id" class="form-input">
                <option value="">请选择供应商（可选）</option>
                <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">
                  {{ supplier.name }}
                </option>
              </select>
            </div>

            <div class="mt-4">
              <label class="form-label">备注</label>
              <textarea
                v-model="singleForm.notes"
                rows="3"
                class="form-input"
                placeholder="其他备注信息..."
              ></textarea>
            </div>
          </div>

          <!-- 提交按钮 -->
          <div class="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <router-link to="/inventory" class="btn btn-secondary">
              取消
            </router-link>
            <button type="submit" class="btn btn-success" :disabled="loading">
              <span v-if="loading" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
              {{ isEditMode ? '保存修改' : '提交入库' }}
            </button>
          </div>
        </div>
      </form>
    </div>

    <!-- 批量入库表单 -->
    <div v-else class="card">
      <form @submit.prevent="submitBatch">
        <div class="space-y-6">
          <!-- 批量信息 -->
          <div>
            <h3 class="text-lg font-medium text-gray-900 mb-4">批量信息</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <!-- 款号 -->
              <div>
                <label class="form-label">款号 <span class="text-red-500">*</span></label>
                <input
                  v-model="batchForm.batch_code"
                  type="text"
                  placeholder="同款商品共用标识"
                  class="form-input"
                  required
                />
              </div>

              <!-- 数量 -->
              <div>
                <label class="form-label">数量 <span class="text-red-500">*</span></label>
                <input
                  v-model="batchForm.quantity"
                  type="number"
                  min="1"
                  max="500"
                  class="form-input"
                  required
                />
              </div>

              <!-- SKU前缀 -->
              <div>
                <label class="form-label">SKU前缀</label>
                <input
                  v-model="batchForm.sku_prefix"
                  type="text"
                  placeholder="如 ITEM"
                  class="form-input"
                />
                <p class="mt-1 text-xs text-gray-500">生成规则：{前缀}-{日期}-{序号}</p>
              </div>
            </div>
          </div>

          <!-- 其余表单部分与单件入库相同，略作调整 -->
          <!-- 分类信息 -->
          <div>
            <h3 class="text-lg font-medium text-gray-900 mb-4">分类信息</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- 材质 -->
              <div>
                <label class="form-label">材质 <span class="text-red-500">*</span></label>
                <select
                  v-model="batchForm.material_id"
                  class="form-input"
                  required
                >
                  <option value="">请选择材质</option>
                  <option v-for="material in materials" :key="material.id" :value="material.id">
                    {{ material.name }}
                  </option>
                </select>
              </div>

              <!-- 器型 -->
              <div>
                <label class="form-label">器型</label>
                <select v-model="batchForm.type_id" class="form-input" :disabled="!batchForm.material_id">
                  <option value="">请选择器型</option>
                  <option v-for="type in types" :key="type.id" :value="type.id">
                    {{ type.name }}
                  </option>
                </select>
              </div>
            </div>

            <!-- 标签 -->
            <div class="mt-4">
              <label class="form-label">标签（可选）</label>
              <div class="space-y-3">
                <div v-for="(groupTags, groupName) in tagGroups" :key="groupName" class="border border-gray-200 rounded-lg p-3">
                  <div class="text-sm font-medium text-gray-700 mb-2">{{ groupName }}</div>
                  <div class="flex flex-wrap gap-2">
                    <label
                      v-for="tag in groupTags"
                      :key="tag.id"
                      class="inline-flex items-center px-3 py-1.5 border rounded-full cursor-pointer transition-colors"
                      :class="batchForm.tag_ids.includes(tag.id) ? 'bg-primary-50 border-primary-200 text-primary-700' : 'border-gray-200 text-gray-700 hover:bg-gray-50'"
                    >
                      <input
                        type="checkbox"
                        :value="tag.id"
                        v-model="batchForm.tag_ids"
                        class="sr-only"
                      />
                      {{ tag.name }}
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 价格信息 -->
          <div>
            <h3 class="text-lg font-medium text-gray-900 mb-4">价格信息 <span class="text-red-500">*</span></h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="form-label">单件进货成本（¥）</label>
                <input
                  v-model="batchForm.cost_price"
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0.00"
                  class="form-input"
                  required
                />
              </div>
              <div>
                <label class="form-label">单件标价（¥）</label>
                <input
                  v-model="batchForm.selling_price"
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0.00"
                  class="form-input"
                  required
                />
              </div>
            </div>
          </div>

          <!-- 其他信息 -->
          <div>
            <h3 class="text-lg font-medium text-gray-900 mb-4">其他信息</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="form-label">克重（克）</label>
                <input v-model="batchForm.weight" type="number" step="0.01" class="form-input" />
              </div>
              <div>
                <label class="form-label">尺寸</label>
                <input v-model="batchForm.size" type="text" placeholder="如：长50mm宽20mm" class="form-input" />
              </div>
              <div>
                <label class="form-label">进货日期</label>
                <input v-model="batchForm.purchase_date" type="date" class="form-input" />
              </div>
            </div>
          </div>

          <!-- 提交按钮 -->
          <div class="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <router-link to="/inventory" class="btn btn-secondary">
              取消
            </router-link>
            <button type="submit" class="btn btn-success" :disabled="loading">
              <span v-if="loading" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
              批量创建 {{ batchForm.quantity }} 件
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>