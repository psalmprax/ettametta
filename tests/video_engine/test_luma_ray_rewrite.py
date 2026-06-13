"""Tests for Phase 13: Luma Ray API rewrite.

Covers the migration from the deprecated Dream Machine endpoint
(`https://api.lumalabs.ai/dream-machine/v1/generations`) to the
current Luma Ray API (`https://api.lumalabs.ai/v1/generations`), plus
`LUMA_API_KEY` settings wiring.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch



# ─────────────────────────────────────────────────────────────────────────────
# Settings: LUMA_API_KEY must exist on both Settings classes
# ─────────────────────────────────────────────────────────────────────────────


class TestLumaApiKeySettings:
    def test_luma_api_key_on_api_settings(self):
        from src.api.config.settings import Settings

        assert "LUMA_API_KEY" in Settings.model_fields
        # Pydantic normalizes `str | None` to `Union[str, NoneType]`
        ann = Settings.model_fields["LUMA_API_KEY"].annotation
        assert ann == str | None or str(ann) in ("str | None", "Union[str, NoneType]")

    def test_luma_api_key_on_video_engine_settings(self):
        from src.services.video_engine.settings import Settings

        assert "LUMA_API_KEY" in Settings.model_fields
        ann = Settings.model_fields["LUMA_API_KEY"].annotation
        assert ann == str | None or str(ann) in ("str | None", "Union[str, NoneType]")

    def test_luma_api_key_default_is_none(self, monkeypatch):
        # Prevent .env from leaking a real key into the test
        monkeypatch.delenv("LUMA_API_KEY", raising=False)
        # Re-import the singleton so it sees the clean env
        from src.api.config.settings import Settings as ApiSettings

        s = ApiSettings()
        assert s.LUMA_API_KEY is None


# ─────────────────────────────────────────────────────────────────────────────
# PROVIDER_CONFIGS: luma endpoint must be the Ray API
# ─────────────────────────────────────────────────────────────────────────────


class TestLumaProviderConfig:
    def test_api_url_is_luma_ray_not_dream_machine(self):
        from src.services.video_engine.free_video_providers import (
            FreeVideoProviderService,
        )

        cfg = FreeVideoProviderService.PROVIDER_CONFIGS["luma"]
        assert cfg["api_url"] == "https://api.lumalabs.ai/v1"
        assert "dream-machine" not in cfg["api_url"]

    def test_model_default_is_ray_2(self):
        from src.services.video_engine.free_video_providers import (
            FreeVideoProviderService,
        )

        cfg = FreeVideoProviderService.PROVIDER_CONFIGS["luma"]
        assert cfg["model_default"] == "ray-2"

    def test_supports_image2video(self):
        from src.services.video_engine.free_video_providers import (
            FreeVideoProviderService,
        )

        cfg = FreeVideoProviderService.PROVIDER_CONFIGS["luma"]
        assert cfg["supports_image2video"] is True


# ─────────────────────────────────────────────────────────────────────────────
# _get_api_key: luma key resolution path
# ─────────────────────────────────────────────────────────────────────────────


class TestLumaKeyResolution:
    def test_get_api_key_returns_luma_key(self):
        from src.services.video_engine.free_video_providers import (
            FreeVideoProviderService,
        )

        svc = FreeVideoProviderService.__new__(FreeVideoProviderService)
        svc.luma_key = "luma-test-abc123"
        svc.runway_key = ""
        svc.pika_key = ""
        svc.zsky_key = ""
        svc.kling_key = ""
        svc.pixverse_key = ""
        svc.replicate_key = ""
        svc.stability_key = ""
        assert svc._get_api_key("luma") == "luma-test-abc123"

    def test_get_api_key_returns_empty_when_luma_key_unset(self):
        from src.services.video_engine.free_video_providers import (
            FreeVideoProviderService,
        )

        svc = FreeVideoProviderService.__new__(FreeVideoProviderService)
        svc.luma_key = ""
        svc.runway_key = ""
        svc.pika_key = ""
        svc.zsky_key = ""
        svc.kling_key = ""
        svc.pixverse_key = ""
        svc.replicate_key = ""
        svc.stability_key = ""
        assert svc._get_api_key("luma") == ""


# ─────────────────────────────────────────────────────────────────────────────
# _generate_luma: payload + headers + response handling
# ─────────────────────────────────────────────────────────────────────────────


def _service():
    from src.services.video_engine.free_video_providers import (
        FreeVideoProviderService,
    )

    svc = FreeVideoProviderService.__new__(FreeVideoProviderService)
    svc.luma_key = "luma-test-xyz"
    return svc


def _config():
    from src.services.video_engine.free_video_providers import (
        FreeVideoProviderService,
    )

    return dict(FreeVideoProviderService.PROVIDER_CONFIGS["luma"])


class TestGenerateLumaPayload:
    def test_post_uses_luma_ray_endpoint(self):
        svc = _service()
        captured = {}

        class _Resp:
            status_code = 201
            text = ""

            def json(self):
                return {"id": "gen-abc", "state": "queued"}

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, headers=None, json=None):
                captured["url"] = url
                captured["headers"] = headers
                captured["json"] = json
                return _Resp()

        with patch("httpx.AsyncClient", _Client):
            with patch.object(
                svc,
                "_poll_luma_job",
                AsyncMock(return_value={"video_uri": "https://x", "metadata": {}}),
            ):
                asyncio.run(
                    svc._generate_luma(
                        "a test prompt",
                        5,
                        "9:16",
                        None,
                        "luma-test-xyz",
                        _config(),
                    )
                )

        assert captured["url"] == "https://api.lumalabs.ai/v1/generations"
        assert captured["headers"]["Authorization"] == "Bearer luma-test-xyz"
        assert captured["json"]["prompt"] == "a test prompt"
        assert captured["json"]["model"] == "ray-2"
        assert captured["json"]["loop"] is False

    def test_duration_is_string_with_s_suffix(self):
        svc = _service()
        captured = {}

        class _Resp:
            status_code = 201

            def json(self):
                return {"id": "gen-1", "state": "queued"}

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, headers=None, json=None):
                captured["json"] = json
                return _Resp()

        with patch("httpx.AsyncClient", _Client):
            with patch.object(
                svc,
                "_poll_luma_job",
                AsyncMock(return_value={"video_uri": "https://x", "metadata": {}}),
            ):
                asyncio.run(
                    svc._generate_luma(
                        "p", 5, "16:9", None, "k", _config()
                    )
                )

        assert captured["json"]["duration"] == "5s"

    def test_duration_clamped_to_config_max(self):
        svc = _service()
        captured = {}

        class _Resp:
            status_code = 201

            def json(self):
                return {"id": "gen-1", "state": "queued"}

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, headers=None, json=None):
                captured["json"] = json
                return _Resp()

        with patch("httpx.AsyncClient", _Client):
            with patch.object(
                svc,
                "_poll_luma_job",
                AsyncMock(return_value={"video_uri": "https://x", "metadata": {}}),
            ):
                asyncio.run(
                    svc._generate_luma(
                        "p", 999, "16:9", None, "k", _config()
                    )
                )

        # max_duration in PROVIDER_CONFIGS["luma"] is 9
        assert captured["json"]["duration"] == "9s"

    def test_invalid_aspect_falls_back_to_16_9(self):
        svc = _service()
        captured = {}

        class _Resp:
            status_code = 201

            def json(self):
                return {"id": "gen-1", "state": "queued"}

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, headers=None, json=None):
                captured["json"] = json
                return _Resp()

        with patch("httpx.AsyncClient", _Client):
            with patch.object(
                svc,
                "_poll_luma_job",
                AsyncMock(return_value={"video_uri": "https://x", "metadata": {}}),
            ):
                asyncio.run(
                    svc._generate_luma(
                        "p", 5, "99:99", None, "k", _config()
                    )
                )

        assert captured["json"]["aspect_ratio"] == "16:9"

    def test_image2video_sends_keyframes(self):
        svc = _service()
        captured = {}

        class _Resp:
            status_code = 201

            def json(self):
                return {"id": "gen-1", "state": "queued"}

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, headers=None, json=None):
                captured["json"] = json
                return _Resp()

        with patch("httpx.AsyncClient", _Client):
            with patch.object(
                svc,
                "_poll_luma_job",
                AsyncMock(return_value={"video_uri": "https://x", "metadata": {}}),
            ):
                asyncio.run(
                    svc._generate_luma(
                        "p", 5, "9:16", "https://img.example/seed.jpg", "k", _config()
                    )
                )

        assert captured["json"]["keyframes"] == {
            "frame0": {"type": "image", "url": "https://img.example/seed.jpg"}
        }

    def test_non_200_returns_none_no_fallback(self):
        svc = _service()

        class _Resp:
            status_code = 401
            text = "Unauthorized"

            def json(self):
                return {}

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, headers=None, json=None):
                return _Resp()

        with patch("httpx.AsyncClient", _Client):
            result = asyncio.run(
                svc._generate_luma("p", 5, "16:9", None, "bad-key", _config())
            )

        assert result is None

    def test_immediate_completion_with_assets(self):
        """If the API ever returns assets.video synchronously, return it
        without polling."""
        svc = _service()

        class _Resp:
            status_code = 201

            def json(self):
                return {
                    "id": "gen-1",
                    "state": "completed",
                    "assets": {"video": "https://cdn.luma/v.mp4"},
                }

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, headers=None, json=None):
                return _Resp()

        with patch("httpx.AsyncClient", _Client):
            with patch.object(
                svc, "_poll_luma_job", AsyncMock()
            ) as poll:
                result = asyncio.run(
                    svc._generate_luma("p", 5, "16:9", None, "k", _config())
                )

        assert result == {
            "video_uri": "https://cdn.luma/v.mp4",
            "metadata": {"model": "ray-2", "aspect_ratio": "16:9"},
        }
        # Polling must not have been called for the sync path
        poll.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# _poll_luma_job: state machine + response shape
# ─────────────────────────────────────────────────────────────────────────────


class TestPollLumaJob:
    def test_poll_returns_video_on_completed(self):
        svc = _service()
        config = _config()

        responses = [
            {"state": "dreaming"},
            {"state": "queued"},
            {
                "state": "completed",
                "assets": {"video": "https://cdn.luma/abc.mp4"},
                "model": "ray-2",
            },
        ]

        class _Resp:
            def __init__(self, data):
                self.status_code = 200
                self._data = data

            def json(self):
                return self._data

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def get(self, url, headers=None):
                return _Resp(responses.pop(0))

        with patch("httpx.AsyncClient", _Client):
            with patch("asyncio.sleep", AsyncMock()):
                result = asyncio.run(
                    svc._poll_luma_job("gen-1", "k", config, max_attempts=10, delay=0.01)
                )

        assert result == {
            "video_uri": "https://cdn.luma/abc.mp4",
            "metadata": {"model": "ray-2", "aspect_ratio": None},
        }

    def test_poll_returns_none_on_failed(self):
        svc = _service()
        config = _config()

        class _Resp:
            status_code = 200

            def json(self):
                return {"state": "failed", "failure_reason": "content_policy_violation"}

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def get(self, url, headers=None):
                return _Resp()

        with patch("httpx.AsyncClient", _Client):
            with patch("asyncio.sleep", AsyncMock()):
                result = asyncio.run(
                    svc._poll_luma_job("gen-1", "k", config, max_attempts=5, delay=0.01)
                )

        assert result is None

    def test_poll_returns_none_on_completed_without_video(self):
        svc = _service()
        config = _config()

        class _Resp:
            status_code = 200

            def json(self):
                return {"state": "completed", "assets": {}}

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def get(self, url, headers=None):
                return _Resp()

        with patch("httpx.AsyncClient", _Client):
            with patch("asyncio.sleep", AsyncMock()):
                result = asyncio.run(
                    svc._poll_luma_job("gen-1", "k", config, max_attempts=5, delay=0.01)
                )

        assert result is None

    def test_poll_uses_correct_endpoint(self):
        svc = _service()
        config = _config()
        captured_url = {}

        class _Resp:
            status_code = 200

            def json(self):
                return {"state": "completed", "assets": {"video": "https://x"}}

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def get(self, url, headers=None):
                captured_url["url"] = url
                return _Resp()

        with patch("httpx.AsyncClient", _Client):
            with patch("asyncio.sleep", AsyncMock()):
                asyncio.run(
                    svc._poll_luma_job("gen-abc", "k", config, max_attempts=5, delay=0.01)
                )

        assert captured_url["url"] == "https://api.lumalabs.ai/v1/generations/gen-abc"

    def test_poll_uses_bearer_auth(self):
        svc = _service()
        config = _config()
        captured_headers = {}

        class _Resp:
            status_code = 200

            def json(self):
                return {"state": "completed", "assets": {"video": "https://x"}}

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def get(self, url, headers=None):
                captured_headers.update(headers or {})
                return _Resp()

        with patch("httpx.AsyncClient", _Client):
            with patch("asyncio.sleep", AsyncMock()):
                asyncio.run(
                    svc._poll_luma_job("g", "luma-my-key", config, max_attempts=5, delay=0.01)
                )

        assert captured_headers["Authorization"] == "Bearer luma-my-key"


# ─────────────────────────────────────────────────────────────────────────────
# generate_video: provider integration — flag-off path skips Luma cleanly
# ─────────────────────────────────────────────────────────────────────────────


class TestGenerateVideoLumaIntegration:
    def test_no_luma_key_skips_luma(self):
        """When LUMA_API_KEY is empty, _get_api_key returns "" and the
        provider loop should skip Luma and try fallbacks (or return None)."""
        svc = _service()
        svc.luma_key = ""  # no key
        svc.runway_key = ""
        svc.pika_key = ""
        svc.zsky_key = ""
        svc.kling_key = ""
        svc.pixverse_key = ""
        svc.replicate_key = ""
        svc.stability_key = ""
        svc.primary_provider = "luma"
        svc.enabled = True
        svc.fallback_providers = []
        svc.circuit_breaker = MagicMock()
        svc.circuit_breaker.is_open = MagicMock(return_value=False)
        svc.circuit_breaker.record_success = MagicMock()
        svc.circuit_breaker.record_failure = MagicMock()

        with patch.object(svc, "_generate_with_browser", AsyncMock(return_value=None)):
            result = asyncio.run(svc.generate_video("p"))

        # No Luma call should have been made; circuit breaker records failure
        svc.circuit_breaker.record_failure.assert_called()
        assert result is None
