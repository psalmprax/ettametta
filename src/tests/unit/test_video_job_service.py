"""
Unit tests for VideoJobService.create_job
=========================================

Validates the service-layer refactor introduced for video job creation:

1. The new explicit parameters are honored:
   - job_id (e.g. a Celery task ID)
   - progress (initial percentage)
   - source_uri (overrides prompt fallback)
   - extra_metadata (merged into the base metadata dict)

2. The metadata merge order is base-first, extra_metadata-second (i.e.
   keys in extra_metadata OVERRIDE the base engine / style / niche values).

3. auto_commit=True commits the transaction; auto_commit=False flushes
   only, so the caller controls the surrounding transaction.
"""

import os

# Set required env vars BEFORE any src.* import that might transitively
# import src.api.utils.security (which checks SECRET_KEY at import time).
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_testing_purposes_123")
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ettametta.db")
os.environ.setdefault("GROQ_API_KEY", "test_groq_key")

import uuid
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import select

from src.api.utils.database import AsyncSessionLocal
from src.api.utils.user_models import UserDB, UserRole
from src.api.utils.models import VideoJobDB
from src.shared.enums import SystemJobStatus
from src.services.video_engine.job_service import VideoJobService


async def _create_test_user(db, suffix: str = "") -> str:
    """Helper: insert a user row and return its id (FK target for VideoJobDB)."""
    user_id = f"test_user_{suffix or uuid.uuid4().hex[:8]}"
    user = UserDB(
        id=user_id,
        email=f"{user_id}@example.com",
        username=user_id,
        hashed_password="hashed_test_password",
        role=UserRole.USER,
    )
    db.add(user)
    await db.flush()
    return user_id


