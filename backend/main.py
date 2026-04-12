"""
FastAPI 应用入口 — 注册路由、中间件、生命周期钩子和静态文件托管。
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

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
from config import IMAGE_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时初始化数据库（建表 + 种子数据）。"""
    init_db()
    yield


app = FastAPI(
    title="玉器店进销存系统",
    description="珠宝玉器实体店进销存管理 API — 支持货品管理、销售出库和利润看板。",
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


# ── 健康检查 ──
@app.get("/api/health", tags=["系统"], summary="健康检查")
def health():
    return {"status": "ok"}


# ── 前端静态文件服务 ──
app.mount("/", StaticFiles(directory="static", html=True), name="frontend")

# ── 图片静态文件服务 ──
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/data/images", StaticFiles(directory=str(IMAGE_DIR)), name="images")


