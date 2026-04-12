# CLAUDE.md — 玉器店进销存系统

## 你在做什么

这是一个面向珠宝玉器实体店店主的进销存管理系统，核心目标不是"记账"，而是**决策支持**——让店主快速回答：哪个批次回本了？哪些货在压货？哪个品类利润率最高？贵金属市价变了我需要调哪些价？

店主经营 36 种材质、2000+ 件库存，通过实体门店和微信/朋友圈销售。系统最终部署在极空间 NAS（Docker）上。

---

## 当前进度（2026-04-12 更新）

### 已完成阶段

| 阶段 | 状态 | 说明 |
|------|------|------|
| **阶段1 — 后端API** | ✅ 已完成 | 14张表 + 10个路由模块，Swagger UI 端到端验证通过 |
| **阶段2 — 前端核心页面** | ✅ 已完成 | 库存列表/详情、双轨入库、销售出库、字典管理、市价管理、移动端适配 |
| **代码审查** | ✅ 已完成 | 修复50个问题（CRITICAL/HIGH/MEDIUM/LOW），已合并到 main |
| **阶段3/4补充功能** | ✅ 已完成 | 图片管理、供应商CRUD、批次回本看板、Excel导出 |

### 功能完成清单（对照 PRD.md）

**P0 核心功能（全部完成）**
- [x] 字典管理 — 材质/器型/标签 CRUD + 系统配置，软删除，种子数据自动插入
- [x] 批次管理 — 创建批次、逐件入库、成本分摊（均摊/按克重/按售价比例）
- [x] 货品入库 — 高货单步入库 + 通货两步入库，SKU 自动生成
- [x] 库存查看 — 列表+详情页，多维度筛选，分页，移动端卡片视图
- [x] 销售出库 — 单件销售 + 套装销售（by_ratio/chain_at_cost 两种分摊方式）
- [x] 贵金属市价管理 — 查看/编辑克重单价，批量重算零售价，历史记录

**P1 分析功能（部分完成）**
- [x] 批次回本看板 — 回本状态列表，进度条，状态标签（新/销售中/已回本/清仓）
- [x] 图片管理 — 上传/删除/列表接口，缩略图生成，前端图片展示与管理
- [x] 供应商管理 — 完整 CRUD，前后端联调
- [x] 客户管理 — 后端 API + 前端页面
- [x] 数据导出 — 库存/销售/入库 Excel 导出（openpyxl）
- [ ] 利润看板 — 按材质/渠道/时间范围的利润分析与图表展示
- [ ] 压货预警 — 超过阈值的在库货品列表，占用资金统计

**P2 扩展功能（未开始）**
- [ ] 镶嵌定制业务（独立模块）
- [ ] Docker 部署到极空间 NAS
- [ ] 借出管理功能

### 后端路由模块（10个，全部实现）

```
routers/dicts.py        — 字典管理 + 系统配置 CRUD
routers/batches.py      — 批次管理 + 成本分摊算法
routers/items.py        — 货品 CRUD + 图片上传/删除/列表
routers/sales.py        — 销售记录 + 套装销售
routers/metal_prices.py — 贵金属市价管理 + 批量重算零售价
routers/dashboard.py    — 看板统计（批次回本、利润概览、库存概览）
routers/customers.py    — 客户管理 CRUD
routers/suppliers.py    — 供应商管理 CRUD
routers/export.py       — 数据导出（Excel: 库存/销售/入库）
```

### 前端页面（10个视图 + 10个组件）

**视图页面**：
```
views/InventoryList.vue      — 库存列表（表格+卡片双视图，筛选/分页）
views/InventoryDetail.vue    — 库存详情（全部字段+规格+图片管理）
views/InventoryAdd.vue       — 入库表单（高货/通货双轨）
views/BatchAdd.vue           — 通货批次录入（逐件添加+触发分摊）
views/SalesList.vue          — 销售列表
views/DictsManagement.vue    — 字典管理（材质/器型/标签/系统配置）
views/MetalPriceManage.vue   — 贵金属市价管理
views/Dashboard.vue          — 看板（批次回本+库存概览+利润概览）
views/SuppliersManagement.vue — 供应商管理（CRUD）
views/CustomerList.vue       — 客户管理
```

**组件**：
```
components/AppLayout.vue      — 应用布局（侧边栏+导航）
components/BundleSaleDialog.vue — 套装销售弹窗
components/SaleDialog.vue      — 单件销售弹窗
components/SaleList.vue        — 销售记录列表
components/CustomerModal.vue   — 客户选择/创建弹窗
components/MaterialModal.vue   — 材质编辑弹窗
components/TypeModal.vue       — 器型编辑弹窗
components/TagModal.vue        — 标签编辑弹窗
components/Pagination.vue      — 分页组件
```

