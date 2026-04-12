# BundleSaleDialog 组件手动测试用例

## 测试概述

**目标**：验证 BundleSaleDialog 组件的前后端关联功能、业务场景覆盖和移动端适配  
**测试对象**：套装出库功能（多件货品合并销售，按比例分摊总价）  
**测试类型**：手动功能测试、集成测试、场景化测试  
**测试环境**：本地开发环境

## 测试环境准备

### 1. 启动后端服务器
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端开发服务器
```bash
cd frontend
npm run dev
```

### 3. 访问应用
- 打开浏览器访问：http://localhost:5173
- 登录系统（如有需要）
- 进入库存管理页面

### 4. 测试数据准备
确保数据库中有以下测试数据：
- 至少3件在库货品（状态为 `in_stock`）
  - 建议：1件吊坠（翡翠，售价 ¥1000）
  - 建议：1件链子（银，售价 ¥200）
  - 建议：1件手镯（和田玉，售价 ¥1500）
- 至少2个客户记录

## 测试场景设计

### 场景1：基础套装销售流程 ✅
**目标**：验证套装销售完整流程（前端+后端）
**前提条件**：选择2件及以上在库货品

| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|----------|----------|
| 1 | 在库存列表页面，勾选2件在库货品（如吊坠和链子） | 货品复选框被选中 | |
| 2 | 点击"套装出库"按钮 | BundleSaleDialog弹窗正确打开 | |
| 3 | 验证弹窗内容 | - 显示"套装出库"标题<br>- 显示"已选 2 件货品"<br>- 显示总标价（¥1200.00）<br>- 显示已选货品列表 | |
| 4 | 输入套装总价：¥900 | - 输入框接收¥900<br>- 下方显示总标价对比 | |
| 5 | 验证价格分摊预览 | - 显示按售价比例分摊预览<br>- 吊坠：约¥750.00 (1000/1200×900)<br>- 链子：约¥150.00 (200/1200×900) | |
| 6 | 选择销售渠道：门店 | 单选按钮被选中 | |
| 7 | 选择成交日期（默认为今天） | 日期选择器显示正确日期 | |
| 8 | 选择客户（可选） | 下拉列表显示客户列表 | |
| 9 | 填写备注（可选） | 文本框接收输入 | |
| 10 | 点击"确认出库"按钮 | - 显示加载状态<br>- 调用后端API `/api/v1/sales/bundle`<br>- 成功后弹窗关闭<br>- 页面显示成功提示 | |
| 11 | 验证后端数据更新 | - 货品状态更新为 `sold`<br>- 创建套装销售记录<br>- 创建销售子记录<br>- 价格分摊正确（¥750, ¥150） | |

### 场景2：不同分摊方法测试 ✅
**目标**：验证不同分摊方法的UI提示和功能
**前提条件**：选择2件货品

| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|----------|----------|
| 1 | 打开套装出库弹窗，选择2件货品（吊坠+链子） | 弹窗正常打开 | |
| 2 | 输入总价：¥900 | 显示按比例分摊预览 | |
| 3 | 查看分摊方式选项 | - 选项1：按售价比例分摊（默认）<br>- 选项2：链子按原价，剩余给主件 | |
| 4 | 选择"链子按原价，剩余给主件" | - 下方显示黄色提示框<br>- 内容："链子按原价分摊：链子/绳子类货品将按原价计算，剩余金额全部分配给主件。具体分摊结果将在提交后由系统计算。" | |
| 5 | 保持此设置并提交表单 | - 调用API时 `alloc_method` 参数为 `chain_at_cost`<br>- 后端按链子原价(¥200)、剩余(¥700)给主件计算 | |

### 场景3：边界条件测试 ✅
#### 子场景3.1：单件货品套装出库
| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|----------|----------|
| 1 | 在库存列表勾选仅1件货品 | 复选框被选中 | |
| 2 | 点击"套装出库"按钮 | - 可能：按钮禁用/不可点击<br>- 可能：点击后显示错误提示"请至少选择2件货品" | |

