"""
Pipeline C：投流策略引擎
=======================
调用推理模型输出投放策略建议。
"""

import logging
from typing import Callable, Awaitable

from app.services.strategy_engine import generate_strategy

logger = logging.getLogger(__name__)


async def run_strategy_pipeline(
    product_name: str,
    selling_points: list[str],
    description: str,
    markets: list[str],
    platforms: list[str],
    update_step: Callable[[str, str], Awaitable[None]],
    update_progress: Callable[[float], Awaitable[None]],
) -> dict:
    """
    执行投流策略分析

    Returns:
        策略字典
    """
    await update_step("strategy_analysis", "in_progress")
    await update_progress(0.5)

    strategy = await generate_strategy(
        product_name=product_name,
        selling_points=selling_points,
        description=description,
        markets=markets,
        platforms=platforms,
    )

    await update_step("strategy_analysis", "done")
    await update_progress(1.0)

    logger.info(f"投流策略生成完成: {strategy.get('recommended_platform', 'N/A')}")
    return strategy
