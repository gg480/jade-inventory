# CLAUDE.md — 玉器店进销存系统

## 你在做什么

这是一个面向珠宝玉器实体店店主的进销存管理系统，核心目标不是"记账"，而是**决策支持**——让店主快速回答：哪个批次回本了？哪些货在压货？哪个品类利润率最高？贵金属市价变了我需要调哪些价？

店主经营 36 种材质、2000+ 件库存，通过实体门店和微信/朋友圈销售。系统最终部署在极空间 NAS（Docker）上。

## ⚠️ 必读的配套文档

开始任何工作之前，先阅读项目根目录下的：

- **`PRD.md`** — 产品需求文档（v2，基于业务调研重构）。包含完整的业务模型、功能优先级、数据模型概览、种子数据。**这是需求的唯一权威来源。**
- **`TECH_SPEC.md`** — 技术规格（如果已创建）。包含详细表结构和 API 契约。

## 珠宝行业核心业务概念

写代码前必须内化以下概念，它们直接影响数据模型和算法设计：

### 1. 双轨库存模型（最重要）

**高货**（翡翠手镯、精品挂件）：唯一件，单独定价，cost_price 即为进价。

**通货**（水晶手串、银饰）：以"批次"为单位进货，整手一个总价，每件有独立 SKU 但共享一个 batch_code。成本通过分摊算法分配到每件。

系统必须同时支持两种模式，在入库流程、成本计算、利润分析上走不同路径。

### 2. 成本分摊算法（通货专用）

| 算法 | 适用场景 | 公式 |
|------|---------|------|
| **均摊** | 珠子类（水晶/朱砂） | 每件成本 = 批次总价 ÷ 数量 |
| **按克重** | 金属类（银饰/18K金） | 每件成本 = (该件克重 ÷ 总克重) × 批次总价 |
| **按售价比例** | 玉器吊坠/手镯 | 每件成本 = (该件售价 ÷ 总售价) × 批次总价 |

分摊在所有货品录完后触发，不是入库时实时算的。

### 3. 定价引擎

分层递进：
```
经营成本 = 分摊成本 × 经营成本率（默认5%，可配置）
底价 = 分摊成本 + 经营成本 + 合理利润
零售价 = 底价 × (1 + 上浮比例（默认30%，可配置）)
```
店主可手动微调每件的实际零售价。所有比例参数存在 sys_config 表中，不硬编码。

### 4. 批次回本模型

店主关心的不是单件毛利，而是**这一手货回本了没有**。
```
批次利润 = 该批次所有已售货品成交价之和 − 批次总进货成本
回本进度 = 已回款 / 批次总成本
```
回本后剩余尾货可以任意促销出清——单件可能亏，但整批不亏。

### 5. 动态品类体系

三级分类：**材质 → 器型 → 标签**，全部存字典表。
- 材质 36 种，带子类（银→990）和产地（翡翠→缅甸）
- 器型决定规格参数（手镯需要圈口，手串需要粒数+珠子口径，戒指需要尺寸）
- **绝对不要在代码中硬编码任何品类枚举**

### 6. 货品状态

```
在库(in_stock) → 已售(sold)
              → 已退(returned)
```
"借出"功能暂不纳入核心开发。

### 7. 贵金属市价管理

贵金属（18K金、银等）售价与市场金价挂钩。市价变动时需批量重算在库货品零售价：
```
新零售价 = 克重 × 新市价单价 + 工费
```

### 8. 套装销售

客户买吊坠+链子合起来议价，系统按比例分摊总价到各件，每件独立记录销售。

### 9. 柜台管理

物理展示柜位置标识，帮助快速找货。字段仅用于展示和筛选。

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.11+ / FastAPI |
| ORM | SQLAlchemy 2.0（Mapped Column 风格） |
| 数据库 | SQLite（`data/jade.db`） |
| 前端 | Vue 3（Composition API）+ Vite |
| 样式 | Tailwind CSS |
| HTTP 客户端 | Axios |
| 图片处理 | Pillow |
| 部署 | Docker + docker-compose → 极空间 NAS |

## 数据模型概览（14张表）