#### 子场景3.2：总价边界值
| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|----------|----------|
| 1 | 选择2件货品，打开弹窗 | 弹窗正常打开 | |
| 2 | 总价输入：0（或负数） | - 可能：输入框拒绝无效值<br>- 可能：显示验证错误<br>- "确认出库"按钮应为禁用状态 | |
| 3 | 总价输入：0.01（极小值） | 输入被接受 | |
| 4 | 总价输入：999999.99（极大值） | 输入被接受 | |

#### 子场景3.3：溢价销售
| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|----------|----------|
| 1 | 选择2件货品，总标价¥1200 | 显示总标价 | |
| 2 | 输入总价：¥1500（大于总标价） | 输入被接受 | |
| 3 | 点击"确认出库" | 后端正常处理溢价销售 | |

### 场景4：表单验证与错误处理 ✅
#### 子场景4.1：必填项验证
| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|----------|----------|
| 1 | 不填写总价，直接点击"确认出库" | - 显示错误提示"请填写有效的套装总价"<br>- 阻止表单提交 | |
| 2 | 填写总价：0，点击提交 | 同样显示错误提示 | |

#### 子场景4.2：API错误处理
| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|----------|----------|
| 1 | 正常填写表单，但停止后端服务器 | 保持后端停止状态 | |
| 2 | 点击"确认出库" | - 显示网络错误提示<br>- 不关闭弹窗<br>- 保持表单数据 | |
| 3 | 重新启动后端服务器 | 后端恢复运行 | |
| 4 | 再次点击"确认出库" | 表单正常提交 | |

#### 子场景4.3：货品状态变化
| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|----------|----------|
| 1 | 选择2件在库货品 | 货品正常选中 | |
| 2 | 在其他浏览器/标签页将其中一件货品售出 | 货品状态变为 `sold` | |
| 3 | 在当前页面打开套装出库弹窗 | 弹窗正常打开 | |
| 4 | 填写表单并提交 | - 后端应验证货品状态<br>- 返回错误提示"货品状态已变更" | |

### 场景5：移动端适配测试 ✅
**前提**：使用浏览器开发者工具模拟移动设备

| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|----------|----------|
| 1 | 设置视口为 iPhone 12 (390×844) | 页面响应式布局 | |
| 2 | 打开库存页面 | 列表适配小屏幕 | |
| 3 | 勾选2件货品，点击"套装出库" | - 弹窗从底部滑出<br>- 圆角：上边20px<br>- 高度：最大90vh<br>- 内容可滚动 | |
| 4 | 表单布局检查 | - 表单项纵向排列<br>- 按钮纵向或适应宽度<br>- 文字大小可读 | |
| 5 | 点击弹窗外部遮罩 | 弹窗关闭，触发 `close` 事件 | |

### 场景6：用户体验流程 ✅
| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|----------|----------|
| 1 | 正常提交成功后 | - 弹窗自动关闭<br>- 页面显示成功提示<br>- 库存列表刷新（已售货品不再显示） | |
| 2 | 点击"取消"按钮 | - 弹窗关闭，无任何操作<br>- 表单数据丢弃 | |
| 3 | 打开弹窗，填写数据后关闭 | 表单数据暂存？ | |
| 4 | 重新打开弹窗 | 表单应重置为初始状态 | |

### 场景7：并发操作测试 ✅
| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|----------|----------|
| 1 | 在浏览器标签页A勾选货品1和2 | 正常选中 | |
| 2 | 在浏览器标签页B勾选货品2和3 | 正常选中 | |
| 3 | 在标签页A提交套装销售（货品1+2） | 销售成功，货品1和2状态更新 | |
| 4 | 立即在标签页B提交套装销售（货品2+3） | - 后端应检测货品2已售出<br>- 返回错误，阻止重复销售 | |

## 测试数据验证

