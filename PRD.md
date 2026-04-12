# PRD — 玉器店进销存管理系统 v2.1

> 本文档面向 AI 开发代理阅读，所有定义、规则、公式均为实现级精度，无需二次解读。

---

## 1. 系统定位

**一句话定义**：面向珠宝玉器实体店的单店单用户轻量进销存系统，核心产出是经营决策数据（批次回本状态、品类利润率、压货预警），而非财务报表。

**用户**：店主1人，兼管进货/销售/库存/分析。无多用户、无权限体系。

**部署**：极空间 NAS（Docker），局域网访问，不依赖外部云服务。

---

## 2. 业务模型

### 2.1 经营闭环

```
看数据（利润/压货/回本）→ 决定拿货（品类/数量/预算）→ 入库（批次/逐件/定价）→ 销售（议价/成交）→ 看数据
```

系统覆盖"入库→销售→看数据"三个环节，"决定拿货"由看板数据间接支持。

### 2.2 双轨库存模型

系统必须同时支持两种完全不同的货品管理模式：

| 维度 | 高货 | 通货 |
|------|------|------|
| 定义 | 唯一性商品（翡翠手镯、精品挂件） | 标准化商品（水晶手串、银饰） |
| 数量 | 1件 | 一批 N 件（通常7-15件） |
| 成本来源 | 直接录入 `cost_price` | 由批次 `total_cost` 通过分摊算法计算 `allocated_cost` |
| 入库流程 | 单步：直接录入所有字段 | 两步：①创建批次 → ②逐件录入 → 触发分摊 |
| 利润视角 | 单件毛利 | 批次回本状态 |
| 数据库标识 | `items.batch_id = NULL` | `items.batch_id IS NOT NULL` |

---

## 3. 核心概念定义

### 3.1 品类体系

三级动态分类，全部存数据库字典表，不得硬编码。

- **材质**（一级）：36种。每种可选 `sub_type`（子类，如银→990）、`origin`（产地，如翡翠→缅甸）、`cost_per_gram`（克重单价，贵金属用）。
- **器型**（二级）：9种。不绑定材质，跨材质通用。每种器型定义 `spec_fields`（JSON数组），声明该器型需要哪些规格参数字段。
- **标签**（三级）：多对多关联货品。按 `group_name` 分组（种水/颜色/工艺/题材）。

### 3.2 规格参数

规格参数由器型驱动，不同器型展示不同字段：

| 器型 | 必要参数 | 可选参数 |
|------|---------|---------|
| 手镯 | `bracelet_size`（圈口） | `weight` |
| 手串/手链、项链、脚链 | `bead_count`（粒数）、`bead_diameter`（珠子口径） | `weight` |
| 戒指 | `ring_size`（戒指尺寸） | `weight` |
| 挂件、吊坠、摆件 | — | `weight`、`size` |
| 耳饰 | — | `weight` |

**规则**：贵金属材质（黄金/银/18K金/铂金/k铂金）的货品，`weight` 字段为必填。其他材质中沉香、蜜蜡、碧玺的珠串类也需称重，但不强制。

### 3.3 货品状态

```
in_stock（在库）──→ sold（已售）
              └──→ returned（已退）
```

仅三种状态。"借出"功能不在当前版本范围内。

### 3.4 柜台

整数标识（如1、2、3），表示物理展示柜位置。仅用于筛选和展示，无业务逻辑依赖。

---

## 4. 定价引擎

### 4.1 公式

所有比例参数存 `sys_config` 表，不硬编码。

```
经营成本 = allocated_cost × operating_cost_rate
底价(floor_price) = allocated_cost + 经营成本
零售价(selling_price) = floor_price × (1 + markup_rate)
```

**默认参数值**：
- `operating_cost_rate` = 0.05（5%）
- `markup_rate` = 0.30（30%）

**行为**：
- 系统计算建议零售价，店主可手动覆盖。
- `floor_price` 和 `selling_price` 均可被手动修改，修改后不再受公式联动。
- 定价引擎在成本分摊完成后自动触发一次，填充 `floor_price` 和建议 `selling_price`。

### 4.2 贵金属市价管理

贵金属货品的零售价与市场克重单价挂钩。

**更新流程**：
1. 店主更新某贵金属材质的 `price_per_gram`
2. 系统查出所有关联该材质、`status=in_stock` 的货品
3. 计算新零售价：`新 selling_price = item_spec.weight × 新 price_per_gram + 工费`（工费 = 原 selling_price - 原克重×原单价，保持不变）
4. 返回受影响货品清单供店主确认
5. 店主确认后批量更新
6. 已售货品不受影响
7. 每次更新在 `metal_prices` 表插入一条历史记录

---

## 5. 成本分摊算法

适用对象：通货批次（`batches` 表的 `cost_alloc_method` 字段决定算法）。

**触发时机**：该批次下所有货品录入完毕后，调用 `/api/v1/batches/:id/allocate`。

**前置校验**：该批次下 `items` 记录数量 == `batches.quantity`，否则报错"货品未录完，当前 {n}/{quantity} 件"。

### 5.1 三种算法

