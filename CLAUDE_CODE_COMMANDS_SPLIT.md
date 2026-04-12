# Claude Code 开发指令集（拆分版）

> 每条指令控制在 500 字以内，确保复制粘贴不被截断。
> 按编号顺序逐条发给 Claude Code，确认通过再发下一条。

---

## 5.1 材质 CRUD

```
创建 backend/routers/__init__.py（空文件）。
创建 backend/routers/dicts.py，先实现材质部分：

GET    /api/v1/dicts/materials — 列表，默认只返回 is_active=true，加 ?include_inactive=true 返回全部
POST   /api/v1/dicts/materials — 新增，校验 name 唯一，重复返回 HTTP 400
PUT    /api/v1/dicts/materials/:id — 编辑
DELETE /api/v1/dicts/materials/:id — 软删除 is_active=false

材质字段：name, sub_type, origin, cost_per_gram, sort_order, is_active。
```

## 5.2 器型 + 标签 CRUD

```
在 dicts.py 中继续添加器型和标签端点：

器型：
GET    /api/v1/dicts/types — 列表，返回含 spec_fields JSON
POST   /api/v1/dicts/types — 新增，name 唯一校验
DELETE /api/v1/dicts/types/:id — 软删除

标签：
GET    /api/v1/dicts/tags — 列表，支持 ?group_name= 筛选
POST   /api/v1/dicts/tags — 新增
DELETE /api/v1/dicts/tags/:id — 软删除

所有 DELETE 都是 is_active=false，不物理删除。
```

## 5.3 系统配置 + 启动验证

```
在 dicts.py 中添加系统配置端点：

GET  /api/v1/config — 返回所有配置项列表
PUT  /api/v1/config/:key — 更新单条配置 { "value": "新值" }

然后创建最小的 backend/main.py：挂载 dicts router + CORS(allow_origins=["*"]) + lifespan 中调 init_db()。

启动验证：
uvicorn main:app --reload --port 8000
访问 /api/v1/dicts/materials 确认返回36个材质。
访问 /api/v1/config 确认返回4条配置。
```

---

## 6.1 批次 CRUD

```
创建 backend/routers/batches.py。

GET  /api/v1/batches — 批次列表，支持 ?page&size&material_id 筛选分页
POST /api/v1/batches — 创建批次 { batch_code, material_id, type_id?, quantity, total_cost, cost_alloc_method, supplier_id?, purchase_date?, notes? }
PUT  /api/v1/batches/:id — 编辑批次

cost_alloc_method 只接受三个值：equal / by_weight / by_price。
batch_code 全局唯一，重复返回400。

写完后在 main.py 中挂载 batches router。
```

## 6.2 成本分摊算法

```
在 batches.py 中添加分摊端点：

POST /api/v1/batches/:id/allocate — 触发成本分摊

逻辑：
1. 校验该批次下 items 数量 == batch.quantity，否则 400 "货品未录完"
2. 根据 cost_alloc_method 执行：
   equal: 每件 = total_cost / quantity
   by_weight: 每件 = (该件weight / 总weight) × total_cost（所有件必须有weight）
   by_price: 每件 = (该件selling_price / 总selling_price) × total_cost
3. 保留2位小数，余数加到最后一件
4. 写入每件的 allocated_cost
```

## 6.3 分摊后定价 + 回本状态

```
分摊完成后，对每件还要做：
1. 从 sys_config 读 operating_cost_rate 和 markup_rate
2. floor_price = allocated_cost × (1 + operating_cost_rate)
3. 如果 selling_price 为0或空，则 selling_price = floor_price × (1 + markup_rate)

然后实现批次详情接口：
GET /api/v1/batches/:id — 返回批次信息 + 关联货品列表 + 回本状态

回本计算：
batch_revenue = SUM(该批次已售货品的 actual_price)
payback_rate = batch_revenue / total_cost
status: new(未售) / selling(销售中) / paid_back(已回本) / cleared(清仓完)
```

## 6.4 批次验证

```
验证批次功能：
1. POST /api/v1/batches 创建批次（material=银的id, quantity=3, total_cost=300, method=equal）
2. 记住返回的批次 id
3. 后续指令7写完 items 后再验证分摊
```

---

## 7.1 货品入库

```
创建 backend/routers/items.py。

POST /api/v1/items — 入库

请求体：sku_code?, name?, batch_id?, material_id, type_id?, cost_price?, selling_price, floor_price?, origin?, counter?, cert_no?, notes?, tag_ids:list[int]=[], spec:{weight?,metal_weight?,size?,bracelet_size?,bead_count?,bead_diameter?,ring_size?}, supplier_id?, purchase_date?

逻辑：
- 有 batch_id（通货）：cost_price 留空，allocated_cost 后续由分摊填充
- 无 batch_id（高货）：cost_price 必填，allocated_cost = cost_price
- 同时创建 item_spec 记录
- status 默认 in_stock
- sku_code 可不传，自动生成

在 main.py 中挂载 items router。
```

