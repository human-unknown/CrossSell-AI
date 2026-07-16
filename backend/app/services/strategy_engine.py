"""
投流策略引擎 — Pipeline C
========================
调用推理模型分析产品与市场，输出投放策略建议。
"""

import json
import logging

from app.services.model_router import get_model_router, ModelRouterError
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def generate_strategy(
    product_name: str,
    selling_points: list[str],
    description: str,
    markets: list[str],
    platforms: list[str],
) -> dict:
    """
    生成投放策略建议

    Returns:
        {
            "recommended_platform": "tiktok",
            "daily_budget_suggestion": {"tiktok": 50, "meta": 30},
            "estimated_roas": "2.5-3.8x",
            "detailed_analysis": "...",
            "content_angles": [...],
            "audience_targeting": {...}
        }
    """
    system_prompt = """You are a senior digital advertising strategist specializing in cross-border e-commerce.

Analyze the product and target markets to provide actionable advertising strategy.
Consider: platform algorithms, audience behavior, budget efficiency, content-to-ad fit.

Output as clean JSON."""

    user_prompt = f"""Create an advertising strategy for:

Product: {product_name}
Selling Points: {', '.join(selling_points)}
Description: {description or '[Not provided]'}
Target Markets: {', '.join(markets)}
Available Platforms: {', '.join(platforms)}

Return JSON:
{{
  "recommended_platform": "which platform to prioritize",
  "daily_budget_suggestion": {{"platform_name": budget_usd}},
  "estimated_roas": "range like 2.5-3.8x",
  "detailed_analysis": "2-3 paragraph strategic analysis",
  "content_angles": ["angle 1", "angle 2", "angle 3"],
  "audience_targeting": {{
    "age_range": "e.g. 18-35",
    "interests": ["interest1", "interest2"],
    "lookalike_source": "suggestion"
  }}
}}"""

    try:
        router = get_model_router()
        result = await router.chat_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=settings.REASONING_MODEL,
            temperature=0.5,
        )
        logger.info(f"投流策略生成成功: {product_name}")
        return result

    except (ModelRouterError, json.JSONDecodeError) as e:
        logger.error(f"投流策略生成失败: {e}")
        return _fallback_strategy(platforms, markets)


def _fallback_strategy(platforms: list[str], markets: list[str]) -> dict:
    """API 失败时的回退策略"""
    primary = platforms[0] if platforms else "tiktok"
    budget = {}
    total = 100
    per_platform = total // max(len(platforms), 1)
    for p in platforms:
        budget[p] = per_platform

    return {
        "recommended_platform": primary,
        "daily_budget_suggestion": budget,
        "estimated_roas": "2.0-3.0x",
        "detailed_analysis": (
            f"For markets {', '.join(markets)}, we recommend starting with "
            f"{primary} as the primary channel due to its high engagement rates "
            f"and cost-effective CPM. Allocate budget gradually and optimize "
            f"based on week-1 performance data. A/B test at least 3 creative angles."
        ),
        "content_angles": [
            "Product demo with real usage scenarios",
            "Customer testimonial / unboxing style",
            "Problem-solution before/after comparison",
        ],
        "audience_targeting": {
            "age_range": "18-45",
            "interests": ["online shopping", "lifestyle products", "tech gadgets"],
            "lookalike_source": "past purchasers",
        },
    }
