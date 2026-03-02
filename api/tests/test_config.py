"""
Test Suite for API Configuration
=================================
Tests for config.py settings and validation
"""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestConfigSettings:
    """Test configuration settings"""
    
    def test_default_settings_exist(self):
        """Test that default settings are defined"""
        from api.config import settings
        
        assert settings.APP_NAME == "ettametta API"
        assert settings.ENV == "development"
        assert settings.ALGORITHM == "HS256"
    
    def test_video_quality_tiers_disabled_by_default(self):
        """Test that video quality tiers are disabled by default"""
        from api.config import settings
        
        assert settings.ENABLE_SOUND_DESIGN == False
        assert settings.ENABLE_MOTION_GRAPHICS == False
        assert settings.AI_VIDEO_PROVIDER == "none"
        assert settings.DEFAULT_QUALITY_TIER == "standard"
    
    def test_agent_frameworks_disabled_by_default(self):
        """Test that agent frameworks are disabled by default"""
        from api.config import settings
        
        assert settings.ENABLE_LANGCHAIN == False
        assert settings.ENABLE_CREWAI == False
        assert settings.ENABLE_INTERPRETER == False
        assert settings.ENABLE_AFFILIATE_API == False
        assert settings.ENABLE_TRADING == False
    
    def test_storage_defaults(self):
        """Test default storage configuration"""
        from api.config import settings
        
        assert settings.STORAGE_PROVIDER == "LOCAL"
        assert settings.STORAGE_REGION == "us-east-1"
    
    def test_database_defaults(self):
        """Test default database configuration"""
        from api.config import settings
        
        assert "sqlite" in settings.DATABASE_URL
        assert "redis" in settings.REDIS_URL
    
    def test_validate_critical_config_no_errors_in_dev(self):
        """Test that validation passes in development"""
        from api.config import Settings
        
        with patch.dict(os.environ, {"ENV": "development", "SECRET_KEY": "dev_key"}):
            settings = Settings()
            report = settings.validate_critical_config()
            assert len(report["errors"]) == 0
    
    def test_validate_critical_config_errors_in_production(self):
        """Test that validation fails in production without proper config"""
        from api.config import Settings
        
        with patch.dict(os.environ, {
            "ENV": "production",
            "SECRET_KEY": "dev_insecure_key",
            "PRODUCTION_DOMAIN": "localhost"
        }):
            settings = Settings()
            report = settings.validate_critical_config()
            # Should have errors for insecure secret and localhost domain
            assert len(report["errors"]) >= 2
            assert any("SECRET_KEY" in err for err in report["errors"])
            assert any("PRODUCTION_DOMAIN" in err for err in report["errors"])

    def test_cors_origins_parsing(self):
        """Test that CORS_ORIGINS is parsed correctly in main.py logic"""
        from api.config import Settings
        settings = Settings()
        settings.CORS_ORIGINS = "http://a.com, http://b.com "
        origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
        assert origins == ["http://a.com", "http://b.com"]


class TestEnvironmentVariables:
    """Test environment variable handling"""
    
    def test_langchain_env_enables_service(self):
        """Test that ENABLE_LANGCHAIN=true enables the service"""
        with patch.dict(os.environ, {"ENABLE_LANGCHAIN": "true", "GROQ_API_KEY": "test_key"}):
            from api.config import Settings
            settings = Settings()
            assert settings.ENABLE_LANGCHAIN == True
    
    def test_crewai_env_enables_service(self):
        """Test that ENABLE_CREWAI=true enables the service"""
        with patch.dict(os.environ, {"ENABLE_CREWAI": "true", "GROQ_API_KEY": "test_key"}):
            from api.config import Settings
            settings = Settings()
            assert settings.ENABLE_CREWAI == True
    
    def test_ai_video_provider_env(self):
        """Test AI_VIDEO_PROVIDER environment variable"""
        with patch.dict(os.environ, {"AI_VIDEO_PROVIDER": "runway"}):
            from api.config import Settings
            settings = Settings()
            assert settings.AI_VIDEO_PROVIDER == "runway"
    
    def test_quality_tier_env(self):
        """Test DEFAULT_QUALITY_TIER environment variable"""
        with patch.dict(os.environ, {"DEFAULT_QUALITY_TIER": "premium"}):
            from api.config import Settings
            settings = Settings()
            assert settings.DEFAULT_QUALITY_TIER == "premium"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