**equal（均摊）**
```
每件 allocated_cost = batch.total_cost / batch.quantity
```
适用：珠子类（水晶/朱砂等），同款同质无差异。

**by_weight（按克重）**
```
total_weight = SUM(每件 item_spec.weight)
每件 allocated_cost = (该件 weight / total_weight) × batch.total_cost
```
适用：金属类（银饰/18K金等）。
前置校验：所有货品的 `item_spec.weight` 不得为 NULL 或 0。

**by_price（按售价比例）**
```
total_selling = SUM(每件 selling_price)
每件 allocated_cost = (该件 selling_price / total_selling) × batch.total_cost
```
适用：玉器吊坠/手镯等品相差异大的商品。
前置校验：所有货品的 `selling_price` 不得为 NULL 或 0。

### 5.2 分摊后操作

分摊完成后，对每件货品：
1. 写入 `items.allocated_cost`
2. 按定价引擎公式计算并写入 `items.floor_price`
3. 计算建议 `selling_price`（如果店主未手动设置过）

**精度要求**：分摊结果保留2位小数。分摊余数（四舍五入产生的差值）加到最后一件上，确保 `SUM(allocated_cost) == batch.total_cost`。

---

## 6. 批次回本模型

### 6.1 计算公式

```
batch_revenue = SUM(该批次所有 status=sold 的货品的 sale_records.actual_price)
batch_profit = batch_revenue - batch.total_cost
payback_rate = batch_revenue / batch.total_cost
```

### 6.2 状态判定

| 条件 | 状态 | 标签颜色 |
|------|------|---------|
| 已售数量 == 0 | `new`（未开始） | 灰色 |
| 0 < 已售数量 < quantity 且 payback_rate < 1.0 | `selling`（销售中） | 蓝色 |
| payback_rate >= 1.0 且 已售数量 < quantity | `paid_back`（已回本） | 绿色 |
| 已售数量 == quantity | `cleared`（清仓完毕） | 绿色 |

### 6.3 核心原则

- 回本判断**只看已收回现金**，不估算在库商品的价值。
- 回本后尾货可任意定价促销，单件亏损是被允许的。
- 系统同时展示两个维度：单件毛利（`actual_price - allocated_cost`）和批次回本状态。

---

## 7. 销售管理

### 7.1 单件销售

**输入**：`item_id`、`actual_price`（成交价）、`channel`（store/wechat）、`sale_date`、`customer_id?`、`note?`

**处理逻辑**（同一事务）：
1. 校验 `items.is_deleted == false`
2. 校验 `items.status == 'in_stock'`（非在库不可售）
3. 自动生成 `sale_no`（规则：`s` + YYYYMMDD + 3位序号）
4. 创建 `sale_records` 记录
5. 更新 `items.status = 'sold'`

### 7.2 套装销售

**场景**：客户买吊坠+链子，合起来议价得一个总价。

**输入**：`item_ids[]`、`total_price`、`alloc_method`（by_ratio/chain_at_cost）、`channel`、`sale_date`、`customer_id?`、`note?`

**处理逻辑**（同一事务）：
1. 校验所有货品可售
2. 创建 `bundle_sales` 记录
3. 按 `alloc_method` 分摊价格到各件：
   - **by_ratio**（按售价比例）：`各件成交价 = (该件 selling_price / SUM(selling_price)) × total_price`
   - **chain_at_cost**（链子按原价）：链子/绳子类（需标记）按 selling_price 计，剩余金额全部分给主件
4. 为每件创建 `sale_records`（`bundle_id` 指向 bundle_sales.id）
5. 所有货品 `status = 'sold'`

### 7.3 议价字段

`sale_records.actual_price`（成交价）与 `items.selling_price`（标价）之差即为议价幅度，无需额外字段。

---

## 8. 功能需求

### 8.1 P0 — 核心功能（阶段1-2）

#### 8.1.1 字典管理
- 材质 CRUD（含 sub_type、origin、cost_per_gram），软删除
- 器型 CRUD（含 spec_fields JSON），软删除
- 标签 CRUD（按 group_name 分组），软删除
- 系统配置读写（key-value）
- 停用的字典项不出现在录入表单中，但已关联的历史数据不受影响
- 初次启动自动插入种子数据（见附录）

#### 8.1.2 批次管理（通货专用）
- 创建批次：batch_code、材质、器型、数量、总价、分摊算法、供应商、进货日期
- 批次下逐件入库货品
- 触发成本分摊（前置校验：货品数量 == batch.quantity）
- 批次详情：含关联货品列表 + 回本状态实时计算

#### 8.1.3 货品入库
- 高货入库：单步，直接录入 cost_price 和所有字段
- 通货入库：关联 batch_id，allocated_cost 由分摊算法填充
- SKU 自动生成：`{材质缩写}-{YYYYMMDD}-{3位序号}`
- 入库时同时创建 item_spec 记录（根据器型的 spec_fields 展示对应字段）
- 入库后 status = in_stock

