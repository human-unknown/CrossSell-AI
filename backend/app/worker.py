"""
后台任务 Worker
===============
协调 Pipeline A/B/C 的执行，更新数据库状态。

这是整个系统的核心调度器——从 API 层接收 task_id，
逐步执行三个 Pipeline 并更新数据库中的任务进度。
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import async_session
from app.models import Task, TaskResult

logger = logging.getLogger(__name__)


async def execute_generation_task(
    task_id: str,
    product_name: str,
    selling_points: list[str],
    description: str,
    markets: list[str],
    platforms: list[str],
    content_types: list[str],
):
    """
    后台执行完整的内容生成任务

    流程：
    1. 如果需要视频 → Pipeline A (视频生产)
    2. 如果需要文案 → Pipeline B (文案矩阵)
    3. Pipeline C (投流策略) — 总是执行
    4. 汇总结果写入数据库
    """
    videos = []
    copies = []
    strategy = None

    # 内联异步回调（在同一个事件循环中运行，无需线程适配）
    async def update_step(step_name: str, status: str):
        await _update_task_step(task_id, step_name, status)

    async def update_progress(progress: float):
        await _update_task_progress(task_id, progress)

    try:
        # --------------------------------------------------------------
        # Pipeline A: 视频生产
        # --------------------------------------------------------------
        if "video" in content_types:
            from app.pipeline.video_pipeline import run_video_pipeline

            logger.info(f"[{task_id}] 启动视频生产流水线")

            videos = await run_video_pipeline(
                task_id=task_id,
                product_name=product_name,
                selling_points=selling_points,
                description=description,
                markets=markets,
                platforms=platforms,
                update_step=update_step,
                update_progress=update_progress,
            )

            logger.info(f"[{task_id}] 视频生产完成: {len(videos)} 个")

        # --------------------------------------------------------------
        # Pipeline B: 文案矩阵
        # --------------------------------------------------------------
        if "copy" in content_types:
            from app.pipeline.copy_pipeline import run_copy_pipeline

            logger.info(f"[{task_id}] 启动文案矩阵生成")

            copies = await run_copy_pipeline(
                product_name=product_name,
                selling_points=selling_points,
                description=description,
                markets=markets,
                platforms=platforms,
                update_step=update_step,
                update_progress=update_progress,
            )

            logger.info(f"[{task_id}] 文案矩阵完成: {len(copies)} 条")

        # --------------------------------------------------------------
        # Pipeline C: 投流策略 (总是执行)
        # --------------------------------------------------------------
        from app.pipeline.strategy_pipeline import run_strategy_pipeline

        logger.info(f"[{task_id}] 启动投流策略分析")

        strategy = await run_strategy_pipeline(
            product_name=product_name,
            selling_points=selling_points,
            description=description,
            markets=markets,
            platforms=platforms,
            update_step=update_step,
            update_progress=update_progress,
        )

        # --------------------------------------------------------------
        # 保存结果到数据库
        # --------------------------------------------------------------
        async with async_session() as db:
            task_result = TaskResult(
                task_id=task_id,
                videos=videos,
                copies=copies,
                strategy=strategy,
            )
            db.add(task_result)

            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one()
            task.status = "completed"
            task.progress = 1.0
            task.current_step = "done"
            task.updated_at = datetime.now(timezone.utc)

            await db.commit()

        logger.info(f"[{task_id}] ✅ 任务完成！视频 {len(videos)} 个，文案 {len(copies)} 条")

    except Exception as e:
        logger.exception(f"[{task_id}] ❌ 任务执行失败: {e}")

        try:
            async with async_session() as db:
                result = await db.execute(select(Task).where(Task.id == task_id))
                task = result.scalar_one()
                task.status = "failed"
                task.error_message = str(e)[:1000]
                task.updated_at = datetime.now(timezone.utc)
                await db.commit()
        except Exception as db_err:
            logger.error(f"[{task_id}] 更新失败状态时出错: {db_err}")


# ------------------------------------------------------------------
# 数据库更新
# ------------------------------------------------------------------

async def _update_task_step(task_id: str, step_name: str, status: str):
    """更新任务中某个步骤的状态"""
    try:
        async with async_session() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if task is None:
                return

            steps = list(task.steps or [])
            found = False
            for step in steps:
                if step.get("name") == step_name:
                    step["status"] = status
                    found = True
                    break
            if not found:
                steps.append({"name": step_name, "status": status})

            task.steps = steps
            task.current_step = step_name
            task.updated_at = datetime.now(timezone.utc)
            await db.commit()
    except Exception as e:
        logger.error(f"更新步骤失败 [{task_id}/{step_name}]: {e}")


async def _update_task_progress(task_id: str, progress: float):
    """更新任务整体进度"""
    try:
        async with async_session() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if task is None:
                return

            task.progress = max(task.progress, min(progress, 1.0))
            task.updated_at = datetime.now(timezone.utc)
            await db.commit()
    except Exception as e:
        logger.error(f"更新进度失败 [{task_id}]: {e}")
