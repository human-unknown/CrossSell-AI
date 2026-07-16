"""
Pytest 配置 — asyncio + 测试数据库
=================================
"""

import pytest
import sys
from pathlib import Path

# 确保 backend 在 Python path 中
sys.path.insert(0, str(Path(__file__).resolve().parent))

pytest_plugins = []


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
