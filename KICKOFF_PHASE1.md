# 开发交底文档 — 阶段1启动

## 你的角色

你是这个项目的全栈开发者。你要根据本文档和配套的三份参考文档（CLAUDE.md、PRD.md、TECH_SPEC.md）来完成开发工作。

## 项目背景（一句话）

给一个珠宝玉器实体店做轻量进销存系统，部署在极空间 NAS 上，核心解决"哪些品类赚钱、哪些在压货"的问题。

## 当前阶段：阶段1 — 后端 API 骨架

### 目标

搭建完整的后端 API，启动后通过 FastAPI 自带的 Swagger UI（/docs）可以操作所有接口。

### 必须阅读的文档

在写任何代码之前，请先完整阅读以下文档并理解其内容：

1. **CLAUDE.md** — 项目总览，包含业务概念、技术栈、项目结构、编码约定
2. **PRD.md** — 产品需求文档，重点看第3节功能需求和第5节种子数据
3. **TECH_SPEC.md** — 技术规格，重点看第2节表结构和第3节 API 契约

### 技术栈（不可更改）

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0（使用 Mapped Column 风格，不用旧的 declarative_base）
- SQLite（数据库文件路径：`data/jade.db`）
- Pydantic V2

### 需要创建的文件（按顺序）

```
backend/
├── requirements.txt       # 依赖清单
├── database.py           # 数据库连接 + init_db() + 种子数据
├── models.py             # ORM 模型（8张表）
├── schemas.py            # Pydantic 请求/响应模型
├── main.py               # FastAPI 入口
└── routers/
    ├── __init__.py
    ├── dicts.py           # 字典管理 API
    ├── items.py           # 货品管理 API
    ├── sales.py           # 销售记录 API
    └── dashboard.py       # 看板统计 API
```

### 关键业务规则（写代码时必须遵守）

1. **动态分类**：材质、器型、标签全部来自字典表，代码中不得出现任何硬编码的品类枚举（如 `if material == "翡翠"` 这种写法是禁止的）。

2. **一物一价 + 批量定价共存**：
   - 每件货品有唯一的 `sku_code`
   - 通货可以有 `batch_code`（同款多件共享），批量入库时系统自动按规则生成 N 个 sku_code
   - SKU 生成规则：`{sku_prefix}-{YYYYMMDD}-{三位序号}`，如 `SJ-20240315-001`

3. **软删除**：
   - 字典表用 `is_active = false` 停用，不物理删除
   - 货品表用 `is_deleted = true` 标记删除
   - 查询列表时默认过滤掉已停用/已删除的数据

4. **销售出库联动**：创建销售记录时，必须同时把对应货品的 status 改为 `sold`，且已售货品不可再次出库。

5. **状态枚举**：货品状态只有四种值 `in_stock`、`sold`、`returned`、`lent_out`，销售渠道只有三种值 `store`、`wechat`、`ecommerce`。

6. **API 响应格式**：所有接口统一返回 `{ "code": 0, "data": ..., "message": "ok" }`，错误时 code 为非零整数。

### 种子数据（init_db 中实现）

首次启动时，如果 dict_material 表为空，自动插入以下数据：

**材质（10个）**：翡翠、和田玉、水晶、白银、珍珠、檀木、朱砂、蜜蜡、玛瑙、南红

**器型（8个，每个材质都关联这8个）**：手镯、挂件、手串/手链、戒指、项链、耳饰、摆件、吊坠

**标签（按分组）**：
- 种水：玻璃种、冰种、糯冰种、糯种、豆种
- 颜色：满绿、飘花、紫罗兰、黄翡、墨翠、无色
- 工艺：手工雕、机雕、素面
- 题材：观音、佛公、平安扣、如意、山水、花鸟

### 数据库模型要点

严格按 TECH_SPEC.md 第2节实现，这里强调几个容易出错的点：

- `dict_type` 的 unique 约束是 `(material_id, name)` 的组合唯一，不是 name 单独唯一
- `item_tag` 是多对多关联表，联合主键 `(item_id, tag_id)`
- `items.purchase_date` 是 DATE 类型（不是 DATETIME），可以为空
- `items.cost_price` 和 `selling_price` 都是 FLOAT，不可为空
- `sale_records.sale_date` 是 DATE 类型，不可为空
- SQLAlchemy 使用 2.0 风格：`Mapped[T]` + `mapped_column()`，不要用旧版的 `Column()` 写法

### API 端点清单

严格按 TECH_SPEC.md 第3节实现，共计约 20 个端点：

**字典（6个）**：材质 GET/POST/PUT/DELETE + 器型 GET/POST/DELETE + 标签 GET/POST/DELETE

**货品（7个）**：列表 GET + 详情 GET + 单件入库 POST + 批量入库 POST + 编辑 PUT + 删除 DELETE + （图片相关3个留到阶段3）

**销售（2个）**：列表 GET + 创建 POST

**看板（5个）**：按品类利润 + 按渠道利润 + 销售趋势 + 压货预警 + 概览数据

### 编码规范

- 所有 Python 函数必须有完整的类型注解
- 使用中文注释
- 文件顶部写模块级别的 docstring 说明这个文件的职责
- 路由函数用中文 summary 和 description，这样 Swagger UI 界面对店主友好

### 验收检查清单

完成后请自行检查以下每一项：

- [ ] `pip install -r requirements.txt` 无报错
- [ ] `uvicorn main:app --reload` 启动成功
- [ ] 首次启动后 `data/jade.db` 文件自动创建
- [ ] /docs 页面可见所有 API 端点
- [ ] 种子数据已自动插入（GET /api/v1/dicts/materials 返回10个材质）
- [ ] 能在 Swagger 上完成：新增材质 → 在该材质下新增器型 → 新增标签
- [ ] 能在 Swagger 上完成：单件入库 → 列表查到 → 详情查到 → 编辑 → 软删除后列表查不到
- [ ] 能在 Swagger 上完成：入库 → 创建销售记录 → 货品状态变为 sold → 再次出库报错
- [ ] 按品类利润接口返回数据正确（毛利 = actual_price - cost_price）
- [ ] 压货预警接口能返回在库超过指定天数的货品

### 开始开发

请按以下顺序逐个文件编写：

1. `requirements.txt`
2. `database.py`（含种子数据逻辑）
3. `models.py`
4. `schemas.py`
5. `routers/dicts.py`
6. `routers/items.py`
7. `routers/sales.py`
8. `routers/dashboard.py`
9. `main.py`

每写完一个文件，简要说明你做了什么和需要注意的点，然后继续下一个。全部完成后，运行验收检查清单。
