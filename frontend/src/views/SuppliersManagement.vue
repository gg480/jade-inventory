<script setup>
import { ref, onMounted } from 'vue'

const suppliers = ref([
  { id: 1, name: '广州翡翠批发市场', contact: '张老板', phone: '13800138000', address: '广州市荔湾区', notes: '主营翡翠手镯' },
  { id: 2, name: '东海珍珠基地', contact: '李经理', phone: '13900139000', address: '浙江省诸暨市', notes: '淡水珍珠供应商' },
  { id: 3, name: '云南银饰工坊', contact: '王师傅', phone: '13700137000', address: '云南省大理市', notes: '手工银饰定制' },
])

const newSupplier = ref({
  name: '',
  contact: '',
  phone: '',
  address: '',
  notes: ''
})

// 添加供货商
function addSupplier() {
  if (!newSupplier.value.name.trim()) {
    alert('请输入供货商名称')
    return
  }

  const newId = suppliers.value.length > 0
    ? Math.max(...suppliers.value.map(s => s.id)) + 1
    : 1

  suppliers.value.push({
    id: newId,
    ...newSupplier.value
  })

  alert('添加成功')
  newSupplier.value = { name: '', contact: '', phone: '', address: '', notes: '' }
}

// 删除供货商
function deleteSupplier(id, name) {
  if (!confirm(`确定要删除供货商 "${name}" 吗？`)) return

  const index = suppliers.value.findIndex(s => s.id === id)
  if (index !== -1) {
    suppliers.value.splice(index, 1)
    alert('删除成功')
  }
}

// 编辑供货商
const editingSupplier = ref(null)
function startEdit(supplier) {
  editingSupplier.value = { ...supplier }
}

function saveEdit() {
  if (!editingSupplier.value.name.trim()) {
    alert('请输入供货商名称')
    return
  }

  const index = suppliers.value.findIndex(s => s.id === editingSupplier.value.id)
  if (index !== -1) {
    suppliers.value[index] = { ...editingSupplier.value }
    alert('保存成功')
    editingSupplier.value = null
  }
}

function cancelEdit() {
  editingSupplier.value = null
}
</script>

<template>
  <div>
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">供货商管理</h1>
      <p class="mt-1 text-sm text-gray-600">管理货品供货商信息</p>
    </div>

    <!-- 添加供货商表单 -->
    <div class="card mb-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">添加新供货商</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="form-label">供货商名称 <span class="text-red-500">*</span></label>
          <input v-model="newSupplier.name" type="text" class="form-input" placeholder="如：广州翡翠批发市场" />
        </div>
        <div>
          <label class="form-label">联系人</label>
          <input v-model="newSupplier.contact" type="text" class="form-input" placeholder="联系人姓名" />
        </div>
        <div>
          <label class="form-label">联系电话</label>
          <input v-model="newSupplier.phone" type="tel" class="form-input" placeholder="手机或固定电话" />
        </div>
        <div>
          <label class="form-label">地址</label>
          <input v-model="newSupplier.address" type="text" class="form-input" placeholder="供货商地址" />
        </div>
        <div class="md:col-span-2">
          <label class="form-label">备注</label>
          <textarea
            v-model="newSupplier.notes"
            rows="2"
            class="form-input"
            placeholder="供货商备注信息..."
          ></textarea>
        </div>
        <div class="md:col-span-2">
          <button @click="addSupplier" class="btn btn-success">
            添加供货商
          </button>
        </div>
      </div>
    </div>

    <!-- 供货商列表 -->
    <div class="card">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">供货商列表</h2>

      <div v-if="suppliers.length === 0" class="text-center py-8 text-gray-500">
        暂无供货商数据
      </div>

      <div v-else class="space-y-4">
        <!-- 编辑模式 -->
        <div v-if="editingSupplier" class="border border-blue-200 rounded-lg p-4 bg-blue-50">
          <h3 class="font-medium text-gray-900 mb-3">编辑供货商</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="form-label">供货商名称 <span class="text-red-500">*</span></label>
              <input v-model="editingSupplier.name" type="text" class="form-input" />
            </div>
            <div>
              <label class="form-label">联系人</label>
              <input v-model="editingSupplier.contact" type="text" class="form-input" />
            </div>
            <div>
              <label class="form-label">联系电话</label>
              <input v-model="editingSupplier.phone" type="tel" class="form-input" />
            </div>
            <div>
              <label class="form-label">地址</label>
              <input v-model="editingSupplier.address" type="text" class="form-input" />
            </div>
            <div class="md:col-span-2">
              <label class="form-label">备注</label>
              <textarea
                v-model="editingSupplier.notes"
                rows="2"
                class="form-input"
              ></textarea>
            </div>
            <div class="md:col-span-2 flex justify-end space-x-3">
              <button @click="cancelEdit" class="btn btn-secondary">
                取消
              </button>
              <button @click="saveEdit" class="btn btn-success">
                保存
              </button>
            </div>
          </div>
        </div>

        <!-- 供货商卡片 -->
        <div
          v-for="supplier in suppliers"
          :key="supplier.id"
          class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <h3 class="font-medium text-gray-900">{{ supplier.name }}</h3>

              <div class="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                <div v-if="supplier.contact" class="flex items-center">
                  <span class="text-gray-500 w-16">联系人：</span>
                  <span class="text-gray-900">{{ supplier.contact }}</span>
                </div>
                <div v-if="supplier.phone" class="flex items-center">
                  <span class="text-gray-500 w-16">电话：</span>
                  <span class="text-gray-900">{{ supplier.phone }}</span>
                </div>
                <div v-if="supplier.address" class="flex items-center md:col-span-2">
                  <span class="text-gray-500 w-16">地址：</span>
                  <span class="text-gray-900">{{ supplier.address }}</span>
                </div>
                <div v-if="supplier.notes" class="flex items-start md:col-span-2">
                  <span class="text-gray-500 w-16">备注：</span>
                  <span class="text-gray-900">{{ supplier.notes }}</span>
                </div>
              </div>
            </div>

            <div class="ml-4 flex space-x-2">
              <button
                @click="startEdit(supplier)"
                class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                title="编辑"
              >
                编辑
              </button>
              <button
                @click="deleteSupplier(supplier.id, supplier.name)"
                class="text-red-600 hover:text-red-800 text-sm font-medium"
                title="删除"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>