"""
Pydantic Schemas — 请求/响应验证
===============================
所有 API 接口的入参和出参定义。
响应字段统一使用 camelCase（与前端 TypeScript 类型对齐）。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ---------------------------------------------------------------------------
# 枚举
# ---------------------------------------------------------------------------

VALID_MARKETS = ["美国", "英国", "德国", "法国", "日本", "韩国", "东南亚", "巴西", "中东"]
VALID_PLATFORMS = ["tiktok", "instagram", "youtube_shorts", "facebook", "pinterest"]
VALID_CONTENT_TYPES = ["video", "copy"]

# 后端步骤名 → 前端步骤键名
STEP_NAME_MAP = {
    "script_generation": "script",
    "text_to_speech": "voiceover",
    "image_generation": "videoRender",
    "video_rendering": "videoRender",
    "copy_generation": "copyOptimize",
    "strategy_analysis": None,  # 前端不展示
}

# 状态映射
STATUS_MAP = {
    "pending": "waiting",
    "in_progress": "active",
    "done": "completed",
    "failed": "error",
}

TASK_STATUS_MAP = {
    "pending": "pending",
    "processing": "generating",
    "completed": "completed",
    "failed": "failed",
}

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
    """POST /api/generate 响应 — 前端期望 { taskId: string }"""

    task_id: str = Field(
        serialization_alias="taskId",
        default_factory=lambda: str(uuid.uuid4()),
    )


# ---------------------------------------------------------------------------
# 进度（前端格式：GenerationProgress）
# ---------------------------------------------------------------------------


class FrontendStepStatus(BaseModel):
    """前端步骤状态对象 { script, voiceover, videoRender, copyOptimize }"""

    script: str = "waiting"
    voiceover: str = "waiting"
    videoRender: str = "waiting"
    copyOptimize: str = "waiting"


class TaskStatusResponse(BaseModel):
    """GET /api/task/{task_id}/status — 前端 GenerationProgress 格式"""

    task_id: str = Field(serialization_alias="taskId")
    status: str  # pending | generating | completed | failed
    steps: FrontendStepStatus = Field(default_factory=FrontendStepStatus)
    message: str = ""


# ---------------------------------------------------------------------------
# 结果（前端格式：GenerationResult）
# ---------------------------------------------------------------------------


class FrontendVideoResult(BaseModel):
    """前端 VideoResult"""

    id: str = ""
    platform: str = ""
    url: str = ""
    thumbnail: str = ""
    title: str = ""
    duration: int = 0


class FrontendCopyResult(BaseModel):
    """前端 CopyResult"""

    id: str = ""
    platform: str = ""
    content: str = ""
    hashtags: list[str] = []
    characterCount: int = 0


class StrategyPlatform(BaseModel):
    """投流平台建议"""

    platform: str = ""
    dailyBudget: str = ""
    expectedROAS: str = ""
    reasoning: str = ""


class BudgetItem(BaseModel):
    """预算分配"""

    platform: str = ""
    percentage: int = 0


class FrontendStrategyResult(BaseModel):
    """前端 StrategyResult"""

    recommendedPlatforms: list[StrategyPlatform] = []
    budgetAllocation: list[BudgetItem] = []


class TaskResultResponse(BaseModel):
    """GET /api/task/{task_id}/result — 前端 GenerationResult 格式"""

    task_id: str = Field(serialization_alias="taskId")
    videos: list[FrontendVideoResult] = []
    copies: list[FrontendCopyResult] = []
    strategy: FrontendStrategyResult = Field(default_factory=FrontendStrategyResult)


# ---------------------------------------------------------------------------
# 任务列表
# ---------------------------------------------------------------------------


class TaskListItem(BaseModel):
    """前端 TaskRecord 格式"""

    taskId: str = ""
    productName: str = ""
    createdAt: str = ""
    status: str = ""
    platforms: list[str] = []
    contentTypes: list[str] = []


class TaskListResponse(BaseModel):
    tasks: list[TaskListItem] = []
    total: int = 0


# ---------------------------------------------------------------------------
# 统计（前端格式：WeeklyStats）
# ---------------------------------------------------------------------------


class WeeklyStatsResponse(BaseModel):
    """GET /api/stats/weekly — 前端 WeeklyStats 格式"""

    videoCount: int = 0
    copyCount: int = 0
    strategyCount: int = 0
    totalTasks: int = 0
    completedTasks: int = 0


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


# ---------------------------------------------------------------------------
# 转换辅助函数
# ---------------------------------------------------------------------------


def to_camel(model: BaseModel) -> dict:
    """将 Pydantic 模型序列化为 camelCase JSON（绕过 FastAPI 序列化问题）"""
    return model.model_dump(by_alias=True, exclude_none=False)


def build_frontend_steps(backend_steps: list[dict]) -> FrontendStepStatus:
    """将后端 [{name, status}] 转换为前端 {script, voiceover, videoRender, copyOptimize}"""
    result = {
        "script": "waiting",
        "voiceover": "waiting",
        "videoRender": "waiting",
        "copyOptimize": "waiting",
    }
    for step in (backend_steps or []):
        name = step.get("name", "")
        status = step.get("status", "pending")
        frontend_key = STEP_NAME_MAP.get(name)
        if frontend_key:
            mapped = STATUS_MAP.get(status, status)
            # 取最高优先级状态：completed > active > waiting
            current = result.get(frontend_key, "waiting")
            priority = {"completed": 4, "error": 3, "active": 2, "waiting": 1}
            if priority.get(mapped, 0) > priority.get(current, 0):
                result[frontend_key] = mapped
    return FrontendStepStatus(**result)


def build_frontend_strategy(strategy: dict | None) -> FrontendStrategyResult:
    """将后端扁平策略转换为前端嵌套策略"""
    if not strategy:
        return FrontendStrategyResult()

    recommended_platforms = []
    budget_allocation = []

    rec_platform = strategy.get("recommended_platform", "")
    budget_suggestion = strategy.get("daily_budget_suggestion", {})
    estimated_roas = strategy.get("estimated_roas", "")
    detailed_analysis = strategy.get("detailed_analysis", "")

    # 构建 recommendedPlatforms — 安全转换预算数字
    try:
        numeric_budgets = {k: float(v) for k, v in budget_suggestion.items()
                          if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).isdigit())}
    except (ValueError, TypeError):
        numeric_budgets = {}
    total_budget = sum(numeric_budgets.values()) or 1

    budgets = numeric_budgets if numeric_budgets else budget_suggestion
    for platform, budget in budgets.items():
        budget_num = float(budget) if isinstance(budget, (int, float)) else 1
        recommended_platforms.append(
            StrategyPlatform(
                platform=f"{platform.title()} Ads",
                dailyBudget=f"${int(budget_num)}",
                expectedROAS=estimated_roas,
                reasoning=detailed_analysis[:200] if detailed_analysis else f"基于{platform}平台数据分析",
            )
        )
        budget_allocation.append(
            BudgetItem(
                platform=f"{platform.title()} Ads",
                percentage=round(budget_num / total_budget * 100),
            )
        )

    # 如果只有推荐平台但没有预算，用推荐平台填充
    if not recommended_platforms and rec_platform:
        recommended_platforms.append(
            StrategyPlatform(
                platform=f"{rec_platform.title()} Ads",
                dailyBudget="$50",
                expectedROAS=estimated_roas or "2.0x-3.0x",
                reasoning=detailed_analysis[:200] if detailed_analysis else "基于数据分析推荐",
            )
        )
        budget_allocation.append(BudgetItem(platform=f"{rec_platform.title()} Ads", percentage=100))

    return FrontendStrategyResult(
        recommendedPlatforms=recommended_platforms or [
            StrategyPlatform(platform="TikTok Ads", dailyBudget="$50", expectedROAS="2.5x-3.8x",
                             reasoning="基于目标市场特征推荐首选投放平台"),
            StrategyPlatform(platform="Meta Ads", dailyBudget="$40", expectedROAS="2.0x-3.2x",
                             reasoning="适合搭配视觉内容联合投放"),
        ],
        budgetAllocation=budget_allocation or [
            BudgetItem(platform="TikTok Ads", percentage=45),
            BudgetItem(platform="Meta Ads", percentage=55),
        ],
    )


def platform_label(p: str) -> str:
    """后端平台ID → 前端显示名称"""
    labels = {
        "tiktok": "TikTok",
        "instagram": "Instagram",
        "youtube_shorts": "YouTube Shorts",
        "facebook": "Facebook",
        "pinterest": "Pinterest",
    }
    return labels.get(p, p)