## 7.2 货品列表 + 详情

```
在 items.py 中添加：

GET /api/v1/items — 列表
筛选：?page&size&material_id&type_id&status&batch_id&counter&keyword
keyword 搜索 sku_code/name/cert_no/notes（OR + LIKE）
joinedload 预加载 material/type/spec/images
响应中计算 age_days = (today - purchase_date).days
分页返回

GET /api/v1/items/:id — 详情
返回完整信息含 spec/tags/images/batch信息
```

## 7.3 货品编辑 + 删除

```
在 items.py 中添加：

PUT    /api/v1/items/:id — 编辑（部分更新，含规格参数和 tag_ids 更新）
DELETE /api/v1/items/:id — 软删除 is_deleted=true

列表查询默认过滤 is_deleted=true 的记录。
```

## 7.4 货品验证

```
验证货品功能：

1. POST 入库一件高货：material_id=翡翠id, cost_price=5000, selling_price=12000
   确认返回 allocated_cost=5000, status=in_stock

2. POST 入库3件通货关联之前创建的批次，每件 selling_price=120, spec 中 weight=10

3. POST /api/v1/batches/{批次id}/allocate
   确认每件 allocated_cost=100.00

4. GET /api/v1/items 确认列表返回4件货品
```

---

## 8.1 单件销售

```
创建 backend/routers/sales.py。

POST /api/v1/sales — 单件销售
请求体：{ item_id, actual_price, channel, sale_date, customer_id?, note? }

逻辑（同一事务）：
1. 校验 item 存在、未删除、status == in_stock
2. 自动生成 sale_no（格式 s20250410001）
3. 创建 sale_records 记录
4. item.status = 'sold'
5. 非 in_stock 的货品返回 400

在 main.py 中挂载 sales router。
```

## 8.2 套装销售

```
在 sales.py 中添加：

POST /api/v1/sales/bundle — 套装销售
请求体：{ item_ids:[], total_price, alloc_method, channel, sale_date, customer_id?, note? }

逻辑（同一事务）：
1. 校验所有 item 可售（in_stock）
2. 创建 bundle_sales 记录
3. 按 alloc_method 分摊（目前只实现 by_ratio）：
   各件成交价 = (该件 selling_price / SUM所有selling_price) × total_price
4. 为每件创建 sale_record，bundle_id 指向 bundle_sales
5. 所有 item.status = 'sold'
```

## 8.3 销售列表

```
在 sales.py 中添加：

GET /api/v1/sales — 销售列表
支持 ?page&size&channel&start_date&end_date&customer_id
JOIN items 返回 item_sku, item_name
计算 gross_profit = actual_price - items.allocated_cost
按 sale_date 倒序
```

## 8.4 销售验证

```
验证销售功能：

1. POST /api/v1/sales 卖出高货，actual_price=10000, channel=store
   确认货品 status=sold

2. 再次 POST 同一件 → 应返回400

3. POST /api/v1/sales 卖出一件通货，actual_price=150
   GET /api/v1/batches/{id} 确认 payback_rate > 0

4. 入库2件新货（吊坠sell=1000, 链子sell=200）
   POST /api/v1/sales/bundle item_ids=[两件id], total_price=900, alloc_method=by_ratio
   确认吊坠成交750 链子成交150 两件均sold
```

---

## 9.1 贵金属市价查询 + 更新

```
创建 backend/routers/metal_prices.py。

GET /api/v1/metal-prices — 当前各贵金属市价（按 material 分组取最新记录）
PUT /api/v1/metal-prices/:material_id — 更新市价（插入新记录到 metal_prices 表）
GET /api/v1/metal-prices/history — 历史记录（?material_id&limit=20）

在 main.py 中挂载 metal_prices router。
```

## 9.2 批量调价

```
在 metal_prices.py 中添加：

POST /api/v1/metal-prices/reprice — 预览批量调价
逻辑：
1. 找到该材质最新 price_per_gram
2. 查出 material_id 匹配、status=in_stock 的货品
3. 工费 = 原 selling_price - item_spec.weight × 旧单价
4. 新 selling_price = weight × 新单价 + 工费
5. 返回 [{sku_code, name, old_price, new_price}]，不实际修改

POST /api/v1/metal-prices/reprice/confirm — 确认后执行实际修改
```

---

## 10.1 概览 + 批次回本看板

```
创建 backend/routers/dashboard.py。

GET /api/v1/dashboard/summary
返回：total_items(在库件数), total_stock_value(库存金额), month_revenue(本月销售), month_profit(本月毛利), month_sold_count(本月件数)

GET /api/v1/dashboard/batch-profit
所有批次回本状态列表，每条：batch_code, material_name, total_cost, quantity, sold_count, revenue, profit, payback_rate, status
支持 ?material_id 和 ?status 筛选

在 main.py 中挂载 dashboard router。
```

## 10.2 利润统计 + 趋势

