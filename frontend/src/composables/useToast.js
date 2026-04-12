import { reactive } from 'vue'

// 全局响应式 toast 列表
const toasts = reactive([])
let toastId = 0

/**
 * 显示 toast 通知
 * @param {string} message - 消息文本
 * @param {object} options - 配置项
 * @param {'success'|'error'|'warning'|'info'} options.type - 消息类型（默认 success）
 * @param {number} options.duration - 显示时长毫秒（默认 3000）
 */
function showToast(message, options = {}) {
  const id = ++toastId
  const { type = 'success', duration = 3000 } = options

  const toast = reactive({
    id,
    message,
    type,
    duration
  })

  toasts.push(toast)

  // 自动移除
  if (duration > 0) {
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  return id
}

// 移除 toast
function removeToast(id) {
  const index = toasts.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.splice(index, 1)
  }
}

// 快捷方法
const toast = {
  /** 成功通知（绿色） */
  success(message, duration) {
    return showToast(message, { type: 'success', duration })
  },
  /** 错误通知（红色） */
  error(message, duration) {
    return showToast(message, { type: 'error', duration })
  },
  /** 警告通知（橙色） */
  warning(message, duration) {
    return showToast(message, { type: 'warning', duration })
  },
  /** 信息通知（蓝色） */
  info(message, duration) {
    return showToast(message, { type: 'info', duration })
  },
  /** 直接调用 */
  show: showToast,
  /** 当前所有 toast（只读） */
  get list() {
    return toasts
  }
}

export default toast
