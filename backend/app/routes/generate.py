"""
API 路由 — 内容生成
==================
POST /api/generate — 触发内容生成任务
"""

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Task, TaskInput, TaskResult
from app.schemas import GenerateRequest, GenerateResponse
from app.worker import execute_generation_task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Generation"])


@router.post("/api/generate", response_model=GenerateResponse, status_code=202)
async def create_generation(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    触发内容生成任务

    接受产品信息和目标配置，创建异步任务并立即返回 task_id。
    前端通过 GET /api/task/{task_id}/status 轮询进度。
    """

    # 1. 创建 Task 记录
    from app.models import generate_uuid
    task_id = generate_uuid()

    task = Task(
        id=task_id,
        status="processing",
        progress=0.0,
        current_step="pending",
        steps=[
            {"name": "script_generation", "status": "pending"},
            {"name": "text_to_speech", "status": "pending"},
            {"name": "image_generation", "status": "pending"},
            {"name": "video_rendering", "status": "pending"},
            {"name": "copy_generation", "status": "pending"},
            {"name": "strategy_analysis", "status": "pending"},
        ],
    )

    # 2. 创建 TaskInput 记录
    task_input = TaskInput(
        task_id=task_id,
        product_name=request.product_name,
        product_selling_points=request.product_selling_points,
        product_description=request.product_description,
        target_markets=request.target_markets,
        target_platforms=request.target_platforms,
        content_types=request.content_types,
        product_image_url=request.product_image_url,
    )

    db.add(task)
    db.add(task_input)
    await db.commit()

    # 3. 在后台执行生成任务
    background_tasks.add_task(
        execute_generation_task,
        task_id=task_id,
        product_name=request.product_name,
        selling_points=request.product_selling_points,
        description=request.product_description or "",
        markets=request.target_markets,
        platforms=request.target_platforms,
        content_types=request.content_types,
    )

    logger.info(f"任务已创建: {task_id} — {request.product_name}")

    return GenerateResponse(task_id=task_id, status="processing")
