import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'

// 全局错误处理
window.addEventListener('error', (event) => {
  console.error('全局错误:', event.error)
  event.preventDefault()
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的 Promise 拒绝:', event.reason)
  event.preventDefault()
})

const app = createApp(App)

// Vue 应用错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue 错误处理:', err, '组件:', vm?.$options?.name, '信息:', info)
}

app.use(router).mount('#app')
