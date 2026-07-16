"""
CrossSell AI — 应用配置
=======================
所有配置项通过环境变量注入，本地开发使用 .env 文件。
"""

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


class Settings(BaseSettings):
    """应用配置，自动从环境变量 / .env 读取"""

    # ---- 应用 ----
    APP_NAME: str = "CrossSell AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # ---- 数据库 ----
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'crosssell.db'}"

    # ---- Model Router API (阿里云百炼国内) ----
    MODEL_ROUTER_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL_ROUTER_API_KEY: str = ""  # 阿里云百炼控制台获取的 API Key

    # ---- 常用模型 (阿里云百炼兼容模式原生ID，不含 qwen/ 前缀) ----
    TEXT_MODEL: str = "qwen-max"          # 高质量文案/脚本
    FAST_TEXT_MODEL: str = "qwen-turbo"   # 快速原型验证
    REASONING_MODEL: str = "deepseek-r1"  # 复杂策略分析
    TTS_MODEL: str = "cosyvoice-v1"       # 语音合成（需达摩院原生API）
    IMAGE_MODEL: str = "wan2.1-t2i-turbo" # 图片生成（需达摩院原生API）
    VIDEO_MODEL: str = "wan2.1-t2v-turbo" # 视频生成（需达摩院原生API）
    VISION_MODEL: str = "qwen-vl-plus"    # 视觉理解

    # ---- API 限流 / 重试 ----
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    REQUEST_TIMEOUT: int = 120  # 秒，视频生成可能较慢

    # ---- CORS ----
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # ---- 输出路径 ----
    OUTPUT_DIR: str = str(OUTPUT_DIR)

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "allow",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
