"""
API 路由 — 任务查询（前端兼容格式）
=================================
GET /api/task/{task_id}/status  — 查询进度 (GenerationProgress)
GET /api/task/{task_id}/result  — 获取结果 (GenerationResult)
GET /api/tasks                  — 历史任务列表 (TaskRecord[])
"""

import logging
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.errors import TaskNotFoundError, TaskNotReadyError
from app.models import Task, TaskInput
from app.schemas import (
    TaskStatusResponse,
    TaskResultResponse,
    TaskListResponse,
    TaskListItem,
    FrontendVideoResult,
    FrontendCopyResult,
    build_frontend_steps,
    build_frontend_strategy,
    platform_label,
    TASK_STATUS_MAP,
    to_camel,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Tasks"])


@router.get("/api/task/{task_id}/status")
async def get_task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    """查询任务进度 — 返回前端 GenerationProgress 格式"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if task is None:
        raise TaskNotFoundError(message=f"Task not found: {task_id}")

    steps_obj = build_frontend_steps(task.steps or [])
    frontend_status = TASK_STATUS_MAP.get(task.status, task.status)

    return to_camel(TaskStatusResponse(
        task_id=task.id,
        status=frontend_status,
        steps=steps_obj,
        message=task.error_message or "",
    ))


@router.get("/api/task/{task_id}/result")
async def get_task_result(task_id: str, db: AsyncSession = Depends(get_db)):
    """获取任务生成结果 — 返回前端 GenerationResult 格式"""
    task_result = await db.execute(
        select(Task).where(Task.id == task_id).options(selectinload(Task.result_data))
    )
    task = task_result.scalar_one_or_none()

    if task is None:
        raise TaskNotFoundError(message=f"Task not found: {task_id}")

    if task.status not in ("completed", "failed"):
        raise TaskNotReadyError(
            message=f"Task result not ready, current status: {task.status}"
        )

    result = task.result_data

    # 转换 videos
    videos: list[FrontendVideoResult] = []
    for v in (result.videos if result else []):
        p = v.get("platform", "")
        videos.append(
            FrontendVideoResult(
                id=str(uuid.uuid4()),
                platform=platform_label(p),
                url=v.get("url") or "",
                thumbnail="",
                title=v.get("script") or v.get("full_script") or "",
                duration=v.get("duration") or 0,
            )
        )

    # 转换 copies
    copies: list[FrontendCopyResult] = []
    for c in (result.copies if result else []):
        p = c.get("platform", "")
        text = c.get("text") or ""
        copies.append(
            FrontendCopyResult(
                id=str(uuid.uuid4()),
                platform=platform_label(p),
                content=text,
                hashtags=c.get("hashtags") or [],
                characterCount=c.get("character_count") or len(text),
            )
        )

    # 转换 strategy
    strategy = build_frontend_strategy(result.strategy if result else None)

    return to_camel(TaskResultResponse(
        task_id=task.id,
        videos=videos,
        copies=copies,
        strategy=strategy,
    ))


@router.get("/api/tasks")
async def list_tasks(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取历史任务列表 — 前端 TaskRecord[] 格式"""
    if page < 1:
        page = 1
    if size < 1 or size > 100:
        size = 20

    # 总数 — 使用 func.count 避免全量加载导致锁冲突
    count_result = await db.execute(select(func.count(Task.id)))
    total = count_result.scalar_one()

    # 分页
    tasks_result = await db.execute(
        select(Task)
        .options(selectinload(Task.input_data))
        .order_by(desc(Task.created_at))
        .offset((page - 1) * size)
        .limit(size)
    )
    tasks = tasks_result.scalars().all()

    items = []
    for task in tasks:
        input_data = task.input_data
        product_name = input_data.product_name if input_data else ""
        platforms = [platform_label(p) for p in (input_data.target_platforms if input_data else [])]
        content_types = input_data.content_types if input_data else []

        items.append(
            TaskListItem(
                taskId=task.id,
                productName=product_name,
                createdAt=task.created_at.isoformat() if task.created_at else "",
                status=TASK_STATUS_MAP.get(task.status, task.status),
                platforms=platforms,
                contentTypes=content_types,
            )
        )

    return to_camel(TaskListResponse(tasks=items, total=total))
