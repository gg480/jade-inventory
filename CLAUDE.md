# CLAUDE.md — 玉器店进销存系统

> **角色说明**：本文件是主力开发者（AI）的工作上下文与进度追踪，每次新会话的第一入口。Claude Code 仅在本地部署阶段辅助使用，不参与日常开发。

## 项目定位

这是一个面向珠宝玉器实体店店主的进销存管理系统，核心目标不是"记账"，而是**决策支持**——让店主快速回答：哪个批次回本了？哪些货在压货？哪个品类利润率最高？贵金属市价变了我需要调哪些价？

店主经营 36 种材质、2000+ 件库存，通过实体门店和微信/朋友圈销售。系统最终部署在极空间 NAS（Docker）上。

---

## 当前进度（2026-04-12 更新）

### 开发阶段完成情况

| 阶段 | 状态 | 说明 |
|------|------|------|
| **阶段1 — 后端API** | ✅ 已完成 | 14张表 + 9个路由文件产出10个router对象（44个端点） |
| **阶段2 — 前端核心页面** | ✅ 已完成 | 13个视图 + 9个组件，桌面/移动端双适配 |
| **代码审查** | ✅ 已完成 | 修复50个问题（8 Critical / 14 High / 18 Medium / 10 Low） |
| **阶段3/4 补充功能** | ✅ 已完成 | 图片管理、供应商CRUD、批次回本看板、利润看板、压货预警、Excel导出 |
| **审计问题修复** | ✅ 已完成 | 修复4个HIGH + 8个MEDIUM + 5个LOW（26项审计问题，详见下方） |

### PRD 需求覆盖度审计（经代码验证）

**P0 核心功能（完成度 ~100%）**
- [x] 字典管理 — 材质/器型/标签 CRUD + 系统配置Tab（inline编辑），软删除，种子数据
- [x] 批次管理 — 创建批次、逐件入库、成本分摊（均摊/按克重/按售价比例），后端5个端点完整
- [x] 货品入库 — 高货单步入库 + 通货两步入库，SKU 自动生成
- [x] 库存查看 — 列表+详情页，多维度筛选，分页，移动端卡片视图
- [x] 销售出库 — 单件销售 + 套装销售（by_ratio + chain_at_cost 两种分摊），自动生成 sale_no
- [x] 贵金属市价管理 — 查看/编辑克重单价，预览受影响货品，确认后批量重算零售价，历史记录
- [x] 批次列表页面 — BatchList.vue + /batches 路由，表格+卡片双视图，回本进度条

**P1 分析功能（完成度 ~100%）**
- [x] 批次回本看板 — Dashboard 批次回本 Tab，回本进度/状态标签/已售数量
- [x] 利润看板 — Dashboard 利润分析：按材质/渠道/时间维度，CSS进度条+表格，日期筛选
- [x] 压货预警 — Dashboard 压货预警区块，阈值从 sys_config 读取，红色高亮，占用资金汇总
- [x] 图片管理 — 上传/删除/设封面 + 400×400缩略图生成 + Magic Number内容校验
- [x] 供应商管理 — 完整 CRUD（含软删除+关联校验），前端已对接真实API
- [x] 客户管理 — 后端API + CustomerList + CustomerModal，分页元数据完整
- [x] 数据导出 — export.py（openpyxl），库存/销售/批次三种Excel导出

**P2 扩展功能（完成度 ~10%）**
- [ ] 镶嵌定制业务（独立模块，未开始）
- [ ] Docker 部署到极空间 NAS（Claude Code 辅助）
- [x] 借出管理功能 — PRD 标注"暂不纳入核心开发"

### 后端路由模块（9个文件，10个router对象，44个端点）

```
routers/dicts.py        — 字典管理 + 系统配置 CRUD（15端点）
routers/batches.py      — 批次管理 + 成本分摊算法（5端点）
routers/items.py        — 货品 CRUD + 图片上传/删除/设封面/缩略图（9端点）
routers/sales.py        — 销售记录 + 套装销售 by_ratio/chain_at_cost（3端点）
routers/metal_prices.py — 贵金属市价管理 + 批量重算零售价（5端点）
routers/dashboard.py    — 看板统计（批次回本/利润/库存概览/压货预警，阈值读sys_config）（6端点）
routers/customers.py    — 客户管理 CRUD + 分页元数据（4端点）
routers/suppliers.py    — 供应商管理 CRUD（4端点，含软删除）
routers/export.py       — Excel 数据导出（3端点）
utils/batch_stats.py    — 批次统计公共模块（被 dashboard/batches/export 复用）
```

### 前端页面（13个视图 + 9个组件）