### 后端数据库检查（销售完成后）

1. **检查 `bundle_sales` 表**
   ```sql
   SELECT * FROM bundle_sales ORDER BY created_at DESC LIMIT 1;
   ```
   - 应有新记录，包含：bundle_no, total_price, alloc_method
   - `alloc_method` 应与前端选择一致

2. **检查 `sale_records` 表**
   ```sql
   SELECT sr.*, i.sku_code, i.selling_price 
   FROM sale_records sr
   JOIN items i ON sr.item_id = i.id
   WHERE sr.bundle_sale_id = [上一步获取的ID]
   ORDER BY sr.id;
   ```
   - 应有2条记录（对应2件货品）
   - `actual_price` 应与前端预览一致

3. **检查 `items` 表**
   ```sql
   SELECT id, sku_code, status FROM items WHERE id IN ([货品ID列表]);
   ```
   - 货品状态应为 `sold`
   - 销售时间应更新

### 价格计算验证

**按比例分摊公式**：
```
单件分配价 = (该件售价 ÷ 总售价) × 套装总价
```

**示例计算**：
- 吊坠售价：¥1000
- 链子售价：¥200  
- 总售价：¥1200
- 套装总价：¥900

```
吊坠分配价 = (1000 ÷ 1200) × 900 = ¥750.00
链子分配价 = (200 ÷ 1200) × 900 = ¥150.00
```

## 测试结果记录表

复制以下表格记录测试结果：

### 场景完成情况

| 场景编号 | 场景名称 | 测试状态 | 问题描述 | 备注 |
|----------|----------|----------|----------|------|
| 1 | 基础套装销售流程 | | | |
| 2 | 不同分摊方法测试 | | | |
| 3.1 | 单件货品套装出库 | | | |
| 3.2 | 总价边界值 | | | |
| 3.3 | 溢价销售 | | | |
| 4.1 | 必填项验证 | | | |
| 4.2 | API错误处理 | | | |
| 4.3 | 货品状态变化 | | | |
| 5 | 移动端适配测试 | | | |
| 6 | 用户体验流程 | | | |
| 7 | 并发操作测试 | | | |

### 问题汇总

| 问题ID | 严重程度 | 场景 | 问题描述 | 复现步骤 | 期望结果 | 实际结果 |
|--------|----------|------|----------|----------|----------|----------|
| 1 | 高/中/低 | | | | | |
| 2 | 高/中/低 | | | | | |

## 自动化测试覆盖

### 已自动化的测试
1. **前端单元测试**（10个用例）✅
   - 渲染基础信息
   - 价格分摊预览计算
   - 表单验证逻辑
   - API调用验证
   - 事件触发验证

2. **后端集成测试**（场景4）✅
   - 套装销售API功能
   - 价格分摊计算
   - 数据一致性

### 需要手动测试的部分
1. **UI/UX交互**：视觉效果、动画、响应式
2. **端到端流程**：从库存列表到销售完成的完整流程
3. **真实网络环境**：API延迟、网络错误
4. **多浏览器兼容性**：Chrome、Firefox、Safari
5. **真实移动设备**：触摸交互、不同屏幕尺寸

## 测试工具与命令

### 前端测试命令
```bash
# 运行单元测试
cd frontend
npm run test:unit

# 运行测试并生成覆盖率报告
npm run test:unit:coverage

# 打开测试UI界面
npm run test:unit:ui
```

### 后端测试命令
```bash
# 运行集成测试
cd backend
python test_sales.py

# 验证套装销售功能
python validate_bundle_sales.py
```

### 开发服务器
```bash
# 启动后端
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动前端
cd frontend
npm run dev
```

## 注意事项

1. **测试数据隔离**：建议在测试前备份数据库，或在测试数据库上进行
2. **并发测试风险**：并发操作可能产生脏数据，建议使用事务或锁机制
3. **移动端测试**：除了模拟器，建议在实际设备上测试触摸交互
4. **浏览器兼容性**：测试主流浏览器的最新版本
5. **性能考虑**：货品数量过多时（如100+件），列表渲染和价格计算性能

