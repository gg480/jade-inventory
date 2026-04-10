import { createRouter, createWebHistory } from 'vue-router'

// 页面组件（暂时用占位组件，后续实现）
const InventoryList = () => import('../views/InventoryList.vue')
const InventoryDetail = () => import('../views/InventoryDetail.vue')
const InventoryAdd = () => import('../views/InventoryAdd.vue')
const SalesList = () => import('../views/SalesList.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const DictsManagement = () => import('../views/DictsManagement.vue')
const SuppliersManagement = () => import('../views/SuppliersManagement.vue')

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
    path: '/inventory/:id',
    name: 'inventory-detail',
    component: InventoryDetail,
    meta: { title: '货品详情' },
    props: true
  },
  {
    path: '/inventory/add',
    name: 'inventory-add',
    component: InventoryAdd,
    meta: { title: '入库表单' }
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
    component: SalesList,
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
    name: 'dicts-management',
    component: DictsManagement,
    meta: { title: '字典管理' }
  },
  {
    path: '/settings/suppliers',
    name: 'suppliers-management',
    component: SuppliersManagement,
    meta: { title: '供货商管理' }
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

export default router