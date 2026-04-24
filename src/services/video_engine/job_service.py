"""
Video Job Service
Moves DB operations from routes to service layer (Clean Architecture)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from src.api.utils.models import VideoJobDB
from src.shared.enums import SystemJobStatus

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
        prompt: str,
        niche: str = "general",
        style: str | None = None,
        status: str = SystemJobStatus.QUEUED,
    ) -> VideoJobDB:
        """Create a new video job"""
        job = VideoJobDB(
            title=title,
            status=status,
            source_url=prompt,
            user_id=user_id,
            metadata={
                "engine": engine,
                "style": style,
                "niche": niche
            }
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_user_jobs(self, user_id: str | None = None, limit: int = 10, offset: int = 0, include_all: bool = False) -> tuple[list[VideoJobDB], int]:
        """Get jobs for a user or all jobs if include_all=True (admin). Returns (jobs, total_count)."""
        from sqlalchemy import func
        
        base_stmt = select(VideoJobDB)
        
        if user_id and not include_all:
            base_stmt = base_stmt.where(VideoJobDB.user_id == user_id)
        
        # Get total count
        count_stmt = select(func.count(VideoJobDB.id)).select_from(base_stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total_count = total_result.scalar() or 0
        
        # Get paginated results
        stmt = base_stmt.order_by(VideoJobDB.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        jobs = list(result.scalars().all())
        
        return jobs, total_count

    async def get_job_by_id(self, job_id: str, user_id: str) -> VideoJobDB | None:
        """Get a specific job"""
        stmt = select(VideoJobDB).where(
            VideoJobDB.id == job_id, VideoJobDB.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

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
                logger.error(f"[JobService] Failed to commit status update: {e}")
                return False
        return False

    async def delete_job(self, job_id: str, user_id: str) -> bool:
        """Delete a job"""
        job = await self.get_job_by_id(job_id, user_id)
        if job:
            await self.db.delete(job)
            await self.db.commit()
            return True
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