class TestCreateJobSignature:
    """Exercise the new explicit kwargs: job_id, progress, source_uri."""

    @pytest.mark.asyncio
    async def test_explicit_job_id_progress_and_source_uri(self, test_db):
        """All new explicit params are persisted verbatim on the job row."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="explicit")
            await db.commit()

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            task_id = str(uuid.uuid4())
            source = "https://example.com/source.mp4"

            job = await service.create_job(
                user_id=user_id,
                title="Explicit Param Test",
                engine="video_transform",
                job_id=task_id,
                progress=42,
                source_uri=source,
            )

            assert job.id == task_id
            assert job.progress == 42
            assert job.source_uri == source
            assert job.title == "Explicit Param Test"
            assert job.user_id == user_id

    @pytest.mark.asyncio
    async def test_prompt_fallback_when_source_uri_omitted(self, test_db):
        """When source_uri is None, prompt is used as the source_uri."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="fallback")
            await db.commit()

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            job = await service.create_job(
                user_id=user_id,
                title="Prompt Fallback",
                engine="veo3",
                job_id=str(uuid.uuid4()),
                prompt="A majestic falcon over snow-capped mountains",
            )

            assert job.source_uri == "A majestic falcon over snow-capped mountains"

    @pytest.mark.asyncio
    async def test_explicit_source_uri_beats_prompt(self, test_db):
        """When both are supplied, source_uri wins over prompt."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="precedence")
            await db.commit()

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            job = await service.create_job(
                user_id=user_id,
                title="Precedence Test",
                engine="veo3",
                job_id=str(uuid.uuid4()),
                prompt="this-is-the-prompt",
                source_uri="https://example.com/override.mp4",
            )

            assert job.source_uri == "https://example.com/override.mp4"


class TestMetadataMergeOrder:
    """Validate base engine/style/niche + extra_metadata override behavior."""

    @pytest.mark.asyncio
    async def test_base_metadata_only_when_no_extra(self, test_db):
        """Without extra_metadata, job_metadata contains only the base keys."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="base")
            await db.commit()

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            job = await service.create_job(
                user_id=user_id,
                title="Base Metadata",
                engine="video_transform",
                job_id=str(uuid.uuid4()),
                niche="Motivation",
                style="Cinematic",
            )

            assert job.job_metadata == {
                "engine": "video_transform",
                "style": "Cinematic",
                "niche": "Motivation",
            }

    @pytest.mark.asyncio
    async def test_extra_metadata_merges_with_base(self, test_db):
        """extra_metadata keys are added alongside the base keys."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="merge")
            await db.commit()

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            job = await service.create_job(
                user_id=user_id,
                title="Merge Test",
                engine="video_transform",
                job_id=str(uuid.uuid4()),
                niche="Motivation",
                style="Cinematic",
                extra_metadata={
                    "platform": "TikTok",
                    "quality_tier": "premium",
                    "analysis_task_id": "task-abc-123",
                },
            )

            assert job.job_metadata == {
                "engine": "video_transform",
                "style": "Cinematic",
                "niche": "Motivation",
                "platform": "TikTok",
                "quality_tier": "premium",
                "analysis_task_id": "task-abc-123",
            }

    @pytest.mark.asyncio
    async def test_extra_metadata_overrides_base_engine(self, test_db):
        """An extra_metadata 'engine' key overrides the base 'engine' value."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="override-engine")
            await db.commit()

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            job = await service.create_job(
                user_id=user_id,
                title="Engine Override",
                engine="video_transform",
                job_id=str(uuid.uuid4()),
                extra_metadata={"engine": "internal"},
            )

            assert job.job_metadata["engine"] == "internal"

    @pytest.mark.asyncio
    async def test_extra_metadata_overrides_base_style_and_niche(self, test_db):
        """extra_metadata can override both 'style' and 'niche' simultaneously."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="override-both")
            await db.commit()

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            job = await service.create_job(
                user_id=user_id,
                title="Override Style+Niche",
                engine="video_transform",
                job_id=str(uuid.uuid4()),
                niche="Motivation",
                style="Cinematic",
                extra_metadata={
                    "style": "Glitch Alpha",
                    "niche": "AI Technology",
                    "platform": "YouTube Shorts",
                },
            )

            assert job.job_metadata["style"] == "Glitch Alpha"
            assert job.job_metadata["niche"] == "AI Technology"
            assert job.job_metadata["engine"] == "video_transform"  # not overridden
            assert job.job_metadata["platform"] == "YouTube Shorts"


class TestAutoCommitBehavior:
    """Validate the auto_commit=True/False transaction contract."""

    @pytest.mark.asyncio
    async def test_auto_commit_true_persists_row(self, test_db):
        """With auto_commit=True (default), the row is queryable after the call."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="autocommit-true")
            await db.commit()

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            job = await service.create_job(
                user_id=user_id,
                title="AutoCommit True",
                engine="video_transform",
                job_id="ac-true-001",
            )

        # Fresh session: the row should already be visible.
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(VideoJobDB).where(VideoJobDB.id == "ac-true-001")
            )
            assert res.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_auto_commit_false_requires_caller_commit(self, test_db):
        """With auto_commit=False, the row is NOT visible until the caller commits."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="autocommit-false")
            await db.commit()

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            await service.create_job(
                user_id=user_id,
                title="AutoCommit False",
                engine="video_transform",
                job_id="ac-false-001",
                auto_commit=False,
            )

        # The job should NOT be visible in a fresh session because
        # the service only flushed; the caller never committed.
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(VideoJobDB).where(VideoJobDB.id == "ac-false-001")
            )
            assert res.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_auto_commit_false_rolls_back_on_failure(self, test_db):
        """A rollback after auto_commit=False discards the flushed job."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="rollback")
            await db.commit()

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            await service.create_job(
                user_id=user_id,
                title="Will Roll Back",
                engine="video_transform",
                job_id="rollback-001",
                auto_commit=False,
            )
            await db.rollback()

        # The flushed job should be gone after rollback.
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(VideoJobDB).where(VideoJobDB.id == "rollback-001")
            )
            assert res.scalar_one_or_none() is None


