"""Tests for Phase 12-01 Task 1: settings-based key resolution in AIVideoGeneratorService.

These tests do NOT require a real API key or network. They patch the `settings`
singleton to verify the service correctly reads from it.
"""
from __future__ import annotations

from unittest.mock import patch


from src.services.video_engine.ai_generator import AIVideoGeneratorService


def _patch_settings(**overrides):
    """Return a patch context-manager that sets the given settings fields."""
    from src.api.config import settings
    return patch.multiple(settings, **overrides)


class TestSettingsBasedKeyResolution:
    def test_runway_key_comes_from_settings(self):
        with _patch_settings(RUNWAY_API_KEY="test-runway-key-abc"):
            svc = AIVideoGeneratorService()
        assert svc.runway_key == "test-runway-key-abc"

    def test_pika_key_comes_from_settings(self):
        with _patch_settings(PIKA_API_KEY="test-pika-key-xyz"):
            svc = AIVideoGeneratorService()
        assert svc.pika_key == "test-pika-key-xyz"

    def test_none_settings_value_normalized_to_empty_string(self):
        """settings.* is Optional[str]; we coerce None/empty to \"\" so _get_api_key is uniform."""
        with _patch_settings(RUNWAY_API_KEY=None, PIKA_API_KEY=None):
            svc = AIVideoGeneratorService()
        assert svc.runway_key == ""
        assert svc.pika_key == ""

    def test_provider_uses_settings_ai_video_provider(self):
        with _patch_settings(AI_VIDEO_PROVIDER="runway", RUNWAY_API_KEY="key-123"):
            svc = AIVideoGeneratorService()
        assert svc.provider == "runway"
        assert svc.enabled is True
        assert svc._get_api_key() == "key-123"

    def test_provider_none_means_disabled(self):
        with _patch_settings(AI_VIDEO_PROVIDER="none", RUNWAY_API_KEY="key-123"):
            svc = AIVideoGeneratorService()
        assert svc.enabled is False

    def test_pika_provider_with_pika_key(self):
        with _patch_settings(AI_VIDEO_PROVIDER="pika", PIKA_API_KEY="pkey-999"):
            svc = AIVideoGeneratorService()
        assert svc.provider == "pika"
        assert svc._get_api_key() == "pkey-999"

    def test_no_os_getenv_in_ai_generator_init(self):
        """Phase 12 acceptance: the service must not CALL os.getenv for the three engine keys.

        We strip comments and docstrings first so a docstring mentioning the
        change (\"...rather than os.getenv...\") doesn't false-positive the check.
        """
        import inspect
        from src.services.video_engine import ai_generator
        source = inspect.getsource(ai_generator.AIVideoGeneratorService.__init__)
        # Strip comments and triple-quoted strings to avoid docstring false-positives
        import re
        stripped = re.sub(r"#.*", "", source)
        stripped = re.sub(r'\"\"\"[\s\S]*?\"\"\"', "", stripped)
        stripped = re.sub(r"'''[\s\S]*?'''", "", stripped)
        assert "os.getenv(" not in stripped, (
            "AIVideoGeneratorService.__init__ must read keys from settings, not os.getenv()"
        )

    def test_get_api_key_for_unknown_provider_returns_none(self):
        with _patch_settings(AI_VIDEO_PROVIDER="none", RUNWAY_API_KEY="k1", PIKA_API_KEY="k2"):
            svc = AIVideoGeneratorService()
        # provider is "none" so no key should resolve
        assert svc._get_api_key() is None