## 附录：测试检查清单

### ✅ 基础功能检查
- [ ] 弹窗能正常打开/关闭
- [ ] 能正确显示已选货品信息
- [ ] 价格分摊预览计算正确
- [ ] 表单能正常提交
- [ ] 提交后弹窗自动关闭
- [ ] 页面显示成功提示

### ✅ 数据验证检查  
- [ ] 后端正确创建套装销售记录
- [ ] 后端正确创建销售子记录
- [ ] 货品状态正确更新为 `sold`
- [ ] 价格分摊计算与前端预览一致
- [ ] 所有必填字段都存储到数据库

### ✅ 错误处理检查
- [ ] 表单验证阻止无效提交
- [ ] 显示友好的错误提示
- [ ] 网络错误时有适当反馈
- [ ] 并发操作有保护机制

### ✅ 用户体验检查
- [ ] 移动端布局合理
- [ ] 触摸交互流畅
- [ ] 加载状态明显
- [ ] 成功/失败反馈清晰
- [ ] 表单重置功能正常

### ✅ 性能检查
- [ ] 弹窗打开速度（<500ms）
- [ ] 价格计算响应（实时）
- [ ] 表单提交响应（<2s）
- [ ] 移动端滑动流畅

---

## 附录：测试数据准备脚本

### 数据库初始化（如果使用SQLite）

创建测试货品和客户数据的SQL脚本：

```sql
-- 1. 确保有必要的材质
INSERT OR IGNORE INTO dict_material (name, is_active) VALUES 
  ('翡翠', 1),
  ('银', 1),
  ('和田玉', 1);

-- 2. 获取材质ID（假设已存在）
SELECT id, name FROM dict_material WHERE name IN ('翡翠', '银', '和田玉');

-- 3. 创建测试货品（状态：in_stock）
-- 注意：需要替换实际的material_id值
INSERT INTO items (sku_code, name, material_id, selling_price, status, purchase_date, created_at, updated_at) VALUES
  ('TEST001', '吊坠', [翡翠材质ID], 1000.00, 'in_stock', date('now'), datetime('now'), datetime('now')),
  ('TEST002', '链子', [银材质ID], 200.00, 'in_stock', date('now'), datetime('now'), datetime('now')),
  ('TEST003', '手镯', [和田玉材质ID], 1500.00, 'in_stock', date('now'), datetime('now'), datetime('now')),
  ('TEST004', '耳环', [银材质ID], 300.00, 'in_stock', date('now'), datetime('now'), datetime('now')),
  ('TEST005', '戒指', [翡翠材质ID], 800.00, 'in_stock', date('now'), datetime('now'), datetime('now'));

-- 4. 创建测试客户
INSERT INTO customers (name, phone, wechat, created_at, updated_at) VALUES
  ('张三', '13800138000', 'zhangsan_wechat', datetime('now'), datetime('now')),
  ('李四', '13900139000', 'lisi_wechat', datetime('now'), datetime('now')),
  ('王五', '13700137000', NULL, datetime('now'), datetime('now'));

-- 5. 验证数据
SELECT 
  i.id, i.sku_code, i.name, dm.name as material_name, i.selling_price, i.status
FROM items i
JOIN dict_material dm ON i.material_id = dm.id
WHERE i.sku_code LIKE 'TEST%'
ORDER BY i.id;

SELECT id, name, phone, wechat FROM customers ORDER BY id;
```

### 使用Python脚本准备数据

创建 `prepare_test_data.py`：