```
在 dashboard.py 中添加：

GET /api/v1/dashboard/profit/by-category(?start_date&end_date)
按材质统计：material_name, revenue, cost, profit, margin_rate, count

GET /api/v1/dashboard/profit/by-channel(?start_date&end_date)
按渠道统计：channel, revenue, profit, count

GET /api/v1/dashboard/trend(?months=12&material_id=)
按月统计：month, revenue, count
```

## 10.3 压货预警

```
在 dashboard.py 中添加：

GET /api/v1/dashboard/stock-aging(?min_days=90)
查询 status=in_stock 且库龄 >= min_days 的货品
返回：sku_code, name, material_name, allocated_cost, selling_price, age_days, counter
按 age_days DESC 排序
顶部聚合返回 total_items 和 total_value

空数据时返回空列表，不报错。
```

---

## 11.1 客户管理

```
创建 backend/routers/customers.py。

GET  /api/v1/customers — 客户列表
POST /api/v1/customers — 新增（自动生成 customer_code: cst+YYYYMMDD+3位序号）
PUT  /api/v1/customers/:id — 编辑
GET  /api/v1/customers/:id — 详情，含该客户的购买记录列表

在 main.py 中挂载。
```

## 11.2 供应商管理

```
创建 backend/routers/suppliers.py。

GET  /api/v1/suppliers — 供应商列表
POST /api/v1/suppliers — 新增
PUT  /api/v1/suppliers/:id — 编辑

在 main.py 中挂载。
```

---

## 12.1 主入口整合

```
更新 backend/main.py，确保挂载全部 router：
dicts, batches, items, sales, metal_prices, dashboard, customers, suppliers

添加 GET /api/health 返回 {"status":"ok"}。
如果 backend/static/ 目录存在，挂载为静态文件。
图片目录 data/images 也挂载为静态文件。
```

## 12.2 启动验证

```
启动验证：
uvicorn main:app --reload --port 8000

检查：
1. /docs 页面所有端点可见
2. GET /api/v1/dicts/materials → 36条
3. GET /api/v1/dicts/types → 9条，每条含 spec_fields
4. GET /api/v1/config → 4条
5. GET /api/v1/metal-prices → 2条
6. GET /api/health → ok

全部通过后告诉我。
```

---

## 13.1 验证：字典

```
端到端验证第1组（字典）：

1. GET /api/v1/dicts/materials → 确认36条
2. POST /api/v1/dicts/materials {"name":"测试石"} → 成功
3. POST /api/v1/dicts/materials {"name":"测试石"} → 400重复
4. DELETE /api/v1/dicts/materials/{id} → 软删除
5. GET /api/v1/dicts/materials → 不含"测试石"

全部通过后告诉我。
```

## 13.2 验证：批次 + 通货

```
端到端验证第2组（批次+通货入库）：

6. POST /api/v1/batches 创建批次：material_id=银的id, quantity=3, total_cost=300, method=equal
7. POST /api/v1/items 入库3件通货，每件 batch_id=上一步id, selling_price=120, spec中weight=10
8. POST /api/v1/batches/{id}/allocate → 每件 allocated_cost=100.00
9. GET /api/v1/batches/{id} → payback_rate=0, status=new

全部通过后告诉我。
```

## 13.3 验证：高货 + 单件销售

```
端到端验证第3组（高货+销售）：

10. POST /api/v1/items 入库1件翡翠吊坠 cost_price=5000, selling_price=12000
11. POST /api/v1/sales item=步骤10的id, actual_price=10000, channel=store → sold
12. POST /api/v1/sales 同一件 → 应返回400

全部通过后告诉我。
```

## 13.4 验证：通货销售 + 回本

```
端到端验证第4组（通货回本）：

13. POST /api/v1/sales 卖出步骤7中的通货第1件, actual_price=150
14. GET /api/v1/batches/{步骤6的id} → payback_rate=0.50, status=selling
15. POST /api/v1/sales 卖出第2件, actual_price=200
16. GET /api/v1/batches/{id} → payback_rate≈1.17, status=paid_back

全部通过后告诉我。
```

## 13.5 验证：套装销售

```
端到端验证第5组（套装）：

17. POST /api/v1/items 入库2件新货：吊坠selling_price=1000, 链子selling_price=200
18. POST /api/v1/sales/bundle item_ids=[两件id], total_price=900, alloc_method=by_ratio
    确认吊坠成交750, 链子成交150, 两件均 status=sold

通过后告诉我。
```

## 13.6 验证：看板

```
端到端验证第6组（看板）：

19. GET /api/v1/dashboard/summary → total_items>0, month_revenue>0
20. GET /api/v1/dashboard/batch-profit → 包含步骤6的批次，status=paid_back

全部20步通过后报告完整结果。
```

---

## 14.1 提交代码

```
阶段1全部验证通过。请执行：

git add .
git commit -m "feat: 阶段1完成 - 后端API（14表/8路由/批次分摊/套装销售/贵金属市价/回本看板）"
git push origin main
```
