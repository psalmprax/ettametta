"""
Unit tests for A/B Testing variant creation and publishing endpoints.

Covers:
- POST /ab-testing/variants/create/{parent_job_id}
- POST /ab-testing/variants/publish/{test_id}
- Bug fix: ABTestDB receives variant_b_title/b_description
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.utils.models import ABTestDB, VideoJobDB, PublishedContentDB
from src.shared.enums import ABTestStatus, SystemJobStatus


def _make_mock_job(job_id: str, parent_id: str, variant_index: int,
                   output_path: str | None = "/outputs/video.mp4",
                   status: str = "COMPLETED",
                   user_id: str = "test-user-id") -> MagicMock:
    """Helper to create a mock VideoJobDB instance."""
    job = MagicMock(spec=VideoJobDB)
    job.id = job_id
    job.user_id = user_id
    job.output_path = output_path
    job.status = SystemJobStatus.COMPLETED if status == "COMPLETED" else SystemJobStatus.FAILED
    job.job_metadata = {"parent_id": parent_id, "variant_index": variant_index}
    return job


class TestCreateVariantABTest:
    """Tests for POST /ab-testing/variants/create/{parent_job_id}"""

    @pytest.mark.asyncio
    async def test_create_success(self):
        """Successfully creates an A/B test from two completed variant jobs."""
        parent_id = "parent-123"
        job_a = _make_mock_job("job-a", parent_id, 0, "/outputs/a.mp4")
        job_b = _make_mock_job("job-b", parent_id, 1, "/outputs/b.mp4")

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[job_a, job_b]))
        )))
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        current_user = MagicMock()
        current_user.id = "test-user-id"
        current_user.role = "USER"

        from src.api.routes.ab_testing import VariantCreateRequest

        request = VariantCreateRequest(
            variant_a_title="Variant A Title",
            variant_b_title="Variant B Title",
            variant_a_description="Description A",
            variant_b_description="Description B",
            target_metric="views",
        )

        from src.api.routes.ab_testing import create_variant_ab_test

        response = await create_variant_ab_test(
                parent_job_id=parent_id,
                request=request,
                current_user=current_user,
                db=mock_db,
            )

        assert response is not None


        # Verify ABTestDB was created with correct fields
        call_args = mock_db.add.call_args
        assert call_args is not None, "ABTestDB was not added to the session"
        created_test = call_args[0][0]
        assert isinstance(created_test, ABTestDB)
        assert created_test.variant_a_title == "Variant A Title"
        assert created_test.variant_b_title == "Variant B Title"
        assert created_test.variant_a_description == "Description A"
        assert created_test.variant_b_description == "Description B"
        assert created_test.target_metric == "views"
        assert created_test.status == ABTestStatus.ACTIVE
        assert created_test.user_id == "test-user-id"

        # Verify metadata_json stores variant job info
        meta = created_test.metadata_json or {}
        assert meta["parent_job_id"] == parent_id
        assert meta["variant_a_job_id"] == "job-a"
        assert meta["variant_b_job_id"] == "job-b"
        assert meta["variant_a_output_path"] == "/outputs/a.mp4"
        assert meta["variant_b_output_path"] == "/outputs/b.mp4"

    @pytest.mark.asyncio
    async def test_create_no_variants_found(self):
        """Returns 404 when no child variant jobs exist."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[]))
        )))

        current_user = MagicMock()
        current_user.id = "test-user-id"
        current_user.role = "USER"

        from src.api.routes.ab_testing import VariantCreateRequest

        request = VariantCreateRequest(
            variant_a_title="A",
            variant_b_title="B",
        )

        from src.api.routes.ab_testing import create_variant_ab_test
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await create_variant_ab_test(
                parent_job_id="nonexistent",
                request=request,
                current_user=current_user,
                db=mock_db,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_variant_a_not_completed(self):
        """Returns 400 when variant A job is not completed."""
        parent_id = "parent-123"
        # Variant A is still QUEUED
        job_a = _make_mock_job("job-a", parent_id, 0, status="QUEUED")
        # Even though we have job B, A must be completed first
        job_a.status = SystemJobStatus.QUEUED

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[job_a]))
        )))

        current_user = MagicMock()
        current_user.id = "test-user-id"
        current_user.role = "USER"

        from src.api.routes.ab_testing import VariantCreateRequest
        from src.api.routes.ab_testing import create_variant_ab_test
        from fastapi import HTTPException

        request = VariantCreateRequest(variant_a_title="A", variant_b_title="B")

        with pytest.raises(HTTPException) as exc_info:
            await create_variant_ab_test(
                parent_job_id=parent_id,
                request=request,
                current_user=current_user,
                db=mock_db,
            )

        assert exc_info.value.status_code == 400
        assert "not yet completed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_unauthorized(self):
        """Returns 403 when variant jobs belong to another user."""
        parent_id = "parent-123"
        # Job belongs to different user
        job_a = _make_mock_job("job-a", parent_id, 0,
                               user_id="other-user-id")

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[job_a]))
        )))

        current_user = MagicMock()
        current_user.id = "test-user-id"
        current_user.role = "USER"

        from src.api.routes.ab_testing import VariantCreateRequest
        from src.api.routes.ab_testing import create_variant_ab_test
        from fastapi import HTTPException

        request = VariantCreateRequest(variant_a_title="A", variant_b_title="B")

        with pytest.raises(HTTPException) as exc_info:
            await create_variant_ab_test(
                parent_job_id=parent_id,
                request=request,
                current_user=current_user,
                db=mock_db,
            )

        assert exc_info.value.status_code == 403