```python
#!/usr/bin/env python3
"""
测试数据准备脚本
执行：python prepare_test_data.py
"""

import sqlite3
from datetime import datetime

def prepare_test_data():
    # 连接到数据库（根据实际路径调整）
    conn = sqlite3.connect('data/jade.db')
    cursor = conn.cursor()
    
    print("=== 准备BundleSaleDialog测试数据 ===")
    
    # 1. 确保材质存在
    cursor.execute("INSERT OR IGNORE INTO dict_material (name, is_active) VALUES (?, ?)", ('翡翠', 1))
    cursor.execute("INSERT OR IGNORE INTO dict_material (name, is_active) VALUES (?, ?)", ('银', 1))
    cursor.execute("INSERT OR IGNORE INTO dict_material (name, is_active) VALUES (?, ?)", ('和田玉', 1))
    
    # 2. 获取材质ID
    cursor.execute("SELECT id, name FROM dict_material WHERE name IN ('翡翠', '银', '和田玉')")
    materials = {row[1]: row[0] for row in cursor.fetchall()}
    print(f"材质ID映射: {materials}")
    
    # 3. 创建测试货品
    test_items = [
        ('TEST001', '吊坠', materials['翡翠'], 1000.00),
        ('TEST002', '链子', materials['银'], 200.00),
        ('TEST003', '手镯', materials['和田玉'], 1500.00),
        ('TEST004', '耳环', materials['银'], 300.00),
        ('TEST005', '戒指', materials['翡翠'], 800.00),
    ]
    
    for sku_code, name, material_id, price in test_items:
        cursor.execute("""
            INSERT OR IGNORE INTO items 
            (sku_code, name, material_id, selling_price, status, purchase_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, date('now'), datetime('now'), datetime('now'))
        """, (sku_code, name, material_id, price, 'in_stock'))
    
    # 4. 创建测试客户
    test_customers = [
        ('张三', '13800138000', 'zhangsan_wechat'),
        ('李四', '13900139000', 'lisi_wechat'),
        ('王五', '13700137000', None),
    ]
    
    for name, phone, wechat in test_customers:
        cursor.execute("""
            INSERT OR IGNORE INTO customers (name, phone, wechat, created_at, updated_at)
            VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """, (name, phone, wechat))
    
    # 提交事务
    conn.commit()
    
    # 5. 验证数据
    print("\n=== 验证测试数据 ===")
    
    cursor.execute("""
        SELECT i.id, i.sku_code, i.name, dm.name as material_name, 
               i.selling_price, i.status
        FROM items i
        JOIN dict_material dm ON i.material_id = dm.id
        WHERE i.sku_code LIKE 'TEST%'
        ORDER BY i.id
    """)
    print("测试货品：")
    for row in cursor.fetchall():
        print(f"  ID:{row[0]} {row[1]} - {row[2]} ({row[3]}) ¥{row[4]:.2f} [{row[5]}]")
    
    cursor.execute("SELECT id, name, phone, wechat FROM customers ORDER BY id")
    print("\n测试客户：")
    for row in cursor.fetchall():
        wechat_info = f", 微信:{row[3]}" if row[3] else ""
        print(f"  ID:{row[0]} {row[1]}, 电话:{row[2]}{wechat_info}")
    
    # 关闭连接
    conn.close()
    print("\n=== 测试数据准备完成 ===")

if __name__ == '__main__':
    prepare_test_data()
```

### 快速重置测试数据

如果需要清理测试数据，可以使用以下SQL：

```sql
-- 谨慎执行：删除测试货品（仅删除TEST开头的）
DELETE FROM items WHERE sku_code LIKE 'TEST%';

-- 谨慎执行：删除测试客户
DELETE FROM customers WHERE name IN ('张三', '李四', '王五');

-- 检查删除结果
SELECT COUNT(*) as item_count FROM items WHERE sku_code LIKE 'TEST%';
SELECT COUNT(*) as customer_count FROM customers WHERE name IN ('张三', '李四', '王五');
```

---

**测试执行人**：__________________  
**测试日期**：__________________  
**测试环境**：__________________  
**总体结论**：✅ 通过 / ⚠️ 部分问题 / ❌ 未通过