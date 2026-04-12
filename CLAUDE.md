# CLAUDE.md — 玉器店进销存系统

## 你在做什么

这是一个面向珠宝玉器实体店店主的进销存管理系统，核心目标不是"记账"，而是**决策支持**——让店主快速回答：哪个批次回本了？哪些货在压货？哪个品类利润率最高？贵金属市价变了我需要调哪些价？

店主经营 36 种材质、2000+ 件库存，通过实体门店和微信/朋友圈销售。系统最终部署在极空间 NAS（Docker）上。

---

## 当前进度（2026-04-12 更新，基于产品评估报告）

### 开发阶段完成情况

| 阶段 | 状态 | 说明 |
|------|------|------|
| **阶段1 — 后端API** | ✅ 已完成 | 14张表 + 10个路由模块（40+接口），Swagger UI 端到端验证通过 |
| **阶段2 — 前端核心页面** | ✅ 已完成 | 10个视图 + 9个组件，桌面端表格视图 + 移动端卡片视图双适配 |
| **代码审查** | ✅ 已完成 | 修复50个问题（8 Critical / 14 High / 18 Medium / 10 Low），已合并到 main |
| **阶段3/4 补充功能** | ✅ 已完成 | 图片管理全链路、供应商前端对接、批次回本看板、Excel导出 |

### PRD 需求覆盖度审计

> 以下评估基于产品评估报告，对照 PRD.md v2.1 逐项审计。

**P0 核心功能（完成度 ~95%）**
- [x] 字典管理 — 材质/器型/标签 CRUD + 系统配置，软删除，种子数据自动插入（36材质/9器型/22标签/4配置/2市价）
- [x] 批次管理 — 创建批次、逐件入库、成本分摊（均摊/按克重/按售价比例），后端完整
- [x] 货品入库 — 高货单步入库 + 通货两步入库，SKU 自动生成（规则：`{材质缩写}-{YYYYMMDD}-{3位序号}`）
- [x] 库存查看 — 列表+详情页，多维度筛选（材质/器型/状态/批次/柜台/关键词），分页，移动端卡片视图
- [x] 销售出库 — 单件销售 + 套装销售（by_ratio/chain_at_cost 两种分摊方式），自动生成 sale_no
- [x] 贵金属市价管理 — 查看/编辑克重单价，预览受影响货品，确认后批量重算零售价，历史记录
- [ ] 批次列表页面 — BatchAdd 完成后缺少独立的 /batches 列表页（当前无此路由定义）

**P1 分析功能（完成度 ~85%）**
- [x] 批次回本看板 — Dashboard 新增批次回本 Tab，调用 /dashboard/batch-profit，展示回本进度/状态标签/已售数量
- [x] 图片管理 — 后端 utils/image.py（上传处理/格式校验/400×400缩略图）+ items.py 图片端点 + 前端 InventoryDetail 图片上传/删除/设封面
- [x] 供应商管理 — 后端完整 CRUD + 前端已从 Mock 数据切换为真实 API 调用
- [x] 客户管理 — 后端 API + 前端 CustomerList 页面 + CustomerModal 组件
- [x] 数据导出 — export.py（openpyxl），支持库存明细/销售记录/入库记录三种 Excel 导出
- [ ] 利润看板 — 按材质/渠道/时间范围的利润分析与专业图表展示（当前 Dashboard 仅有简易 HTML div 条形图）
- [ ] 压货预警 — 超过 sys_config.aging_threshold_days 的在库货品列表，占用资金统计，高成本+长库龄突出标记

**P2 扩展功能（完成度 ~33%）**
- [ ] 镶嵌定制业务（独立模块，未开始）
- [ ] Docker 部署到极空间 NAS（缺少 Dockerfile/docker-compose.yml/.dockerignore，是最终交付关键环节）
- [ ] 借出管理功能（PRD 明确标注"暂不纳入核心开发"）

### 后端路由模块（10个）

```
routers/dicts.py        — 字典管理 + 系统配置 CRUD
routers/batches.py      — 批次管理 + 成本分摊算法（均摊/按克重/按售价比例）
routers/items.py        — 货品 CRUD + 图片上传/删除/列表/设封面
routers/sales.py        — 销售记录 + 套装销售（by_ratio/chain_at_cost）
routers/metal_prices.py — 贵金属市价管理 + 批量重算零售价
routers/dashboard.py    — 看板统计（批次回本、利润概览、库存概览）
routers/customers.py    — 客户管理 CRUD
routers/suppliers.py    — 供应商管理 CRUD
routers/export.py       — Excel 数据导出（库存/销售/入库，openpyxl）
```

### 前端页面（10个视图 + 9个组件）

