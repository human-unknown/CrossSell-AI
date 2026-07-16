"""
统计 API 测试
=============
GET /api/stats/weekly
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database import async_session, Base, engine
from app.models import Task, TaskResult


@pytest_asyncio.fixture
async def client():
    """FastAPI 测试客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    """每个测试前清空数据库并重建表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ------------------------------------------------------------------
# 辅助函数
# ------------------------------------------------------------------


def _now():
    return datetime.now(timezone.utc)


def _this_week():
    """本周的某个时间点"""
    return _now() - timedelta(hours=1)


def _last_week():
    """上周的某个时间点"""
    return _now() - timedelta(days=8)


async def _create_task(
    task_id: str,
    status: str,
    created_at: datetime,
    videos: list | None = None,
    copies: list | None = None,
    strategy: dict | None = None,
):
    """创建一条完整任务记录"""
    async with async_session() as db:
        task = Task(
            id=task_id,
            status=status,
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(task)

        if videos is not None or copies is not None or strategy is not None:
            result = TaskResult(
                task_id=task_id,
                videos=videos or [],
                copies=copies or [],
                strategy=strategy,
            )
            db.add(result)

        await db.commit()


# ------------------------------------------------------------------
# 测试
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_weekly_stats_empty(client):
    """空数据 — 所有统计应为 0"""
    response = await client.get("/api/stats/weekly")
    assert response.status_code == 200

    data = response.json()
    assert data["videoCount"] == 0
    assert data["copyCount"] == 0
    assert data["strategyCount"] == 0
    assert data["totalTasks"] == 0
    assert data["completedTasks"] == 0


@pytest.mark.asyncio
async def test_weekly_stats_with_data(client):
    """有数据 — 正确统计本周 completed 任务的结果"""
    now = _this_week()

    # 本周完成的 2 个任务
    await _create_task("t1", "completed", now,
                       videos=[{"url": "v1.mp4"}, {"url": "v2.mp4"}],
                       copies=[{"text": "copy1"}, {"text": "copy2"}, {"text": "copy3"}],
                       strategy={"roas": "3x"})
    await _create_task("t2", "completed", now + timedelta(hours=1),
                       videos=[{"url": "v3.mp4"}],
                       copies=[{"text": "copy4"}],
                       strategy={"roas": "2x"})

    # 本周 processing（未完成）不应计入统计
    await _create_task("t3", "processing", now + timedelta(hours=2))

    # 上周 completed — 不应计入本周统计
    await _create_task("t4", "completed", _last_week(),
                       videos=[{"url": "old.mp4"}],
                       copies=[{"text": "old"}],
                       strategy={"roas": "1x"})

    response = await client.get("/api/stats/weekly")
    assert response.status_code == 200

    data = response.json()
    assert data["totalTasks"] == 3          # t1 + t2 + t3 (本周所有任务)
    assert data["completedTasks"] == 2      # t1 + t2
    assert data["videoCount"] == 3          # 2+1
    assert data["copyCount"] == 4           # 3+1
    assert data["strategyCount"] == 2       # t1 + t2 都有 strategy


@pytest.mark.asyncio
async def test_weekly_stats_strategy_null_not_counted(client):
    """strategy 为 null 的 completed 任务不应计入 total_strategies"""
    now = _this_week()

    await _create_task("t1", "completed", now,
                       videos=[],
                       copies=[{"text": "c1"}],
                       strategy=None)

    response = await client.get("/api/stats/weekly")
    assert response.status_code == 200

    data = response.json()
    assert data["strategyCount"] == 0
    assert data["copyCount"] == 1


@pytest.mark.asyncio
async def test_weekly_stats_excludes_failed_tasks(client):
    """failed 状态的任务不计入视频/文案/策略统计"""
    now = _this_week()

    await _create_task("t1", "failed", now,
                       videos=[{"url": "bad.mp4"}],
                       copies=[{"text": "bad copy"}],
                       strategy={"roas": "0x"})

    response = await client.get("/api/stats/weekly")
    assert response.status_code == 200

    data = response.json()
    assert data["totalTasks"] == 1       # 本周创建了1个任务
    assert data["videoCount"] == 0       # 但不计入
    assert data["copyCount"] == 0
    assert data["strategyCount"] == 0
