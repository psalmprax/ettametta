import pytest
import os
from unittest.mock import patch


class TestCoreSettings:
    def test_defaults_load(self):
        from src.core.config import CoreSettings
        s = CoreSettings()
        assert s.APP_NAME == "Ettametta API"
        assert s.DEBUG is True
        assert s.PORT == 8000
        assert s.DEFAULT_TIMEOUT == 60
        assert s.LLM_TIMEOUT == 240
        assert s.MAX_RENDER_FRAMES == 2700

    def test_database_url_default(self):
        from src.core.config import CoreSettings
        s = CoreSettings()
        assert "sqlite" in s.DATABASE_URL

    def test_redis_url_default(self):
        from src.core.config import CoreSettings
        s = CoreSettings()
        assert "redis" in s.REDIS_URL

    def test_api_key_none_by_default(self):
        from src.core.config import CoreSettings
        s = CoreSettings()
        assert s.GROQ_API_KEY is None
        assert s.OPENAI_API_KEY is None
        assert s.ELEVENLABS_API_KEY is None

    def test_ollama_defaults(self):
        from src.core.config import CoreSettings
        s = CoreSettings()
        assert s.OLLAMA_MODEL == "llama3.2:1b"
        assert "11434" in s.OLLAMA_URL

    def test_resilience_defaults(self):
        from src.core.config import CoreSettings
        s = CoreSettings()
        assert s.DEFAULT_RETRY_COUNT == 3
        assert s.RETRY_MULTIPLIER == 1
        assert s.RETRY_MIN_WAIT == 2
        assert s.RETRY_MAX_WAIT == 10

    def test_env_var_override(self):
        with patch.dict(os.environ, {"APP_NAME": "CustomApp", "PORT": "9000"}):
            from src.core.config import CoreSettings
            s = CoreSettings()
            assert s.APP_NAME == "CustomApp"
            assert s.PORT == 9000

    def test_redirect_uri_properties(self):
        from src.core.config import CoreSettings
        s = CoreSettings()
        assert "/publish/auth/youtube/callback" in s.GOOGLE_YOUTUBE_REDIRECT_URI
        assert "/publish/auth/tiktok/callback" in s.TIKTOK_REDIRECT_URI

    def test_effective_gpu_queue_slots_env_override(self):
        from src.core.config import CoreSettings
        s = CoreSettings()
        with patch.dict(os.environ, {"GPU_QUEUE_SLOTS": "4"}):
            assert s.EFFECTIVE_GPU_QUEUE_SLOTS == 4


class TestApiSettings:
    def test_inherits_core(self):
        from src.api.config.settings import Settings
        s = Settings()
        assert hasattr(s, "APP_NAME")
        assert hasattr(s, "GATEWAY_HOST")

    def test_gateway_host_default(self):
        from src.api.config.settings import Settings
        s = Settings()
        assert s.GATEWAY_HOST == "localhost"

    def test_persisted_analysis_default(self):
        from src.api.config.settings import Settings
        s = Settings()
        assert s.ENABLE_PERSISTED_ANALYSIS is False

    def test_snapchat_redirect_uri(self):
        from src.api.config.settings import Settings
        s = Settings()
        assert "/publish/auth/snapchat/callback" in s.SNAPCHAT_REDIRECT_URI

    def test_twitch_redirect_uri(self):
        from src.api.config.settings import Settings
        s = Settings()
        assert "/publish/auth/twitch/callback" in s.TWITCH_REDIRECT_URI

    def test_debug_validator_true_strings(self):
        from src.api.config.settings import Settings
        for val in ["1", "true", "yes", "on"]:
            result = Settings.parse_debug(val)
            assert result is True

    def test_debug_validator_false_strings(self):
        from src.api.config.settings import Settings
        for val in ["0", "false", "no", "off", "production"]:
            result = Settings.parse_debug(val)
            assert result is False

    def test_debug_validator_bool_passthrough(self):
        from src.api.config.settings import Settings
        assert Settings.parse_debug(True) is True
        assert Settings.parse_debug(False) is False

    def test_debug_validator_invalid(self):
        from src.api.config.settings import Settings
        with pytest.raises(ValueError):
            Settings.parse_debug("maybe")

    def test_validate_critical_config(self):
        from src.api.config.settings import Settings
        s = Settings()
        result = s.validate_critical_config()
        assert "errors" in result
        assert "warnings" in result


class TestWorkerSettings:
    def test_can_load_core(self):
        from src.core.config import CoreSettings
        s = CoreSettings()
        assert s.ENV is not None
        assert s.DATABASE_URL is not None

    def test_core_settings_properties(self):
        from src.core.config import CoreSettings
        s = CoreSettings()
        vram = s.DETECTED_GPU_VRAM_GB
        assert vram is None or isinstance(vram, int)

    def test_model_config_allows_extra(self):
        from src.core.config import CoreSettings
        s = CoreSettings()
        assert s.model_config.get("extra") == "ignore"