**视图页面**：
```
views/InventoryList.vue      — 库存列表（表格+卡片双视图，筛选/分页）
views/InventoryDetail.vue    — 库存详情（全部字段+规格+图片管理）
views/InventoryAdd.vue       — 入库表单（高货/通货双轨）
views/BatchAdd.vue           — 通货批次录入（逐件添加+触发分摊）
views/SalesList.vue          — 销售列表 + 单件/套装销售
views/DictsManagement.vue    — 字典管理（材质/器型/标签/系统配置 4个Tab）
views/MetalPriceManage.vue   — 贵金属市价管理
views/Dashboard.vue          — 看板（批次回本+库存概览+利润概览）
views/SuppliersManagement.vue — 供应商管理（CRUD，已对接真实API）
views/CustomerList.vue       — 客户管理
```

**组件**：
```
components/AppLayout.vue      — 应用布局（侧边栏+导航）
components/BundleSaleDialog.vue — 套装销售弹窗（by_ratio/chain_at_cost 分摊）
components/SaleDialog.vue      — 单件销售弹窗
components/SaleList.vue        — 销售记录列表
components/CustomerModal.vue   — 客户选择/创建弹窗
components/MaterialModal.vue   — 材质编辑弹窗
components/TypeModal.vue       — 器型编辑弹窗
components/TagModal.vue        — 标签编辑弹窗
components/Pagination.vue      — 分页组件
```

### 已识别的关键问题与风险（来自评估报告）

> 以下问题在后续开发中已部分修复，保留记录供参考。

1. ~~**图片管理全链路断裂**~~ — 已修复。原始问题：数据库模型和前端API已就绪但后端完全缺失，backend/utils/image.py 不存在，items.py 无图片端点。现已在 commit 6f647f7 中完成全链路实现。

2. ~~**批次回本看板前端缺失**~~ — 已修复。原始问题：后端 /dashboard/batch-profit 已就绪但前端无专属展示区域，这是系统核心价值主张。现已在 Dashboard.vue 中新增批次回本 Tab。

3. ~~**供应商前端 Mock 数据**~~ — 已修复。原始问题：SuppliersManagement.vue 使用硬编码 Mock 数组，用户操作不会影响实际数据库。现已切换为真实 API 调用。

4. **看板图表展示粗糙** — 当前仍存在。Dashboard.vue 使用简单 HTML div 条形图，缺少专业可视化库。建议引入 ECharts 或 Chart.js，实现柱状图/折线图/饼图，支持时间范围筛选，适配移动端触屏。

5. **批次列表页缺失** — 当前仍存在。BatchAdd 完成后无独立批次列表页面，/batches 路由未定义。后端接口已就绪，需新建前端页面。

### 技术债务（来自评估报告）

1. **测试覆盖不足** — 仅 BundleSaleDialog 有单元测试文件，其余组件和接口均无测试覆盖。建议引入 pytest（后端）和 Vitest（前端）。
2. **无数据库迁移工具** — 表结构变更仅依赖 SQLAlchemy 的 create_all，生产环境存在风险。建议引入 Alembic 进行版本化管理。
3. **前端状态管理分散** — 各页面使用本地 ref/reactive，dict.js store 是良好开始但未扩展。建议引入 Pinia 集中管理。
4. **遗留文件** — HelloWorld.vue（Vite 默认模板）仍存在于项目中，应予清理。
5. **数据库初始化安全** — 已在代码审查中修复。原 C-01 级严重问题（启动时 DROP ALL 表导致数据丢失）已改为安全 create_all 策略，仅显式 RESET_DB=true 时重建。

### 下一步待开发（优先级排序）

| 优先级 | 任务 | PRD 对应 | 预计工时 | 依赖 |
|--------|------|---------|---------|------|
| **P0** | 利润看板（专业图表） | PRD 8.2.2 | 2天 | 需引入 ECharts |
| **P0** | 压货预警 | PRD 8.2.3 | 1天 | 后端接口部分已有 |
| **P1** | 批次列表页面 | PRD 8.1.2 | 0.5天 | 后端已就绪 |
| **P1** | Docker 部署 | PRD 阶段4 | 1天 | 最终交付关键 |
| **P2** | 端到端测试 | — | 2天 | — |
| **P2** | 清理技术债务 | — | 1天 | — |
| **P3** | 镶嵌定制模块 | PRD P2 | — | 独立模块 |

### Git 提交历史

```
9bab021  Merge branch 'fix/code-review-issues' into main     ← main HEAD
6f647f7  feat: 完成剩余功能 - 图片管理/供应商CRUD/批次回本看板/Excel导出
d2d89c1  Merge pull request #2 from gg480/fix/code-review-issues
71e874c  fix: 代码审查修复 — 50个问题 (CRITICAL/HIGH/MEDIUM/LOW)
c3356a3  Merge branch 'master' into main
2ac06ee  feat: 阶段2完成 - 前端（库存列表/双轨入库/销售出库/字典管理/市价管理/移动端适配）
8c2ff2a  feat: 阶段1完成 - 后端API（14表/8路由/批次分摊/套装销售/贵金属市价/回本看板）
```

