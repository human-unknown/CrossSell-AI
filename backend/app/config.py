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

    # ---- Model Router API (阿里云百炼) ----
    MODEL_ROUTER_BASE_URL: str = "https://model-router.edu-aliyun.com/v1"
    MODEL_ROUTER_API_KEY: str = ""  # 赛方发放，踩点时可用阿里云百炼免费额度

    # ---- 常用模型 ----
    TEXT_MODEL: str = "qwen/qwen3.7-max"
    FAST_TEXT_MODEL: str = "qwen/qwen3.5-flash"
    REASONING_MODEL: str = "qwen/deepseek-r1"
    TTS_MODEL: str = "qwen/qwen3-tts-instruct-flash"
    IMAGE_MODEL: str = "qwen/wan2.7-image-pro"
    VIDEO_MODEL: str = "qwen/wan2.7-t2v"
    VISION_MODEL: str = "qwen/qwen3-vl-plus"

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
