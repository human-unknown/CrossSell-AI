"""
API 路由 — 健康检查
==================
"""

from fastapi import APIRouter

from app.config import get_settings
from app.schemas import HealthResponse

router = APIRouter(tags=["System"])
settings = get_settings()


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """服务健康检查"""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        service=settings.APP_NAME,
    )
