# CLAUDE.md — 玉器店进销存系统

## 你在做什么

这是一个面向珠宝玉器实体店店主的轻量级进销存管理系统。店主经营翡翠、水晶、白银、珍珠、檀木、朱砂等多材质品类，库存 2000+ 件，通过实体门店和微信/朋友圈销售。系统最终部署在极空间 NAS（Docker）上。

**核心目标：让店主清楚每个品类赚不赚钱、哪些货在压资金。**

## 珠宝行业关键业务概念

开始写任何代码之前，必须理解以下概念——它们直接影响数据模型和交互设计：

### 1. 一物一价 vs 批量定价（最重要）
- **高货**（翡翠手镯、精品挂件）：世界上只有这一件，唯一编号，唯一价格。
- **通货**（水晶手串、朱砂手串、银饰）：同款有几十件，统一进价统一售价。
- 系统必须同时支持两种模式。高货用 `sku_code` 唯一标识；通货用 `batch_code` 把同款归组，共享价格。

### 2. 动态品类体系
- 三级分类：**材质 → 器型 → 标签**
- 所有分类存在数据库字典表中，店主可随时新增（比如明天进了一批蜜蜡，直接加）。
- **绝对不要在代码中硬编码任何品类枚举。**

### 3. 货品状态流转
```
          ┌──→ 已售(sold)
在库(in_stock)──┼──→ 借出(lent_out) ──→ 在库 / 已售
          └──→ 已退(returned)
```
- 「借出」是朋友圈代卖的常见场景：货给朋友帮忙卖，卖掉了记销售，没卖退回来。

### 4. 利润计算
- 毛利 = 实际成交价 - 进货成本
- 毛利率 = 毛利 / 实际成交价
- 看板核心维度：按材质、按渠道、按时间段

### 5. 库龄与压货
- 库龄 = 今天 - 进货日期
- 超过阈值（默认 90 天）视为压货，需要在看板中预警
- 压货意味着资金被占用，是店主最关心的经营风险之一

## 技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| 后端 | Python 3.11+ / FastAPI | 轻量、自带 API 文档、Python 数据处理方便 |
| ORM | SQLAlchemy 2.0 | 类型注解风格，Mapped Column |
| 数据库 | SQLite | 零运维，2000件数据量足够，备份=拷贝文件 |
| 前端 | Vue 3 (Composition API) + Vite | 轻量、上手快 |
| 样式 | Tailwind CSS | 原子化，不用写 CSS 文件 |
| HTTP 客户端 | Axios | 前端调后端 API |
| 图片处理 | Pillow | 缩略图生成 |
| 部署 | Docker + docker-compose | 极空间 NAS 原生支持 |

## 项目结构

```
jade-inventory/
├── CLAUDE.md
├── README.md
├── backend/
│   ├── main.py               # FastAPI 入口
│   ├── database.py           # 引擎、session、init_db()
│   ├── models.py             # 所有 ORM 模型
│   ├── schemas.py            # Pydantic 请求/响应模型
│   ├── routers/
│   │   ├── dicts.py          # 字典管理（材质/器型/标签）
│   │   ├── items.py          # 货品 CRUD
│   │   ├── sales.py          # 销售记录
│   │   └── dashboard.py      # 统计看板
│   ├── utils/
│   │   └── image.py          # 图片上传/缩略图
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js        # dev 时 proxy /api → localhost:8000
│   ├── tailwind.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js
│       ├── api/index.js      # axios 实例 + 各模块 API 函数
│       ├── views/            # 页面级组件
│       └── components/       # 通用组件
├── data/
│   ├── jade.db               # 运行时自动生成
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
# API 文档自动可用：http://localhost:8000/docs

# 前端开发
cd frontend && npm install && npm run dev
# 访问 http://localhost:5173，API 请求自动代理到 8000

# 前端构建（输出到 backend/static/，由后端托管）
cd frontend && npm run build

# Docker
docker-compose up --build
```

## API 规范

- 路径前缀：`/api/v1/`
- 列表接口统一分页：`?page=1&size=20`
- 筛选用 query string：`?material_id=1&status=in_stock`
- 成功响应：`{ "code": 0, "data": ..., "message": "ok" }`
- 错误响应：`{ "code": 非零, "data": null, "message": "错误描述" }`
- 字典项删除一律用软删除（`is_active = false`），不物理删除

## 编码约定

- Python：PEP8，类型注解完整，中文注释
- Vue：`<script setup>` + Composition API，不用 Options API
- 命名：数据库字段 snake_case，前端 JS 变量 camelCase，API 传输 snake_case
- 前端构建产物输出到 `backend/static/`，生产模式由 FastAPI 直接托管

## 开发阶段

| 阶段 | 范围 |
|------|------|
| **阶段1** | 后端骨架：database.py + models.py + schemas.py + 字典 CRUD + 货品 CRUD + 销售记录 |
| **阶段2** | 前端页面：库存列表（筛选/搜索/分页）、入库表单、销售出库、字典管理 |
| **阶段3** | 利润看板 + 压货预警 + 图片上传管理 |
| **阶段4** | Docker 打包 + 极空间部署文档 |

**每个阶段结束后系统应可独立运行。** 阶段1完成后可通过 Swagger UI 操作；阶段2完成后有完整前端。