class TestGetUserJobs:
    """Validate get_user_jobs filtering, pagination, and admin include_all."""

    @pytest.mark.asyncio
    async def test_returns_only_jobs_for_user(self, test_db):
        """Jobs belonging to other users must not leak into the result."""
        async with AsyncSessionLocal() as db:
            alice = await _create_test_user(db, suffix="alice")
            bob = await _create_test_user(db, suffix="bob")
            service = VideoJobService(db)
            for i in range(3):
                await service.create_job(
                    user_id=alice,
                    title=f"Alice Job {i}",
                    engine="video_transform",
                    job_id=f"alice-{i}",
                )
            for i in range(2):
                await service.create_job(
                    user_id=bob,
                    title=f"Bob Job {i}",
                    engine="video_transform",
                    job_id=f"bob-{i}",
                )

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            jobs, total = await service.get_user_jobs(user_id=alice, limit=10, offset=0)

        assert total == 3
        assert len(jobs) == 3
        assert all(j["id"].startswith("alice-") for j in jobs)

    @pytest.mark.asyncio
    async def test_pagination_limit_and_offset(self, test_db):
        """Limit and offset slice the unified result list correctly."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="pager")
            service = VideoJobService(db)
            for i in range(5):
                await service.create_job(
                    user_id=user_id,
                    title=f"Pager Job {i}",
                    engine="video_transform",
                    job_id=f"pager-{i}",
                )

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            page1, total1 = await service.get_user_jobs(user_id=user_id, limit=2, offset=0)
            page2, total2 = await service.get_user_jobs(user_id=user_id, limit=2, offset=2)
            page3, total3 = await service.get_user_jobs(user_id=user_id, limit=2, offset=4)

        assert total1 == total2 == total3 == 5
        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1
        # No overlap between pages
        page1_ids = {j["id"] for j in page1}
        page2_ids = {j["id"] for j in page2}
        page3_ids = {j["id"] for j in page3}
        assert page1_ids.isdisjoint(page2_ids)
        assert page1_ids.isdisjoint(page3_ids)
        assert page2_ids.isdisjoint(page3_ids)

    @pytest.mark.asyncio
    async def test_unified_dict_shape(self, test_db):
        """Returned dicts contain the canonical keys/values from the service."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="shape")
            service = VideoJobService(db)
            await service.create_job(
                user_id=user_id,
                title="Shape Test",
                engine="video_transform",
                job_id="shape-001",
                source_uri="https://example.com/x.mp4",
            )

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            jobs, total = await service.get_user_jobs(user_id=user_id)

        assert total == 1
        job = jobs[0]
        assert job["id"] == "shape-001"
        assert job["title"] == "Shape Test"
        assert job["source_uri"] == "https://example.com/x.mp4"
        assert job["engine"] == "video_transform"
        assert job["progress"] == 0
        # Status is normalized to its .value
        assert job["status"] == SystemJobStatus.QUEUED.value
        # created_at is populated
        assert job["created_at"] is not None


