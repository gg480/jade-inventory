# CLAUDE.md — 玉器店进销存系统

## 你在做什么

这是一个面向珠宝玉器实体店店主的进销存管理系统，核心目标不是"记账"，而是**决策支持**——让店主快速回答：哪个批次回本了？哪些货在压货？哪个品类利润率最高？贵金属市价变了我需要调哪些价？

店主经营 36 种材质、2000+ 件库存，通过实体门店和微信/朋友圈销售。系统最终部署在极空间 NAS（Docker）上。

---

## 当前进度（2026-04-12 更新，经全面代码审计验证）

### 开发阶段完成情况

| 阶段 | 状态 | 说明 |
|------|------|------|
| **阶段1 — 后端API** | ✅ 已完成 | 14张表 + 9个路由文件产出10个router对象（43个端点） |
| **阶段2 — 前端核心页面** | ✅ 已完成 | 11个视图 + 10个组件，桌面/移动端双适配 |
| **代码审查** | ✅ 已完成 | 修复50个问题（8 Critical / 14 High / 18 Medium / 10 Low），已合并到 main |
| **阶段3/4 补充功能** | ✅ 已完成 | 图片管理、供应商对接、批次回本看板、利润看板、压货预警、Excel导出 |

### PRD 需求覆盖度审计（经代码验证）

**P0 核心功能（完成度 ~92%）**
- [x] 字典管理 — 材质/器型/标签 CRUD + 系统配置，软删除，种子数据自动插入（36材质/9器型/22标签/4配置/2市价）
- [x] 批次管理 — 创建批次、逐件入库、成本分摊（均摊/按克重/按售价比例），后端5个端点完整
- [x] 货品入库 — 高货单步入库 + 通货两步入库，SKU 自动生成（规则：`{材质缩写}-{YYYYMMDD}-{3位序号}`）
- [x] 库存查看 — 列表+详情页，多维度筛选（材质/器型/状态/批次/柜台/关键词），分页，移动端卡片视图
- [x] 销售出库 — 单件销售 + 套装销售，自动生成 sale_no。⚠️ chain_at_cost 分摊方式后端未实现（仅 by_ratio）
- [x] 贵金属市价管理 — 查看/编辑克重单价，预览受影响货品，确认后批量重算零售价，历史记录
- [ ] 批次列表页面 — BatchAdd 完成后跳转 `/batches` 但该路由未定义，无 BatchList.vue

**P1 分析功能（完成度 ~95%）**
- [x] 批次回本看板 — Dashboard 批次回本 Tab，表格展示回本进度/状态标签/已售数量
- [x] 利润看板 — Dashboard 利润分析：按材质利润（CSS进度条）、按渠道利润（门店/微信/电商）、销售趋势（月度列表），日期筛选
- [x] 压货预警 — Dashboard 压货预警区块，可配置阈值天数，红色高亮，底部汇总（件数+占用资金）
- [x] 图片管理 — items.py 图片上传/删除/设封面端点，前端 InventoryDetail 图片上传/删除/设封面。⚠️ 缺少缩略图生成（Pillow已安装但未使用）
- [x] 供应商管理 — 后端 CRU（⚠️ 缺 Delete 端点）+ 前端已对接真实 API
- [x] 客户管理 — 后端 API + 前端 CustomerList 页面 + CustomerModal 组件。⚠️ 客户列表缺少分页元数据
- [x] 数据导出 — export.py（openpyxl），库存/销售/批次三种 Excel 导出

**P2 扩展功能（完成度 ~0%）**
- [ ] 镶嵌定制业务（独立模块，未开始）
- [ ] Docker 部署到极空间 NAS（❌ 缺少 Dockerfile / docker-compose.yml / .dockerignore / .env.example）
- [ ] 借出管理功能（PRD 明确标注"暂不纳入核心开发"）

### 后端路由模块（9个文件，10个router对象，43个端点）

```
routers/dicts.py        — 字典管理 + 系统配置 CRUD（15端点）
routers/batches.py      — 批次管理 + 成本分摊算法（5端点）
routers/items.py        — 货品 CRUD + 图片上传/删除/设封面（9端点）
routers/sales.py        — 销售记录 + 套装销售（3端点）
routers/metal_prices.py — 贵金属市价管理 + 批量重算零售价（5端点）
routers/dashboard.py    — 看板统计（批次回本/利润/库存概览/压货预警）（6端点）
routers/customers.py    — 客户管理 CRUD（4端点）
routers/suppliers.py    — 供应商管理 CRU（3端点，⚠️ 缺 Delete）
routers/export.py       — Excel 数据导出（3端点）
```

### 前端页面（11个视图 + 10个组件）

