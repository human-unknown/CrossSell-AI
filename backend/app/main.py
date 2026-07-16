"""
CrossSell AI — FastAPI 应用入口
===============================
跨境社媒内容引擎后端服务。

启动方式:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

API 文档:
    http://localhost:8000/docs    (Swagger UI)
    http://localhost:8000/redoc   (ReDoc)
"""

import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings, OUTPUT_DIR
from app.database import init_db, close_db
from app.errors import AppError
from app.routes import health, generate, tasks, stats

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 应用生命周期
# ---------------------------------------------------------------------------

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动 / 关闭时的初始化与清理"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    await init_db()
    logger.info("✅ 数据库初始化完成")

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    yield

    logger.info("🛑 应用关闭中...")
    await close_db()
    logger.info("✅ 数据库连接已关闭")


# ---------------------------------------------------------------------------
# FastAPI 实例
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="跨境品牌卖家 AI 社媒内容引擎 — 产品卖点 → 多平台本土化内容 → 智能投流全链路自动化",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS 中间件
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# 静态文件（输出的视频 / 图片）
# ---------------------------------------------------------------------------

app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# ---------------------------------------------------------------------------
# 全局异常处理
# ---------------------------------------------------------------------------


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """业务异常 — 根据子类返回对应 status_code"""
    logger.warning(
        f"业务异常 [{exc.error_code}] {request.method} {request.url.path}: {exc.message}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """未预期的内部错误"""
    logger.exception(f"未处理异常: {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "status_code": 500,
        },
    )


# ---------------------------------------------------------------------------
# 注册路由
# ---------------------------------------------------------------------------

app.include_router(health.router)
app.include_router(generate.router)
app.include_router(tasks.router)
app.include_router(stats.router, prefix="/api/stats", tags=["Stats"])


# ---------------------------------------------------------------------------
# 根路径
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
    }