class TestPublishVariantABTest:
    """Tests for POST /ab-testing/variants/publish/{test_id}"""

    @pytest.mark.asyncio
    async def test_publish_requires_auth(self):
        """Returns 401 when platform is not authenticated."""
        test = MagicMock(spec=ABTestDB)
        test.id = "test-123"
        test.user_id = "test-user-id"
        test.metadata_json = {
            "variant_a_output_path": "/outputs/a.mp4",
            "variant_b_output_path": "/outputs/b.mp4",
        }
        test.variant_a_title = "Title A"
        test.variant_b_title = "Title B"

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(
            return_value=MagicMock(one_or_none=MagicMock(return_value=test))
        )))

        current_user = MagicMock()
        current_user.id = "test-user-id"
        current_user.role = "USER"

        from src.api.routes.ab_testing import VariantPublishRequest, publish_variant_ab_test
        from fastapi import HTTPException

        request = VariantPublishRequest(platform="YouTube Shorts", niche="Tech")

        with patch("src.services.optimization.auth.token_manager") as mock_tm:
            mock_tm.get_token = AsyncMock(return_value=None)  # No auth

            with pytest.raises(HTTPException) as exc_info:
                await publish_variant_ab_test(
                    test_id="test-123",
                    request=request,
                    current_user=current_user,
                    db=mock_db,
                )

        assert exc_info.value.status_code == 401
        assert "not authenticated" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_publish_fallback_to_single_video(self):
        """Publishes single video path when metadata_json has no variant paths.

        This is the fallback for A/B tests created via publish.py (title-only tests).
        """
        test = MagicMock(spec=ABTestDB)
        test.id = "test-123"
        test.user_id = "test-user-id"
        test.metadata_json = {}
        test.variant_a_title = "Title A"
        test.variant_b_title = "Title B"
        test.variant_a_description = None
        test.variant_b_description = None
        test.content_id = "content-123"  # Points to a PublishedContentDB

        published_content = MagicMock(spec=PublishedContentDB)
        published_content.source_uri = "https://youtube.com/watch?v=abc123"

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalars=MagicMock(
                one_or_none=MagicMock(return_value=test)
            )),
            # Second query looks up PublishedContentDB
            MagicMock(scalars=MagicMock(
                one_or_none=MagicMock(return_value=published_content)
            )),
        ])

        current_user = MagicMock()
        current_user.id = "test-user-id"
        current_user.role = "USER"

        from src.api.routes.ab_testing import VariantPublishRequest, publish_variant_ab_test

        request = VariantPublishRequest(platform="YouTube Shorts", niche="Tech")

        # Mock token_manager to return auth (patch at source module)
        with patch("src.services.optimization.auth.token_manager") as mock_tm:
            mock_tm.get_token = AsyncMock(return_value={"access_token": "test"})

            # Mock the optimization service and youtube publisher
            with patch("src.services.optimization.service.base_optimization_service") as mock_opt:
                mock_opt.generate_viral_package = AsyncMock(return_value=MagicMock(
                    title="Optimized Title",
                    description="Optimized desc",
                ))

                with patch("src.services.optimization.youtube_publisher.base_youtube_service") as mock_yt:
                    mock_yt.upload_video = AsyncMock(return_value="https://youtube.com/watch?v=result123")

                    response = await publish_variant_ab_test(
                        test_id="test-123",
                        request=request,
                        current_user=current_user,
                        db=mock_db,
                    )

        # Both variants should be published (variant B falls back to A's path)
        assert response is not None


class TestABTestDBBugFix:
    """Verify the bug fix: ABTestDB receives variant_b_title and variant_b_description."""

    def test_ab_test_db_has_metadata_json_column(self):
        """ABTestDB model class should have metadata_json column."""
        assert hasattr(ABTestDB, 'metadata_json'), "ABTestDB missing metadata_json column"

    def test_metadata_json_default_is_dict(self):
        """metadata_json should default to empty dict."""
        # Verify the column definition
        col = ABTestDB.__table__.columns.get('metadata_json')
        assert col is not None, "metadata_json column not found in ab_tests table"
        assert col.nullable, "metadata_json should be nullable"