**视图页面（11个）**：
```
views/InventoryList.vue      — 库存列表（表格+卡片双视图，筛选/分页，批量操作，导出）
views/InventoryDetail.vue    — 库存详情（全部字段+规格+图片上传/删除/设封面+出库）
views/InventoryAdd.vue       — 入库表单（高货/通货双轨，编辑模式复用，⚠️ 7处console.log残留）
views/BatchAdd.vue           — 通货批次录入（逐件添加+触发分摊，⚠️ 完成后跳转到不存在的/batches）
views/SalesList.vue          — 销售列表（筛选/分页，⚠️ 未用统一Pagination组件）
views/DictsManagement.vue    — 字典管理（材质/器型/标签 3个Tab，⚠️ 缺少"系统配置"Tab）
views/MetalPriceManage.vue   — 贵金属市价管理（编辑+预览+确认+历史记录）
views/Dashboard.vue          — 看板（概览卡片+利润分析+批次回本+压货预警+导出，⚠️ 概览卡片有重复）
views/SuppliersManagement.vue — 供应商管理（CRU，已对接真实API）
views/CustomerList.vue       — 客户管理（搜索+购买记录展开）
views/SaleList.vue           — 销售记录子组件（在 SalesList 内嵌使用）
```

**组件（10个，含1个残留）**：
```
components/AppLayout.vue       — 应用布局（桌面顶栏+移动端底栏，⚠️ 移动端缺少"客户"入口）
components/BundleSaleDialog.vue — 套装销售弹窗（⚠️ chain_at_cost 标记为"开发中"已禁用）
components/SaleDialog.vue       — 单件销售弹窗
components/SaleList.vue         — 销售记录列表
components/CustomerModal.vue    — 客户选择/创建弹窗
components/MaterialModal.vue    — 材质编辑弹窗
components/TypeModal.vue        — 器型编辑弹窗
components/TagModal.vue         — 标签编辑弹窗
components/Pagination.vue       — 分页组件
components/HelloWorld.vue       — ❌ Vite 脚手架残留，未被引用，应删除
```

### 全栈代码审计发现（2026-04-12）

> 以下问题经逐行代码审计确认，按严重程度分级。

#### 🔴 HIGH — 必须修复（4个）

| # | 位置 | 问题 | 影响 |
|---|------|------|------|
| H1 | `sales.py L278` | 套装销售**不支持 chain_at_cost 分摊方式**，代码强制拒绝非 by_ratio 方法，但 schemas.py 声称支持 by_ratio/chain_at_cost | 前后端契约不一致，套装销售功能不完整 |
| H2 | `items.py upload_images` | 图片上传**未生成缩略图**（PRD 要求 400×400），Pillow 已安装但未使用 | 列表页加载原图影响性能，移动端流量浪费 |
| H3 | `items.py L628-632` | 图片上传**仅校验扩展名，未校验文件内容**（Magic Number） | 安全风险：可上传伪装为 .jpg 的恶意文件 |
| H4 | `DictsManagement.vue` | **缺少"系统配置"Tab** — 后端 API 已就绪（GET/PUT /config/），但前端无管理界面 | 经营成本率/上浮比例等关键参数无法通过 UI 修改 |

#### ⚠️ MEDIUM — 应当修复（12个）

| # | 位置 | 问题 |
|---|------|------|
| M1 | `BatchAdd.vue:787` | 完成后跳转 `/batches` 但路由未定义，用户看到空白页 |
| M2 | `InventoryAdd.vue` | 7 处 `console.log` 调试残留 |
| M3 | `router/index.js:97` | `console.log` 调试残留 |
| M4 | `Dashboard.vue:212-233` | 概览卡片有2张重复（"在库货品"和"本月销售"各出现两次），复制粘贴错误 |
| M5 | `SuppliersManagement.vue` | 后端缺少 DELETE 端点，供应商只能新增/编辑，无法停用/删除 |
| M6 | `customers.py` | 客户列表传了 page/size 参数但**响应缺少 pagination 元数据** |
| M7 | `suppliers.py L78,117` | HTTPException detail 使用字典格式而非字符串，与其他路由返回格式不一致 |
| M8 | `dashboard.py L33` | 压货阈值使用 `config.ALERT_DAYS` 硬编码，**未从 sys_config.aging_threshold_days 读取** |
| M9 | `dashboard.py / batches.py / export.py` | 批次统计逻辑**重复实现3次**（约50行/处），违反 DRY 原则 |
| M10 | `dashboard.py L314-370` | 压货预警全量加载在库货品到内存再做 Python 级过滤，数据量大时性能差 |
| M11 | `InventoryList.vue:745-838` | 内嵌了完整的出库模态框，与独立的 SaleDialog 组件功能重复 |
| M12 | `SaleList.vue` | 自实现分页逻辑，未使用统一的 Pagination 组件 |

#### ℹ️ LOW — 建议优化（10个）

