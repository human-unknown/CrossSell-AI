"""
错误处理测试
============
验证 AppError 体系：错误码、status_code、响应格式。
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database import Base, engine


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ------------------------------------------------------------------
# 测试
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_task_not_found_error_format(client):
    """TaskNotFoundError 返回 404 + 标准错误格式"""
    response = await client.get("/api/task/nonexistent-id/status")

    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "TASK_NOT_FOUND"
    assert data["status_code"] == 404
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_task_not_ready_error_format(client):
    """TaskNotReadyError 返回 425 + 标准错误格式"""
    # 创建 processing 状态的任务
    create_resp = await client.post("/api/generate", json={
        "product_name": "Test",
        "product_selling_points": ["S1"],
        "target_markets": ["美国"],
        "target_platforms": ["tiktok"],
        "content_types": ["copy"],
    })
    task_id = create_resp.json()["taskId"]

    response = await client.get(f"/api/task/{task_id}/result")

    assert response.status_code == 425
    data = response.json()
    assert data["error_code"] == "TASK_NOT_READY"
    assert data["status_code"] == 425
    assert "detail" in data


@pytest.mark.asyncio
async def test_validation_error_422_passthrough(client):
    """FastAPI 自带的 422 不做修改，保持 RequestValidationError 行为"""
    response = await client.post("/api/generate", json={
        "product_name": "",
        "product_selling_points": [],
        "target_markets": [],
        "target_platforms": [],
        "content_types": [],
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_app_error_status_code_mapping(client):
    """验证错误类属性正确映射"""
    from app.errors import TaskNotFoundError, TaskNotReadyError, AIServiceError, RateLimitError

    assert TaskNotFoundError.status_code == 404
    assert TaskNotFoundError.error_code == "TASK_NOT_FOUND"

    assert TaskNotReadyError.status_code == 425
    assert TaskNotReadyError.error_code == "TASK_NOT_READY"

    assert AIServiceError.status_code == 502
    assert RateLimitError.status_code == 429