class TestGetJobById:
    """Validate get_job_by_id ownership scoping and not-found behavior."""

    @pytest.mark.asyncio
    async def test_returns_job_for_owner(self, test_db):
        """Owner can fetch their own job by id."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="owner")
            service = VideoJobService(db)
            await service.create_job(
                user_id=user_id,
                title="Owner Lookup",
                engine="video_transform",
                job_id="owner-001",
            )

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            result = await service.get_job_by_id("owner-001", user_id)

        assert result is not None
        assert result["id"] == "owner-001"
        assert result["title"] == "Owner Lookup"
        assert result["engine"] == "video_transform"
        assert result["status"] == SystemJobStatus.QUEUED.value

    @pytest.mark.asyncio
    async def test_returns_none_for_wrong_user(self, test_db):
        """Looking up another user's job must return None (not leak data)."""
        async with AsyncSessionLocal() as db:
            alice = await _create_test_user(db, suffix="alice-priv")
            bob = await _create_test_user(db, suffix="bob-priv")
            service = VideoJobService(db)
            await service.create_job(
                user_id=alice,
                title="Alice's Secret Job",
                engine="video_transform",
                job_id="secret-001",
            )

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            result = await service.get_job_by_id("secret-001", bob)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_id(self, test_db):
        """Unknown job_id must return None, not raise."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="missing")
            service = VideoJobService(db)
            result = await service.get_job_by_id("does-not-exist", user_id)

        assert result is None


class TestUpdateJobStatus:
    """Validate update_job_status enum coercion and success/failure paths."""

    @pytest.mark.asyncio
    async def test_updates_status_with_enum_value(self, test_db):
        """Passing a SystemJobStatus enum updates the job's status column."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="upd-enum")
            service = VideoJobService(db)
            await service.create_job(
                user_id=user_id,
                title="Enum Update",
                engine="video_transform",
                job_id="upd-001",
            )

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            ok = await service.update_job_status("upd-001", SystemJobStatus.PROCESSING)

        assert ok is True
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(VideoJobDB).where(VideoJobDB.id == "upd-001"))
            job = res.scalar_one()
            assert job.status == SystemJobStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_updates_status_with_uppercase_string(self, test_db):
        """A valid uppercase string must be coerced to the enum and applied."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="upd-str")
            service = VideoJobService(db)
            await service.create_job(
                user_id=user_id,
                title="String Update",
                engine="video_transform",
                job_id="upd-002",
            )

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            ok = await service.update_job_status("upd-002", "COMPLETED")

        assert ok is True
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(VideoJobDB).where(VideoJobDB.id == "upd-002"))
            job = res.scalar_one()
            assert job.status == SystemJobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_invalid_string_status_returns_false(self, test_db):
        """An unknown status string must be rejected (returns False, no change)."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="upd-bad")
            service = VideoJobService(db)
            await service.create_job(
                user_id=user_id,
                title="Invalid Status",
                engine="video_transform",
                job_id="upd-003",
            )

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            ok = await service.update_job_status("upd-003", "NOT_A_REAL_STATUS")

        assert ok is False
        # Original status must be untouched.
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(VideoJobDB).where(VideoJobDB.id == "upd-003"))
            job = res.scalar_one()
            assert job.status == SystemJobStatus.QUEUED

    @pytest.mark.asyncio
    async def test_missing_job_returns_false(self, test_db):
        """Updating a non-existent job_id must return False."""
        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            ok = await service.update_job_status("ghost-job", SystemJobStatus.QUEUED)
        assert ok is False