### Git 提交历史

```
9bab021  Merge branch 'fix/code-review-issues' into main     ← 当前 HEAD (main)
6f647f7  feat: 完成剩余功能 - 图片管理/供应商CRUD/批次回本看板/Excel导出
d2d89c1  Merge pull request #2 from gg480/fix/code-review-issues
71e874c  fix: 代码审查修复 — 50个问题 (CRITICAL/HIGH/MEDIUM/LOW)
c3356a3  Merge branch 'master' into main
2ac06ee  feat: 阶段2完成 - 前端（库存列表/双轨入库/销售出库/字典管理/市价管理/移动端适配）
8c2ff2a  feat: 阶段1完成 - 后端API（14表/8路由/批次分摊/套装销售/贵金属市价/回本看板）
```

### 下一步待开发

1. **利润看板**（PRD 8.2.2）— 按材质/渠道/时间维度的利润分析 + 图表（考虑 ECharts 或 Chart.js）
2. **压货预警**（PRD 8.2.3）— 超阈值在库货品列表 + 占用资金统计
3. **Docker 部署**（PRD 阶段4）— docker-compose + 极空间 NAS 适配
4. **端到端测试** — 完整业务流程回归验证
5. **UI 打磨** — 看板图表、动画过渡、加载状态优化

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
├── CLAUDE.md                  # ← 你正在看的文件（含进度）
├── PRD.md                     # ← 产品需求文档 v2.1（必读，需求唯一权威来源）
├── TECH_SPEC.md               # ← 技术规格（必读）
├── backend/
│   ├── main.py               # FastAPI 入口，注册所有路由
│   ├── config.py             # 配置项（图片存储路径、允许格式等）
│   ├── database.py           # 引擎、session、init_db()、种子数据
│   ├── models.py             # 14张表的 ORM 模型
│   ├── schemas.py            # Pydantic 请求/响应模型
│   ├── routers/
│   │   ├── dicts.py          # 字典管理 + 系统配置
│   │   ├── batches.py        # 批次管理 + 成本分摊
│   │   ├── items.py          # 货品 CRUD + 图片上传/删除/列表
│   │   ├── sales.py          # 销售记录 + 套装销售
│   │   ├── metal_prices.py   # 贵金属市价管理
│   │   ├── dashboard.py      # 看板统计（批次回本+利润+库存概览）
│   │   ├── customers.py      # 客户管理
│   │   ├── suppliers.py      # 供应商管理
│   │   └── export.py         # Excel 导出（库存/销售/入库）
│   ├── utils/
│   │   └── image.py          # 图片上传/缩略图工具
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js        # proxy /api → localhost:8001
│   ├── tailwind.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js   # 10个路由
│       ├── api/
│       │   ├── index.js      # 统一 API 封装
│       │   └── images.js     # 图片专用 API
│       ├── store/
│       │   └── dict.js       # 字典状态管理
│       ├── views/            # 10个页面
│       └── components/       # 9个组件
├── data/
│   ├── jade.db               # SQLite 数据库
│   └── images/               # 货品图片存储
└── .gitignore
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

## 开发阶段（原始规划 vs 实际进度）

| 阶段 | 原始规划 | 实际完成情况 |
|------|---------|-------------|
| **阶段1** | 数据库 + 全部 API | ✅ 14张表 + 10个路由模块（含 export.py），已通过验证 |
| **阶段2** | 前端核心页面 + 移动端适配 | ✅ 10个视图 + 9个组件，移动端响应式 |
| **阶段3** | 看板（回本/利润/压货） | ⚠️ 批次回本看板已完成，利润分析和压货预警待开发 |
| **阶段4** | 图片/客户/导出/Docker | ⚠️ 图片管理+客户+导出已完成，Docker部署待完成 |

## 关键约束（红线）

1. **不硬编码品类** — 所有分类来自字典表
2. **不硬编码业务参数** — 经营成本率/上浮比例/压货天数等全部走 sys_config
3. **不物理删除** — 字典用 is_active，货品用 is_deleted
4. **不引入外部数据库** — 只用 SQLite
5. **前端必须适配手机** — 店主日常用手机操作
6. **批次成本分摊必须在货品录完后触发** — 不是入库时实时算
7. **回本判断只看已回款现金** — 不估算库存价值
