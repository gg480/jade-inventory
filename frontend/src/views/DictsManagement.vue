<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const activeTab = ref('materials') // materials, types, tags
const loading = ref(false)

const materials = ref([])
const types = ref([])
const tags = ref([])

// 新增表单
const newMaterial = ref({ name: '', description: '' })
const newType = ref({ name: '', material_id: '', description: '' })
const newTag = ref({ name: '', group_name: '', description: '' })

// 获取字典数据
async function fetchDicts() {
  loading.value = true
  try {
    if (activeTab.value === 'materials') {
      materials.value = await api.dicts.getMaterials()
    } else if (activeTab.value === 'types') {
      // 需要先获取材质列表
      const materialData = await api.dicts.getMaterials()
      materials.value = materialData
      types.value = await api.dicts.getTypes()
    } else if (activeTab.value === 'tags') {
      tags.value = await api.dicts.getTags()
      groupTags()
    }
  } catch (error) {
    console.error('获取字典数据失败:', error)
    alert('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 添加新材质
async function addMaterial() {
  if (!newMaterial.value.name.trim()) {
    alert('请输入材质名称')
    return
  }
  try {
    await api.dicts.createMaterial(newMaterial.value)
    alert('添加成功')
    newMaterial.value = { name: '', description: '' }
    fetchDicts()
  } catch (error) {
    alert(`添加失败: ${error.message}`)
  }
}

// 删除材质
async function deleteMaterial(id, name) {
  if (!confirm(`确定要删除材质 "${name}" 吗？`)) return
  try {
    await api.dicts.deleteMaterial(id)
    alert('删除成功')
    fetchDicts()
  } catch (error) {
    alert(`删除失败: ${error.message}`)
  }
}

// 添加新器型
async function addType() {
  if (!newType.value.name.trim()) {
    alert('请输入器型名称')
    return
  }
  if (!newType.value.material_id) {
    alert('请选择所属材质')
    return
  }
  try {
    await api.dicts.createType(newType.value)
    alert('添加成功')
    newType.value = { name: '', material_id: '', description: '' }
    fetchDicts()
  } catch (error) {
    alert(`添加失败: ${error.message}`)
  }
}

// 删除器型
async function deleteType(id, name) {
  if (!confirm(`确定要删除器型 "${name}" 吗？`)) return
  try {
    await api.dicts.deleteType(id)
    alert('删除成功')
    fetchDicts()
  } catch (error) {
    alert(`删除失败: ${error.message}`)
  }
}

// 添加新标签
async function addTag() {
  if (!newTag.value.name.trim()) {
    alert('请输入标签名称')
    return
  }
  try {
    await api.dicts.createTag(newTag.value)
    alert('添加成功')
    newTag.value = { name: '', group_name: '', description: '' }
    fetchDicts()
  } catch (error) {
    alert(`添加失败: ${error.message}`)
  }
}

// 删除标签
async function deleteTag(id, name) {
  if (!confirm(`确定要删除标签 "${name}" 吗？`)) return
  try {
    await api.dicts.deleteTag(id)
    alert('删除成功')
    fetchDicts()
  } catch (error) {
    alert(`删除失败: ${error.message}`)
  }
}

// 标签分组
const tagGroups = ref({})
function groupTags() {
  const groups = {}
  tags.value.forEach(tag => {
    const group = tag.group_name || '其他'
    if (!groups[group]) groups[group] = []
    groups[group].push(tag)
  })
  tagGroups.value = groups
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
        </nav>
      </div>
    </div>

    <!-- 材质管理 -->
    <div v-if="activeTab === 'materials'" class="space-y-6">
      <!-- 添加材质表单 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">添加新材质</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="form-label">材质名称</label>
            <input v-model="newMaterial.name" type="text" class="form-input" placeholder="如：翡翠" />
          </div>
          <div>
            <label class="form-label">描述（可选）</label>
            <input v-model="newMaterial.description" type="text" class="form-input" placeholder="材质描述" />
          </div>
          <div class="flex items-end">
            <button @click="addMaterial" class="btn btn-success w-full">
              添加材质
            </button>
          </div>
        </div>
      </div>

      <!-- 材质列表 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">材质列表</h2>
        <div v-if="loading" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        </div>
        <div v-else-if="materials.length === 0" class="text-center py-8 text-gray-500">
          暂无材质数据
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="material in materials"
            :key="material.id"
            class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
          >
            <div class="flex items-start justify-between">
              <div>
                <h3 class="font-medium text-gray-900">{{ material.name }}</h3>
                <p v-if="material.description" class="mt-1 text-sm text-gray-600">
                  {{ material.description }}
                </p>
                <p v-else class="mt-1 text-sm text-gray-400">暂无描述</p>
              </div>
              <button
                @click="deleteMaterial(material.id, material.name)"
                class="text-red-600 hover:text-red-800 text-sm"
                title="删除"
              >
                ✕
              </button>
            </div>
            <div class="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
              创建于 {{ new Date(material.created_at).toLocaleDateString() }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 器型管理 -->
    <div v-if="activeTab === 'types'" class="space-y-6">
      <!-- 添加器型表单 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">添加新器型</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label class="form-label">器型名称</label>
            <input v-model="newType.name" type="text" class="form-input" placeholder="如：手镯" />
          </div>
          <div>
            <label class="form-label">所属材质</label>
            <select v-model="newType.material_id" class="form-input">
              <option value="">请选择材质</option>
              <option v-for="material in materials" :key="material.id" :value="material.id">
                {{ material.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="form-label">描述（可选）</label>
            <input v-model="newType.description" type="text" class="form-input" placeholder="器型描述" />
          </div>
          <div class="flex items-end">
            <button @click="addType" class="btn btn-success w-full">
              添加器型
            </button>
          </div>
        </div>
      </div>

      <!-- 器型列表 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">器型列表</h2>
        <div v-if="loading" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        </div>
        <div v-else-if="types.length === 0" class="text-center py-8 text-gray-500">
          暂无器型数据
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="type in types"
            :key="type.id"
            class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
          >
            <div class="flex items-start justify-between">
              <div>
                <h3 class="font-medium text-gray-900">{{ type.name }}</h3>
                <p v-if="type.material_name" class="mt-1 text-sm text-gray-600">
                  材质：{{ type.material_name }}
                </p>
                <p v-if="type.description" class="mt-1 text-sm text-gray-600">
                  {{ type.description }}
                </p>
                <p v-else class="mt-1 text-sm text-gray-400">暂无描述</p>
              </div>
              <button
                @click="deleteType(type.id, type.name)"
                class="text-red-600 hover:text-red-800 text-sm"
                title="删除"
              >
                ✕
              </button>
            </div>
            <div class="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
              创建于 {{ new Date(type.created_at).toLocaleDateString() }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 标签管理 -->
    <div v-if="activeTab === 'tags'" class="space-y-6">
      <!-- 添加标签表单 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">添加新标签</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label class="form-label">标签名称</label>
            <input v-model="newTag.name" type="text" class="form-input" placeholder="如：新品" />
          </div>
          <div>
            <label class="form-label">分组名称</label>
            <input v-model="newTag.group_name" type="text" class="form-input" placeholder="如：状态" />
          </div>
          <div>
            <label class="form-label">描述（可选）</label>
            <input v-model="newTag.description" type="text" class="form-input" placeholder="标签描述" />
          </div>
          <div class="flex items-end">
            <button @click="addTag" class="btn btn-success w-full">
              添加标签
            </button>
          </div>
        </div>
      </div>

      <!-- 标签列表 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">标签列表</h2>
        <div v-if="loading" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        </div>
        <div v-else-if="tags.length === 0" class="text-center py-8 text-gray-500">
          暂无标签数据
        </div>
        <div v-else class="space-y-6">
          <div v-for="(groupTags, groupName) in tagGroups" :key="groupName">
            <h3 class="text-md font-medium text-gray-900 mb-3">{{ groupName }}</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              <div
                v-for="tag in groupTags"
                :key="tag.id"
                class="border border-gray-200 rounded-lg p-3 hover:bg-gray-50"
              >
                <div class="flex items-start justify-between">
                  <div>
                    <span class="font-medium text-gray-900">{{ tag.name }}</span>
                    <p v-if="tag.description" class="mt-1 text-sm text-gray-600">
                      {{ tag.description }}
                    </p>
                  </div>
                  <button
                    @click="deleteTag(tag.id, tag.name)"
                    class="text-red-600 hover:text-red-800 text-sm"
                    title="删除"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>