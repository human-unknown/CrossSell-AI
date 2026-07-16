"""
图片生成服务 — Pipeline A Step 3
===============================
调用 Model Router 图片生成 API 生成产品场景图素材。
"""

import logging
import httpx
from pathlib import Path

from app.services.model_router import get_model_router, ModelRouterError
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def generate_product_scenes(
    product_name: str,
    selling_points: list[str],
    market: str,
    num_scenes: int = 3,
) -> list[str]:
    """
    为产品生成场景图

    Args:
        product_name: 产品名称
        selling_points: 核心卖点
        market: 目标市场（影响图片风格）
        num_scenes: 生成场景图数量

    Returns:
        图片 URL 列表
    """
    market_style_hints = {
        "美国": "modern American lifestyle, bright natural lighting, clean aesthetic",
        "日本": "minimalist Japanese style, soft lighting, zen atmosphere",
        "德国": "modern European design, functional, professional lighting",
        "法国": "elegant French lifestyle, romantic, warm tones",
        "韩国": "trendy Korean aesthetic, soft pastel, cozy atmosphere",
        "东南亚": "tropical vibrant, colorful, natural outdoor",
    }

    style = market_style_hints.get(market, "professional product photography, clean background")

    prompts = []
    for i, sp in enumerate(selling_points[:num_scenes]):
        prompt = (
            f"Professional product photography of {product_name}, "
            f"highlighting feature: {sp}. "
            f"Style: {style}. "
            f"Clean composition, commercial use, high quality, 16:9."
        )
        prompts.append(prompt)

    try:
        router = get_model_router()
        image_urls = []

        for prompt in prompts:
            urls = await router.generate_image(
                prompt=prompt,
                model=settings.IMAGE_MODEL,
                size="1024x1024",
                n=1,
            )
            image_urls.extend(urls)
            logger.info(f"图片生成成功: {prompt[:60]}...")

        return image_urls

    except ModelRouterError as e:
        logger.error(f"图片生成失败: {e}")
        # 返回占位图（后续可用本地素材库替代）
        return [f"https://placehold.co/1024x1024?text={product_name}+Scene+{i+1}" for i in range(num_scenes)]


async def download_image(url: str, output_path: Path) -> Path:
    """下载图片到本地"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    logger.info(f"图片已下载: {output_path}")
    return output_path
