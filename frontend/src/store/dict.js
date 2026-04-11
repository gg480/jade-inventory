import { ref } from 'vue'
import api from '../api'

// 缓存状态
const materials = ref([])
const tags = ref([])
const typesByMaterial = ref({}) // { materialId: types[] }
const loading = ref(false)

// 标志是否已加载
const loaded = {
  materials: false,
  tags: false,
}

/**
 * 获取材质列表（带缓存）
 * @param {boolean} forceRefresh 强制刷新
 * @returns {Promise<Array>}
 */
async function loadMaterials(forceRefresh = false) {
  if (loaded.materials && !forceRefresh && materials.value.length > 0) {
    return materials.value
  }
  try {
    loading.value = true
    const data = await api.dicts.getMaterials()
    materials.value = data
    loaded.materials = true
    return data
  } catch (error) {
    console.error('加载材质失败:', error)
    throw error
  } finally {
    loading.value = false
  }
}

/**
 * 获取标签列表（带缓存）
 * @param {boolean} forceRefresh 强制刷新
 * @returns {Promise<Array>}
 */
async function loadTags(forceRefresh = false) {
  if (loaded.tags && !forceRefresh && tags.value.length > 0) {
    return tags.value
  }
  try {
    loading.value = true
    const data = await api.dicts.getTags()
    tags.value = data
    loaded.tags = true
    return data
  } catch (error) {
    console.error('加载标签失败:', error)
    throw error
  } finally {
    loading.value = false
  }
}

/**
 * 根据材质ID获取器型列表（带缓存）
 * @param {number} materialId
 * @param {boolean} forceRefresh 强制刷新
 * @returns {Promise<Array>}
 */
async function loadTypesByMaterial(materialId, forceRefresh = false) {
  if (!materialId) {
    return []
  }
  if (!forceRefresh && typesByMaterial.value[materialId]) {
    return typesByMaterial.value[materialId]
  }
  try {
    loading.value = true
    const data = await api.dicts.getTypes(materialId)
    typesByMaterial.value[materialId] = data
    return data
  } catch (error) {
    console.error(`加载材质 ${materialId} 的器型失败:`, error)
    throw error
  } finally {
    loading.value = false
  }
}

/**
 * 清空材质缓存
 */
function clearMaterialsCache() {
  materials.value = []
  loaded.materials = false
}

/**
 * 清空标签缓存
 */
function clearTagsCache() {
  tags.value = []
  loaded.tags = false
}

/**
 * 清空器型缓存（可指定材质ID）
 */
function clearTypesCache(materialId = null) {
  if (materialId) {
    delete typesByMaterial.value[materialId]
  } else {
    typesByMaterial.value = {}
  }
}

/**
 * 添加或更新材质（更新缓存）
 */
function updateMaterialInCache(material) {
  const index = materials.value.findIndex(m => m.id === material.id)
  if (index >= 0) {
    materials.value[index] = material
  } else {
    materials.value.push(material)
  }
}

/**
 * 添加或更新标签（更新缓存）
 */
function updateTagInCache(tag) {
  const index = tags.value.findIndex(t => t.id === tag.id)
  if (index >= 0) {
    tags.value[index] = tag
  } else {
    tags.value.push(tag)
  }
}

/**
 * 添加或更新器型（更新缓存）
 */
function updateTypeInCache(type) {
  const materialId = type.material_id
  if (!materialId) return
  if (!typesByMaterial.value[materialId]) {
    typesByMaterial.value[materialId] = []
  }
  const index = typesByMaterial.value[materialId].findIndex(t => t.id === type.id)
  if (index >= 0) {
    typesByMaterial.value[materialId][index] = type
  } else {
    typesByMaterial.value[materialId].push(type)
  }
}

/**
 * 从缓存中删除材质（软删除）
 */
function removeMaterialFromCache(id) {
  const index = materials.value.findIndex(m => m.id === id)
  if (index >= 0) {
    materials.value.splice(index, 1)
  }
  // 同时清空该材质的器型缓存
  delete typesByMaterial.value[id]
}

/**
 * 从缓存中删除标签
 */
function removeTagFromCache(id) {
  const index = tags.value.findIndex(t => t.id === id)
  if (index >= 0) {
    tags.value.splice(index, 1)
  }
}

/**
 * 从缓存中删除器型
 */
function removeTypeFromCache(id, materialId) {
  if (!materialId) return
  if (typesByMaterial.value[materialId]) {
    const index = typesByMaterial.value[materialId].findIndex(t => t.id === id)
    if (index >= 0) {
      typesByMaterial.value[materialId].splice(index, 1)
    }
  }
}

export function useDictStore() {
  return {
    // 状态
    materials,
    tags,
    typesByMaterial,
    loading,
    // 加载方法
    loadMaterials,
    loadTags,
    loadTypesByMaterial,
    // 缓存管理
    clearMaterialsCache,
    clearTagsCache,
    clearTypesCache,
    // 更新缓存
    updateMaterialInCache,
    updateTagInCache,
    updateTypeInCache,
    removeMaterialFromCache,
    removeTagFromCache,
    removeTypeFromCache,
  }
}