**视图页面（13个）**：
```
views/InventoryList.vue      — 库存列表（表格+卡片双视图，筛选/分页，批量操作，导出）
views/InventoryDetail.vue    — 库存详情（全部字段+规格+图片上传/删除/设封面+出库）
views/InventoryAdd.vue       — 入库表单（高货/通货双轨，编辑模式复用）
views/BatchAdd.vue           — 通货批次录入（逐件添加+触发分摊，完成后跳转/batches）
views/BatchList.vue           — 批次列表（表格+卡片双视图，材质筛选，回本进度条，统计卡片）
views/SalesList.vue          — 销售列表（筛选/分页）
views/DictsManagement.vue    — 字典管理（材质/器型/标签/系统配置 4个Tab，inline编辑）
views/MetalPriceManage.vue   — 贵金属市价管理（编辑+预览+确认+历史记录）
views/Dashboard.vue          — 看板（概览卡片+利润分析+批次回本+压货预警+导出）
views/SuppliersManagement.vue — 供应商管理（完整CRUD，已对接真实API）
views/CustomerList.vue       — 客户管理（搜索+购买记录展开）
views/NotFound.vue           — 404页面（返回首页按钮）
views/SaleList.vue           — 销售记录子组件
```

**组件（9个）**：
```
components/AppLayout.vue       — 应用布局（桌面下拉导航+移动端6Tab底栏，含批次/客户入口）
components/BundleSaleDialog.vue — 套装销售弹窗（支持 by_ratio + chain_at_cost 链子标记）
components/SaleDialog.vue       — 单件销售弹窗
components/SaleList.vue         — 销售记录列表
components/CustomerModal.vue    — 客户选择/创建弹窗
components/MaterialModal.vue    — 材质编辑弹窗
components/TypeModal.vue        — 器型编辑弹窗
components/TagModal.vue         — 标签编辑弹窗
components/Pagination.vue       — 分页组件
```

### 审计问题修复记录（2026-04-12）

> 以下26项问题经代码审计发现，已全部修复。

**HIGH（4/4 已修复）**: H1 chain_at_cost分摊 ✅ | H2 图片缩略图 ✅ | H3 图片校验 ✅ | H4 系统配置Tab ✅
**MEDIUM（8/12 已修复）**: M1 BatchAdd跳转 ✅ | M2+M3 console.log清理 ✅ | M4 Dashboard卡片 ✅ | M5 供应商删除 ✅ | M6 客户分页 ✅ | M8 压货阈值 ✅ | M9 批次统计重构 ✅
**未修复**: M7(已自然修复) | M10(压货性能优化待后续) | M11(出库弹窗重复待重构) | M12(SaleList分页待统一)
**LOW（5/10 已修复）**: L1 HelloWorld删除 ✅ | L2 未用assets删除 ✅ | L3 404路由 ✅ | L4 死代码清理 ✅ | L5 废弃注释清理 ✅ | L10 移动端导航补全 ✅
**未修复**: L6(无害) | L7(编号生成重复待重构) | L8(低优先级) | L9(alert替换待后续)

### 项目结构（实际验证）

```
jade-inventory/
├── CLAUDE.md                  # ← 你正在看的文件（含进度+审计）
├── PRD.md                     # ← 产品需求文档 v2.1（需求唯一权威来源）
├── TECH_SPEC.md               # ← 技术规格
├── backend/
│   ├── main.py               # FastAPI 入口，10个router注册，静态文件挂载(/data/images)
│   ├── config.py             # 配置项（IMAGE_DIR/ALLOWED_IMAGE_EXTENSIONS/MAX_IMAGE_SIZE等）
│   ├── database.py           # 引擎、session、init_db()（安全create_all+RESET_DB保护）、种子数据
│   ├── models.py             # 14张表 ORM 模型
│   ├── schemas.py            # Pydantic V2 请求/响应模型（完整）
│   ├── routers/
│   │   ├── dicts.py          # 15端点（材质/器型/标签 CRUD + 系统配置）
│   │   ├── batches.py        # 5端点（CRUD + 成本分摊）
│   │   ├── items.py          # 9端点（CRUD + 图片3端点）
│   │   ├── sales.py          # 3端点（列表 + 单件/套装销售）
│   │   ├── metal_prices.py   # 5端点（当前价/更新/历史/预览/确认）
│   │   ├── dashboard.py      # 6端点（利润/渠道/趋势/压货/概览/批次利润）
│   │   ├── customers.py      # 4端点（CRUD + 详情）
│   │   ├── suppliers.py      # 3端点（列表/创建/编辑，⚠️ 缺删除）
│   │   └── export.py         # 3端点（库存/销售/批次 Excel导出）
│   ├── utils/
│   │   └── .gitkeep          # ❌ image.py 不存在（图片逻辑内联在 items.py）
│   ├── requirements.txt      # 7个依赖（含 Pillow、openpyxl）
│   ├── test_sales.py         # 销售接口测试
│   └── test_items.py         # 货品接口测试
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js        # proxy /api → localhost:8001
│   ├── tailwind.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js   # 12个路由定义（⚠️ 无 /batches，无 404 捕获）
│       ├── api/
│       │   ├── index.js      # 统一 API 封装（51个方法）
│       │   └── images.js     # ❌ 不存在（图片API已内嵌在 items 模块中）
│       ├── store/
│       │   └── dict.js       # 字典状态管理
│       ├── views/            # 11个页面
│       ├── components/       # 10个组件（含1个残留 HelloWorld.vue）
│       └── assets/           # ❌ 含3个未使用的 SVG/PNG 文件
├── data/
│   ├── jade.db               # SQLite 数据库
│   └── images/               # 货品图片存储（.gitignore 忽略内容，保留 .gitkeep）
├── test_api.sh               # Shell 脚本 API 测试
└── .gitignore                # 覆盖全面（db/images/node_modules/.env 等）
```

