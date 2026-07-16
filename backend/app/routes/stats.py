"""
API 路由 — 统计（前端兼容格式）
===============================
GET /api/stats/weekly — Dashboard 本周统计 (WeeklyStats)
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Task
from app.schemas import WeeklyStatsResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _week_start() -> datetime:
    """返回本周一 00:00:00 UTC"""
    now = datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("/weekly", response_model=WeeklyStatsResponse)
async def get_weekly_stats(db: AsyncSession = Depends(get_db)):
    """
    获取本周 Dashboard 统计数据 — 返回前端 WeeklyStats 格式。

    统计范围：本周一 00:00:00 UTC 至今。
    """
    week_start = _week_start()

    # ---- 本周全部任务 ----
    tasks_result = await db.execute(
        select(Task).where(Task.created_at >= week_start)
    )
    all_tasks = tasks_result.scalars().all()
    total_tasks = len(all_tasks)

    # ---- 本周完成的任务 + 结果 ----
    completed_result = await db.execute(
        select(Task)
        .where(Task.status == "completed", Task.created_at >= week_start)
        .options(selectinload(Task.result_data))
    )
    completed_tasks = completed_result.scalars().all()

    video_count = 0
    copy_count = 0
    strategy_count = 0

    for task in completed_tasks:
        result = task.result_data
        if result is None:
            continue

        videos = result.videos or []
        copies = result.copies or []

        video_count += len(videos)
        copy_count += len(copies)

        if result.strategy:
            strategy_count += 1

    completed_tasks_count = len(completed_tasks)

    logger.info(
        f"Weekly stats: tasks={total_tasks} completed={completed_tasks_count} "
        f"videos={video_count} copies={copy_count} strategies={strategy_count}"
    )

    return WeeklyStatsResponse(
        videoCount=video_count,
        copyCount=copy_count,
        strategyCount=strategy_count,
        totalTasks=total_tasks,
        completedTasks=completed_tasks_count,
    )
