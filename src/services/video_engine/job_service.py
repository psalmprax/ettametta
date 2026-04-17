"""
Video Job Service
Moves DB operations from routes to service layer (Clean Architecture)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from src.api.utils.models import VideoJobDB

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
        status: str = "pending",
    ) -> VideoJobDB:
        """Create a new video job"""
        job = VideoJobDB(
            title=title,
            status=status,
            input_url=prompt,
            niche=niche,
            user_id=user_id,
            engine=engine,
            style=style,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_user_jobs(self, user_id: str, limit: int = 10) -> list[VideoJobDB]:
        """Get jobs for a user"""
        stmt = (
            select(VideoJobDB)
            .where(VideoJobDB.user_id == user_id)
            .order_by(VideoJobDB.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_job_by_id(self, job_id: str, user_id: str) -> VideoJobDB | None:
        """Get a specific job"""
        stmt = select(VideoJobDB).where(
            VideoJobDB.id == job_id, VideoJobDB.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_job_status(self, job_id: str, status: str) -> bool:
        """Update job status"""
        stmt = select(VideoJobDB).where(VideoJobDB.id == job_id)
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        if job:
            job.status = status
            await self.db.commit()
            return True
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


# Dependency injection helper
def get_video_job_service(db: AsyncSession) -> VideoJobService:
    """Factory for VideoJobService"""
    return VideoJobService(db)
