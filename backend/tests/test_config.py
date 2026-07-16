"""
配置测试
=======
"""

from app.config import Settings, get_settings


class TestSettings:
    """配置测试"""

    def test_default_settings(self):
        """默认配置应有必要字段"""
        settings = Settings()
        assert settings.APP_NAME == "CrossSell AI"
        assert settings.APP_VERSION == "0.1.0"
        assert "sqlite" in settings.DATABASE_URL.lower()
        assert settings.TEXT_MODEL == "qwen-max"

    def test_get_settings_singleton(self):
        """get_settings 应返回单例"""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_cors_origins_default(self):
        """默认 CORS 应包含 localhost"""
        settings = Settings()
        assert any("localhost" in origin for origin in settings.CORS_ORIGINS)
