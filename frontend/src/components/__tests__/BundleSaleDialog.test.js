import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BundleSaleDialog from '../BundleSaleDialog.vue'
import api from '../../api' // 这将自动使用__mocks__中的模拟版本
import mockApi from '../../api/__mocks__/index.js' // 直接导入mock对象
import { setupDefaultMocks, resetAllMocks } from '../../api/__mocks__/index.js'

// 确保api模块被模拟
vi.mock('../../api')

describe('BundleSaleDialog', () => {
  const mockItems = [
    { id: 1, sku_code: 'TEST001', material_name: '翡翠', name: '吊坠', selling_price: 1000 },
    { id: 2, sku_code: 'TEST002', material_name: '银', name: '链子', selling_price: 200 }
  ]

  let wrapper

  beforeEach(() => {
    // 重置所有mocks
    resetAllMocks()
    // 设置默认mock实现
    setupDefaultMocks()

    wrapper = mount(BundleSaleDialog, {
      props: {
        items: mockItems,
        visible: true
      }
    })
  })

  it('渲染基础信息', () => {
    expect(wrapper.text()).toContain('套装出库')
    expect(wrapper.text()).toContain('已选 2 件货品')
    expect(wrapper.text()).toContain('总标价：¥1200.00')
  })

  it('显示已选货品列表', () => {
    expect(wrapper.text()).toContain('TEST001')
    expect(wrapper.text()).toContain('TEST002')
    expect(wrapper.text()).toContain('吊坠')
    expect(wrapper.text()).toContain('链子')
    expect(wrapper.text()).toContain('¥1000.00')
    expect(wrapper.text()).toContain('¥200.00')
  })

  it('价格分摊预览计算正确', async () => {
    // 设置总价
    const totalPriceInput = wrapper.find('input[type="number"]')
    await totalPriceInput.setValue('900')

    // 验证预览计算
    expect(wrapper.text()).toContain('¥750.00') // 吊坠分配
    expect(wrapper.text()).toContain('¥150.00') // 链子分配

    // 验证分配方式显示
    expect(wrapper.text()).toContain('按售价比例分摊')
  })

  it('表单验证阻止无效提交 - 空总价', async () => {
    // 不填总价直接提交
    const submitButton = wrapper.find('button[type="submit"]')
    await submitButton.trigger('click')

    // 应该阻止提交并显示错误
    expect(mockApi.sales.createBundleSale).not.toHaveBeenCalled()
  })

  it('表单验证阻止无效提交 - 零总价', async () => {
    // 设置总价为0
    await wrapper.find('input[type="number"]').setValue('0')

    const submitButton = wrapper.find('button[type="submit"]')
    await submitButton.trigger('click')

    // 应该阻止提交
    expect(mockApi.sales.createBundleSale).not.toHaveBeenCalled()
  })

  it('成功提交调用正确API', async () => {
    // 填写有效数据
    await wrapper.find('input[type="number"]').setValue('900')
    await wrapper.find('select').setValue('store')
    await wrapper.find('input[type="date"]').setValue('2024-04-12')

    // 提交表单
    await wrapper.find('form').trigger('submit.prevent')

    // 验证API调用参数
    expect(mockApi.sales.createBundleSale).toHaveBeenCalledWith({
      item_ids: [1, 2],
      total_price: 900,
      alloc_method: 'by_ratio',
      channel: 'store',
      sale_date: '2024-04-12',
      customer_id: undefined,
      note: ''
    })
  })

  it('切换分摊方式更新UI', async () => {
    // 默认是按比例分摊
    expect(wrapper.text()).toContain('按售价比例分摊')

    // 先设置总价，否则预览区域不会显示
    await wrapper.find('input[type="number"]').setValue('900')

    // 切换到链子按原价
    const chainAtCostRadio = wrapper.findAll('input[type="radio"]')[1]
    await chainAtCostRadio.setValue(true)

    // 应该显示链子按原价的提示
    expect(wrapper.text()).toContain('链子按原价分摊')
  })

  it('关闭对话框触发close事件', async () => {
    const cancelButton = wrapper.find('button.btn-secondary')
    await cancelButton.trigger('click')

    // 应该触发close事件
    expect(wrapper.emitted()).toHaveProperty('close')
  })

  it('加载客户列表', async () => {
    // 组件加载时会调用getCustomers
    expect(mockApi.customers.getCustomers).toHaveBeenCalled()
  })

  it('表单重置功能', async () => {
    // 先填写一些数据
    await wrapper.find('input[type="number"]').setValue('900')
    await wrapper.find('select').setValue('store')
    await wrapper.find('input[type="date"]').setValue('2024-04-12')
    await wrapper.find('textarea').setValue('测试备注')

    // 关闭再重新打开应该重置表单
    await wrapper.setProps({ visible: false })
    await wrapper.setProps({ visible: true })

    // 验证表单已重置
    expect(wrapper.find('input[type="number"]').element.value).toBe('')
    expect(wrapper.find('textarea').element.value).toBe('')
  })
})