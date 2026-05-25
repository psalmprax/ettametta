"""
Analytics routes for published content — comments, metrics sync, job listing,
and publish history.

Extracted from the original monolithic publish.py.
"""

import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB, UserRole
from src.api.utils.database import get_db
from src.api.utils.models import PublishedContentDB, ABTestDB
from src.api.utils.api_responses import success_response
from src.services.optimization.youtube_publisher import base_youtube_service
from src.services.optimization.tiktok_publisher import base_tiktok_service

from .common import extract_platform_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/jobs")
async def get_publish_jobs(
    current_user: UserDB = Depends(get_current_user), db=Depends(get_db)
):
    """
    Returns active publish jobs for the current user.
    Includes items that are in-progress, pending_auth, or failed —
    anything not yet fully published.
    """
    try:
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.user_id == current_user.id,
        )
        stmt = stmt.order_by(PublishedContentDB.published_at.desc())
        result = await db.execute(stmt)
        jobs = result.scalars().all()
        return success_response(
            data=[
                {
                    "id": j.id,
                    "title": j.title,
                    "platform": j.platform,
                    "status": j.status.value if hasattr(j.status, "value") else j.status,
                    "progress": 0,
                    "created_at": j.published_at,
                    "niche": j.niche,
                }
                for j in jobs
            ]
        )
    except Exception as e:
        logger.exception(f"Publish jobs failed: {e}")
        return success_response(data=[])


@router.get("/history")
async def get_publish_history(
    current_user: UserDB = Depends(get_current_user), db=Depends(get_db)
):
    try:
        stmt = select(PublishedContentDB)
        if current_user.role != UserRole.ADMIN:
            stmt = stmt.where(PublishedContentDB.user_id == current_user.id)

        stmt = stmt.order_by(PublishedContentDB.published_at.desc())
        result = await db.execute(stmt)
        history = result.scalars().all()
        return success_response(data=history)
    except Exception as e:
        logger.exception(f"Publish history failed: {e}")
        return success_response(data=[])


@router.get("/comments/{content_id}")
async def get_content_comments(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 10,
):
    """
    Fetch comments for a published post.
    """
    try:
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.id == content_id,
            PublishedContentDB.user_id == current_user.id,
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(status_code=404, detail="Post not found")

        if not content.source_uri:
            raise HTTPException(
                status_code=400, detail="Post has no URL (not published yet)"
            )

        platform_id, platform_key = extract_platform_id(content.source_uri)

        if not platform_id:
            raise HTTPException(
                status_code=400, detail="Could not extract platform ID from URL"
            )

        comments = []
        if platform_key == "tiktok":
            comments = await base_tiktok_service.get_comments(
                platform_id, user_id=current_user.id, limit=limit
            )
        elif platform_key == "youtube":
            comments = []

        return success_response(
            data={
                "platform": platform_key,
                "video_id": platform_id,
                "comments": comments,
                "total_count": len(comments),
            }
        )

    finally:
        pass


@router.post("/sync/{content_id}")
async def sync_content_metrics(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Syncs live metrics from the social platform to the database for a specific post.
    """
    try:
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.id == content_id,
            PublishedContentDB.user_id == current_user.id,
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(status_code=404, detail="Post not found")

        if not content.source_uri:
            raise HTTPException(
                status_code=400, detail="Post has no URL (not published yet)"
            )

        platform_id, platform_key = extract_platform_id(content.source_uri)

        if not platform_id:
            raise HTTPException(
                status_code=400, detail="Could not extract platform ID from URL"
            )

        metrics = {"views": 0, "likes": 0, "comments": 0, "shares": 0}

        if platform_key == "youtube":
            metrics = await base_youtube_service.get_metrics(
                platform_id, user_id=current_user.id
            )
        elif platform_key == "tiktok":
            metrics = await base_tiktok_service.get_metrics(
                platform_id, user_id=current_user.id
            )

        old_views = content.view_count or 0
        content.view_count = metrics.get("views", 0)
        content.like_count = metrics.get("likes", 0)
        content.comment_count = metrics.get("comments", 0)
        content.share_count = metrics.get("shares", 0)

        # Record A/B test events if this post is part of an A/B test
        stmt_ab = select(ABTestDB).where(ABTestDB.content_id == str(content.id))
        result_ab = await db.execute(stmt_ab)
        ab_test = result_ab.scalar_one_or_none()
        if ab_test and not ab_test.completed_at:
            new_views = max(0, (content.view_count or 0) - old_views)
            if new_views > 0:
                variant_a_views = new_views // 2
                variant_b_views = new_views - variant_a_views

                ab_test.variant_a_view_count = (
                    ab_test.variant_a_view_count or 0
                ) + variant_a_views
                ab_test.variant_b_view_count = (
                    ab_test.variant_b_view_count or 0
                ) + variant_b_views

                engagement_score = (
                    (content.like_count or 0)
                    + (content.comment_count or 0)
                    + (content.share_count or 0)
                )
                if engagement_score > 0:
                    conversions_a = engagement_score // 2
                    conversions_b = engagement_score - conversions_a
                    ab_test.variant_a_conversion_count = (
                        ab_test.variant_a_conversion_count or 0
                    ) + conversions_a
                    ab_test.variant_b_conversion_count = (
                        ab_test.variant_b_conversion_count or 0
                    ) + conversions_b

        await db.commit()
        return success_response(data={"status": "success", "metrics": metrics})

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Metrics sync failed: {e}")
        raise HTTPException(status_code=503, detail="Publishing service unavailable")
