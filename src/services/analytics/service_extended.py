"""
Extended Analytics Service
Consolidates all analytics-related database operations from routes into service layer.
Follows Clean Architecture principles for better testability and separation of concerns.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.utils.models import (
    PublishedContentDB,
    VideoJobDB,
    NicheTrendDB,
    ABTestDB,
)
from src.shared.enums import SystemJobStatus, ContentPublishStatus
from src.api.utils.user_models import UserRole
import logging
import datetime

logger = logging.getLogger(__name__)


class AnalyticsServiceExtended:
    """
    Service layer for analytics operations.
    Consolidates all database query logic from analytics routes.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # POST LISTING
    # ============================================================

    async def list_published_posts(
        self,
        user_id: str,
        user_role: UserRole,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[PublishedContentDB], int]:
        """
        List all published posts with pagination.
        
        Args:
            user_id: ID of the user
            user_role: Role of the user (for admin access)
            page: Page number
            size: Page size
            
        Returns:
            Tuple of (posts list, total count)
        """
        # Base query
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.status == ContentPublishStatus.PUBLISHED
        )
        
        # User isolation (unless admin)
        if user_role != UserRole.ADMIN:
            stmt = stmt.where(PublishedContentDB.user_id == user_id)
        
        # Order by published date
        stmt = stmt.order_by(PublishedContentDB.published_at.desc())
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total_items = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size)
        
        result = await self.db.execute(stmt)
        posts = result.scalars().all()
        
        return posts, total_items

    # ============================================================
    # REPORT SUMMARY
    # ============================================================

    async def get_report_summary(
        self,
        user_id: str,
        user_role: UserRole,
    ) -> Dict[str, Any]:
        """
        Get summary statistics for all posts.
        
        Args:
            user_id: ID of the user
            user_role: Role of the user
            
        Returns:
            Dictionary with summary statistics
        """
        # Base query for posts
        post_stmt = select(PublishedContentDB).where(
            PublishedContentDB.status == ContentPublishStatus.PUBLISHED
        )
        
        # User isolation
        if user_role != UserRole.ADMIN:
            post_stmt = post_stmt.where(PublishedContentDB.user_id == user_id)
        
        # Count total posts
        count_stmt = select(func.count()).select_from(post_stmt.subquery())
        result = await self.db.execute(count_stmt)
        total_posts = result.scalar() or 0
        
        # Get metrics
        metrics_stmt = select(
            func.sum(PublishedContentDB.view_count).label("total_views"),
            func.sum(PublishedContentDB.like_count).label("total_likes"),
            func.sum(PublishedContentDB.share_count).label("total_shares"),
            func.avg(PublishedContentDB.retention_rate).label("avg_retention"),
        )
        
        if user_role != UserRole.ADMIN:
            metrics_stmt = metrics_stmt.where(PublishedContentDB.user_id == user_id)
        
        result = await self.db.execute(metrics_stmt)
        row = result.fetchone()
        
        total_views = row.total_views or 0
        total_likes = row.total_likes or 0
        total_shares = row.total_shares or 0
        avg_retention = row.avg_retention or 0.0
        
        return {
            "total_posts": total_posts,
            "total_views": int(total_views),
            "total_likes": int(total_likes),
            "total_shares": int(total_shares),
            "avg_views": int(total_views / total_posts) if total_posts > 0 else 0,
            "avg_likes": int(total_likes / total_posts) if total_posts > 0 else 0,
            "avg_retention": float(avg_retention),
        }

    # ============================================================
    # STATS SUMMARY (DASHBOARD)
    # ============================================================

    async def get_stats_summary(
        self,
        user_id: str,
        user_role: UserRole,
    ) -> Dict[str, Any]:
        """
        Get dashboard summary statistics.
        
        Args:
            user_id: ID of the user
            user_role: Role of the user
            
        Returns:
            Dictionary with dashboard statistics
        """
        # Count published posts
        post_stmt = select(PublishedContentDB).where(
            PublishedContentDB.status == ContentPublishStatus.PUBLISHED
        )
        
        if user_role != UserRole.ADMIN:
            post_stmt = post_stmt.where(PublishedContentDB.user_id == user_id)
        
        result = await self.db.execute(
            select(func.count()).select_from(post_stmt.subquery())
        )
        total_posts = result.scalar() or 0
        
        # Count video jobs
        job_stmt = select(VideoJobDB)
        
        if user_role != UserRole.ADMIN:
            job_stmt = job_stmt.where(VideoJobDB.user_id == user_id)
        
        result = await self.db.execute(
            select(func.count()).select_from(job_stmt.subquery())
        )
        total_jobs = result.scalar() or 0
        
        # Calculate success rate
        success_rate = (total_posts / total_jobs * 100) if total_jobs > 0 else 0
        
        # Get metrics from published content
        metrics_stmt = select(
            func.sum(PublishedContentDB.view_count).label("total_views"),
            func.sum(PublishedContentDB.like_count).label("total_likes"),
            func.sum(PublishedContentDB.share_count).label("total_shares"),
            func.sum(PublishedContentDB.comment_count).label("total_comments"),
            func.avg(PublishedContentDB.retention_rate).label("avg_retention"),
        )
        
        if user_role != UserRole.ADMIN:
            metrics_stmt = metrics_stmt.where(PublishedContentDB.user_id == user_id)
        
        result = await self.db.execute(metrics_stmt)
        row = result.fetchone()
        
        total_views = row.total_views or 0
        total_likes = row.total_likes or 0
        total_shares = row.total_shares or 0
        total_comments = row.total_comments or 0
        avg_retention = row.avg_retention or 0.0
        
        # Calculate engagement score
        engagement_score = 0.0
        if total_views > 0:
            engagement_score = ((total_likes + total_comments + total_shares) / total_views) * 100
        
        # Count active trends
        result = await self.db.execute(
            select(func.count(NicheTrendDB.niche.distinct()))
        )
        active_trends_count = result.scalar() or 0
        
        # Calculate velocity (recent trends)
        yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
        result = await self.db.execute(
            select(func.count(NicheTrendDB.id)).where(
                NicheTrendDB.last_updated >= yesterday
            )
        )
        recent_count = result.scalar() or 0
        
        # Count pending jobs
        result = await self.db.execute(
            select(func.count(VideoJobDB.id)).where(
                VideoJobDB.status.in_([
                    SystemJobStatus.QUEUED,
                    SystemJobStatus.PROCESSING,
                    SystemJobStatus.RENDERING,
                ])
            )
        )
        pending_jobs = result.scalar() or 0
        
        # Calculate engine load
        MAX_CAPACITY = 10
        engine_load = int((pending_jobs / MAX_CAPACITY) * 100) if MAX_CAPACITY > 0 else 0
        
        # Format reach
        if total_views >= 1000000:
            reach_formatted = f"{total_views / 1000000:.1f}M"
        elif total_views >= 1000:
            reach_formatted = f"{total_views / 1000:.1f}K"
        else:
            reach_formatted = str(total_views)
        
        return {
            "active_trends": active_trends_count,
            "videos_processed": total_jobs,
            "total_reach": reach_formatted,
            "success_rate": f"{success_rate:.1f}%",
            "recent_discovery_count": recent_count,
            "engine_load": f"{engine_load}%",
            "velocity": "High" if recent_count > 5 else "Nominal",
            "total_views": total_views,
            "total_likes": total_likes,
            "total_shares": total_shares,
            "total_comments": total_comments,
            "avg_retention": round(avg_retention, 2),
            "engagement_score": round(engagement_score, 2),
            "pending_jobs": pending_jobs,
        }

    # ============================================================
    # AB TEST RESULTS
    # ============================================================

    async def get_ab_test_results(
        self,
        content_id: str,
    ) -> Dict[str, Any]:
        """
        Get A/B test results for specific content.
        
        Args:
            content_id: ID of the content
            
        Returns:
            Dictionary with A/B test results
        """
        stmt = select(ABTestDB).where(ABTestDB.content_id == content_id)
        result = await self.db.execute(stmt)
        test = result.scalar_one_or_none()
        
        if not test:
            raise ValueError("A/B test not found for this content")
        
        winner = "A" if test.variant_a_view_count > test.variant_b_view_count else "B"
        
        return {
            "test_id": test.id,
            "variant_a_title": test.variant_a_title,
            "variant_b_title": test.variant_b_title,
            "variant_a_view_count": test.variant_a_view_count,
            "variant_b_view_count": test.variant_b_view_count,
            "winner": winner,
            "created_at": test.created_at,
        }

    # ============================================================
    # EXPORT
    # ============================================================

    async def export_posts(
        self,
        user_id: str,
        user_role: UserRole,
    ) -> List[Tuple[str, str, str, int, int, int, Optional[datetime.datetime]]]:
        """
        Export all published posts for CSV download.
        
        Args:
            user_id: ID of the user
            user_role: Role of the user
            
        Returns:
            List of tuples with post data
        """
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.status == ContentPublishStatus.PUBLISHED
        )
        
        if user_role != UserRole.ADMIN:
            stmt = stmt.where(PublishedContentDB.user_id == user_id)
        
        stmt = stmt.order_by(PublishedContentDB.published_at.desc())
        
        result = await self.db.execute(stmt)
        posts = result.scalars().all()
        
        return [
            (
                post.id,
                post.platform,
                post.title,
                post.view_count,
                post.like_count,
                post.share_count,
                post.published_at,
            )
            for post in posts
        ]

    # ============================================================
    # STORAGE STATS
    # ============================================================

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage usage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        from src.services.storage.manager import storage_manager
        from src.api.config import settings
        
        current_size = storage_manager.get_output_dir_size()
        threshold_bytes = storage_manager.threshold_bytes
        
        return {
            "current_size_gb": round(current_size / (1024**3), 2),
            "threshold_gb": storage_manager.threshold_gb,
            "usage_percent": round((current_size / threshold_bytes) * 100, 1)
            if threshold_bytes > 0
            else 0,
            "status": "Healthy"
            if current_size < threshold_bytes * 0.9
            else "Warning"
            if current_size < threshold_bytes
            else "Critical",
            "provider": settings.STORAGE_PROVIDER,
        }

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def verify_content_access(
        self,
        post_id: str,
        user_id: str,
        user_role: UserRole,
    ) -> PublishedContentDB:
        """
        Verify that user has access to specific content.
        
        Args:
            post_id: ID of the post
            user_id: ID of the user
            user_role: Role of the user
            
        Returns:
            PublishedContentDB object
            
        Raises:
            HTTPException: If content not found or access denied
        """
        from fastapi import HTTPException
        
        stmt = select(PublishedContentDB).where(PublishedContentDB.id == post_id)
        result = await self.db.execute(stmt)
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        if content.user_id != user_id and user_role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return content
