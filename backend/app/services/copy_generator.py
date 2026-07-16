"""
多平台文案生成服务 — Pipeline B
==============================
并发调用 LLM 为每个 (平台 × 市场) 生成本土化社媒文案。
"""

import asyncio
import json
import logging

from app.services.model_router import get_model_router, ModelRouterError
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 平台文案规范
PLATFORM_COPY_GUIDE = {
    "tiktok": {
        "max_chars": 150,
        "tone": "casual, trendy, Gen-Z voice",
        "best_practices": "short sentences, strong emoji use, trending sounds references",
    },
    "instagram": {
        "max_chars": 2200,
        "tone": "aesthetic, inspirational, lifestyle-oriented",
        "best_practices": "storytelling, 5-10 hashtags, emoji spacing, line breaks",
    },
    "youtube_shorts": {
        "max_chars": 500,
        "tone": "educational, entertaining, value-first",
        "best_practices": "question hook, curiosity gap, strong CTA",
    },
    "facebook": {
        "max_chars": 63206,
        "tone": "friendly, conversational, community-building",
        "best_practices": "question to engage, relatable story, link CTA",
    },
    "pinterest": {
        "max_chars": 500,
        "tone": "inspirational, helpful, aspirational",
        "best_practices": "keyword-rich, 'save for later' prompts, lifestyle context",
    },
}


async def generate_copy_batch(
    product_name: str,
    selling_points: list[str],
    description: str,
    markets: list[str],
    platforms: list[str],
) -> list[dict]:
    """
    并发为所有 (平台 × 市场) 组合生成文案

    Returns:
        [
          {
            "platform": "instagram",
            "language": "en",
            "market": "美国",
            "text": "Meet your new adventure buddy...",
            "hashtags": ["#portablespeaker", "#outdoorgear"],
            "character_count": 280
          },
          ...
        ]
    """
    tasks = []
    for platform in platforms:
        for market in markets:
            tasks.append(
                _generate_single_copy(product_name, selling_points, description, market, platform)
            )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    copies = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"文案生成失败: #{i} {result}")
            copies.append(_fallback_copy(tasks[i]))
        else:
            copies.append(result)

    return copies


async def _generate_single_copy(
    product_name: str,
    selling_points: list[str],
    description: str,
    market: str,
    platform: str,
) -> dict:
    """生成单个 (平台 × 市场) 的社媒文案"""
    guide = PLATFORM_COPY_GUIDE.get(platform, PLATFORM_COPY_GUIDE["tiktok"])

    system_prompt = f"""You are an expert cross-border e-commerce social media copywriter.

Platform: {platform}
Tone: {guide['tone']}
Best practices: {guide['best_practices']}
Target market: {market}

Write copy in the local language of the target market. Focus on benefits, create desire, and include a call to action.
Output as JSON with fields: platform, language, market, text, hashtags, character_count."""

    user_prompt = f"""Write a compelling {platform} post for this product:

Product: {product_name}
Key Selling Points: {', '.join(selling_points)}
Description: {description or '[Not provided]'}
Market: {market}

Return JSON:
{{
  "platform": "{platform}",
  "language": "en",
  "market": "{market}",
  "text": "the full post copy",
  "hashtags": ["#tag1", "#tag2"],
  "character_count": 0
}}"""

    try:
        router = get_model_router()
        result = await router.chat_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=settings.TEXT_MODEL,
            temperature=0.85,
        )
        # 确保 character_count 正确
        result["character_count"] = len(result.get("text", ""))
        logger.info(f"文案生成: {product_name} / {platform} / {market}")
        return result

    except (ModelRouterError, json.JSONDecodeError) as e:
        logger.error(f"文案生成失败 [{platform}/{market}]: {e}")
        return _fallback_copy_params(product_name, selling_points, market, platform)


def _fallback_copy(task_coro) -> dict:
    """从 gather task 恢复回退"""
    return {}


def _fallback_copy_params(
    product_name: str,
    selling_points: list[str],
    market: str,
    platform: str,
) -> dict:
    """API 失败时的回退文案"""
    text = f"Discover the {product_name}! {'. '.join(selling_points)}. Shop now! 🛍️"
    return {
        "platform": platform,
        "language": "en",
        "market": market,
        "text": text,
        "hashtags": [f"#{word}" for word in product_name.split()[:3]],
        "character_count": len(text),
    }
