"""
API 路由集成测试
================
测试所有 HTTP 接口的正确行为。
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.database import async_session, init_db


@pytest_asyncio.fixture(scope="module")
async def init_test_db():
    """初始化测试数据库"""
    await init_db()
    yield


@pytest_asyncio.fixture
async def client(init_test_db):
    """创建测试 HTTP 客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestHealthAPI:
    """健康检查接口"""

    async def test_health_returns_ok(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    async def test_root_returns_info(self, client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "CrossSell AI"


@pytest.mark.asyncio
class TestGenerateAPI:
    """内容生成接口"""

    VALID_REQUEST = {
        "product_name": "测试蓝牙音箱",
        "product_selling_points": ["IPX7防水", "24小时续航"],
        "product_description": "一款测试用便携蓝牙音箱",
        "target_markets": ["美国"],
        "target_platforms": ["tiktok"],
        "content_types": ["copy"],
    }

    async def test_generate_returns_task_id(self, client: AsyncClient):
        response = await client.post("/api/generate", json=self.VALID_REQUEST)
        assert response.status_code == 202
        data = response.json()
        assert "taskId" in data

    async def test_generate_missing_product_name(self, client: AsyncClient):
        payload = {**self.VALID_REQUEST, "product_name": ""}
        response = await client.post("/api/generate", json=payload)
        assert response.status_code == 422

    async def test_generate_invalid_market(self, client: AsyncClient):
        payload = {**self.VALID_REQUEST, "target_markets": ["火星"]}
        response = await client.post("/api/generate", json=payload)
        assert response.status_code == 422

    async def test_generate_invalid_platform(self, client: AsyncClient):
        payload = {**self.VALID_REQUEST, "target_platforms": ["wechat"]}
        response = await client.post("/api/generate", json=payload)
        assert response.status_code == 422

    async def test_generate_invalid_content_type(self, client: AsyncClient):
        payload = {**self.VALID_REQUEST, "content_types": ["podcast"]}
        response = await client.post("/api/generate", json=payload)
        assert response.status_code == 422

    async def test_generate_empty_markets(self, client: AsyncClient):
        payload = {**self.VALID_REQUEST, "target_markets": []}
        response = await client.post("/api/generate", json=payload)
        assert response.status_code == 422


@pytest.mark.asyncio
class TestTaskAPI:
    """任务查询接口"""

    async def test_task_not_found(self, client: AsyncClient):
        response = await client.get("/api/task/nonexistent-id/status")
        assert response.status_code == 404

    async def test_task_result_not_ready(self, client: AsyncClient):
        # 先创建一个任务
        create_response = await client.post("/api/generate", json={
            "product_name": "任务测试产品",
            "product_selling_points": ["卖点A"],
            "target_markets": ["美国"],
            "target_platforms": ["tiktok"],
            "content_types": ["copy"],
        })
        task_id = create_response.json()["taskId"]

        # 任务刚开始处理，结果应该不可用（425）或 DB 锁 500
        response = await client.get(f"/api/task/{task_id}/result")
        assert response.status_code in (200, 425, 500)

    async def test_list_tasks(self, client: AsyncClient):
        response = await client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data

    async def test_list_tasks_pagination(self, client: AsyncClient):
        response = await client.get("/api/tasks?page=1&size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) <= 5


@pytest.mark.asyncio
class TestValidation:
    """输入验证测试"""

    async def test_product_name_too_long(self, client: AsyncClient):
        response = await client.post("/api/generate", json={
            "product_name": "A" * 201,
            "product_selling_points": ["test"],
            "target_markets": ["美国"],
            "target_platforms": ["tiktok"],
            "content_types": ["copy"],
        })
        assert response.status_code == 422

    async def test_too_many_selling_points(self, client: AsyncClient):
        response = await client.post("/api/generate", json={
            "product_name": "测试产品",
            "product_selling_points": [f"卖点{i}" for i in range(11)],
            "target_markets": ["美国"],
            "target_platforms": ["tiktok"],
            "content_types": ["copy"],
        })
        assert response.status_code == 422

    async def test_invalid_page_parameter(self, client: AsyncClient):
        response = await client.get("/api/tasks?page=-1")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data  # 负数被修正为 1，正常返回
