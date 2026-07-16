"""
TTS 语音合成服务 — Pipeline A Step 2
===================================
调用 Model Router TTS API 将脚本文本转为语音。
"""

import logging
from pathlib import Path

from app.services.model_router import get_model_router, ModelRouterError
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def generate_audio(
    text: str,
    language: str = "en",
    output_path: str | Path | None = None,
    voice: str = "Chelsie",
) -> bytes:
    """
    将文本转为语音

    Args:
        text: 要合成的文本（脚本的完整叙述）
        language: 语言代码 (en/ja/de/fr/ko/pt/ar)
        output_path: 如指定，将音频写入文件
        voice: 音色

    Returns:
        音频数据 (bytes)
    """
    try:
        router = get_model_router()
        audio_data = await router.text_to_speech(
            text=text,
            model=settings.TTS_MODEL,
            language=language,
            voice=voice,
        )

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(audio_data)
            logger.info(f"TTS 音频已保存: {path} ({len(audio_data)} bytes)")

        return audio_data

    except ModelRouterError as e:
        logger.error(f"TTS 生成失败: {e}")
        raise