```
dict_material ──1:N──→ batches ──1:N──→ items ──1:1──→ item_spec
dict_material ──1:N──→ items                  ──1:N──→ item_images
dict_material ──1:N──→ metal_prices           ──1:N──→ sale_records
dict_type     ──1:N──→ items
dict_tag      ──M:N──→ items (通过 item_tag)
suppliers     ──1:N──→ batches
customers     ──1:N──→ sale_records
bundle_sales  ──1:N──→ sale_records
sys_config（系统配置，键值对）
```

核心表说明：
- **batches**：通货批次，记录整手进货信息和分摊算法
- **items**：货品主表，高货直接记 cost_price，通货通过 batch_id 关联批次、allocated_cost 由分摊算法填充
- **item_spec**：规格参数（克重/圈口/粒数等），由器型驱动展示哪些字段
- **bundle_sales**：套装销售，一次交易包含多件货品
- **metal_prices**：贵金属市价历史记录
- **sys_config**：所有业务参数（经营成本率、上浮比例、压货天数等）

## 项目结构

```
jade-inventory/
├── CLAUDE.md                  # ← 你正在看的文件
├── PRD_v2.md                  # ← 产品需求文档（必读）
├── TECH_SPEC.md               # ← 技术规格（必读）
├── backend/
│   ├── main.py               # FastAPI 入口
│   ├── database.py           # 引擎、session、init_db()、种子数据
│   ├── models.py             # 14张表的 ORM 模型
│   ├── schemas.py            # Pydantic 请求/响应模型
│   ├── routers/
│   │   ├── dicts.py          # 字典管理 + 系统配置
│   │   ├── batches.py        # 批次管理 + 成本分摊
│   │   ├── items.py          # 货品 CRUD
│   │   ├── sales.py          # 销售记录 + 套装销售
│   │   ├── metal_prices.py   # 贵金属市价管理
│   │   ├── dashboard.py      # 看板统计
│   │   ├── customers.py      # 客户管理
│   │   └── suppliers.py      # 供应商管理
│   ├── utils/
│   │   └── image.py          # 图片上传/缩略图
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js
│       ├── api/index.js
│       ├── views/
│       └── components/
├── data/
│   ├── jade.db
│   └── images/
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## 开发命令

```bash
# 后端
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端开发
cd frontend && npm install && npm run dev

# 前端构建
cd frontend && npm run build

# Docker
docker-compose up --build
```

## 编码约定

### Python
- PEP8，类型注解必须完整
- SQLAlchemy 2.0：`Mapped[T]` + `mapped_column()`
- 中文注释

### Vue
- `<script setup>` + Composition API
- 组件文件名 PascalCase

### 命名
- 数据库字段：`snake_case`
- 前端 JS：`camelCase`
- API 传输：`snake_case`

### API 规范
- 路径前缀：`/api/v1/`
- 分页：`?page=1&size=20`
- 响应：`{ "code": 0, "data": ..., "message": "ok" }`
- 字典项软删除（`is_active = false`），货品软删除（`is_deleted = true`）

## 开发阶段

| 阶段 | 范围 | 完成标志 |
|------|------|----------|
| **阶段1** | 数据库 + 全部 API（14张表、8个路由模块） | Swagger UI 可跑通全部端点，端到端验证20步通过 |
| **阶段2** | 前端：库存列表、双轨入库、销售出库、字典管理、市价管理 | 浏览器可完成完整业务流程，手机可用 |
| **阶段3** | 看板：批次回本、利润分析、压货预警、图表 | 店主可基于看板做经营决策 |
| **阶段4** | 图片管理、客户管理、数据导出、Docker 部署 | 极空间 NAS 一键部署 |

## 关键约束（红线）

1. **不硬编码品类** — 所有分类来自字典表
2. **不硬编码业务参数** — 经营成本率/上浮比例/压货天数等全部走 sys_config
3. **不物理删除** — 字典用 is_active，货品用 is_deleted
4. **不引入外部数据库** — 只用 SQLite
5. **前端必须适配手机** — 店主日常用手机操作
6. **批次成本分摊必须在货品录完后触发** — 不是入库时实时算
7. **回本判断只看已回款现金** — 不估算库存价值
