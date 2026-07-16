"""
服务层单元测试
=============
测试 Model Router 客户端、脚本生成、视频合成等核心逻辑。
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.script_generator import generate_script, _fallback_script
from app.services.copy_generator import generate_copy_batch
from app.services.strategy_engine import generate_strategy, _fallback_strategy
from app.services.video_composer import VideoComposer
from app.services.model_router import ModelRouterClient


class TestScriptGenerator:
    """脚本生成器测试"""

    @pytest.mark.asyncio
    async def test_fallback_script_structure(self):
        """回退脚本应有完整结构"""
        script = _fallback_script(
            product_name="Test Product",
            selling_points=["Feature A", "Feature B"],
            market="美国",
            platform="tiktok",
            duration=15,
            language="en",
        )
        assert "scenes" in script
        assert "hook" in script
        assert "hashtags" in script
        assert "full_script" in script
        assert len(script["scenes"]) > 0

    @pytest.mark.asyncio
    async def test_generate_script_with_mock(self):
        """模拟 API 调用测试脚本生成"""
        with patch(
            "app.services.script_generator.get_model_router"
        ) as mock_router:
            mock_client = AsyncMock()
            mock_client.chat_json.return_value = {
                "platform": "tiktok",
                "market": "美国",
                "language": "en",
                "duration": 15,
                "hook": "Check this out!",
                "scenes": [
                    {"scene": 1, "visual": "Test visual", "audio": "Test audio", "duration": 5},
                ],
                "hashtags": ["#test"],
                "full_script": "Test full script",
            }
            mock_router.return_value = mock_client

            result = await generate_script(
                product_name="Test",
                selling_points=["S1"],
                description="Desc",
                market="美国",
                platform="tiktok",
            )
            assert result["platform"] == "tiktok"
            assert len(result["scenes"]) > 0


class TestCopyGenerator:
    """文案生成器测试"""

    @pytest.mark.asyncio
    async def test_generate_copy_batch_returns_list(self):
        """模拟批量文案生成"""
        with patch(
            "app.services.copy_generator.get_model_router"
        ) as mock_router:
            mock_client = AsyncMock()
            mock_client.chat_json.return_value = {
                "platform": "tiktok",
                "language": "en",
                "market": "美国",
                "text": "Test copy text",
                "hashtags": ["#test"],
                "character_count": 14,
            }
            mock_router.return_value = mock_client

            copies = await generate_copy_batch(
                product_name="Test",
                selling_points=["S1"],
                description="Desc",
                markets=["美国"],
                platforms=["tiktok", "instagram"],
            )
            assert isinstance(copies, list)
            assert len(copies) == 2


class TestStrategyEngine:
    """投流策略引擎测试"""

    @pytest.mark.asyncio
    async def test_fallback_strategy_structure(self):
        """回退策略应有完整结构"""
        strategy = _fallback_strategy(
            platforms=["tiktok", "instagram"],
            markets=["美国"],
        )
        assert "recommended_platform" in strategy
        assert "daily_budget_suggestion" in strategy
        assert "estimated_roas" in strategy
        assert "detailed_analysis" in strategy

    @pytest.mark.asyncio
    async def test_generate_strategy_with_mock(self):
        """模拟投流策略生成"""
        with patch(
            "app.services.strategy_engine.get_model_router"
        ) as mock_router:
            mock_client = AsyncMock()
            mock_client.chat_json.return_value = {
                "recommended_platform": "tiktok",
                "daily_budget_suggestion": {"tiktok": 50},
                "estimated_roas": "2.5-3.8x",
                "detailed_analysis": "Test analysis",
                "content_angles": ["angle1"],
                "audience_targeting": {"age_range": "18-35"},
            }
            mock_router.return_value = mock_client

            result = await generate_strategy(
                product_name="Test",
                selling_points=["S1"],
                description="Desc",
                markets=["美国"],
                platforms=["tiktok"],
            )
            assert result["recommended_platform"] == "tiktok"


class TestModelRouterClient:
    """Model Router 客户端测试"""

    def test_client_initialization(self):
        """客户端应正确初始化"""
        client = ModelRouterClient()
        assert client._base_url is not None
        assert client._timeout > 0
        assert client._max_retries > 0