---

## 必读的配套文档

开始任何工作之前，先阅读项目根目录下的：

- **`PRD.md`** — 产品需求文档 v2.1，包含完整业务模型、功能优先级、数据模型概览、种子数据。**这是需求的唯一权威来源。**
- **`TECH_SPEC.md`** — 技术规格，包含详细表结构和 API 契约。

---

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

分摊在所有货品录完后触发，不是入库时实时算的。分摊余数加到最后一件，确保 SUM(allocated_cost) == batch.total_cost。

### 3. 定价引擎

分层递进：
```
经营成本 = 分摊成本 × 经营成本率（默认5%，可配置）
底价 = 分摊成本 + 经营成本
零售价 = 底价 × (1 + 上浮比例（默认30%，可配置））
```
店主可手动微调每件的实际零售价。所有比例参数存在 sys_config 表中，不硬编码。分摊完成后自动触发一次定价引擎，填充 floor_price 和建议 selling_price。

### 4. 批次回本模型（系统核心价值主张）

店主关心的不是单件毛利，而是**这一手货回本了没有**。
```
batch_revenue = SUM(该批次所有 status=sold 的货品的 sale_records.actual_price)
batch_profit = batch_revenue - batch.total_cost
payback_rate = batch_revenue / batch.total_cost
```

状态判定：new（未开始，灰色）→ selling（销售中，蓝色）→ paid_back（已回本，绿色）→ cleared（清仓完毕，绿色）

回本后剩余尾货可以任意促销出清——单件可能亏，但整批不亏。回本判断只看已回款现金，不估算库存价值。

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
新零售价 = 克重 × 新市价单价 + 工费（工费保持不变）
```
更新流程：编辑市价 → 预览受影响货品 → 确认后批量更新 → 插入 metal_prices 历史记录。

### 8. 套装销售

客户买吊坠+链子合起来议价，系统按比例分摊总价到各件，每件独立记录销售。
- **by_ratio**（按售价比例）：各件成交价 = (该件 selling_price / SUM(selling_price)) × total_price
- **chain_at_cost**（链子按原价）：链子/绳子类按 selling_price 计，剩余金额全部分给主件

### 9. 柜台管理

物理展示柜位置标识（整数如1、2、3），帮助快速找货。字段仅用于展示和筛选。

---

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
| Excel 导出 | openpyxl |
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
- **batches**：通货批次，记录整手进货信息和分摊算法（cost_alloc_method）
- **items**：货品主表，高货直接记 cost_price，通货通过 batch_id 关联批次、allocated_cost 由分摊算法填充
- **item_spec**：规格参数（克重/圈口/粒数等），由器型的 spec_fields JSON 驱动展示哪些字段
- **item_images**：货品图片，支持多张+封面标记
- **bundle_sales**：套装销售，一次交易包含多件货品，各件独立 sale_records
- **metal_prices**：贵金属市价历史记录
- **sys_config**：所有业务参数（operating_cost_rate=0.05, markup_rate=0.30, aging_threshold_days=90, default_alloc_method=equal）

## 项目结构

```
jade-inventory/
├── CLAUDE.md                  # ← 你正在看的文件（含进度+评估）
├── PRD.md                     # ← 产品需求文档 v2.1（必读，需求唯一权威来源）
├── TECH_SPEC.md               # ← 技术规格（必读）
├── backend/
│   ├── main.py               # FastAPI 入口，注册所有路由，静态文件挂载
│   ├── config.py             # 配置项（图片存储路径、允许格式/大小等）
│   ├── database.py           # 引擎、session、init_db()、种子数据
│   ├── models.py             # 14张表的 ORM 模型
│   ├── schemas.py            # Pydantic V2 请求/响应模型
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

# Docker（待创建）
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

## 关键约束（红线）

1. **不硬编码品类** — 所有分类来自字典表
2. **不硬编码业务参数** — 经营成本率/上浮比例/压货天数等全部走 sys_config
3. **不物理删除** — 字典用 is_active，货品用 is_deleted
4. **不引入外部数据库** — 只用 SQLite
5. **前端必须适配手机** — 店主日常用手机操作，375px 宽度优先
6. **批次成本分摊必须在货品录完后触发** — 不是入库时实时算
7. **回本判断只看已回款现金** — 不估算库存价值
8. **数据库安全初始化** — 仅 RESET_DB=true 时才 DROP ALL，正常启动用 create_all
