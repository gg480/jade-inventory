import '@testing-library/jest-dom'
import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// 全局测试配置
config.global.stubs = {
  // 全局stub配置，可根据需要添加
}

// 全局mocks
global.console = {
  ...console,
  // 可以重定向某些console方法
  error: vi.fn(),
  warn: vi.fn(),
}

// 添加测试辅助函数
global.setupTest = () => {
  // 测试辅助函数
}