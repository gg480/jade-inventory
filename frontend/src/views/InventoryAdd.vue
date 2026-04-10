<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const props = defineProps({
  id: { type: String, default: null }
})

const router = useRouter()
const mode = ref('single') // 'single' 或 'batch'
const isEditMode = computed(() => !!props.id)
const loading = ref(false)
const loadingItem = ref(false)

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


// 单件入库表单
const singleForm = reactive({
  sku_code: '',
  batch_code: '',
  material_id: null,
  type_id: null,
  tag_ids: [],
  cost_price: '',
  selling_price: '',
  weight: '',
  size: '',
  cert_no: '',
  notes: '',
  supplier_id: null,
  purchase_date: ''
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

// 字典数据
const materials = ref([])
const types = ref([])
const tags = ref([])

// 获取字典数据
async function fetchDicts() {
  try {
    // 获取材质
    const materialData = await api.dicts.getMaterials()
    materials.value = materialData

    // 获取标签
    const tagData = await api.dicts.getTags()
    tags.value = tagData
  } catch (error) {
    console.error('获取字典数据失败:', error)
    alert(`加载字典数据失败: ${error.message}\n请确保后端服务正在运行，然后刷新页面。`)
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
    singleForm.batch_code = item.batch_code || ''
    singleForm.material_id = item.material_id
    singleForm.type_id = item.type_id || null
    singleForm.tag_ids = item.tags.map(tag => tag.id)
    singleForm.cost_price = item.cost_price.toString()
    singleForm.selling_price = item.selling_price.toString()
    singleForm.weight = item.weight ? item.weight.toString() : ''
    singleForm.size = item.size || ''
    singleForm.cert_no = item.cert_no || ''
    singleForm.notes = item.notes || ''
    singleForm.supplier_id = item.supplier_id || null
    singleForm.purchase_date = item.purchase_date || ''
    // 根据材质ID加载器型列表
    if (item.material_id) {
      await updateTypesByMaterial(item.material_id, false)
    }
  } catch (error) {
    alert(`加载货品失败: ${error.message}`)
    router.push('/inventory')
  } finally {
    loadingItem.value = false
  }
}

// 根据材质ID更新器型列表
async function updateTypesByMaterial(materialId, shouldClearType = true) {
  // 如果需要，清除当前表单的器型选择
  if (shouldClearType) {
    if (mode.value === 'single') {
      singleForm.type_id = null
    } else {
      batchForm.type_id = null
    }
  }

  if (!materialId) {
    types.value = []
    return
  }
  try {
    const typeData = await api.dicts.getTypes(materialId)
    types.value = typeData
  } catch (error) {
    console.error('获取器型失败:', error)
    types.value = []
  }
}

// 提交单件入库（或编辑）
async function submitSingle() {
  if (!validateSingleForm()) return

  loading.value = true
  try {
    const formData = {
      // 编辑模式下不传 sku_code（后端不允许修改）
      ...(isEditMode.value ? {} : { sku_code: singleForm.sku_code }),
      batch_code: singleForm.batch_code || null,
      material_id: singleForm.material_id ? parseInt(singleForm.material_id) : null,
      type_id: singleForm.type_id ? parseInt(singleForm.type_id) : null,
      tag_ids: singleForm.tag_ids.map(id => parseInt(id)),
      cost_price: parseFloat(singleForm.cost_price),
      selling_price: parseFloat(singleForm.selling_price),
      weight: singleForm.weight ? parseFloat(singleForm.weight) : null,
      size: singleForm.size || null,
      cert_no: singleForm.cert_no || null,
      notes: singleForm.notes || null,
      supplier_id: singleForm.supplier_id ? parseInt(singleForm.supplier_id) : null,
      purchase_date: singleForm.purchase_date || null
    }

    if (isEditMode.value) {
      await api.items.updateItem(props.id, formData)
      alert('编辑成功！')
    } else {
      await api.items.createItem(formData)
      alert('入库成功！')
    }
    router.push('/inventory')
  } catch (error) {
    alert(`${isEditMode.value ? '编辑' : '入库'}失败: ${error.message}`)
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
    alert(`批量入库成功！已创建 ${batchForm.quantity} 件货品`)
    router.push('/inventory')
  } catch (error) {
    alert(`批量入库失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

// 表单验证
function validateSingleForm() {
  if (!singleForm.sku_code.trim()) {
    alert('请填写SKU编号')
    return false
  }
  if (!singleForm.material_id) {
    alert('请选择材质')
    return false
  }
  if (!singleForm.cost_price || parseFloat(singleForm.cost_price) <= 0) {
    alert('请填写有效的进价')
    return false
  }
  if (!singleForm.selling_price || parseFloat(singleForm.selling_price) <= 0) {
    alert('请填写有效的售价')
    return false
  }
  return true
}

function validateBatchForm() {
  if (!batchForm.batch_code.trim()) {
    alert('请填写款号')
    return false
  }
  if (!batchForm.material_id) {
    alert('请选择材质')
    return false
  }
  if (!batchForm.cost_price || parseFloat(batchForm.cost_price) <= 0) {
    alert('请填写有效的进价')
    return false
  }
  if (!batchForm.selling_price || parseFloat(batchForm.selling_price) <= 0) {
    alert('请填写有效的售价')
    return false
  }
  if (!batchForm.quantity || parseInt(batchForm.quantity) < 1) {
    alert('请填写有效的数量')
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
  tags.value.forEach(tag => {
    if (!groups[tag.group_name || '其他']) {
      groups[tag.group_name || '其他'] = []
    }
    groups[tag.group_name || '其他'].push(tag)
  })
  return groups
})

onMounted(async () => {
  await fetchDicts()
  if (isEditMode.value) {
    mode.value = 'single' // 编辑模式固定为单件
    await loadItem()
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

          <!-- 价格信息 -->
          <div>
            <h3 class="text-lg font-medium text-gray-900 mb-4">价格信息 <span class="text-red-500">*</span></h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="form-label">进货成本（元）</label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">¥</span>
                  <input
                    v-model="singleForm.cost_price"
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="0.00"
                    class="form-input pl-8"
                    required
                  />
                </div>
              </div>
              <div>
                <label class="form-label">标价（元）</label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">¥</span>
                  <input
                    v-model="singleForm.selling_price"
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="0.00"
                    class="form-input pl-8"
                    required
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- 其他信息 -->
          <div>
            <h3 class="text-lg font-medium text-gray-900 mb-4">其他信息</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="form-label">克重（克）</label>
                <input v-model="singleForm.weight" type="number" step="0.01" class="form-input" />
              </div>
              <div>
                <label class="form-label">尺寸</label>
                <input v-model="singleForm.size" type="text" placeholder="如：长50mm宽20mm" class="form-input" />
              </div>
              <div>
                <label class="form-label">证书编号</label>
                <input v-model="singleForm.cert_no" type="text" class="form-input" />
              </div>
              <div>
                <label class="form-label">进货日期</label>
                <input v-model="singleForm.purchase_date" type="date" class="form-input" />
              </div>
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
                <label class="form-label">单件进货成本（元）</label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">¥</span>
                  <input
                    v-model="batchForm.cost_price"
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="0.00"
                    class="form-input pl-8"
                    required
                  />
                </div>
              </div>
              <div>
                <label class="form-label">单件标价（元）</label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">¥</span>
                  <input
                    v-model="batchForm.selling_price"
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="0.00"
                    class="form-input pl-8"
                    required
                  />
                </div>
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