"""
FastAPI 应用入口 — 注册路由、中间件、生命周期钩子和静态文件托管。
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path


# ── 配置路径（支持环境变量覆盖，适配 Docker / 本地开发）──
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", "/app/config"))
DATA_DIR_ROOT = Path(os.getenv("DATA_DIR", "/app/data"))
TEMPLATE_DIR = Path(os.getenv("TEMPLATE_DIR", "/app/templates"))


# ── 首次启动：自动生成配置文件到持久化目录 ──
def _ensure_config_files() -> None:
    """
    容器首次启动时，自动将内置配置模板写入配置目录。
    如果 .env 已存在（用户之前修改过），则跳过，不覆盖用户配置。
    这样 config/ 映射到本地后，用户可以在NAS文件管理中直接看到和编辑配置文件。
    """
    # 如果 config 目录不存在，则自动创建
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    env_file = CONFIG_DIR / ".env"
    # 模板放在 templates/ 下，不会被 volume 挂载覆盖
    template_file = TEMPLATE_DIR / "env.template"

    if not env_file.exists() and template_file.exists():
        import shutil
        shutil.copy2(str(template_file), str(env_file))
        print("[config] 首次启动：已从模板生成 .env，请编辑此文件配置 JWT_SECRET 等参数")

    # 确保 data 目录也存在
    DATA_DIR_ROOT.mkdir(parents=True, exist_ok=True)
    (DATA_DIR_ROOT / "images").mkdir(parents=True, exist_ok=True)
    (DATA_DIR_ROOT / "barcodes").mkdir(parents=True, exist_ok=True)

try:
    _ensure_config_files()
except PermissionError:
    print("[config] 跳过配置文件生成（无写入权限，可能为本地开发环境）")

# ── 自动加载 .env（必须放在所有业务模块导入之前）──
def _load_config_env() -> None:
    """
    从配置目录的 .env 加载环境变量。
    文件不存在则跳过，不报错。
    格式：每行 KEY=VALUE，支持 # 注释和空行。
    仅对未设置的环境变量生效（不覆盖 docker-compose/environment 中已设置的值）。
    """
    env_path = CONFIG_DIR / ".env"
    if not env_path.exists():
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        print(f"[config] 加载 .env 失败: {e}")

try:
    _load_config_env()
except Exception:
    pass

# ── 以下为正常的模块导入（此时 config/.env 已加载到 os.environ）──
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers.dicts import router as dicts_router
from routers.dicts import router_config
from routers.batches import router as batches_router
from routers.items import router as items_router
from routers.sales import router as sales_router
from routers.customers import router as customers_router
from routers.suppliers import router as suppliers_router
from routers.dashboard import router as dashboard_router
from routers.metal_prices import router as metal_prices_router
from routers.export import router as export_router
from routers.label import router as label_router
from routers.pricing import router as pricing_router
from routers.auth import router as auth_router
from config import IMAGE_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时初始化数据库（建表 + 种子数据）。"""
    init_db()
    yield


app = FastAPI(
    title="玉器店进销存系统",
    description="珠宝玉器实体店进销存管理 API — 支持货品管理、销售管理和利润看板。",
    version="1.0.0",
    lifespan=lifespan,
)

# ── 全局异常处理：统一包装为 ApiResponse 格式 ──

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "data": None, "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 取第一条校验错误的描述作为 message
    errors = exc.errors()
    msg = errors[0].get("msg", str(exc)) if errors else str(exc)
    return JSONResponse(
        status_code=422,
        content={"code": 422, "data": None, "message": msg},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    # 如果请求的不是 API 路径，返回前端 index.html（SPA 路由）
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"code": 404, "data": None, "message": "Not Found"}
        )
    # 返回前端入口页面
    return FileResponse("static/index.html")


# ── CORS（通过环境变量配置允许的来源，默认开发模式允许所有）──
_CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
_origins_list = _CORS_ORIGINS.split(",") if _CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 调试中间件：仅在 DEBUG=true 时记录请求路径
_DEBUG_MODE = os.getenv("DEBUG", "").lower() == "true"

@app.middleware("http")
async def log_requests(request: Request, call_next):
    if _DEBUG_MODE:
        import time
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        print(f"[{response.status_code}] {request.method} {request.url.path} - {duration:.3f}s")
    else:
        response = await call_next(request)
    return response

# ── API 路由（统一前缀 /api/v1）──
_API_PREFIX = "/api/v1"

app.include_router(dicts_router,      prefix=_API_PREFIX)
app.include_router(router_config,     prefix=_API_PREFIX)
app.include_router(batches_router,    prefix=_API_PREFIX)
app.include_router(items_router,      prefix=_API_PREFIX)
app.include_router(sales_router,      prefix=_API_PREFIX)
app.include_router(customers_router,  prefix=_API_PREFIX)
app.include_router(suppliers_router,   prefix=_API_PREFIX)
app.include_router(dashboard_router,    prefix=_API_PREFIX)
app.include_router(metal_prices_router,  prefix=_API_PREFIX)
app.include_router(export_router,       prefix=_API_PREFIX)
app.include_router(label_router,        prefix=_API_PREFIX)
app.include_router(pricing_router,      prefix=_API_PREFIX)
app.include_router(auth_router,        prefix=_API_PREFIX)


# ── 健康检查 ──
@app.get("/api/health", tags=["系统"], summary="健康检查")
def health():
    return {"status": "ok"}


# ── 前端静态文件服务 ──
app.mount("/", StaticFiles(directory="static", html=True), name="frontend")

# ── 图片静态文件服务 ──
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/data/images", StaticFiles(directory=str(IMAGE_DIR)), name="images")
