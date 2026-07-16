"""
API 路由 — 任务查询
==================
GET /api/task/{task_id}/status  — 查询进度
GET /api/task/{task_id}/result  — 获取结果
GET /api/tasks                  — 历史任务列表
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Task, TaskInput, TaskResult
from app.schemas import (
    TaskStatusResponse,
    TaskResultResponse,
    TaskListResponse,
    TaskListItem,
    StepStatus,
    VideoResult,
    CopyResult,
    StrategyResult,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Tasks"])


@router.get("/api/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    """查询任务进度"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        current_step=task.current_step,
        steps=[StepStatus(**s) for s in (task.steps or [])],
        error_message=task.error_message,
    )


@router.get("/api/task/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(task_id: str, db: AsyncSession = Depends(get_db)):
    """获取任务生成结果"""
    # 查询任务
    task_result = await db.execute(
        select(Task).where(Task.id == task_id).options(selectinload(Task.result_data))
    )
    task = task_result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    if task.status not in ("completed", "failed"):
        raise HTTPException(
            status_code=425,
            detail=f"任务尚未完成，当前状态: {task.status}",
        )

    result = task.result_data

    return TaskResultResponse(
        task_id=task.id,
        status=task.status,
        videos=[VideoResult(**v) for v in (result.videos if result else [])],
        copies=[CopyResult(**c) for c in (result.copies if result else [])],
        strategy=StrategyResult(**(result.strategy)) if (result and result.strategy) else None,
    )


@router.get("/api/tasks", response_model=TaskListResponse)
async def list_tasks(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取历史任务列表"""
    if page < 1:
        page = 1
    if size < 1 or size > 100:
        size = 20

    # 总数
    count_result = await db.execute(select(Task))
    total = len(count_result.scalars().all())

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
        product_name = ""
        if task.input_data:
            product_name = task.input_data.product_name

        items.append(
            TaskListItem(
                task_id=task.id,
                product_name=product_name,
                status=task.status,
                progress=task.progress,
                created_at=task.created_at,
            )
        )

    return TaskListResponse(items=items, total=total, page=page, size=size)
