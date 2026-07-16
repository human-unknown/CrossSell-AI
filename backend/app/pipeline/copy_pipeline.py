"""
Pipeline B：多平台文案矩阵
=========================
编排文案生成 → 结果聚合
"""

import logging
from typing import Callable, Awaitable

from app.services.copy_generator import generate_copy_batch

logger = logging.getLogger(__name__)


async def run_copy_pipeline(
    product_name: str,
    selling_points: list[str],
    description: str,
    markets: list[str],
    platforms: list[str],
    update_step: Callable[[str, str], Awaitable[None]],
    update_progress: Callable[[float], Awaitable[None]],
) -> list[dict]:
    """
    执行多平台文案生成流水线

    Returns:
        文案列表
    """
    await update_step("copy_generation", "in_progress")
    await update_progress(0.0)

    copies = await generate_copy_batch(
        product_name=product_name,
        selling_points=selling_points,
        description=description,
        markets=markets,
        platforms=platforms,
    )

    await update_step("copy_generation", "done")
    await update_progress(1.0)

    logger.info(f"文案矩阵完成: {len(copies)} 条文案")
    return copies
