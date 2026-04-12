# TECH_SPEC v2 — 技术规格

## 1. 架构

```
浏览器（手机/电脑）
    │ HTTP
    ▼
FastAPI (port 8000)
    ├── /api/v1/*          → JSON API
    ├── /data/images/*     → 静态图片
    └── /*                 → Vue SPA（生产模式）
    │
    ▼
SQLite (data/jade.db)
```

单进程部署，极空间 Docker 直接映射端口。

## 2. 数据模型

### 2.1 ER 关系

```
dict_material  1──N  batches
dict_material  1──N  items
dict_material  1──N  metal_prices
dict_type      1──N  items
dict_tag       M──N  items          (通过 item_tag)
suppliers      1──N  batches
batches        1──N  items
items          1──1  item_spec
items          1──N  item_images
items          1──N  sale_records
customers      1──N  sale_records
bundle_sales   1──N  sale_records
```

### 2.2 表结构（14张表）

#### dict_material（材质字典）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 材质名称 |
| sub_type | VARCHAR(50) | NULLABLE | 材质子类（如990、淡水珠、k999） |
| origin | VARCHAR(100) | NULLABLE | 默认产地（如缅甸、浙江） |
| cost_per_gram | FLOAT | NULLABLE | 克重单价（贵金属用，如银25、18K金780） |
| sort_order | INTEGER | DEFAULT 0 | 排序权重 |
| is_active | BOOLEAN | DEFAULT TRUE | 软删除 |

#### dict_type（器型字典）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 器型名称 |
| spec_fields | TEXT | NULLABLE | JSON，该器型需要的规格字段列表 |
| sort_order | INTEGER | DEFAULT 0 | |
| is_active | BOOLEAN | DEFAULT TRUE | |

spec_fields 示例：
- 手镯: `["weight","bracelet_size"]`
- 手串: `["weight","bead_count","bead_diameter"]`
- 戒指: `["weight","ring_size"]`

注意：器型不再强制挂在材质下面（v1 的 material_id FK 取消），因为同一种器型可跨材质使用。

#### dict_tag（标签字典）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 标签名称 |
| group_name | VARCHAR(50) | NULLABLE | 分组：种水/颜色/工艺/题材 |
| is_active | BOOLEAN | DEFAULT TRUE | |

#### item_tag（货品-标签关联）

| 字段 | 类型 | 约束 |
|------|------|------|
| item_id | INTEGER | PK, FK → items.id |
| tag_id | INTEGER | PK, FK → dict_tag.id |

#### suppliers（供货商）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| name | VARCHAR(100) | NOT NULL | 名称 |
| contact | VARCHAR(100) | NULLABLE | 联系方式 |
| notes | TEXT | NULLABLE | 备注 |
| is_active | BOOLEAN | DEFAULT TRUE | |

#### customers（客户）★新增

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| customer_code | VARCHAR(50) | UNIQUE | 自动生成（cst+日期+序号） |
| name | VARCHAR(100) | NOT NULL | 姓名/微信名 |
| phone | VARCHAR(20) | NULLABLE | 电话 |
| wechat | VARCHAR(100) | NULLABLE | 微信号 |
| notes | TEXT | NULLABLE | 备注（如"熟客"） |
| is_active | BOOLEAN | DEFAULT TRUE | |
| created_at | DATETIME | AUTO | |

#### batches（批次表，通货专用）★新增

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| batch_code | VARCHAR(50) | UNIQUE, NOT NULL | 批次编号 |
| material_id | INTEGER | FK → dict_material.id | 材质 |
| type_id | INTEGER | FK, NULLABLE | 器型（整批通常同器型） |
| quantity | INTEGER | NOT NULL | 总数量 |
| total_cost | FLOAT | NOT NULL | 批次总进价 |
| cost_alloc_method | VARCHAR(20) | NOT NULL | equal / by_weight / by_price |
| supplier_id | INTEGER | FK, NULLABLE | 供货商 |
| purchase_date | DATE | NULLABLE | 进货日期 |
| notes | TEXT | NULLABLE | |
| created_at | DATETIME | AUTO | |

