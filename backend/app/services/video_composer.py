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
        filter_parts, sub_files = self._build_filtergraph(
            images=images,
            durations=actual_durations,
            spec=spec,
            scene_subtitles=scene_subtitles,
            logo_path=logo_path,
            output_base=output_path.parent,
        )

        # 构建 FFmpeg 命令
        cmd = self._build_command(
            images=images,
            audio_path=audio_path,
            filter_parts=filter_parts,
            output_path=output_path,
            logo_path=logo_path,
        )

        await self._execute(cmd, output_path)

        # 清理临时字幕文件
        for f in sub_files:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass

        return output_path

    # ------------------------------------------------------------------
    # Filtergraph 构建
    # ------------------------------------------------------------------

    def _build_filtergraph(
        self,
        images: list[Path],
        durations: list[float],
        spec: dict,
        scene_subtitles: list[str] | None = None,
        logo_path: Path | str | None = None,
        output_base: Path | None = None,
    ) -> tuple[str, list[Path]]:
        """
        构建 FFmpeg complex filtergraph

        管线（修复 subtitle timing）:
          image[n] → scale+pad+fps → [v_n]
            → (可选) drawtext → [s_n]     ← 字幕在 xfade 之前！
          [s_0]...[s_n] → xfade → fade → (可选) overlay logo → [outv]
        """

        w, h = spec["width"], spec["height"]
        fps = spec["fps"]
        n = len(images)
        subs = scene_subtitles or []

        filters: list[str] = []

        # ==== 步骤 1: 每张图 → 缩放 + pad + fps + (字幕) ====
        scene_tags: list[str] = []
        subtitle_files: list[Path] = []  # 记录所有临时字幕文件，compose 结束时清理

        for i in range(n):
            raw_tag = f"raw{i}"
            # 基础变换
            filters.append(
                f"[{i}:v]"
                f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
                f"setsar=1,"
                f"fps={fps},"
                f"format=yuv420p"
                f"[{raw_tag}]"
            )

            # 字幕：写入临时文件，用 textfile 引用（彻底避免转义问题）
            if i < len(subs) and subs[i].strip():
                subbed_tag = f"s{i}"
                # 写入临时文件（UTF-8，无 BOM）
                sub_file = (output_base or Path(".")) / f"_sub_{i}.txt"
                sub_file.write_text(subs[i].strip(), encoding="utf-8")
                subtitle_files.append(sub_file)
                # 转义冒号——FFmpeg filter 中 : 是参数分隔符，Windows 盘符需转义
                safe_path = str(sub_file.resolve()).replace("\\", "/").replace(":", "\\:")
                filters.append(
                    f"[{raw_tag}]"
                    f"drawtext="
                    f"textfile='{safe_path}':"
                    f"fontsize={self.SUBTITLE_FONTSIZE}:"
                    f"fontcolor={self.SUBTITLE_FONTCOLOR}:"
                    f"bordercolor={self.SUBTITLE_BORDER_COLOR}:"
                    f"borderw={self.SUBTITLE_BORDER_WIDTH}:"
                    f"x=(w-text_w)/2:"
                    f"y=h-th-60"
                    f"[{subbed_tag}]"
                )
                scene_tags.append(subbed_tag)
            else:
                scene_tags.append(raw_tag)

        # ==== 步骤 2: 场景间 crossfade ====
        merged = scene_tags[0]
        for i in range(1, n):
            next_tag = f"merged_{i}"
            offset = sum(durations[:i]) - self.CROSSFADE_DURATION
            filters.append(
                f"[{merged}][{scene_tags[i]}]"
                f"xfade=transition=fade:duration={self.CROSSFADE_DURATION}:offset={max(offset, 0.5)}"
                f"[{next_tag}]"
            )
            merged = next_tag

        # ==== 步骤 3: 全局淡入淡出 ====
        total = sum(durations)
        fade_end = total - self.FADE_DURATION - self.CROSSFADE_DURATION * (n - 1)
        filters.append(
            f"[{merged}]"
            f"fade=t=in:d={self.FADE_DURATION},"
            f"fade=t=out:d={self.FADE_DURATION}:st={max(fade_end, 0.5)}"
            f"[faded]"
        )
        current_stream = "faded"

        # ==== 步骤 4: Logo 水印 ====
        if logo_path:
            logo_tag = f"[{n}:v]"
            filters.append(
                f"[{current_stream}]{logo_tag}"
                f"overlay=W-w-20:H-h-40:format=auto,"
                f"format=yuv420p"
                f"[watermarked]"
            )
            current_stream = "watermarked"

        # 最终输出
        filters.append(f"[{current_stream}]format=yuv420p[outv]")

        return ";".join(filters), subtitle_files

    @staticmethod
    def _escape_drawtext(text: str) -> str:
        """清理字幕文本中的危险字符（改用 textfile 方案后只需清理换行符）"""
        # 移除换行符和控制字符，保留其他所有内容
        return text.replace("\n", " ").replace("\r", "").replace("\t", " ")

    # ------------------------------------------------------------------
    # 命令构建 & 执行
    # ------------------------------------------------------------------

    def _build_command(
        self,
        images: list[Path],
        audio_path: Path,
        filter_parts: str,
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
        """确定每个场景的时长，确保总时长匹配音频避免黑屏"""
        n = len(images)

        if scene_durations and len(scene_durations) == n:
            # 安全兜底：如果场景总时长小于音频时长，拉伸最后一帧填补
            if audio_path.exists():
                audio_len = await self._get_audio_duration(audio_path)
                scene_sum = sum(scene_durations)
                if scene_sum < audio_len - 0.5:  # 差距大于0.5秒才修正
                    durations = list(scene_durations)
                    durations[-1] += (audio_len - scene_sum)
                    return durations
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