#### 8.1.4 库存查看
- 列表字段：SKU、名称、批次号、材质、器型、分摊成本、零售价、库龄、柜台、缩略图
- 筛选维度：材质、器型、状态、批次、柜台、关键词（SKU/名称/证书/备注）
- 分页：默认20条/页
- 详情页：全部字段 + 规格参数 + 图片列表 + 批次信息（如有）
- 移动端卡片视图，桌面端表格视图

#### 8.1.5 销售出库
- 单件销售（7.1 节逻辑）
- 套装销售（7.2 节逻辑）
- 已售不可重复出库

#### 8.1.6 贵金属市价管理
- 查看/编辑各贵金属材质当前克重单价
- 更新后预览受影响货品清单
- 确认后批量重算零售价
- 保留市价变动历史记录

### 8.2 P1 — 分析功能（阶段3）

#### 8.2.1 批次回本看板
- 所有通货批次的回本状态列表
- 每批次显示：编号、材质、总成本、数量、已售数、已回款、回本进度%、状态标签
- 支持按回本进度/材质/时间排序和筛选
- 点击批次可展开查看该批次下所有货品

#### 8.2.2 利润看板
- 按材质：销售额、成本、毛利、毛利率、件数
- 按渠道：门店 vs 微信
- 时间范围：本月/本季/本年/自定义
- 图表展示

#### 8.2.3 压货预警
- 在库超过 `aging_threshold_days`（默认90天）的货品列表
- 按库龄降序
- 显示占用资金（SUM of allocated_cost）
- 高成本+长库龄的货品突出标记

#### 8.2.4 图片管理
- 入库时上传多张图片
- 设置封面图
- 自动生成缩略图（400×400）
- 快速查找某件货的图片（店主需发微信给客户）

#### 8.2.5 客户管理
- 客户档案：姓名、电话、微信号、备注
- 销售记录可关联客户
- 查看客户购买历史

### 8.3 P2 — 扩展功能（阶段4+）

- 供应商管理
- 数据导出（Excel）
- 镶嵌定制业务（独立模块）

---

## 9. 非功能需求

| 需求 | 指标 |
|------|------|
| 响应式 | 所有页面适配 375px 宽度（手机优先） |
| 性能 | 2000件数据量级，列表加载 < 1秒 |
| 备份 | SQLite单文件 + images目录，极空间文件同步即可 |
| 离线 | 本地NAS部署，无外部依赖 |
| 参数化 | 所有业务参数走 sys_config，不硬编码 |

---

## 10. 开发阶段

| 阶段 | 范围 | 完成标志 |
|------|------|----------|
| 1 | 14张表 + 8个路由模块 + 全部API | Swagger UI 端到端验证20步通过 |
| 2 | 前端核心页面 + 移动端适配 | 浏览器完成完整业务流程 |
| 3 | 批次回本看板 + 利润看板 + 压货预警 | 店主可做经营决策 |
| 4 | 图片 + 客户 + 导出 + Docker | 极空间一键部署 |

---

## 附录A：种子数据

### 材质（36种）

```
黄金(sub:k999) | 银(sub:990, gram:25) | k铂金 | 铂金 | 18K金(gram:780)
翡翠(origin:缅甸) | 和田玉 | 珍珠(sub:淡水珠, origin:浙江) | 朱砂 | 蜜蜡
碧玺 | 青金石 | 黑曜石 | 金曜石 | 玛瑙 | 琥珀
锆石(origin:梧州) | 斑彩螺(origin:意大利) | 金虎眼 | 虎眼
粉晶 | 紫水晶 | 莹石 | 绿幽灵 | 白幽灵 | 彩幽灵
金发晶 | 钛晶 | 巴西黄水晶 | 人工黄水晶 | 红幽灵
蓝晶石 | 海蓝宝 | 天河石 | 红绿宝石共生 | 车花透辉石
```

### 器型（9种，含 spec_fields）

```json
{ "name": "手镯",      "spec_fields": ["weight","bracelet_size"] }
{ "name": "挂件",      "spec_fields": ["weight","size"] }
{ "name": "吊坠",      "spec_fields": ["weight","size"] }
{ "name": "手串/手链", "spec_fields": ["weight","bead_count","bead_diameter"] }
{ "name": "项链",      "spec_fields": ["weight","bead_count","bead_diameter"] }
{ "name": "脚链",      "spec_fields": ["weight","bead_count","bead_diameter"] }
{ "name": "戒指",      "spec_fields": ["weight","ring_size"] }
{ "name": "耳饰",      "spec_fields": ["weight"] }
{ "name": "摆件",      "spec_fields": ["weight","size"] }
```

### 标签（22个，4组）

```
种水: 玻璃种, 冰种, 糯冰种, 糯种, 豆种
颜色: 满绿, 飘花, 紫罗兰, 黄翡, 墨翠, 无色
工艺: 手工雕, 机雕, 素面
题材: 观音, 佛公, 平安扣, 如意, 山水, 花鸟
```

### 系统配置（4条）

```
operating_cost_rate = "0.05"    # 经营成本率
markup_rate = "0.30"            # 零售价上浮比例
aging_threshold_days = "90"     # 压货预警天数
default_alloc_method = "equal"  # 默认分摊算法
```

### 贵金属初始市价（2条）

```
18K金: 780 元/克
银(990): 25 元/克
```