#### items（货品主表）★大量变更

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| sku_code | VARCHAR(50) | UNIQUE, INDEX | 唯一编号 |
| name | VARCHAR(200) | NULLABLE | 商品名称 |
| batch_id | INTEGER | FK → batches.id, NULLABLE | 通货关联批次，高货为空 |
| material_id | INTEGER | FK, NOT NULL | 材质 |
| type_id | INTEGER | FK, NULLABLE | 器型 |
| cost_price | FLOAT | NULLABLE | 高货进价（通货此字段为空） |
| allocated_cost | FLOAT | NULLABLE | 分摊成本（通货由算法填充，高货=cost_price） |
| selling_price | FLOAT | NOT NULL | 零售价/标价 |
| floor_price | FLOAT | NULLABLE | 底价（最低可接受价） |
| origin | VARCHAR(100) | NULLABLE | 产地 |
| counter | INTEGER | NULLABLE | 柜台号 |
| cert_no | VARCHAR(100) | NULLABLE | 证书编号 |
| notes | TEXT | NULLABLE | 备注 |
| supplier_id | INTEGER | FK, NULLABLE | 供货商 |
| status | VARCHAR(20) | DEFAULT 'in_stock' | in_stock / sold / returned |
| purchase_date | DATE | NULLABLE | 进货日期 |
| created_at | DATETIME | AUTO | |
| updated_at | DATETIME | AUTO ON UPDATE | |
| is_deleted | BOOLEAN | DEFAULT FALSE | 软删除 |

索引：`ix_items_status`, `ix_items_material`, `ix_items_batch`

#### item_spec（货品规格参数）★新增

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| item_id | INTEGER | FK → items.id, UNIQUE | 一件货一条规格 |
| weight | FLOAT | NULLABLE | 总克重 |
| metal_weight | FLOAT | NULLABLE | 金属克重 |
| size | VARCHAR(100) | NULLABLE | 通用尺寸描述 |
| bracelet_size | VARCHAR(50) | NULLABLE | 圈口（手镯） |
| bead_count | INTEGER | NULLABLE | 粒数（手串/项链） |
| bead_diameter | VARCHAR(50) | NULLABLE | 珠子口径 |
| ring_size | VARCHAR(50) | NULLABLE | 戒指尺寸 |

#### item_images（货品图片）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| item_id | INTEGER | FK → items.id | |
| filename | VARCHAR(255) | NOT NULL | 存储文件名 |
| is_cover | BOOLEAN | DEFAULT FALSE | 是否封面 |
| created_at | DATETIME | AUTO | |

#### sale_records（销售记录）★变更

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| sale_no | VARCHAR(50) | UNIQUE | 销售单号（自动生成） |
| item_id | INTEGER | FK → items.id | |
| actual_price | FLOAT | NOT NULL | 实际成交价 |
| channel | VARCHAR(50) | NOT NULL | store / wechat |
| sale_date | DATE | NOT NULL | |
| customer_id | INTEGER | FK, NULLABLE | 关联客户 |
| bundle_id | INTEGER | FK → bundle_sales.id, NULLABLE | 套装销售关联 |
| note | TEXT | NULLABLE | 备注 |
| created_at | DATETIME | AUTO | |

索引：`ix_sale_date`, `ix_sale_channel`

#### bundle_sales（套装销售）★新增

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| bundle_no | VARCHAR(50) | UNIQUE | 套装单号 |
| total_price | FLOAT | NOT NULL | 套装总价 |
| alloc_method | VARCHAR(20) | NOT NULL | by_ratio / chain_at_cost |
| sale_date | DATE | NOT NULL | |
| channel | VARCHAR(50) | NOT NULL | |
| customer_id | INTEGER | FK, NULLABLE | |
| note | TEXT | NULLABLE | |
| created_at | DATETIME | AUTO | |

#### metal_prices（贵金属市价记录）★新增

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| material_id | INTEGER | FK → dict_material.id | |
| price_per_gram | FLOAT | NOT NULL | 克重单价 |
| effective_date | DATE | NOT NULL | 生效日期 |
| created_at | DATETIME | AUTO | |

#### sys_config（系统配置）★新增

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| key | VARCHAR(100) | UNIQUE, NOT NULL | 配置键 |
| value | TEXT | NOT NULL | 配置值 |
| description | VARCHAR(200) | NULLABLE | 说明 |

初始配置：operating_cost_rate=0.05, markup_rate=0.30, aging_threshold_days=90, default_alloc_method=equal

## 3. API 契约

### 3.1 通用约定

