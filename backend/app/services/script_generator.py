"""
脚本生成服务 — Pipeline A Step 1
===============================
调用大语言模型将产品信息转化为短视频分镜脚本。
"""

import json
import logging

from app.services.model_router import get_model_router, ModelRouterError
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 平台视频配置
PLATFORM_CONFIG = {
    "tiktok": {"aspect": "9:16", "max_duration": 60, "style": "快节奏、强视觉冲击、hook开头"},
    "instagram": {"aspect": "4:5", "max_duration": 90, "style": "精致美学、生活方式、自然过渡"},
    "youtube_shorts": {"aspect": "9:16", "max_duration": 60, "style": "信息量足、教程感、节奏明快"},
    "facebook": {"aspect": "1:1", "max_duration": 120, "style": "亲切真实、社交属性、故事感"},
    "pinterest": {"aspect": "2:3", "max_duration": 60, "style": "高审美、灵感型、图文并茂"},
}

# 市场语言映射
MARKET_LANGUAGES = {
    "美国": "en",
    "英国": "en",
    "德国": "de",
    "法国": "fr",
    "日本": "ja",
    "韩国": "ko",
    "东南亚": "en",
    "巴西": "pt",
    "中东": "ar",
}


async def generate_script(
    product_name: str,
    selling_points: list[str],
    description: str,
    market: str,
    platform: str,
    duration: int = 15,
) -> dict:
    """
    为指定产品和平台生成短视频脚本

    Returns:
        {
            "platform": "tiktok",
            "market": "美国",
            "language": "en",
            "duration": 15,
            "scenes": [
                {"scene": 1, "visual": "...", "audio": "...", "duration": 5},
                ...
            ],
            "hook": "...",
            "hashtags": [...],
            "full_script": "..."
        }
    """
    platform_cfg = PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG["tiktok"])
    language = MARKET_LANGUAGES.get(market, "en")

    system_prompt = f"""You are a professional short-video scriptwriter specializing in cross-border e-commerce social media marketing.

Target market: {market}
Platform: {platform} ({platform_cfg['style']})
Video format: {platform_cfg['aspect']}, max {min(duration, platform_cfg['max_duration'])} seconds

Output requirements:
1. Write the script in the target language ({language})
2. Structure as JSON with scenes, each containing visual description, audio/voiceover, and duration
3. Open with a strong hook (first 3 seconds must grab attention)
4. Include platform-appropriate hashtags
5. Focus on benefits, not just features"""

    user_prompt = f"""Create a short video script for the following product:

Product: {product_name}
Key Selling Points: {', '.join(selling_points)}
Description: {description or '[No description provided]'}
Target Duration: {duration} seconds

Output as JSON:
{{
  "platform": "{platform}",
  "market": "{market}",
  "language": "{language}",
  "duration": {duration},
  "hook": "3-second hook text",
  "scenes": [
    {{"scene": 1, "visual": "describe what to show", "audio": "voiceover or sound effect", "duration": 5}},
    ...
  ],
  "hashtags": ["#tag1", "#tag2", ...],
  "full_script": "complete narration text"
}}"""

    try:
        router = get_model_router()
        result = await router.chat_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=settings.TEXT_MODEL,
            temperature=0.8,
        )
        logger.info(f"脚本生成成功: {product_name} / {platform} / {market}")
        return result

    except (ModelRouterError, json.JSONDecodeError) as e:
        logger.error(f"脚本生成失败: {e}")
        return _fallback_script(product_name, selling_points, market, platform, duration, language)


def _fallback_script(
    product_name: str,
    selling_points: list[str],
    market: str,
    platform: str,
    duration: int,
    language: str,
) -> dict:
    """当 API 调用失败时的回退脚本模板"""
    return {
        "platform": platform,
        "market": market,
        "language": language,
        "duration": duration,
        "hook": f"Check out the amazing {product_name}!",
        "scenes": [
            {
                "scene": 1,
                "visual": f"Product reveal shot of {product_name}",
                "audio": f"Introducing the {product_name} - {selling_points[0] if selling_points else 'amazing quality'}",
                "duration": int(duration * 0.2),
            },
            {
                "scene": 2,
                "visual": f"Feature demonstration: {selling_points[1] if len(selling_points) > 1 else 'key features'}",
                "audio": ", ".join(selling_points),
                "duration": int(duration * 0.5),
            },
            {
                "scene": 3,
                "visual": "Call to action / product shot with price",
                "audio": f"Get your {product_name} today! Link in bio.",
                "duration": int(duration * 0.3),
            },
        ],
        "hashtags": ["#product", "#shopping", f"#{platform}"],
        "full_script": f"Introducing the {product_name}! {', '.join(selling_points)}. Get yours today!",
    }
