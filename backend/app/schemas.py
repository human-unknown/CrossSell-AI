"""
Pydantic Schemas — 请求/响应验证
===============================
所有 API 接口的入参和出参定义。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# 枚举
# ---------------------------------------------------------------------------

VALID_MARKETS = ["美国", "英国", "德国", "法国", "日本", "韩国", "东南亚", "巴西", "中东"]
VALID_PLATFORMS = ["tiktok", "instagram", "youtube_shorts", "facebook", "pinterest"]
VALID_CONTENT_TYPES = ["video", "copy"]
VALID_STEP_NAMES = [
    "script_generation",
    "text_to_speech",
    "image_generation",
    "video_rendering",
    "copy_generation",
    "strategy_analysis",
]

# ---------------------------------------------------------------------------
# 生成请求
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    """POST /api/generate 请求体"""

    product_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        examples=["便携式蓝牙音箱"],
        description="产品名称",
    )
    product_selling_points: list[str] = Field(
        default_factory=list,
        max_length=10,
        examples=[["IPX7防水", "24小时续航", "TWS串联立体声"]],
        description="产品核心卖点",
    )
    product_description: Optional[str] = Field(
        default=None,
        max_length=2000,
        examples=["一款适合户外露营的便携蓝牙音箱..."],
        description="产品详细描述",
    )
    target_markets: list[str] = Field(
        default_factory=list,
        min_length=1,
        examples=[["美国", "日本"]],
        description="目标市场",
    )
    target_platforms: list[str] = Field(
        default_factory=list,
        min_length=1,
        examples=[["tiktok", "instagram", "youtube_shorts"]],
        description="目标平台",
    )
    content_types: list[str] = Field(
        default_factory=list,
        min_length=1,
        examples=[["video", "copy"]],
        description="内容类型",
    )
    product_image_url: Optional[str] = Field(
        default=None,
        max_length=500,
        examples=["https://example.com/product.jpg"],
        description="产品图片URL（可选）",
    )

    @field_validator("target_markets")
    @classmethod
    def check_markets(cls, v: list[str]) -> list[str]:
        invalid = set(v) - set(VALID_MARKETS)
        if invalid:
            raise ValueError(f"不支持的市场: {invalid}. 支持: {VALID_MARKETS}")
        return v

    @field_validator("target_platforms")
    @classmethod
    def check_platforms(cls, v: list[str]) -> list[str]:
        invalid = set(v) - set(VALID_PLATFORMS)
        if invalid:
            raise ValueError(f"不支持的平台: {invalid}. 支持: {VALID_PLATFORMS}")
        return v

    @field_validator("content_types")
    @classmethod
    def check_content_types(cls, v: list[str]) -> list[str]:
        invalid = set(v) - set(VALID_CONTENT_TYPES)
        if invalid:
            raise ValueError(f"不支持的内容类型: {invalid}. 支持: {VALID_CONTENT_TYPES}")
        return v


class GenerateResponse(BaseModel):
    """POST /api/generate 响应"""

    task_id: str
    status: str = "processing"


# ---------------------------------------------------------------------------
# 步骤状态
# ---------------------------------------------------------------------------


class StepStatus(BaseModel):
    name: str
    status: str  # pending | in_progress | done | failed
    error: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """GET /api/task/{task_id}/status 响应"""

    task_id: str
    status: str  # pending | processing | completed | failed
    progress: float
    current_step: Optional[str] = None
    steps: list[StepStatus] = []
    error_message: Optional[str] = None


# ---------------------------------------------------------------------------
# 结果
# ---------------------------------------------------------------------------


class VideoResult(BaseModel):
    platform: str
    url: Optional[str] = None
    script: Optional[str] = None
    duration: Optional[int] = None


class CopyResult(BaseModel):
    platform: str
    language: str
    market: str
    text: str
    hashtags: list[str] = []
    character_count: int


class StrategyResult(BaseModel):
    recommended_platform: Optional[str] = None
    daily_budget_suggestion: dict[str, float] = {}
    estimated_roas: Optional[str] = None
    detailed_analysis: Optional[str] = None


class TaskResultResponse(BaseModel):
    """GET /api/task/{task_id}/result 响应"""

    task_id: str
    status: str
    videos: list[VideoResult] = []
    copies: list[CopyResult] = []
    strategy: Optional[StrategyResult] = None


# ---------------------------------------------------------------------------
# 任务列表
# ---------------------------------------------------------------------------


class TaskListItem(BaseModel):
    task_id: str
    product_name: str
    status: str
    progress: float
    created_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskListItem]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# 通用
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    service: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