- 基础路径：`/api/v1`
- 分页：`page`（从1开始）、`size`（默认20，最大100）
- 响应：`{ "code": 0, "data": ..., "message": "ok" }`

### 3.2 字典 + 配置

```
GET    /api/v1/dicts/materials              # ?include_inactive=true
POST   /api/v1/dicts/materials              # { name, sub_type?, origin?, cost_per_gram?, sort_order? }
PUT    /api/v1/dicts/materials/:id
DELETE /api/v1/dicts/materials/:id          # 软删除

GET    /api/v1/dicts/types                  # 返回含 spec_fields
POST   /api/v1/dicts/types                  # { name, spec_fields?, sort_order? }
DELETE /api/v1/dicts/types/:id

GET    /api/v1/dicts/tags                   # ?group_name=种水
POST   /api/v1/dicts/tags                   # { name, group_name? }
DELETE /api/v1/dicts/tags/:id

GET    /api/v1/config                       # 所有配置
PUT    /api/v1/config/:key                  # { value }
```

### 3.3 批次管理 ★新增

```
GET    /api/v1/batches                      # ?page&size&material_id
GET    /api/v1/batches/:id                  # 详情：含关联货品 + 回本状态
POST   /api/v1/batches                      # 创建批次
PUT    /api/v1/batches/:id                  # 编辑
POST   /api/v1/batches/:id/allocate         # 触发成本分摊
```

### 3.4 货品

```
GET    /api/v1/items                        # ?page&size&material_id&type_id&status&batch_id&counter&keyword
GET    /api/v1/items/:id                    # 详情：含 spec/tags/images/batch_info
POST   /api/v1/items                        # 入库（高货或通货单件）
PUT    /api/v1/items/:id                    # 编辑（含规格）
DELETE /api/v1/items/:id                    # 软删除
```

### 3.5 销售

```
GET    /api/v1/sales                        # ?page&size&channel&start_date&end_date&customer_id
POST   /api/v1/sales                        # 单件销售
       { item_id, actual_price, channel, sale_date, customer_id?, note? }
POST   /api/v1/sales/bundle                 # 套装销售 ★新增
       { item_ids[], total_price, alloc_method, channel, sale_date, customer_id?, note? }
```

### 3.6 贵金属市价 ★新增

```
GET    /api/v1/metal-prices                 # 当前各贵金属市价
PUT    /api/v1/metal-prices/:material_id    # 更新市价
GET    /api/v1/metal-prices/history         # 历史记录
POST   /api/v1/metal-prices/reprice         # 预览批量调价
POST   /api/v1/metal-prices/reprice/confirm # 确认执行
```

### 3.7 看板

```
GET    /api/v1/dashboard/summary            # 概览
GET    /api/v1/dashboard/batch-profit       # ★批次回本看板
GET    /api/v1/dashboard/profit/by-category # 按材质利润
GET    /api/v1/dashboard/profit/by-channel  # 按渠道利润
GET    /api/v1/dashboard/trend              # 按月趋势（?months&material_id）
GET    /api/v1/dashboard/stock-aging        # 压货预警（?min_days=90）
```

### 3.8 客户 + 供应商

```
GET/POST/PUT    /api/v1/customers
GET             /api/v1/customers/:id       # 含购买记录

GET/POST/PUT    /api/v1/suppliers
```

## 4. 前端路由

```
/                        → 重定向到 /inventory
/inventory               → 库存列表（主页）
/inventory/:id           → 货品详情
/inventory/add           → 高货入库
/inventory/batch         → 通货批次入库（两步流程）
/sales                   → 销售记录列表
/dashboard               → 利润看板 + 批次回本
/settings/dicts          → 字典管理
/settings/metal-prices   → 贵金属市价管理
/settings/suppliers      → 供货商管理
/customers               → 客户管理
```

## 5. Docker 部署

```yaml
version: "3.8"
services:
  jade:
    build: .
    ports:
      - "8080:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DB_PATH=/app/data/jade.db
      - IMAGE_DIR=/app/data/images
    restart: unless-stopped
```

## 6. 种子数据

首次启动 `init_db()` 时自动插入：
- 36种材质（含子类、产地、贵金属克重单价）
- 9种器型（含 spec_fields JSON）
- 22个标签（4个分组）
- 4条系统配置
- 2条贵金属初始市价（18K金780、银25）

详见 PRD_v2.md 附录。
