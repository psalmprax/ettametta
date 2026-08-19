"""
Video Job Service
Moves DB operations from routes to service layer (Clean Architecture)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from src.api.utils.models import VideoJobDB
from src.shared.enums import SystemJobStatus
from src.api.utils.user_models import UserRole

logger = logging.getLogger(__name__)


class VideoJobService:
    """Service layer for video job operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_job(
        self,
        user_id: str,
        title: str,
        engine: str,
        prompt: str = "",
        niche: str = "general",
        style: str | None = None,
        status: str = SystemJobStatus.QUEUED,
        job_id: str | None = None,
        progress: int = 0,
        source_uri: str | None = None,
        extra_metadata: dict | None = None,
        auto_commit: bool = True,
    ) -> VideoJobDB:
        """Create a new video job

        Args:
            user_id: Owner of the job
            title: Display title
            engine: Engine name (e.g. video_transform)
            prompt: Original prompt text (used as source_uri if no explicit source_uri given)
            niche: Content niche
            style: Visual style
            status: Initial job status
            job_id: Explicit job ID (e.g. Celery task ID). Auto-generated if None.
            progress: Initial progress percentage
            source_uri: Source URL. Falls back to prompt if not provided.
            extra_metadata: Additional metadata fields merged into base engine/style/niche dict
            auto_commit: If True (default), commits the transaction. If False, flushes
                to the session so the caller can commit as part of a larger atomic
                transaction (matches CreditService.consume_credits convention).
        """
        metadata = {
            "engine": engine,
            "style": style,
            "niche": niche,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        job = VideoJobDB(
            id=job_id,
            title=title,
            status=status,
            progress=progress,
            source_uri=source_uri or prompt,
            user_id=user_id,
            job_metadata=metadata,
        )
        self.db.add(job)
        if auto_commit:
            await self.db.commit()
        else:
            await self.db.flush()
        await self.db.refresh(job)
        return job

    async def get_user_jobs(self, user_id: str | None = None, limit: int = 10, offset: int = 0, include_all: bool = False) -> tuple[list[dict], int]:
        """
        Get jobs for a user or all jobs if include_all=True (admin).
        Aggregates results from both standard Video engine and Nexus high-fidelity engine.
        Returns (unified_jobs, total_count).
        """
        from src.api.utils.models import NexusJobDB

        # 1. Fetch Video Jobs
        video_stmt = select(VideoJobDB)
        if user_id and not include_all:
            video_stmt = video_stmt.where(VideoJobDB.user_id == user_id)

        video_result = await self.db.execute(video_stmt.order_by(VideoJobDB.created_at.desc()))
        video_jobs = list(video_result.scalars().all())

        # 2. Fetch Nexus Jobs
        nexus_stmt = select(NexusJobDB)
        if user_id and not include_all:
            nexus_stmt = nexus_stmt.where(NexusJobDB.user_id == user_id)

        nexus_result = await self.db.execute(nexus_stmt.order_by(NexusJobDB.created_at.desc()))
        nexus_jobs = list(nexus_result.scalars().all())

        # 3. Unify and Normalize
        unified_list = []

        for v in video_jobs:
            try:
                # Defensive check for status and metadata
                try:
                    status_val = v.status.value if hasattr(v.status, 'value') else v.status
                except Exception:
                    status_val = str(v.status) if v.status else "UNKNOWN"

                unified_list.append({
                    "id": v.id,
                    "title": v.title or f"Video Job {v.id[:8] if v.id else '???'}",
                    "status": status_val,
                    "progress": v.progress or 0,
                    "source_uri": v.source_uri,
                    "output_path": v.output_path,
                    "job_metadata": v.job_metadata or {},
                    "created_at": v.created_at,
                    "engine": "video_transform"
                })
            except Exception as e:
                logger.exception(f"[JobService] Error normalizing video job {v.id if hasattr(v, 'id') else 'unknown'}: {e}")
                continue

        for n in nexus_jobs:
            try:
                try:
                    status_val = n.status.value if hasattr(n.status, 'value') else n.status
                except Exception:
                    status_val = str(n.status) if n.status else "UNKNOWN"

                unified_list.append({
                    "id": n.id,
                    "title": f"Nexus Production: {n.niche}" if hasattr(n, 'niche') else f"Nexus Job {n.id[:8] if n.id else '???'}",
                    "status": status_val,
                    "progress": n.progress or 0,
                    "source_uri": "Cinema Mode / Studio",
                    "output_path": n.output_path,
                    "job_metadata": n.job_metadata or {},
                    "created_at": n.created_at,
                    "engine": "nexus_compose"
                })
            except Exception as e:
                logger.exception(f"[JobService] Error normalizing nexus job {n.id if hasattr(n, 'id') else 'unknown'}: {e}")
                continue

        # 4. Sort and Paginate
        # Defensive sorting: ensure created_at is not None
        from datetime import datetime
        def safe_sort_key(x):
            dt = x.get("created_at")
            if not dt:
                return datetime.min
            # Standard: Ensure naive for comparison with datetime.min
            if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt

        unified_list.sort(key=safe_sort_key, reverse=True)
        total_count = len(unified_list)
        paginated_jobs = unified_list[offset:offset+limit]

        return paginated_jobs, total_count

    async def get_job_by_id(self, job_id: str, user_id: str) -> dict | None:
        """Get a specific job from either Video or Nexus tables"""
        from src.api.utils.models import NexusJobDB

        # Check Video jobs first
        stmt = select(VideoJobDB).where(
            VideoJobDB.id == job_id, VideoJobDB.user_id == user_id
        )
        result = await self.db.execute(stmt)
        v = result.scalar_one_or_none()
        if v:
            return {
                "id": v.id,
                "title": v.title,
                "status": v.status.value if hasattr(v.status, 'value') else v.status,
                "progress": v.progress,
                "source_uri": v.source_uri,
                "output_path": v.output_path,
                "job_metadata": v.job_metadata,
                "created_at": v.created_at,
                "updated_at": v.updated_at,
                "engine": "video_transform"
            }

        # Check Nexus jobs
        stmt_n = select(NexusJobDB).where(
            NexusJobDB.id == job_id, NexusJobDB.user_id == user_id
        )
        result_n = await self.db.execute(stmt_n)
        n = result_n.scalar_one_or_none()
        if n:
            return {
                "id": n.id,
                "title": f"Nexus Production: {n.niche}",
                "status": n.status.value if hasattr(n.status, 'value') else n.status,
                "progress": n.progress,
                "source_uri": "Cinema Mode / Studio",
                "output_path": n.output_path,
                "job_metadata": n.job_metadata,
                "created_at": n.created_at,
                "updated_at": n.updated_at,
                "engine": "nexus_compose"
            }

        return None

    async def update_job_status(self, job_id: str, status: SystemJobStatus | str) -> bool:
        """Update job status with strict enum enforcement"""
        if isinstance(status, str):
            try:
                status = SystemJobStatus[status.upper()]
            except KeyError:
                logger.warning(f"[JobService] Invalid status string: {status}, ignoring update.")
                return False

        stmt = select(VideoJobDB).where(VideoJobDB.id == job_id)
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        if job:
            job.status = status
            try:
                await self.db.commit()
                return True
            except Exception as e:
                await self.db.rollback()
                logger.exception(f"[JobService] Failed to commit status update: {e}")
                return False
        return False

    async def delete_job(self, job_id: str, user_id: str) -> bool:
        """Delete a job from either Video or Nexus tables"""
        from src.api.utils.models import NexusJobDB

        # Check Video jobs
        stmt = select(VideoJobDB).where(
            VideoJobDB.id == job_id, VideoJobDB.user_id == user_id
        )
        result = await self.db.execute(stmt)
        v = result.scalar_one_or_none()
        if v:
            await self.db.delete(v)
            await self.db.commit()
            return True

        # Check Nexus jobs
        stmt_n = select(NexusJobDB).where(
            NexusJobDB.id == job_id, NexusJobDB.user_id == user_id
        )
        result_n = await self.db.execute(stmt_n)
        n = result_n.scalar_one_or_none()
        if n:
            await self.db.delete(n)
            await self.db.commit()
            return True

        return False

    async def abort_job(self, job_id: str, user_id: str, user_role: UserRole) -> bool:
        """
        Abort a running video job.

        Args:
            job_id: ID of the job to abort
            user_id: ID of the user requesting abort
            user_role: Role of the user (for admin check)

        Returns:
            True if job was aborted, False otherwise
        """
        from src.api.utils.celery import celery_app
        from src.api.routes.ws import notify_job_update_sync
        from src.api.utils.models import NexusJobDB

        try:
            # Try Video jobs first
            stmt = select(VideoJobDB).where(VideoJobDB.id == job_id)
            result = await self.db.execute(stmt)
            job = result.scalar_one_or_none()

            # Try Nexus jobs if not found
            if not job:
                stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
                result = await self.db.execute(stmt)
                job = result.scalar_one_or_none()

            if not job:
                logger.warning(f"[JobService] Job {job_id} not found for abort")
                return False

            # Check authorization
            if user_role != UserRole.ADMIN and job.user_id != user_id:
                logger.warning(f"[JobService] User {user_id} not authorized to abort job {job_id}")
                return False

            # Revoke Celery task
            celery_app.control.revoke(job_id, terminate=True)

            # Update job status
            job.status = SystemJobStatus.ABORTED
            await self.db.commit()

            # Notify WebSocket clients
            notify_job_update_sync(
                {
                    "id": job_id,
                    "status": SystemJobStatus.ABORTED.value,
                    "progress": job.progress,
                    "output_path": job.output_path,
                }
            )

            logger.info(f"[JobService] Job {job_id} aborted successfully")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"[JobService] Failed to abort job {job_id}: {e}")
            return False

    async def count_user_jobs(self, user_id: str) -> int:
        """Count total jobs for user"""
        from sqlalchemy import func

        stmt = select(func.count(VideoJobDB.id)).where(VideoJobDB.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0


from fastapi import Depends
from src.api.utils.database import get_db

# Dependency injection helper
def get_video_job_service(db=Depends(get_db)) -> VideoJobService:
    """Factory for VideoJobService"""
    return VideoJobService(db)
