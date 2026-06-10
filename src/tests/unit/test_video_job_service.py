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

import uuid
import pytest
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
