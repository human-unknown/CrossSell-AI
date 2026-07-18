"""
Pipeline A：短视频生产流水线
===========================
编排：脚本生成 → 配音生成 → 素材准备 → FFmpeg合成
"""

import logging
from pathlib import Path
from typing import Callable, Awaitable

from app.config import get_settings, BASE_DIR
from app.services.script_generator import generate_script
from app.services.tts_service import generate_audio
from app.services.image_service import generate_product_scenes, download_image
from app.services.video_composer import get_video_composer

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_video_pipeline(
    task_id: str,
    product_name: str,
    selling_points: list[str],
    description: str,
    markets: list[str],
    platforms: list[str],
    update_step: Callable[[str, str], Awaitable[None]],
    update_progress: Callable[[float], Awaitable[None]],
) -> list[dict]:
    """
    执行完整的短视频生产流水线

    Args:
        task_id: 任务 ID（用于输出目录）
        product_name: 产品名称
        selling_points: 卖点列表
        description: 产品描述
        markets: 目标市场列表
        platforms: 目标平台列表
        update_step: 步骤状态更新回调 (step_name, status)
        update_progress: 进度更新回调 (0.0 ~ 1.0)

    Returns:
        视频结果列表
    """
    results = []
    output_base = Path(settings.OUTPUT_DIR) / task_id
    output_base.mkdir(parents=True, exist_ok=True)

    total_combos = len(platforms) * len(markets)
    completed = 0

    for platform in platforms:
        for market in markets:
            combo_key = f"{platform}_{market}"

            # --- Step 1: 脚本生成 ---
            await update_step("script_generation", "in_progress")
            await update_progress(completed / total_combos)

            try:
                script = await generate_script(
                    product_name=product_name,
                    selling_points=selling_points,
                    description=description,
                    market=market,
                    platform=platform,
                )
                logger.info(f"[{combo_key}] 脚本生成完成")
            except Exception as e:
                logger.error(f"[{combo_key}] 脚本生成失败: {e}")
                await update_step("script_generation", "failed")
                completed += 1
                continue

            await update_step("script_generation", "done")

            # --- Step 2: 配音生成 ---
            await update_step("text_to_speech", "in_progress")
            await update_progress((completed + 0.25) / total_combos)

            audio_path = output_base / f"{combo_key}_audio.wav"
            language = script.get("language", "en")
            full_script = script.get("full_script", "")
            try:
                await generate_audio(
                    text=full_script,
                    language=language,
                    output_path=audio_path,
                )
                logger.info(f"[{combo_key}] 配音生成完成")
            except Exception as e:
                # TTS 失败不阻塞流水线 — 生成静音占位音频
                # 使用 script 中实际场景总时长，避免 15s 默认值导致黑屏
                _scenes = script.get("scenes", [])
                _fallback_dur = sum(s.get("duration", 3) for s in _scenes[:5]) if _scenes else 15.0
                logger.warning(f"[{combo_key}] 配音生成失败(fallback BGM): {e}")
                _create_bgm_audio(audio_path, duration=max(_fallback_dur, 5.0))

            await update_step("text_to_speech", "done")

            # --- Step 3: 素材准备 ---
            await update_step("image_generation", "in_progress")
            await update_progress((completed + 0.5) / total_combos)

            try:
                image_urls = await generate_product_scenes(
                    product_name=product_name,
                    selling_points=selling_points,
                    market=market,
                    num_scenes=min(len(script.get("scenes", [])), 5),
                )
                # 下载图片到本地
                image_paths = []
                for i, url in enumerate(image_urls):
                    local_path = output_base / f"{combo_key}_scene_{i+1}.jpg"
                    await download_image(url, local_path)
                    image_paths.append(local_path)
                logger.info(f"[{combo_key}] 素材准备完成 ({len(image_paths)} 张)")
            except Exception as e:
                logger.error(f"[{combo_key}] 素材准备失败: {e}")
                # 素材非致命，用空列表继续
                image_paths = []

            await update_step("image_generation", "done")

            # --- Step 4: FFmpeg 合成 ---
            await update_step("video_rendering", "in_progress")
            await update_progress((completed + 0.75) / total_combos)

            video_path = output_base / f"{combo_key}_video.mp4"
            try:
                if image_paths and audio_path.exists():
                    composer = get_video_composer()
                    scenes = script.get("scenes", [])
                    # 截断到图片数量，避免 durations/subtitles 与 images 长度不匹配
                    scene_durations = [s.get("duration", 3) for s in scenes[:len(image_paths)]]
                    scene_subtitles = [
                        s.get("audio", s.get("visual", "")) for s in scenes[:len(image_paths)]
                    ]
                    await composer.compose(
                        images=image_paths,
                        audio_path=audio_path,
                        platform=platform,
                        output_path=video_path,
                        scene_durations=scene_durations if scene_durations else None,
                        scene_subtitles=scene_subtitles if any(scene_subtitles) else None,
                    )
                    video_url = f"/output/{task_id}/{video_path.name}"
                else:
                    video_url = None
                    logger.warning(f"[{combo_key}] 无素材可合成，跳过视频生成")
            except Exception as e:
                logger.error(f"[{combo_key}] FFmpeg 合成失败: {e}")
                video_url = None

            await update_step("video_rendering", "done")

            results.append({
                "platform": platform,
                "market": market,
                "url": video_url,
                "script": script.get("full_script", ""),
                "duration": script.get("duration", 15),
            })

            completed += 1
            await update_progress(completed / total_combos)

    return results


def _create_silent_audio(path: Path, duration: float = 15.0, sample_rate: int = 44100):
    """生成静音 WAV 占位文件（TTS 不可用时的兜底）"""
    import struct
    import wave

    path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(duration * sample_rate)

    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))


def _create_bgm_audio(path: Path, duration: float = 15.0):
    """生成柔和背景音 WAV（TTS 降级方案）。

    优先用 FFmpeg sine 滤镜（带淡入淡出），
    不可用时退回纯 Python 440Hz 正弦波生成。
    """
    import struct
    import wave
    import math
    import subprocess
    import shutil

    path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        try:
            cmd = [
                ffmpeg, "-y",
                "-f", "lavfi",
                "-i", f"sine=frequency=440:duration={duration}:sample_rate=44100",
                "-af", f"volume=-18dB,afade=t=in:d=1,afade=t=out:d=1:st={max(duration - 1, 1)}",
                "-ac", "1",
                str(path),
            ]
            subprocess.run(cmd, capture_output=True, check=True, timeout=30)
            if path.exists() and path.stat().st_size > 0:
                logger.info(f"BGM 生成成功 (FFmpeg): {path} ({path.stat().st_size} bytes)")
                return
        except Exception:
            logger.warning("FFmpeg BGM 失败，回退纯 Python 合成")

    # ---- 纯 Python 正弦波（零外部依赖）----
    sample_rate = 44100
    num_samples = int(duration * sample_rate)
    # 440Hz, 振幅 15%（≈ -16.5dB，不刺耳），带淡入淡出包络
    fade_samples = int(1.0 * sample_rate)  # 1s 淡入/淡出

    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # 包络：前 fade_samples 线性淡入，后 fade_samples 线性淡出
        if i < fade_samples:
            envelope = i / fade_samples
        elif i > num_samples - fade_samples:
            envelope = (num_samples - i) / fade_samples
        else:
            envelope = 1.0
        value = int(0.15 * 32767 * math.sin(2 * math.pi * 440 * t) * envelope)
        samples.append(value)

    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * num_samples, *samples))

    logger.info(f"BGM 生成成功 (Python): {path} ({path.stat().st_size} bytes)")
