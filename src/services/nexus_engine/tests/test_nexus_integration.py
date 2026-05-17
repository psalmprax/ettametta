"""
Integration-style tests for Nexus orchestration and publishing flows.

Tests the end-to-end flow from request parsing through service orchestration
to publication, with mocking at external boundaries (database, file system).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.api.routes.nexus import NexusComposeRequest
from src.shared.enums import SystemJobStatus


class TestNexusComposeRequest:
    """Validate NexusComposeRequest Pydantic model behavior."""

    def test_minimal_request(self):
        """A request with just a niche should produce sensible defaults."""
        req = NexusComposeRequest(niche="AI Technology")
        assert req.niche == "AI Technology"
        assert req.topic is None
        assert req.visual_paths is None
        assert req.voiceover_paths is None
        assert req.script_segments is None
        assert req.automation_mode == "manual"
        assert req.blueprint_id == "viral-reskin"
        assert req.cinema_mode is False
        assert req.generate_thumbnail is False

    def test_partial_automation_request(self):
        """PARTIAL mode should be accepted by the model."""
        req = NexusComposeRequest(niche="Motivation", automation_mode="partial")
        assert req.automation_mode == "partial"

    def test_full_automation_request(self):
        """FULL mode should accept all fields."""
        req = NexusComposeRequest(
            niche="AI Technology",
            topic="Neural Networks in 2026",
            automation_mode="full",
            blueprint_id="story-factory",
            cinema_mode=True,
            generate_thumbnail=True,
            job_metadata={"auto_publish": True, "platforms": ["youtube"]},
        )
        assert req.automation_mode == "full"
        assert req.blueprint_id == "story-factory"
        assert req.cinema_mode is True
        assert req.job_metadata["auto_publish"] is True

    def test_blueprint_default(self):
        """Default blueprint should be viral-reskin."""
        req1 = NexusComposeRequest(niche="test")
        req2 = NexusComposeRequest(niche="test", blueprint_id="custom-bp")
        assert req1.blueprint_id == "viral-reskin"
        assert req2.blueprint_id == "custom-bp"


class TestNexusComposePipeline:
    """Integration-style test for the Nexus compose background task."""

    @pytest.mark.asyncio
    async def test_run_nexus_composition_manual_no_blueprint(self):
        """
        Manual mode without matching blueprint should call assemble_video.

        Explicitly sets blueprint_id=None to bypass the blueprint execution path
        and reach the manual assembly code path.
        """
        from src.api.routes.nexus import run_nexus_composition

        request = NexusComposeRequest(
            niche="Motivation",
            script_segments=[{"text": "Test", "type": "hook"}],
            voiceover_paths=["/tmp/voice.mp3"],
            visual_paths=["/tmp/video.mp4"],
            blueprint_id=None,
        )

        mock_job = MagicMock()
        mock_job.id = "test-job-123"
        mock_job.niche = "Motivation"
        mock_job.status = SystemJobStatus.COMPOSING

        mock_db = AsyncMock()
        mock_db.__aenter__.return_value = mock_db
        mock_db.__aexit__.return_value = None

        mock_scalar_result = MagicMock()
        mock_scalar_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute = AsyncMock(return_value=mock_scalar_result)

        with (
            patch("src.api.routes.nexus.async_session_factory", return_value=mock_db),
            patch(
                "src.api.routes.ws.notify_nexus_job_update_sync",
                return_value=None,
            ),
            patch(
                "src.api.routes.nexus.base_nexus_service.assemble_video",
                new_callable=AsyncMock,
                return_value="/tmp/output.mp4",
            ),
        ):
            await run_nexus_composition("test-job-123", request)

            from src.api.routes.nexus import base_nexus_service

            base_nexus_service.assemble_video.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_nexus_composition_with_blueprint(self):
        """Blueprint execution path should call execute_blueprint."""
        from src.api.routes.nexus import run_nexus_composition

        request = NexusComposeRequest(
            niche="AI Technology",
            blueprint_id="viral-reskin",
            automation_mode="full",
        )

        mock_job = MagicMock()
        mock_job.id = "test-job-blueprint"
        mock_job.niche = "AI Technology"
        mock_job.status = SystemJobStatus.COMPOSING
        mock_job.output_path = None

        mock_db = AsyncMock()
        mock_db.__aenter__.return_value = mock_db
        mock_db.__aexit__.return_value = None

        mock_scalar_result = MagicMock()
        mock_scalar_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute = AsyncMock(return_value=mock_scalar_result)

        with (
            patch("src.api.routes.nexus.async_session_factory", return_value=mock_db),
            patch(
                "src.api.routes.ws.notify_nexus_job_update_sync",
                return_value=None,
            ),
            patch(
                "src.services.nexus_engine.blueprints.get_blueprint_by_id",
                new_callable=AsyncMock,
                return_value={"id": "viral-reskin", "nodes": []},
            ),
            patch(
                "src.services.nexus_engine.blueprints.execute_blueprint",
                new_callable=AsyncMock,
                return_value={
                    "status": "success",
                    "results": {"egress": {"output_path": "/tmp/output.mp4"}},
                },
            ),
        ):
            await run_nexus_composition("test-job-blueprint", request)

            from src.services.nexus_engine.blueprints import execute_blueprint

            execute_blueprint.assert_awaited_once()


class TestPublishingService:
    """Test the PublishingService API with mocked external boundaries."""

    @pytest.mark.asyncio
    async def test_publish_to_platform_youtube_success(self):
        """YouTube upload via publish_to_platform should succeed."""
        from src.services.publishing.service import base_publishing_service

        mock_response = {
            "platform": "youtube",
            "status": "published",
            "video_id": "vid1",
            "url": "https://youtube.com/watch?v=vid1",
            "published_at": datetime.utcnow().isoformat(),
        }

        with patch.object(
            base_publishing_service.youtube,
            "upload_video",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await base_publishing_service.publish_to_platform(
                user_id="test-user",
                platform="youtube",
                video_path="/tmp/test.mp4",
                metadata={"title": "Test Video", "tags": ["test"]},
            )

        assert result["status"] == "published"
        assert result["platform"] == "youtube"

    @pytest.mark.asyncio
    async def test_publish_to_platform_unsupported_raises(self):
        """Unsupported platform should raise ValueError."""
        from src.services.publishing.service import base_publishing_service

        with pytest.raises(ValueError, match="Unsupported platform"):
            await base_publishing_service.publish_to_platform(
                user_id="test-user",
                platform="snapchat",
                video_path="/tmp/test.mp4",
                metadata={"title": "Test"},
            )

    @pytest.mark.asyncio
    async def test_publish_to_multiple_all_success(self):
        """All platforms succeed in batch publish."""
        from src.services.publishing.service import base_publishing_service

        with (
            patch.object(
                base_publishing_service,
                "publish_to_platform",
                new_callable=AsyncMock,
                return_value={
                    "platform": "mock",
                    "status": "published",
                    "video_id": "mock123",
                    "url": "https://mock.example/video",
                    "published_at": datetime.utcnow().isoformat(),
                },
            ),
        ):
            result = await base_publishing_service.publish_to_multiple(
                user_id="test-user",
                platforms=["youtube", "tiktok", "instagram"],
                video_path="/tmp/test.mp4",
                metadata={"title": "Test Video", "tags": ["test"]},
            )

        assert result["published"] == 3
        assert result["failed"] == 0
        assert result["total"] == 3
        assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_publish_to_multiple_partial_failure(self):
        """One platform fails, others succeed — error isolation."""
        from src.services.publishing.service import base_publishing_service

        async def mock_publish(user_id, platform, video_path, metadata):
            if platform == "youtube":
                raise RuntimeError("YouTube API unavailable")
            return {
                "platform": platform,
                "status": "published",
                "video_id": "mock123",
                "url": f"https://{platform}.example/video",
                "published_at": datetime.utcnow().isoformat(),
            }

        with (
            patch.object(
                base_publishing_service,
                "publish_to_platform",
                new_callable=AsyncMock,
                side_effect=mock_publish,
            ),
        ):
            result = await base_publishing_service.publish_to_multiple(
                user_id="test-user",
                platforms=["youtube", "tiktok", "instagram"],
                video_path="/tmp/test.mp4",
                metadata={"title": "Test"},
            )

        assert result["published"] == 2
        assert result["failed"] == 1
        assert result["total"] == 3

        youtube_result = next(
            r for r in result["results"] if r["platform"] == "youtube"
        )
        assert youtube_result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_publish_to_multiple_unsupported_platform(self):
        """
        Unsupported platform errors appear in results, not as exceptions.

        publish_to_multiple uses asyncio.gather(return_exceptions=True) so
        ValueError from individual tasks is captured in the results dict.
        """
        from src.services.publishing.service import base_publishing_service

        with (
            patch.object(
                base_publishing_service,
                "publish_to_platform",
                new_callable=AsyncMock,
                side_effect=ValueError("Unsupported platform: snapchat"),
            ),
        ):
            result = await base_publishing_service.publish_to_multiple(
                user_id="test-user",
                platforms=["snapchat"],
                video_path="/tmp/test.mp4",
                metadata={"title": "Test"},
            )

        assert result["published"] == 0
        assert result["failed"] == 1
        assert result["total"] == 1
        snap_result = result["results"][0]
        assert snap_result["status"] == "failed"