| # | 位置 | 问题 |
|---|------|------|
| L1 | `components/HelloWorld.vue` | Vite 脚手架残留，未被引用，应删除 |
| L2 | `assets/vite.svg, hero.png, vue.svg` | 未使用的资源文件，应删除 |
| L3 | `router/index.js` | 无 404 捕获路由（`/:pathMatch(.*)*`） |
| L4 | `InventoryList.vue:53` | `showList` 变量始终为 true，死代码 |
| L5 | `DictsManagement.vue:197-237` | 大量注释掉的废弃代码 |
| L6 | `items.py L39` | `_EDITABLE_STATUS` 包含 `lent_out` 但借出功能未开发 |
| L7 | `sales.py L222-235 / L348-363` | 单件/套装销售编号生成逻辑重复实现 |
| L8 | `metal_prices.py L107` | `effective_date` 硬编码为今天，不支持自定义生效日期 |
| L9 | 全局 | 约 50+ 处 `alert()` 用作用户提示，建议替换为统一 Toast 组件 |
| L10 | `AppLayout.vue` | 移动端底部 Tab 栏缺少"客户"和"供应商"入口 |

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
| **P0-BUG** | 实现 chain_at_cost 套装分摊 | 后端修复 | sales.py 仅支持 by_ratio，PRD 要求两种方式 |
| **P0-BUG** | 图片缩略图生成 | 后端修复 | items.py 使用 Pillow 生成 400×400 缩略图 |
| **P0-BUG** | 图片文件内容校验 | 后端修复 | Magic Number 检测，防止伪装文件上传 |
| **P0-BUG** | 新增"系统配置"Tab | 前端修复 | DictsManagement.vue 缺少配置管理 UI |
| **P0-BUG** | 修复 BatchAdd 跳转 | 前端修复 | 跳转 /batches 改为 /inventory 或新建批次列表页 |
| **P0-BUG** | 修复 Dashboard 卡片重复 | 前端修复 | 概览卡片2张重复，复制粘贴错误 |
| **P1** | 新增批次列表页面 | 前端新功能 | BatchList.vue + /batches 路由 |
| **P1** | 压货阈值读 sys_config | 后端修复 | dashboard.py 应从数据库读 aging_threshold_days 而非 config.ALERT_DAYS |
| **P1** | 供应商删除端点 | 后端新功能 | DELETE /suppliers/{id} 软删除 |
| **P1** | 客户列表分页元数据 | 后端修复 | 响应中补充 pagination 字段 |
| **P1** | 清理调试代码 | 全栈清理 | 删除 console.log × 8处、HelloWorld.vue、未使用 assets |
| **P1** | 引入 ECharts 图表 | 前端优化 | 替换 Dashboard 的 CSS 进度条为交互式图表 |
| **P2** | Docker 部署 | 基础设施 | Dockerfile + docker-compose.yml + .dockerignore + .env.example |
| **P2** | 提取重复批次统计逻辑 | 后端重构 | dashboard/batches/export 三处重复代码提取为公共模块 |
| **P2** | 统一 alert 为 Toast | 前端优化 | 全局约 50+ 处 alert() 替换 |
| **P2** | 移动端导航补全 | 前端优化 | 底部 Tab 增加"客户"/"供应商"入口 |
| **P2** | 增加测试覆盖 | 质量保障 | 后端 pytest + 前端 Vitest，覆盖看板/批次/导出模块 |
| **P3** | 镶嵌定制模块 | 新功能 | PRD P2，独立模块 |

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
- **by_ratio**（按售价比例）：各件成交价 = (该件 selling_price / SUM(selling_price)) × total_price ✅ 已实现
- **chain_at_cost**（链子按原价）：链子/绳子类按 selling_price 计，剩余金额全部分给主件 ❌ 后端未实现

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
| 图片处理 | Pillow（已安装，缩略图功能待实现） |
| Excel 导出 | openpyxl |
| 测试 | pytest（后端）/ Vitest（前端，配置存在但覆盖不足） |
| 部署 | Docker + docker-compose → 极空间 NAS（❌ 待创建） |

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

# Docker（待创建）
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
2. **不硬编码业务参数** — 经营成本率/上浮比例/压货天数等全部走 sys_config（⚠️ dashboard.py 压货阈值当前违规使用了 config.ALERT_DAYS）
3. **不物理删除** — 字典用 is_active，货品用 is_deleted
4. **不引入外部数据库** — 只用 SQLite
5. **前端必须适配手机** — 店主日常用手机操作，375px 宽度优先
6. **批次成本分摊必须在货品录完后触发** — 不是入库时实时算
7. **回本判断只看已回款现金** — 不估算库存价值
8. **数据库安全初始化** — 仅 RESET_DB=true 时才 DROP ALL，正常启动用 create_all
9. **套装销售必须支持两种分摊方式** — by_ratio 和 chain_at_cost（⚠️ chain_at_cost 当前未实现）