class TestDeleteJob:
    """Validate delete_job ownership scoping and dual-table lookup."""

    @pytest.mark.asyncio
    async def test_deletes_job_for_owner(self, test_db):
        """Owner can delete their own job; subsequent lookup returns None."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="del-owner")
            service = VideoJobService(db)
            await service.create_job(
                user_id=user_id,
                title="Delete Me",
                engine="video_transform",
                job_id="del-001",
            )

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            ok = await service.delete_job("del-001", user_id)

        assert ok is True
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(VideoJobDB).where(VideoJobDB.id == "del-001"))
            assert res.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_cannot_delete_another_users_job(self, test_db):
        """Bob attempting to delete Alice's job returns False and leaves it intact."""
        async with AsyncSessionLocal() as db:
            alice = await _create_test_user(db, suffix="alice-del")
            bob = await _create_test_user(db, suffix="bob-del")
            service = VideoJobService(db)
            await service.create_job(
                user_id=alice,
                title="Alice Owns This",
                engine="video_transform",
                job_id="del-002",
            )

        async with AsyncSessionLocal() as db:
            service = VideoJobService(db)
            ok = await service.delete_job("del-002", bob)

        assert ok is False
        # Job must still exist.
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(VideoJobDB).where(VideoJobDB.id == "del-002"))
            assert res.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_delete_missing_returns_false(self, test_db):
        """Deleting a non-existent job_id returns False (no exception)."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="del-missing")
            service = VideoJobService(db)
            ok = await service.delete_job("never-existed", user_id)
        assert ok is False


class TestAbortJob:
    """Validate abort_job: authorization, Celery revoke, status flip, WS notify."""

    @pytest.mark.asyncio
    async def test_owner_can_abort_own_job(self, test_db):
        """Owner aborting their own job: status -> ABORTED, Celery revoked, WS notified."""
        async with AsyncSessionLocal() as db:
            user_id = await _create_test_user(db, suffix="abort-owner")
            service = VideoJobService(db)
            await service.create_job(
                user_id=user_id,
                title="Abortable Job",
                engine="video_transform",
                job_id="abort-001",
            )

        with patch("src.api.utils.celery.celery_app") as mock_celery, \
             patch("src.api.routes.ws.notify_job_update_sync") as mock_notify:
            mock_celery.control.revoke = MagicMock()
            mock_notify.return_value = None

            async with AsyncSessionLocal() as db:
                service = VideoJobService(db)
                ok = await service.abort_job("abort-001", user_id, UserRole.USER)

        assert ok is True
        # Celery revoke was called with terminate=True.
        mock_celery.control.revoke.assert_called_once_with("abort-001", terminate=True)
        # WS notifier was called.
        assert mock_notify.call_count == 1
        notify_arg = mock_notify.call_args[0][0]
        assert notify_arg["id"] == "abort-001"
        assert notify_arg["status"] == SystemJobStatus.ABORTED.value

        # Status is persisted as ABORTED.
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(VideoJobDB).where(VideoJobDB.id == "abort-001"))
            job = res.scalar_one()
            assert job.status == SystemJobStatus.ABORTED

    @pytest.mark.asyncio
    async def test_admin_can_abort_any_job(self, test_db):
        """An ADMIN user can abort a job they don't own."""
        async with AsyncSessionLocal() as db:
            alice = await _create_test_user(db, suffix="abort-alice")
            service = VideoJobService(db)
            await service.create_job(
                user_id=alice,
                title="Alice's Running Job",
                engine="video_transform",
                job_id="abort-002",
            )

        with patch("src.api.utils.celery.celery_app") as mock_celery, \
             patch("src.api.routes.ws.notify_job_update_sync") as mock_notify:
            mock_celery.control.revoke = MagicMock()
            mock_notify.return_value = None

            # Admin (different user_id) aborts Alice's job
            async with AsyncSessionLocal() as db:
                service = VideoJobService(db)
                ok = await service.abort_job(
                    "abort-002",
                    "some_admin_id",
                    UserRole.ADMIN,
                )

        assert ok is True
        mock_celery.control.revoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_owner_non_admin_cannot_abort(self, test_db):
        """A regular user cannot abort another user's job; status remains unchanged."""
        async with AsyncSessionLocal() as db:
            alice = await _create_test_user(db, suffix="abort-alice-2")
            bob = await _create_test_user(db, suffix="abort-bob")
            service = VideoJobService(db)
            await service.create_job(
                user_id=alice,
                title="Alice's Protected Job",
                engine="video_transform",
                job_id="abort-003",
            )

        with patch("src.api.utils.celery.celery_app") as mock_celery, \
             patch("src.api.routes.ws.notify_job_update_sync") as mock_notify:
            mock_celery.control.revoke = MagicMock()
            mock_notify.return_value = None

            async with AsyncSessionLocal() as db:
                service = VideoJobService(db)
                ok = await service.abort_job("abort-003", bob, UserRole.USER)

        assert ok is False
        # Celery revoke must NOT have been called.
        mock_celery.control.revoke.assert_not_called()
        mock_notify.assert_not_called()
        # Status must still be QUEUED.
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(VideoJobDB).where(VideoJobDB.id == "abort-003"))
            job = res.scalar_one()
            assert job.status == SystemJobStatus.QUEUED

    @pytest.mark.asyncio
    async def test_abort_missing_job_returns_false(self, test_db):
        """Aborting a non-existent job_id returns False; no Celery revoke."""
        with patch("src.api.utils.celery.celery_app") as mock_celery, \
             patch("src.api.routes.ws.notify_job_update_sync") as mock_notify:
            mock_celery.control.revoke = MagicMock()
            mock_notify.return_value = None

            async with AsyncSessionLocal() as db:
                user_id = await _create_test_user(db, suffix="abort-ghost")
                service = VideoJobService(db)
                ok = await service.abort_job("ghost-abort", user_id, UserRole.USER)

        assert ok is False
        mock_celery.control.revoke.assert_not_called()
        mock_notify.assert_not_called()
