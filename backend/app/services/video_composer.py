"""
视频合成服务 — Pipeline A Step 4
==============================
使用 FFmpeg 将图片序列 + 音频 + 字幕合成为短视频。
"""

import asyncio
import logging
import tempfile
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VideoComposer:
    """FFmpeg 视频合成器"""

    # 平台输出规格
    PLATFORM_SPECS = {
        "tiktok": {"width": 1080, "height": 1920, "fps": 30},
        "instagram": {"width": 1080, "height": 1350, "fps": 30},
        "youtube_shorts": {"width": 1080, "height": 1920, "fps": 30},
        "facebook": {"width": 1080, "height": 1080, "fps": 30},
        "pinterest": {"width": 1000, "height": 1500, "fps": 25},
    }

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_path

    def _get_spec(self, platform: str) -> dict:
        return self.PLATFORM_SPECS.get(platform, self.PLATFORM_SPECS["tiktok"])

    async def compose(
        self,
        images: list[Path],
        audio_path: Path,
        platform: str,
        output_path: Path,
        subtitles: str | None = None,
        scene_durations: list[float] | None = None,
    ) -> Path:
        """
        合成视频

        Args:
            images: 图片素材路径列表
            audio_path: 配音文件路径
            platform: 目标平台
            output_path: 输出视频路径
            subtitles: SRT 字幕内容（可选）
            scene_durations: 每张图片的展示时长（秒），默认均分

        Returns:
            输出视频路径
        """
        spec = self._get_spec(platform)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 如果没有指定时长，均分音频长度
        if not scene_durations and audio_path.exists():
            duration = await self._get_audio_duration(audio_path)
            per_image = duration / len(images) if images else duration
            scene_durations = [per_image] * len(images)

        # 生成输入文件列表（FFmpeg concat 格式）
        concat_file = await self._create_concat_file(images, scene_durations or [3] * len(images))

        # 构建 FFmpeg 命令
        cmd_parts = [self.ffmpeg, "-y"]

        # 图片输入（通过 concat demuxer）
        cmd_parts += ["-f", "concat", "-safe", "0", "-i", str(concat_file)]

        # 音频输入
        cmd_parts += ["-i", str(audio_path)]

        # 视频编码参数
        cmd_parts += [
            "-vf", (
                f"scale={spec['width']}:{spec['height']}:force_original_aspect_ratio=decrease,"
                f"pad={spec['width']}:{spec['height']}:(ow-iw)/2:(oh-ih)/2,"
                f"fps={spec['fps']},"
                f"format=yuv420p"
            ),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            "-movflags", "+faststart",
        ]

        # 字幕（如有）
        if subtitles:
            # 将字幕写入临时文件
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".srt", delete=False, encoding="utf-8"
            ) as f:
                f.write(subtitles)
                srt_path = Path(f.name)
            cmd_parts += ["-vf", f"subtitles={srt_path}:force_style='FontSize=24,Alignment=2'"]

        cmd_parts.append(str(output_path))

        # 执行
        cmd_str = " ".join(str(p) for p in cmd_parts)
        logger.info(f"执行 FFmpeg: {cmd_str}")

        process = await asyncio.create_subprocess_shell(
            cmd_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")[:500]
            logger.error(f"FFmpeg 合成失败: {error_msg}")
            raise RuntimeError(f"FFmpeg failed: {error_msg}")
        else:
            logger.info(f"视频合成成功: {output_path}")

        # 清理临时文件
        concat_file.unlink(missing_ok=True)
        if subtitles and 'srt_path' in locals():
            srt_path.unlink(missing_ok=True)

        return output_path

    async def _create_concat_file(
        self, images: list[Path], durations: list[float]
    ) -> Path:
        """创建 FFmpeg concat demuxer 输入文件"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            for img, dur in zip(images, durations):
                f.write(f"file '{img.as_posix()}'\n")
                f.write(f"duration {dur}\n")
            # 最后一张图也要写一次（concat 约定）
            if images:
                f.write(f"file '{images[-1].as_posix()}'\n")
            return Path(f.name)

    async def _get_audio_duration(self, audio_path: Path) -> float:
        """获取音频时长（秒）"""
        import subprocess
        cmd = [
            self.ffmpeg, "-i", str(audio_path),
            "-f", "null", "-"
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        stderr_text = stderr.decode("utf-8", errors="replace")

        # 从 FFmpeg 输出中解析 Duration
        for line in stderr_text.split("\n"):
            if "Duration:" in line:
                parts = line.split("Duration:")[1].strip().split(",")[0]
                h, m, s = parts.split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)
        return 15.0  # 默认 15 秒


# ------------------------------------------------------------------
# 单例
# ------------------------------------------------------------------

_composer: VideoComposer | None = None


def get_video_composer() -> VideoComposer:
    global _composer
    if _composer is None:
        _composer = VideoComposer()
    return _composer
