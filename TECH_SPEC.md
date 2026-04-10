# TECH_SPEC — 技术规格

## 1. 架构

```
浏览器（手机/电脑）
    │ HTTP
    ▼
FastAPI (port 8000)
    ├── /api/v1/*          → JSON API
    ├── /data/images/*     → 静态图片
    └── /*                 → Vue SPA 静态文件（生产模式）
    │
    ▼
SQLite (data/jade.db)
```

单进程部署，不需要 Nginx/反向代理。极空间 Docker 直接映射端口。

## 2. 数据模型

### 2.1 ER 关系

```
dict_material  1──N  dict_type
dict_material  1──N  items
dict_type      1──N  items
dict_tag       M──N  items       (通过 item_tag 关联表)
suppliers      1──N  items
items          1──N  item_images
items          1──N  sale_records
```

### 2.2 表结构

#### dict_material（材质字典）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 材质名称 |
| sort_order | INTEGER | DEFAULT 0 | 排序权重 |
| is_active | BOOLEAN | DEFAULT TRUE | 软删除标记 |

#### dict_type（器型字典）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | |
| material_id | INTEGER | FK → dict_material.id | 所属材质 |
| name | VARCHAR(50) | NOT NULL | 器型名称 |
| sort_order | INTEGER | DEFAULT 0 | |
| is_active | BOOLEAN | DEFAULT TRUE | |

约束：`UNIQUE(material_id, name)`

#### dict_tag（标签字典）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 标签名称 |
| group_name | VARCHAR(50) | NULLABLE | 分组：种水/工艺/题材 |
| is_active | BOOLEAN | DEFAULT TRUE | |

#### item_tag（货品-标签关联表）

| 字段 | 类型 | 约束 |
|------|------|------|
| item_id | INTEGER | PK, FK → items.id |
| tag_id | INTEGER | PK, FK → dict_tag.id |

#### suppliers（供货商）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | |
| name | VARCHAR(100) | NOT NULL | 名称 |
| contact | VARCHAR(100) | NULLABLE | 联系方式 |
| notes | TEXT | NULLABLE | 备注 |
| is_active | BOOLEAN | DEFAULT TRUE | |

#### items（货品，核心表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | |
| sku_code | VARCHAR(50) | UNIQUE, INDEX | 唯一编号 |
| batch_code | VARCHAR(50) | NULLABLE, INDEX | 批次款号（通货用） |
| material_id | INTEGER | FK, NOT NULL | 材质 |
| type_id | INTEGER | FK, NULLABLE | 器型 |
| cost_price | FLOAT | NOT NULL | 进货成本 |
| selling_price | FLOAT | NOT NULL | 标价 |
| weight | FLOAT | NULLABLE | 克重 |
| size | VARCHAR(100) | NULLABLE | 尺寸 |
| cert_no | VARCHAR(100) | NULLABLE | 证书编号 |
| notes | TEXT | NULLABLE | 备注 |
| supplier_id | INTEGER | FK, NULLABLE | 供货商 |
| status | VARCHAR(20) | DEFAULT 'in_stock' | in_stock/sold/returned/lent_out |
| purchase_date | DATE | NULLABLE | 进货日期 |
| created_at | DATETIME | AUTO | |
| updated_at | DATETIME | AUTO ON UPDATE | |
| is_deleted | BOOLEAN | DEFAULT FALSE | 软删除 |

索引：`ix_items_status`, `ix_items_material`

#### item_images（货品图片）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | |
| item_id | INTEGER | FK → items.id | |
| filename | VARCHAR(255) | NOT NULL | 存储文件名 |
| is_cover | BOOLEAN | DEFAULT FALSE | 是否封面 |
| created_at | DATETIME | AUTO | |

#### sale_records（销售记录）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | |
| item_id | INTEGER | FK → items.id | |
| actual_price | FLOAT | NOT NULL | 实际成交价 |
| channel | VARCHAR(50) | NOT NULL | store/wechat/ecommerce |
| sale_date | DATE | NOT NULL | 成交日期 |
| customer_note | TEXT | NULLABLE | 客户/交易备注 |
| created_at | DATETIME | AUTO | |

索引：`ix_sale_records_date`, `ix_sale_records_channel`

## 3. API 契约

### 3.1 通用约定

