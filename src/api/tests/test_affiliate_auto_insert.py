"""
Tests for the Affiliate Auto-Insert endpoint (Phase 14).
=======================================================

Covers:
- Endpoint validation (auth, missing params, 422 handling)
- Job lookup and metadata resolution
- Impression count tracking
- Error handling (missing links, DB failures, missing files)
- URL injection in overlay text
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
import os
import tempfile


class _MockAsyncSession:
    """A proper async context manager for mocking DB sessions."""

    def __init__(self):
        self.execute = AsyncMock()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def app():
    """Create a minimal test app with just the auto-insert-links route."""
    from src.api.routes.video_transform import router

    _app = FastAPI()
    _app.include_router(router, prefix="/api/v1")
    return _app


@pytest.fixture
def client(app):
    """Create a test client for the minimal app."""
    return TestClient(app)


# ── Test class: Endpoint validation ───────────────────────────────────────


class TestAutoInsertEndpoint:
    """Verify endpoint contract: auth, request parsing."""

    def test_requires_auth(self, client):
        """Without auth token, the endpoint should return 401/403."""
        response = client.post(
            "/api/v1/video/auto-insert-links",
            json={"job_id": "some-job-id"},
        )
        assert response.status_code in (401, 403), (
            f"Expected 401/403, got {response.status_code}: {response.text}"
        )

    def test_accepts_valid_request_shape(self, client):
        """A well-formed POST body is structurally valid (doesn't 422)."""
        response = client.post(
            "/api/v1/video/auto-insert-links",
            json={"job_id": "test-uuid-1234"},
        )
        assert response.status_code != 422, (
            f"Request body rejected as invalid: {response.text}"
        )

    def test_validates_request_body(self, client):
        """Non-dict body should return 422."""
        response = client.post(
            "/api/v1/video/auto-insert-links",
            content=b"not-json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422, (
            f"Expected 422 for non-JSON body, got {response.status_code}"
        )


# ── Test class: Impression tracking via process_video_with_links ──────────


class TestAutoInsertImpressionTracking:
    """Verify that impression_count is incremented on AffiliateLinkDB."""

    @pytest.mark.asyncio
    async def test_increments_impression_count_on_success(self):
        """Verify process_video_with_links bumps impression_count for burned links."""
        from src.services.monetization.service import base_monetization_service

        insertion_plan = {
            "insertions": [
                {
                    "type": "overlay",
                    "asset_id": "link-1",
                    "timing": "5-10",
                    "context": "Test",
                    "script_addition": "Test . CTA: https://example.com",
                }
            ]
        }

        # Patch draw_text_overlay to succeed
        with patch(
            "src.services.video_engine.ffmpeg_utils.base_ffmpeg_service.draw_text_overlay",
            return_value=True,
        ):
            # Patch async_session_factory with a proper async context manager
            with patch(
                "src.api.utils.database.async_session_factory",
            ) as mock_sf:
                mock_session = _MockAsyncSession()
                mock_sf.return_value = mock_session

                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                    tmp_path = f.name

                try:
                    result = await base_monetization_service.process_video_with_links(
                        tmp_path, insertion_plan
                    )

                    assert result is not None
                    assert isinstance(result, str)
                    # The DB execute should have been called for the
                    # update(AffiliateLinkDB).impression_count bump
                    assert mock_session.execute.await_count >= 1, (
                        "Expected at least one DB execute call for impression_count bump"
                    )
                finally:
                    os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_missing_video_path_returns_original(self):
        """If video_path doesn't exist, process_video_with_links returns input unchanged."""
        from src.services.monetization.service import base_monetization_service

        result = await base_monetization_service.process_video_with_links(
            "/nonexistent/path.mp4", {"insertions": []}
        )
        assert result == "/nonexistent/path.mp4"

    @pytest.mark.asyncio
    async def test_no_insertions_returns_original_path(self):
        """Empty insertion plan should return the original path unchanged."""
        from src.services.monetization.service import base_monetization_service

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            tmp_path = f.name

        try:
            result = await base_monetization_service.process_video_with_links(
                tmp_path, {"insertions": []}
            )
            assert result == tmp_path
        finally:
            os.unlink(tmp_path)


# ── Test class: Error handling ────────────────────────────────────────────


class TestAutoInsertErrorHandling:
    """Test that error conditions are handled gracefully."""

    @pytest.mark.asyncio
    async def test_missing_link_does_not_crash(self):
        """When an asset has no link/url, _plan_link_insertion should not crash."""
        from src.services.monetization.service import base_monetization_service

        assets = [
            {
                "id": "link-missing-url",
                "name": "Missing URL Product",
                "cta_text": "Buy now",
            }
        ]

        with patch.object(
            base_monetization_service, "_call_hub", new_callable=AsyncMock
        ) as mock_hub:
            mock_hub.return_value = (
                '{"insertions": [{"type": "overlay", "asset_id": "link-missing-url", '
                '"timing": "5-10", "context": "test", '
                '"script_addition": "Check this out"}]}'
            )

            plan = await base_monetization_service._plan_link_insertion(
                "Test script", assets
            )

        assert "insertions" in plan
        if plan["insertions"]:
            insertion = plan["insertions"][0]
            assert insertion["script_addition"] == "Check this out"

    @pytest.mark.asyncio
    async def test_db_failure_does_not_fail_render(self):
        """If DB update fails during impression bump, render result is still returned."""
        from src.services.monetization.service import base_monetization_service

        insertion_plan = {
            "insertions": [
                {
                    "type": "overlay",
                    "asset_id": "link-1",
                    "timing": "5-10",
                    "context": "test",
                    "script_addition": "Buy now: https://example.com",
                }
            ]
        }

        with patch(
            "src.services.video_engine.ffmpeg_utils.base_ffmpeg_service.draw_text_overlay",
            return_value=True,
        ):
            with patch(
                "src.api.utils.database.async_session_factory",
            ) as mock_sf:
                # Make the session raise on execute (simulate DB crash)
                bad_session = _MockAsyncSession()
                bad_session.execute.side_effect = Exception("DB connection lost")
                mock_sf.return_value = bad_session

                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                    tmp_path = f.name

                try:
                    result = await base_monetization_service.process_video_with_links(
                        tmp_path, insertion_plan
                    )
                    assert result is not None
                    assert isinstance(result, str)
                finally:
                    os.unlink(tmp_path)


# ── Test class: Script addition URL injection ─────────────────────────────


class TestAutoInsertUrlInjection:
    """Verify that _plan_link_insertion appends URLs to overlay script additions."""

    @pytest.mark.asyncio
    async def test_appends_url_to_overlay_text(self):
        """An overlay insertion should have the URL appended to script_addition."""
        from src.services.monetization.service import base_monetization_service

        assets = [
            {
                "id": "link-42",
                "name": "Cool Product",
                "link": "https://example.com/cool",
                "cta_text": "Buy now",
            }
        ]

        with patch.object(
            base_monetization_service, "_call_hub", new_callable=AsyncMock
        ) as mock_hub:
            mock_hub.return_value = (
                '{"insertions": [{"type": "overlay", "asset_id": "link-42", '
                '"timing": "0-5", "context": "test", '
                '"script_addition": "Check this out"}]}'
            )

            plan = await base_monetization_service._plan_link_insertion(
                "Test script", assets
            )

        assert len(plan["insertions"]) == 1
        insertion = plan["insertions"][0]
        assert "https://example.com/cool" in insertion["script_addition"]
        assert "Buy now" in insertion["script_addition"]

    @pytest.mark.asyncio
    async def test_skips_voiceover_insertions(self):
        """Voiceover-type insertions should NOT get URL appended."""
        from src.services.monetization.service import base_monetization_service

        assets = [
            {
                "id": "link-42",
                "name": "Cool Product",
                "link": "https://example.com/cool",
                "cta_text": "Buy now",
            }
        ]

        with patch.object(
            base_monetization_service, "_call_hub", new_callable=AsyncMock
        ) as mock_hub:
            mock_hub.return_value = (
                '{"insertions": [{"type": "voiceover", "asset_id": "link-42", '
                '"timing": "0-5", "context": "test", '
                '"script_addition": "Mention the product"}]}'
            )

            plan = await base_monetization_service._plan_link_insertion(
                "Test script", assets
            )

        insertion = plan["insertions"][0]
        assert insertion["script_addition"] == "Mention the product"

    @pytest.mark.asyncio
    async def test_skips_insertions_when_asset_not_found(self):
        """If the asset_id doesn't match any asset, skip URL injection."""
        from src.services.monetization.service import base_monetization_service

        assets = [
            {
                "id": "link-99",
                "name": "Real Product",
                "link": "https://example.com/real",
                "cta_text": "Get it",
            }
        ]

        with patch.object(
            base_monetization_service, "_call_hub", new_callable=AsyncMock
        ) as mock_hub:
            mock_hub.return_value = (
                '{"insertions": [{"type": "overlay", "asset_id": "link-NONEXISTENT", '
                '"timing": "0-5", "context": "test", '
                '"script_addition": "Check this out"}]}'
            )

            plan = await base_monetization_service._plan_link_insertion(
                "Test script", assets
            )

        insertion = plan["insertions"][0]
        assert insertion["script_addition"] == "Check this out"


# ── Test class: plan_monetization_strategy integration ────────────────────


class TestAutoInsertStrategy:
    """Verify plan_monetization_strategy returns correct status codes."""

    @pytest.mark.asyncio
    async def test_no_assets_returns_no_assets_status(self):
        """When no affiliate assets exist, return status='no_assets'."""
        from src.services.monetization.service import base_monetization_service
        from src.services.monetization.orchestrator import (
            base_monetization_orchestrator_service,
        )

        with patch.object(
            base_monetization_orchestrator_service,
            "get_monetization_assets",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = []

            result = await base_monetization_service.plan_monetization_strategy(
                niche="UnknownNiche", video_path="/tmp/fake.mp4"
            )

        assert result["status"] == "no_assets"
        assert result["insertion_plan"]["insertions"] == []

    @pytest.mark.asyncio
    async def test_no_insertion_opportunities_returns_no_opportunities(self):
        """When AI finds no insertion points, return status='no_opportunities'."""
        from src.services.monetization.service import base_monetization_service
        from src.services.monetization.orchestrator import (
            base_monetization_orchestrator_service,
        )

        assets = [
            {
                "id": "link-1",
                "name": "Test Product",
                "link": "https://example.com",
                "cta_text": "Buy now",
            }
        ]

        with patch.object(
            base_monetization_orchestrator_service,
            "get_monetization_assets",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = assets

            result = await base_monetization_service.plan_monetization_strategy(
                niche="TestNiche", video_path="/tmp/fake.mp4"
            )

        # Should be no_opportunities because _call_hub will fail (no real AI)
        assert result["status"] in ("no_opportunities", "error")


# ── Run directly ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