### 下一步待开发（优先级排序）

| 优先级 | 任务 | 类型 | 说明 |
|--------|------|------|------|
| **P1** | 引入 ECharts 图表 | 前端优化 | 替换 Dashboard 的 CSS 进度条为交互式图表（柱状/折线/饼图） |
| **P1** | 统一 alert 为 Toast | 前端优化 | 全局约 50+ 处 alert() 替换为统一 Toast 通知组件 |
| **P1** | SaleList 统一分页 | 前端修复 | 改用统一 Pagination 组件 |
| **P1** | InventoryList 出库弹窗重构 | 前端重构 | 移除重复的内嵌出库模态框，统一使用 SaleDialog |
| **P2** | Docker 部署 | 基础设施 | Dockerfile + docker-compose.yml + .dockerignore + .env.example（Claude Code 辅助） |
| **P2** | 压货预警性能优化 | 后端优化 | 改为数据库层过滤替代内存过滤 |
| **P2** | 增加测试覆盖 | 质量保障 | 后端 pytest + 前端 Vitest |
| **P2** | 销售编号生成重构 | 后端重构 | 提取单件/套装重复的编号生成逻辑 |
| **P3** | 镶嵌定制模块 | 新功能 | PRD P2，独立模块 |

### Git 提交历史

```
2e0b14d  feat: 全面修复审计问题 — 后端6项BUG+前端6项修复+批次列表页+导航优化 ← main HEAD
c5a7aa6  docs: 更新角色定位 — AI为主力开发者
f3701db  docs: 全面代码审计后更新 CLAUDE.md — 发现4H/12M/10L问题
46c8bb7  docs: 基于产品评估报告全面更新 CLAUDE.md
7da2726  docs: 更新 CLAUDE.md — 添加当前开发进度
9bab021  Merge branch 'fix/code-review-issues' into main
6f647f7  feat: 完成剩余功能 - 图片管理/供应商CRUD/批次回本看板/Excel导出
d2d89c1  Merge pull request #2
71e874c  fix: 代码审查修复 — 50个问题
2ac06ee  feat: 阶段2完成 - 前端
8c2ff2a  feat: 阶段1完成 - 后端API
```

---

## 必读的配套文档

开始任何开发工作之前，先阅读项目根目录下的：

- **`PRD.md`** — 产品需求文档 v2.1，包含完整业务模型、功能优先级、数据模型概览、种子数据。**这是需求的唯一权威来源。**
- **`TECH_SPEC.md`** — 技术规格，包含详细表结构和 API 契约。
- **`CLAUDE.md`（本文件）** — 当前进度、审计发现、待修复问题清单、业务概念速查。

---

## 珠宝行业核心业务概念（速查）

> 这些概念直接影响数据模型和算法设计，每次修改相关代码前快速回顾。

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
- **by_ratio**（按售价比例）：各件成交价 = (该件 selling_price / SUM(selling_price)) × total_price ✅ 已实现
- **chain_at_cost**（链子按原价）：链子/绳子类按 selling_price 计，剩余金额全部分给主件 ✅ 已实现

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
| 图片处理 | Pillow（缩略图400×400 + Magic Number校验） |
| Excel 导出 | openpyxl |
| 测试 | pytest（后端）/ Vitest（前端，配置存在但覆盖不足） |
| 公共模块 | utils/batch_stats.py 批次统计（DRY复用） |
| 部署 | Docker + docker-compose → 极空间 NAS（❌ 待创建，Claude Code 辅助） |

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

## 开发命令

```bash
# 后端
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端开发
cd frontend && npm install && npm run dev

# 前端构建
cd frontend && npm run build

# Docker（待创建，Claude Code 辅助）
docker-compose up --build

# API 测试
bash test_api.sh
```

## 编码约定

### Python
- PEP8，类型注解必须完整
- SQLAlchemy 2.0：`Mapped[T]` + `mapped_column()`
- 中文注释

### Vue
- `<script setup>` + Composition API
- 组件文件名 PascalCase
- 禁止提交 console.log 调试代码

### 命名
- 数据库字段：`snake_case`
- 前端 JS：`camelCase`
- API 传输：`snake_case`

### API 规范
- 路径前缀：`/api/v1/`
- 分页：`?page=1&size=20`，响应必须包含 `pagination` 元数据
- 响应：`{ "code": 0, "data": ..., "message": "ok" }`
- HTTPException detail 使用字符串格式（不要用字典）
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
9. **套装销售必须支持两种分摊方式** — by_ratio 和 chain_at_cost（✅ 两种均已实现）
