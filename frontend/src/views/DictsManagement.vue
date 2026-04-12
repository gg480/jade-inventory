<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'
import MaterialModal from '../components/MaterialModal.vue'
import TypeModal from '../components/TypeModal.vue'
import TagModal from '../components/TagModal.vue'

const activeTab = ref('materials') // materials, types, tags, config
const loading = ref(false)

// 材质相关
const materials = ref([])
const showMaterialModal = ref(false)
const editingMaterial = ref(null)
const modalMode = ref('add') // 'add' or 'edit'
const modalLoading = ref(false)

// 器型相关
const types = ref([])
const showTypeModal = ref(false)
const editingType = ref(null)
const typeModalMode = ref('add') // 'add' or 'edit'
const typeModalLoading = ref(false)
const newType = ref({ name: '', material_id: '', description: '' }) // 保持兼容性，稍后移除material_id

// 标签相关
const tags = ref([])
const showTagModal = ref(false)
const editingTag = ref(null)
const tagModalMode = ref('add') // 'add' or 'edit'
const tagModalLoading = ref(false)
const tagGroups = ref({})
const collapsedGroups = ref([])
const newTag = ref({ name: '', group_name: '', description: '' })

// 系统配置相关
const configList = ref([])
const editingConfigKey = ref(null)
const editingConfigValue = ref('')
const configSaving = ref(false)
const configLoading = ref(false)
const configNameMap = {
  operating_cost_rate: '经营成本率',
  markup_rate: '零售价上浮比例',
  aging_threshold_days: '压货预警天数',
  default_alloc_method: '默认分摊算法'
}

