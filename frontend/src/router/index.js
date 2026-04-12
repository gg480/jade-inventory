import { createRouter, createWebHistory } from 'vue-router'

// 页面组件（懒加载）
const InventoryList = () => import('../views/InventoryList.vue')
const InventoryDetail = () => import('../views/InventoryDetail.vue')
const InventoryAdd = () => import('../views/InventoryAdd.vue')
const BatchAdd = () => import('../views/BatchAdd.vue')
const SaleList = () => import('../views/SalesList.vue') // 实际文件名为 SalesList.vue
const Dashboard = () => import('../views/Dashboard.vue')
const DictManage = () => import('../views/DictsManagement.vue') // 实际文件名为 DictsManagement.vue
const MetalPriceManage = () => import('../views/MetalPriceManage.vue')
const CustomerList = () => import('../views/CustomerList.vue')
const SuppliersManagement = () => import('../views/SuppliersManagement.vue')
const BatchList = () => import('../views/BatchList.vue')
const NotFound = () => import('../views/NotFound.vue')

const routes = [
  {
    path: '/',
    redirect: '/inventory',
  },
  {
    path: '/inventory',
    name: 'inventory',
    component: InventoryList,
    meta: { title: '库存列表' }
  },
  {
    path: '/batches',
    name: 'batch-list',
    component: BatchList,
    meta: { title: '批次列表' }
  },
  {
    path: '/inventory/add',
    name: 'inventory-add',
    component: InventoryAdd,
    meta: { title: '高货入库' }
  },
  {
    path: '/inventory/batch',
    name: 'batch-add',
    component: BatchAdd,
    meta: { title: '通货批次入库' }
  },
  {
    path: '/inventory/:id',
    name: 'inventory-detail',
    component: InventoryDetail,
    meta: { title: '货品详情' },
    props: true
  },
  {
    path: '/inventory/edit/:id',
    name: 'inventory-edit',
    component: InventoryAdd,
    meta: { title: '编辑货品' },
    props: true
  },
  {
    path: '/sales',
    name: 'sales',
    component: SaleList,
    meta: { title: '销售记录' }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: Dashboard,
    meta: { title: '利润看板' }
  },
  {
    path: '/settings/dicts',
    name: 'dict-manage',
    component: DictManage,
    meta: { title: '字典管理' }
  },
  {
    path: '/settings/metal',
    name: 'metal-price-manage',
    component: MetalPriceManage,
    meta: { title: '贵金属市价管理' }
  },
  {
    path: '/customers',
    name: 'customers',
    component: CustomerList,
    meta: { title: '客户管理' }
  },
  {
    path: '/settings/suppliers',
    name: 'suppliers-management',
    component: SuppliersManagement,
    meta: { title: '供货商管理' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFound,
    meta: { title: '页面不存在' }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫：设置页面标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 玉器店进销存` : '玉器店进销存'
  next()
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
})

export default router