"""
FastAPI 应用入口 — 注册路由、中间件、生命周期钩子和静态文件托管。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers import dicts, items, sales, dashboard


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


# ── CORS（开发阶段允许所有来源，生产可收窄到实际域名）──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API 路由（统一前缀 /api/v1）──
_API_PREFIX = "/api/v1"

app.include_router(dicts.router,      prefix=_API_PREFIX)
app.include_router(items.router,      prefix=_API_PREFIX)
app.include_router(sales.router,      prefix=_API_PREFIX)
app.include_router(dashboard.router,  prefix=_API_PREFIX)


# ── 健康检查 ──
@app.get("/api/health", tags=["系统"], summary="健康检查")
def health():
    return {"status": "ok"}


# ── 生产模式：托管前端构建产物 ──
_STATIC_DIR = Path(__file__).parent / "static"
if _STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