- 基础路径：`/api/v1`
- 认证：初期无认证（局域网内使用），后续可加 Basic Auth
- 分页参数：`page`（从1开始）、`size`（默认20，最大100）
- 响应包装：所有接口返回 `{ "code": 0, "data": ..., "message": "ok" }`

### 3.2 字典接口

```
GET    /api/v1/dicts/materials              # 材质列表（?include_inactive=true）
POST   /api/v1/dicts/materials              # 新增材质 { name, sort_order }
PUT    /api/v1/dicts/materials/:id          # 编辑材质
DELETE /api/v1/dicts/materials/:id          # 停用材质（软删除）

GET    /api/v1/dicts/types                  # 器型列表（?material_id=1）
POST   /api/v1/dicts/types                  # 新增器型 { material_id, name, sort_order }
DELETE /api/v1/dicts/types/:id              # 停用器型

GET    /api/v1/dicts/tags                   # 标签列表（?group_name=种水）
POST   /api/v1/dicts/tags                   # 新增标签 { name, group_name }
DELETE /api/v1/dicts/tags/:id               # 停用标签
```

### 3.3 货品接口

```
GET    /api/v1/items                        # 货品列表
       ?page=1&size=20
       &material_id=1&type_id=2&status=in_stock
       &keyword=关键词（搜编号/款号/证书/备注）

GET    /api/v1/items/:id                    # 货品详情（含图片列表）

POST   /api/v1/items                        # 单件入库
       { sku_code, batch_code?, material_id, type_id?, tag_ids[],
         cost_price, selling_price, weight?, size?, cert_no?,
         notes?, supplier_id?, purchase_date? }

POST   /api/v1/items/batch                  # 批量入库
       { batch_code, material_id, type_id?, tag_ids[], quantity,
         cost_price, selling_price, sku_prefix?,
         weight?, size?, supplier_id?, purchase_date? }

PUT    /api/v1/items/:id                    # 编辑货品（部分更新）

DELETE /api/v1/items/:id                    # 软删除货品

POST   /api/v1/items/:id/images             # 上传图片（multipart/form-data）
DELETE /api/v1/items/:id/images/:image_id   # 删除图片
PUT    /api/v1/items/:id/images/:image_id/cover  # 设为封面
```

### 3.4 销售接口

```
GET    /api/v1/sales                        # 销售列表（?page&size&channel&start_date&end_date）
POST   /api/v1/sales                        # 创建销售记录（同时将货品标记为 sold）
       { item_id, actual_price, channel, sale_date, customer_note? }
```

### 3.5 看板接口

```
GET    /api/v1/dashboard/profit/by-category   # 按材质的利润统计（?start_date&end_date）
GET    /api/v1/dashboard/profit/by-channel    # 按渠道的利润统计
GET    /api/v1/dashboard/trend                # 按月销售趋势（?months=12&material_id=）
GET    /api/v1/dashboard/stock-aging          # 压货预警（?min_days=90）
GET    /api/v1/dashboard/summary              # 概览数据（总库存/总资金/本月销售等）
```

## 4. 前端路由

```
/                    → 重定向到 /inventory
/inventory           → 库存列表（主页）
/inventory/:id       → 货品详情
/inventory/add       → 入库表单（单件/批量切换）
/sales               → 销售记录列表
/dashboard           → 利润看板
/settings/dicts      → 字典管理（材质/器型/标签）
/settings/suppliers  → 供货商管理
```

## 5. Docker 部署

```yaml
# docker-compose.yml
version: "3.8"
services:
  jade:
    build: .
    ports:
      - "8080:8000"
    volumes:
      - ./data:/app/data    # 数据库 + 图片持久化
    environment:
      - DB_PATH=/app/data/jade.db
      - IMAGE_DIR=/app/data/images
    restart: unless-stopped
```

```dockerfile
# Dockerfile
FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/ .
RUN npm ci && npm run build

FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=frontend /build/../backend/static ./static
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

极空间 Docker 管理器配置：
- 网络模式：bridge
- 端口映射：宿主机 8080 → 容器 8000
- 卷挂载：极空间共享文件夹路径 → `/app/data`
- 重启策略：unless-stopped

## 6. 种子数据

首次启动时，如果 `dict_material` 表为空，自动插入预置分类。详见 PRD.md 第5节。
种子数据逻辑写在 `database.py` 的 `init_db()` 函数中。
