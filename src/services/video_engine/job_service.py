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

    async def get_user_jobs(self, user_id: str | None = None, limit: int = 10, offset: int = 0, include_all: bool = False) -> tuple[list[dict], int]:
        """
        Get jobs for a user or all jobs if include_all=True (admin). 
        Aggregates results from both standard Video engine and Nexus high-fidelity engine.
        Returns (unified_jobs, total_count).
        """
        from sqlalchemy import func
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
            unified_list.append({
                "id": v.id,
                "title": v.title,
                "status": v.status,
                "progress": v.progress,
                "source_url": v.source_url,
                "output_path": v.output_path,
                "job_metadata": v.job_metadata,
                "created_at": v.created_at,
                "engine": "video_transform"
            })
            
        for n in nexus_jobs:
            unified_list.append({
                "id": n.id,
                "title": f"Nexus Production: {n.niche}",
                "status": n.status,
                "progress": n.progress,
                "source_url": "Cinema Mode / Studio",
                "output_path": n.output_path,
                "job_metadata": n.job_metadata,
                "created_at": n.created_at,
                "engine": "nexus_compose"
            })
            
        # 4. Sort and Paginate
        unified_list.sort(key=lambda x: x["created_at"], reverse=True)
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
                "status": v.status,
                "progress": v.progress,
                "source_url": v.source_url,
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
                "status": n.status,
                "progress": n.progress,
                "source_url": "Cinema Mode / Studio",
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
