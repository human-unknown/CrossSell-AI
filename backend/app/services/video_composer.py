"""
视频合成服务 — Pipeline A Step 4（增强版）
===========================================
使用 FFmpeg 将图片序列 + 音频 + 字幕 + 特效合成为短视频。

增强功能:
  - 淡入/淡出 + 场景间 crossfade 转场
  - 逐场景字幕叠加（drawtext filter）
  - 可选手写 logo 水印
"""

import asyncio
import logging
import tempfile
import shutil
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VideoComposer:
    """FFmpeg 视频合成器（增强版）"""

    # 平台输出规格（全部竖屏 9:16）
    PLATFORM_SPECS = {
        "tiktok":         {"width": 1080, "height": 1920, "fps": 30},
        "instagram":      {"width": 1080, "height": 1350, "fps": 30},
        "youtube_shorts": {"width": 1080, "height": 1920, "fps": 30},
        "facebook":       {"width": 1080, "height": 1080, "fps": 30},
        "pinterest":      {"width": 1000, "height": 1500, "fps": 25},
    }

    # 字幕默认样式
    SUBTITLE_FONTSIZE = 32
    SUBTITLE_FONTCOLOR = "white"
    SUBTITLE_BORDER_COLOR = "black@0.6"
    SUBTITLE_BORDER_WIDTH = 2

    # 转场
    FADE_DURATION = 0.5       # 淡入淡出时长（秒）
    CROSSFADE_DURATION = 0.3  # 场景间 crossfade（秒）

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_path

    # ------------------------------------------------------------------
    # 公共入口
    # ------------------------------------------------------------------

    async def compose(
        self,
        images: list[Path],
        audio_path: Path,
        platform: str,
        output_path: Path,
        scene_durations: list[float] | None = None,
        scene_subtitles: list[str] | None = None,
        logo_path: Path | str | None = None,
    ) -> Path:
        """
        合成短视频

        Args:
            images:          图片素材路径列表
            audio_path:      配音文件路径
            platform:        目标平台 (tiktok/instagram/youtube_shorts/...)
            output_path:     输出视频路径
            scene_durations: 每张图片的展示时长（秒），默认均分
            scene_subtitles: 逐场景字幕文本列表，长度应与 scenes 一致
            logo_path:       品牌 logo 图片路径（可选，覆盖右下角）

        Returns:
            输出视频路径
        """
        spec = self._get_spec(platform)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        n = len(images)
        if n == 0:
            raise ValueError("至少需要 1 张图片素材")

        # 计算每张图的时长
        actual_durations = await self._resolve_durations(
            audio_path, images, scene_durations
        )
        total_duration = sum(actual_durations)

        # 构建 filtergraph
        filter_parts = await self._build_filtergraph(
            images=images,
            durations=actual_durations,
            spec=spec,
            scene_subtitles=scene_subtitles,
            logo_path=logo_path,
        )

        # 构建 FFmpeg 命令
        cmd = self._build_command(
            images=images,
            audio_path=audio_path,
            filter_parts=filter_parts,
            spec=spec,
            output_path=output_path,
            logo_path=logo_path,
        )

        await self._execute(cmd, output_path)
        return output_path

    # ------------------------------------------------------------------
    # Filtergraph 构建
    # ------------------------------------------------------------------

    async def _build_filtergraph(
        self,
        images: list[Path],
        durations: list[float],
        spec: dict,
        scene_subtitles: list[str] | None = None,
        logo_path: Path | str | None = None,
    ) -> str:
        """构建 FFmpeg complex filtergraph"""

        w, h = spec["width"], spec["height"]
        fps = spec["fps"]
        n = len(images)

        filters: list[str] = []

        # ==== 步骤 1: 每张图 → 缩放 + 居中 pad + 设置显示时长 ====
        padded: list[str] = []
        for i in range(n):
            tag = f"v{i}"
            filters.append(
                f"[{i}:v]"
                f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
                f"setsar=1,"
                f"fps={fps},"
                f"format=yuv420p"
                f"[{tag}]"
            )
            padded.append(tag)

        # ==== 步骤 2: 场景间 crossfade + 全局淡入淡出 ====
        merged = padded[0]
        for i in range(1, n):
            next_tag = f"merged_{i}"
            offset = sum(durations[:i]) - self.CROSSFADE_DURATION
            filters.append(
                f"[{merged}][{padded[i]}]"
                f"xfade=transition=fade:duration={self.CROSSFADE_DURATION}:offset={max(offset, 0.5)}"
                f"[{next_tag}]"
            )
            merged = next_tag

        # 全局淡入淡出
        fade_end = sum(durations) - self.FADE_DURATION
        filters.append(
            f"[{merged}]"
            f"fade=t=in:d={self.FADE_DURATION},"
            f"fade=t=out:d={self.FADE_DURATION}:st={max(fade_end, 0.5)}"
            f"[faded]"
        )
        current_stream = "faded"

        # ==== 步骤 3: 逐场景字幕 ====
        if scene_subtitles:
            subtitle_filters = self._build_subtitle_filters(
                durations=durations,
                subtitles=scene_subtitles,
                w=w, h=h,
            )
            if subtitle_filters:
                # 把上一个输出加上字幕
                for i, sf in enumerate(subtitle_filters):
                    out_tag = f"subbed_{i}" if i < len(subtitle_filters) - 1 else "subbed"
                    filters.append(f"[{current_stream}]{sf}[{out_tag}]")
                    current_stream = out_tag

        # ==== 步骤 4: Logo 水印 ====
        if logo_path:
            logo_tag = f"[{n}:v]"
            wm_y = h - 40
            filters.append(
                f"[{current_stream}]{logo_tag}"
                f"overlay=W-w-20:{wm_y}-overlay_h:format=auto,"
                f"format=yuv420p"
                f"[watermarked]"
            )
            current_stream = "watermarked"

        # 最终输出标签
        filters.append(f"[{current_stream}]format=yuv420p[outv]")

        return ";".join(filters)

    def _build_subtitle_filters(
        self,
        durations: list[float],
        subtitles: list[str],
        w: int,
        h: int,
    ) -> list[str]:
        """为每个场景构建 drawtext filter，带 enable 时间条件"""

        filters = []
        elapsed = 0.0

        for i, text in enumerate(subtitles):
            if not text or not text.strip():
                elapsed += durations[i]
                continue

            start_t = elapsed
            end_t = elapsed + durations[i]
            elapsed = end_t

            # 转义特殊字符
            safe_text = (
                text.replace("\\", "\\\\")
                .replace(":", "\\:")
                .replace("'", "\\'")
            )

            # 字幕放在底部，居中
            draw = (
                f"drawtext="
                f"text='{safe_text}':"
                f"fontsize={self.SUBTITLE_FONTSIZE}:"
                f"fontcolor={self.SUBTITLE_FONTCOLOR}:"
                f"bordercolor={self.SUBTITLE_BORDER_COLOR}:"
                f"borderw={self.SUBTITLE_BORDER_WIDTH}:"
                f"x=(w-text_w)/2:"
                f"y=h-th-60:"
                f"enable='between(t,{start_t},{end_t})'"
            )
            filters.append(draw)

        return filters

    # ------------------------------------------------------------------
    # 命令构建 & 执行
    # ------------------------------------------------------------------

    def _build_command(
        self,
        images: list[Path],
        audio_path: Path,
        filter_parts: str,
        spec: dict,
        output_path: Path,
        logo_path: Path | str | None = None,
    ) -> list[str]:
        """构建 FFmpeg 命令行参数"""

        cmd = [self.ffmpeg, "-y"]

        # 图片输入
        for img in images:
            cmd += ["-loop", "1", "-i", str(img)]

        # Logo 输入（在音频之前，使 filtergraph 中 [{n}:v] 指向它）
        if logo_path:
            cmd += ["-i", str(logo_path)]

        # 音频输入
        cmd += ["-i", str(audio_path)]

        # 滤镜
        audio_idx = len(images) + (1 if logo_path else 0)
        cmd += [
            "-filter_complex", filter_parts,
            "-map", "[outv]",
            "-map", f"{audio_idx}:a",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            "-movflags", "+faststart",
        ]

        cmd.append(str(output_path))
        return cmd

    async def _execute(self, cmd: list[str], output_path: Path) -> None:
        """执行 FFmpeg 命令"""
        cmd_str = " ".join(str(p) for p in cmd)
        logger.info(f"FFmpeg ({len(cmd)} args) → {output_path.name}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")
            # 只保留关键错误行
            lines = [l for l in error_msg.split("\n") if "error" in l.lower() or "Error" in l]
            logger.error(f"FFmpeg 失败: {chr(10).join(lines[-5:])}")
            raise RuntimeError(
                f"FFmpeg failed (exit {process.returncode}): "
                f"{error_msg[-300:]}"
            )

        logger.info(f"视频合成成功: {output_path} ({output_path.stat().st_size} bytes)")

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    async def _resolve_durations(
        self,
        audio_path: Path,
        images: list[Path],
        scene_durations: list[float] | None,
    ) -> list[float]:
        """确定每个场景的时长"""
        n = len(images)

        if scene_durations and len(scene_durations) == n:
            return list(scene_durations)

        if audio_path.exists():
            audio_len = await self._get_audio_duration(audio_path)
            per = audio_len / n
            return [per] * n

        return [3.0] * n

    async def _get_audio_duration(self, audio_path: Path) -> float:
        """获取音频时长（秒）"""
        cmd = [self.ffmpeg, "-i", str(audio_path), "-f", "null", "-"]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        text = stderr.decode("utf-8", errors="replace")

        for line in text.split("\n"):
            if "Duration:" in line:
                parts = line.split("Duration:")[1].strip().split(",")[0]
                h, m, s = parts.strip().split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)

        return 15.0

    def _get_spec(self, platform: str) -> dict:
        return self.PLATFORM_SPECS.get(platform, self.PLATFORM_SPECS["tiktok"])


# ------------------------------------------------------------------
# 单例
# ------------------------------------------------------------------

_composer: VideoComposer | None = None


def _find_ffmpeg() -> str:
    """Auto-detect FFmpeg binary location."""
    # 1. 优先从系统 PATH 查找
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    # 2. WorkBuddy 托管
    managed = Path.home() / ".workbuddy" / "binaries" / "ffmpeg" / "ffmpeg.exe"
    if managed.exists():
        return str(managed)
    # 3. 常见安装路径
    for candidate in [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]:
        if Path(candidate).exists():
            return candidate
    return "ffmpeg"


def get_video_composer() -> VideoComposer:
    global _composer
    if _composer is None:
        path = _find_ffmpeg()
        logger.info(f"FFmpeg detected at: {path}")
        _composer = VideoComposer(ffmpeg_path=path)
    return _composer