// 获取字典数据
async function fetchDicts() {
  loading.value = true
  try {
    if (activeTab.value === 'materials') {
      // 获取所有材质（包含已停用的）
      materials.value = await api.dicts.getMaterials(true)
    } else if (activeTab.value === 'types') {
      // 获取所有器型（包含已停用的） - 独立于材质
      types.value = await api.dicts.getTypes(true)
    } else if (activeTab.value === 'tags') {
      // 获取所有标签（包含已停用的）
      tags.value = await api.dicts.getTags(null, true)
      groupTags()
    } else if (activeTab.value === 'config') {
      // 获取系统配置
      await fetchConfig()
    }
  } catch (error) {
    console.error('获取字典数据失败:', error)
    alert('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 移动端检测
const isMobile = computed(() => window.innerWidth < 768)

// 打开新增材质模态框
function openAddModal() {
  editingMaterial.value = null
  modalMode.value = 'add'
  showMaterialModal.value = true
}

// 打开编辑材质模态框
function openEditModal(material) {
  editingMaterial.value = material
  modalMode.value = 'edit'
  showMaterialModal.value = true
}

// 处理材质表单提交
async function handleMaterialSubmit(formData) {
  modalLoading.value = true
  try {
    if (modalMode.value === 'add') {
      await api.dicts.createMaterial(formData)
      alert('添加成功')
    } else {
      await api.dicts.updateMaterial(editingMaterial.value.id, formData)
      alert('编辑成功')
    }
    showMaterialModal.value = false
    fetchDicts()
  } catch (error) {
    // 错误信息已由API拦截器展示
    console.error('保存材质失败:', error)
  } finally {
    modalLoading.value = false
  }
}

// 切换材质状态（停用/启用）
async function toggleMaterialStatus(material) {
  const action = material.is_active ? '停用' : '启用'
  if (!confirm(`确定要${action}材质 "${material.name}" 吗？`)) return

  try {
    if (material.is_active) {
      // 停用：调用删除接口（软删除）
      await api.dicts.deleteMaterial(material.id)
    } else {
      // 启用：更新 is_active 为 true
      await api.dicts.updateMaterial(material.id, { is_active: true })
    }
    alert(`${action}成功`)
    fetchDicts()
  } catch (error) {
    console.error(`${action}材质失败:`, error)
  }
}

// 打开新增器型模态框
function openAddTypeModal() {
  editingType.value = null
  typeModalMode.value = 'add'
  showTypeModal.value = true
}

// 打开编辑器型模态框
function openEditTypeModal(type) {
  editingType.value = type
  typeModalMode.value = 'edit'
  showTypeModal.value = true
}

// 处理器型表单提交
async function handleTypeSubmit(formData) {
  typeModalLoading.value = true
  try {
    if (typeModalMode.value === 'add') {
      await api.dicts.createType(formData)
      alert('添加成功')
    } else {
      await api.dicts.updateType(editingType.value.id, formData)
      alert('编辑成功')
    }
    showTypeModal.value = false
    fetchDicts()
  } catch (error) {
    // 错误信息已由API拦截器展示
    console.error('保存器型失败:', error)
  } finally {
    typeModalLoading.value = false
  }
}

// 切换器型状态（停用/启用）
async function toggleTypeStatus(type) {
  const action = type.is_active ? '停用' : '启用'
  if (!confirm(`确定要${action}器型 "${type.name}" 吗？`)) return

  try {
    if (type.is_active) {
      // 停用：调用删除接口（软删除）
      await api.dicts.deleteType(type.id)
    } else {
      // 启用：更新 is_active 为 true
      await api.dicts.updateType(type.id, { is_active: true })
    }
    alert(`${action}成功`)
    fetchDicts()
  } catch (error) {
    console.error(`${action}器型失败:`, error)
  }
}

// 解析spec_fields JSON字符串为数组
function parseSpecFields(specFieldsJson) {
  if (!specFieldsJson) return []
  try {
    return JSON.parse(specFieldsJson)
  } catch (e) {
    console.error('解析spec_fields失败:', e)
    return []
  }
}

// 获取规格字段显示名称
function getSpecFieldLabel(field) {
  const map = {
    weight: '重量',
    size: '尺寸',
    bracelet_size: '圈口',
    bead_count: '粒数',
    bead_diameter: '珠子口径',
    ring_size: '戒指尺寸',
    metal_weight: '金属重量'
  }
  return map[field] || field
}

// 标签分组
function groupTags() {
  const groups = {}
  tags.value.forEach(tag => {
    const group = tag.group_name || '其他'
    if (!groups[group]) groups[group] = []
    groups[group].push(tag)
  })
  tagGroups.value = groups
}

// 获取所有现有的分组名称（用于下拉框）
function getExistingGroups() {
  const groups = new Set()
  tags.value.forEach(tag => {
    if (tag.group_name) {
      groups.add(tag.group_name)
    }
  })
  return Array.from(groups)
}

// 切换分组折叠状态
function toggleGroup(groupName) {
  const index = collapsedGroups.value.indexOf(groupName)
  if (index > -1) {
    collapsedGroups.value.splice(index, 1)
  } else {
    collapsedGroups.value.push(groupName)
  }
}

// 检查分组是否折叠
function isGroupCollapsed(groupName) {
  return collapsedGroups.value.includes(groupName)
}

// 打开新增标签模态框
function openAddTagModal() {
  editingTag.value = null
  tagModalMode.value = 'add'
  showTagModal.value = true
}

// 打开编辑标签模态框
function openEditTagModal(tag) {
  editingTag.value = tag
  tagModalMode.value = 'edit'
  showTagModal.value = true
}

// 处理标签表单提交
async function handleTagSubmit(formData) {
  tagModalLoading.value = true
  try {
    if (tagModalMode.value === 'add') {
      await api.dicts.createTag(formData)
      alert('添加成功')
    } else {
      await api.dicts.updateTag(editingTag.value.id, formData)
      alert('编辑成功')
    }
    showTagModal.value = false
    fetchDicts()
  } catch (error) {
    // 错误信息已由API拦截器展示
    console.error('保存标签失败:', error)
  } finally {
    tagModalLoading.value = false
  }
}

// 切换标签状态（停用/启用）
async function toggleTagStatus(tag) {
  const action = tag.is_active ? '停用' : '启用'
  if (!confirm(`确定要${action}标签 "${tag.name}" 吗？`)) return

  try {
    if (tag.is_active) {
      // 停用：调用删除接口（软删除）
      await api.dicts.deleteTag(tag.id)
    } else {
      // 启用：更新 is_active 为 true
      await api.dicts.updateTag(tag.id, { is_active: true })
    }
    alert(`${action}成功`)
    fetchDicts()
  } catch (error) {
    console.error(`${action}标签失败:`, error)
  }
}

// 获取系统配置
async function fetchConfig() {
  configLoading.value = true
  try {
    const data = await api.dicts.getConfig()
    // 后端返回数组或对象，统一转为数组
    if (Array.isArray(data)) {
      configList.value = data
    } else if (data && typeof data === 'object') {
      configList.value = Object.entries(data).map(([key, value]) => ({ key, value }))
    } else {
      configList.value = []
    }
  } catch (error) {
    console.error('获取系统配置失败:', error)
    alert('获取系统配置失败')
  } finally {
    configLoading.value = false
  }
}

// 开始编辑配置
function startEditConfig(config) {
  editingConfigKey.value = config.key
  editingConfigValue.value = String(config.value || '')
}

// 取消编辑配置
function cancelEditConfig() {
  editingConfigKey.value = null
  editingConfigValue.value = ''
}

// 保存配置
async function saveConfig() {
  if (!editingConfigKey.value) return
  configSaving.value = true
  try {
    await api.dicts.updateConfig(editingConfigKey.value, editingConfigValue.value)
    alert('保存成功')
    editingConfigKey.value = null
    editingConfigValue.value = ''
    await fetchConfig()
  } catch (error) {
    console.error('保存配置失败:', error)
  } finally {
    configSaving.value = false
  }
}

// 获取配置项中文名称
function getConfigName(key) {
  return configNameMap[key] || key
}

onMounted(() => {
  fetchDicts()
})
</script>

<template>
  <div>
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">字典管理</h1>
      <p class="mt-1 text-sm text-gray-600">管理材质、器型、标签等基础数据</p>
    </div>

    <!-- 标签页 -->
    <div class="card mb-6">
      <div class="border-b border-gray-200">
        <nav class="-mb-px flex">
          <button
            @click="activeTab = 'materials'; fetchDicts()"
            :class="[
              'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'materials'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            材质管理
          </button>
          <button
            @click="activeTab = 'types'; fetchDicts()"
            :class="[
              'ml-8 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'types'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            器型管理
          </button>
          <button
            @click="activeTab = 'tags'; fetchDicts()"
            :class="[
              'ml-8 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'tags'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            标签管理
          </button>
          <button
            @click="activeTab = 'config'; fetchDicts()"
            :class="[
              'ml-8 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'config'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            系统配置
          </button>
        </nav>
      </div>
    </div>

    <!-- 材质管理 -->
    <div v-if="activeTab === 'materials'" class="space-y-6">
      <!-- 新增按钮 -->
      <div class="card">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">材质管理</h2>
          <button @click="openAddModal" class="btn btn-success">
            新增材质
          </button>
        </div>
      </div>

      <!-- 材质列表 -->
      <div class="card">
        <div v-if="loading" class="text-center py-12">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p class="mt-2 text-gray-500">加载中...</p>
        </div>
        <div v-else-if="materials.length === 0" class="text-center py-12">
          <div class="text-gray-400 text-5xl mb-4">💎</div>
          <h3 class="text-lg font-medium text-gray-900 mb-1">暂无材质数据</h3>
          <p class="text-gray-500">点击上方"新增材质"按钮添加材质</p>
        </div>
        <div v-else>
          <!-- 桌面端表格 (md以上显示) -->
          <div class="hidden md:block">
            <div class="table-container">
              <table class="table">
                <thead>
                  <tr>
                    <th class="w-40">名称</th>
                    <th class="w-32">子类</th>
                    <th class="w-40">产地</th>
                    <th class="w-32 text-right">克重单价</th>
                    <th class="w-24 text-right">排序</th>
                    <th class="w-24">状态</th>
                    <th class="w-40">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="material in materials" :key="material.id" :class="{'bg-gray-50': !material.is_active}">
                    <td class="font-medium">{{ material.name }}</td>
                    <td>{{ material.sub_type || '—' }}</td>
                    <td>{{ material.origin || '—' }}</td>
                    <td class="text-right">
                      <span v-if="material.cost_per_gram">¥{{ material.cost_per_gram.toFixed(2) }}</span>
                      <span v-else class="text-gray-400">—</span>
                    </td>
                    <td class="text-right">{{ material.sort_order }}</td>
                    <td>
                      <span :class="`px-2 py-1 text-xs rounded-full ${material.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`">
                        {{ material.is_active ? '启用' : '停用' }}
                      </span>
                    </td>
                    <td>
                      <div class="flex space-x-2">
                        <button @click="openEditModal(material)" class="btn btn-sm btn-secondary">
                          编辑
                        </button>
                        <button @click="toggleMaterialStatus(material)" :class="`btn btn-sm ${material.is_active ? 'btn-danger' : 'btn-success'}`">
                          {{ material.is_active ? '停用' : '启用' }}
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 移动端卡片 (md以下显示) -->
          <div class="md:hidden space-y-4">
            <div v-for="material in materials" :key="material.id" class="border border-gray-200 rounded-lg p-4" :class="{'bg-gray-50': !material.is_active}">
              <div class="flex justify-between items-start mb-3">
                <div>
                  <h3 class="font-medium text-gray-900">{{ material.name }}</h3>
                  <div class="flex flex-wrap gap-2 mt-1">
                    <span v-if="material.sub_type" class="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full">{{ material.sub_type }}</span>
                    <span v-if="material.origin" class="px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded-full">{{ material.origin }}</span>
                  </div>
                </div>
                <span :class="`px-2 py-1 text-xs rounded-full ${material.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`">
                  {{ material.is_active ? '启用' : '停用' }}
                </span>
              </div>
              <div class="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <div class="text-sm text-gray-500">克重单价</div>
                  <div class="font-medium">
                    <span v-if="material.cost_per_gram">¥{{ material.cost_per_gram.toFixed(2) }}</span>
                    <span v-else class="text-gray-400">—</span>
                  </div>
                </div>
                <div>
                  <div class="text-sm text-gray-500">排序</div>
                  <div class="font-medium">{{ material.sort_order }}</div>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-100 flex justify-between">
                <button @click="openEditModal(material)" class="btn btn-sm btn-secondary flex-1 mr-2">
                  编辑
                </button>
                <button @click="toggleMaterialStatus(material)" :class="`btn btn-sm flex-1 ${material.is_active ? 'btn-danger' : 'btn-success'}`">
                  {{ material.is_active ? '停用' : '启用' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 材质模态框 -->
      <MaterialModal
        :visible="showMaterialModal"
        :material="editingMaterial"
        :mode="modalMode"
        :loading="modalLoading"
        @submit="handleMaterialSubmit"
        @cancel="showMaterialModal = false"
      />
    </div>

    <!-- 器型管理 -->
    <div v-if="activeTab === 'types'" class="space-y-6">
      <!-- 新增按钮 -->
      <div class="card">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">器型管理</h2>
          <button @click="openAddTypeModal" class="btn btn-success">
            新增器型
          </button>
        </div>
      </div>

      <!-- 器型列表 -->
      <div class="card">
        <div v-if="loading" class="text-center py-12">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p class="mt-2 text-gray-500">加载中...</p>
        </div>
        <div v-else-if="types.length === 0" class="text-center py-12">
          <div class="text-gray-400 text-5xl mb-4">📦</div>
          <h3 class="text-lg font-medium text-gray-900 mb-1">暂无器型数据</h3>
          <p class="text-gray-500">点击上方"新增器型"按钮添加器型</p>
        </div>
        <div v-else>
          <!-- 桌面端表格 (md以上显示) -->
          <div class="hidden md:block">
            <div class="table-container">
              <table class="table">
                <thead>
                  <tr>
                    <th class="w-40">名称</th>
                    <th class="w-64">规格字段</th>
                    <th class="w-24 text-right">排序</th>
                    <th class="w-24">状态</th>
                    <th class="w-40">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="type in types" :key="type.id" :class="{'bg-gray-50': !type.is_active}">
                    <td class="font-medium">{{ type.name }}</td>
                    <td>
                      <div class="flex flex-wrap gap-1">
                        <span
                          v-for="field in parseSpecFields(type.spec_fields)"
                          :key="field"
                          class="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full"
                        >
                          {{ getSpecFieldLabel(field) }}
                        </span>
                        <span v-if="parseSpecFields(type.spec_fields).length === 0" class="text-gray-400 text-sm">
                          —
                        </span>
                      </div>
                    </td>
                    <td class="text-right">{{ type.sort_order }}</td>
                    <td>
                      <span :class="`px-2 py-1 text-xs rounded-full ${type.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`">
                        {{ type.is_active ? '启用' : '停用' }}
                      </span>
                    </td>
                    <td>
                      <div class="flex space-x-2">
                        <button @click="openEditTypeModal(type)" class="btn btn-sm btn-secondary">
                          编辑
                        </button>
                        <button @click="toggleTypeStatus(type)" :class="`btn btn-sm ${type.is_active ? 'btn-danger' : 'btn-success'}`">
                          {{ type.is_active ? '停用' : '启用' }}
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 移动端卡片 (md以下显示) -->
          <div class="md:hidden space-y-4">
            <div v-for="type in types" :key="type.id" class="border border-gray-200 rounded-lg p-4" :class="{'bg-gray-50': !type.is_active}">
              <div class="flex justify-between items-start mb-3">
                <div>
                  <h3 class="font-medium text-gray-900">{{ type.name }}</h3>
                  <div class="flex flex-wrap gap-1 mt-1">
                    <span
                      v-for="field in parseSpecFields(type.spec_fields)"
                      :key="field"
                      class="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full"
                    >
                      {{ getSpecFieldLabel(field) }}
                    </span>
                    <span v-if="parseSpecFields(type.spec_fields).length === 0" class="text-gray-400 text-xs">
                      无规格字段
                    </span>
                  </div>
                </div>
                <span :class="`px-2 py-1 text-xs rounded-full ${type.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`">
                  {{ type.is_active ? '启用' : '停用' }}
                </span>
              </div>
              <div class="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <div class="text-sm text-gray-500">排序</div>
                  <div class="font-medium">{{ type.sort_order }}</div>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-100 flex justify-between">
                <button @click="openEditTypeModal(type)" class="btn btn-sm btn-secondary flex-1 mr-2">
                  编辑
                </button>
                <button @click="toggleTypeStatus(type)" :class="`btn btn-sm flex-1 ${type.is_active ? 'btn-danger' : 'btn-success'}`">
                  {{ type.is_active ? '停用' : '启用' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 器型模态框 -->
      <TypeModal
        :visible="showTypeModal"
        :type="editingType"
        :mode="typeModalMode"
        :loading="typeModalLoading"
        @submit="handleTypeSubmit"
        @cancel="showTypeModal = false"
      />
    </div>

    <!-- 标签管理 -->
    <div v-if="activeTab === 'tags'" class="space-y-6">
      <!-- 新增按钮 -->
      <div class="card">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">标签管理</h2>
          <button @click="openAddTagModal" class="btn btn-success">
            新增标签
          </button>
        </div>
      </div>

      <!-- 标签列表 -->
      <div class="card">
        <div v-if="loading" class="text-center py-12">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p class="mt-2 text-gray-500">加载中...</p>
        </div>
        <div v-else-if="tags.length === 0" class="text-center py-12">
          <div class="text-gray-400 text-5xl mb-4">🏷️</div>
          <h3 class="text-lg font-medium text-gray-900 mb-1">暂无标签数据</h3>
          <p class="text-gray-500">点击上方"新增标签"按钮添加标签</p>
        </div>
        <div v-else class="space-y-6">
          <div v-for="(groupTags, groupName) in tagGroups" :key="groupName">
            <!-- 分组标题（可点击折叠） -->
            <div
              @click="toggleGroup(groupName)"
              class="flex items-center justify-between cursor-pointer mb-3 p-2 hover:bg-gray-50 rounded-lg"
            >
              <div class="flex items-center">
                <svg
                  :class="`w-4 h-4 mr-2 transform transition-transform ${isGroupCollapsed(groupName) ? 'rotate-90' : ''}`"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
                <h3 class="text-md font-medium text-gray-900">{{ groupName }}</h3>
                <span class="ml-2 text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                  {{ groupTags.length }} 个标签
                </span>
              </div>
              <span class="text-sm text-gray-500">
                {{ isGroupCollapsed(groupName) ? '点击展开' : '点击收起' }}
              </span>
            </div>

            <!-- 分组内容（可折叠） -->
            <div v-if="!isGroupCollapsed(groupName)" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              <div
                v-for="tag in groupTags"
                :key="tag.id"
                class="border border-gray-200 rounded-lg p-3 hover:bg-gray-50"
                :class="{'bg-gray-50': !tag.is_active}"
              >
                <div class="flex items-start justify-between">
                  <div>
                    <div class="flex items-center">
                      <span class="font-medium text-gray-900">{{ tag.name }}</span>
                      <span :class="`ml-2 px-1.5 py-0.5 text-xs rounded-full ${tag.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`">
                        {{ tag.is_active ? '启用' : '停用' }}
                      </span>
                    </div>
                    <p v-if="tag.description" class="mt-1 text-sm text-gray-600">
                      {{ tag.description }}
                    </p>
                  </div>
                  <div class="flex space-x-1">
                    <button
                      @click="openEditTagModal(tag)"
                      class="text-blue-600 hover:text-blue-800 text-sm"
                      title="编辑"
                    >
                      ✎
                    </button>
                    <button
                      @click="toggleTagStatus(tag)"
                      :class="`text-sm ${tag.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'}`"
                      :title="tag.is_active ? '停用' : '启用'"
                    >
                      {{ tag.is_active ? '×' : '✓' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 标签模态框 -->
      <TagModal
        :visible="showTagModal"
        :tag="editingTag"
        :mode="tagModalMode"
        :loading="tagModalLoading"
        :existing-groups="getExistingGroups()"
        @submit="handleTagSubmit"
        @cancel="showTagModal = false"
      />
    </div>

    <!-- 系统配置 -->
    <div v-if="activeTab === 'config'" class="space-y-6">
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900">系统配置</h2>
        <p class="mt-1 text-sm text-gray-500">管理系统参数，如成本率、预警天数等</p>
      </div>

      <div class="card">
        <div v-if="configLoading" class="text-center py-12">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p class="mt-2 text-gray-500">加载中...</p>
        </div>
        <div v-else-if="configList.length === 0" class="text-center py-12">
          <div class="text-gray-400 text-5xl mb-4">⚙️</div>
          <h3 class="text-lg font-medium text-gray-900 mb-1">暂无配置数据</h3>
        </div>
        <div v-else>
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  <th class="w-48">配置项名称</th>
                  <th class="w-56">配置 Key</th>
                  <th>当前值</th>
                  <th class="w-32">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="config in configList" :key="config.key">
                  <td class="font-medium">{{ getConfigName(config.key) }}</td>
                  <td>
                    <code class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">{{ config.key }}</code>
                  </td>
                  <td>
                    <div v-if="editingConfigKey === config.key">
                      <input
                        v-model="editingConfigValue"
                        type="text"
                        class="form-input w-48"
                        @keyup.enter="saveConfig"
                        @keyup.escape="cancelEditConfig"
                        :disabled="configSaving"
                      />
                    </div>
                    <span v-else class="text-gray-900">{{ config.value }}</span>
                  </td>
                  <td>
                    <div v-if="editingConfigKey === config.key" class="flex space-x-2">
                      <button @click="saveConfig" class="btn btn-sm btn-success" :disabled="configSaving">
                        {{ configSaving ? '保存中...' : '保存' }}
                      </button>
                      <button @click="cancelEditConfig" class="btn btn-sm btn-secondary" :disabled="configSaving">
                        取消
                      </button>
                    </div>
                    <button v-else @click="startEditConfig(config)" class="btn btn-sm btn-secondary">
                      编辑
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>