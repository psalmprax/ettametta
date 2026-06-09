"""
Scheduling routes — schedule posts, list scheduled, cancel scheduled, and
get AI-suggested optimal posting times.

Extracted from the original monolithic publish.py.
"""

import uuid
import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.database import get_db
from src.api.utils.models import ScheduledPostDB
from src.api.utils.api_responses import success_response
from src.api.utils.subscription import credits_required
from src.shared.enums import ContentPublishStatus
from src.services.payment.credit_service import credit_service
from src.services.optimization.service import base_optimization_service
from src.services.optimization.scheduler import smart_scheduler

from .common import PublishRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/scheduled")
async def get_scheduled_posts(
    current_user: UserDB = Depends(get_current_user), db=Depends(get_db)
):
    """Get scheduled posts waiting for publish."""
    try:
        stmt = select(ScheduledPostDB).where(
            ScheduledPostDB.user_id == current_user.id,
            ScheduledPostDB.scheduled_time > datetime.datetime.now(datetime.timezone.utc),
        )
        stmt = stmt.order_by(ScheduledPostDB.scheduled_time.asc())
        result = await db.execute(stmt)
        scheduled = result.scalars().all()
        return [
            {
                "id": p.id,
                "video_path": p.video_path,
                "platform": p.platform,
                "scheduled_time": p.scheduled_time,
                "status": p.status.value if hasattr(p.status, "value") else p.status,
                "parallel_allowed": p.parallel_allowed,
                "engagement_prediction": p.engagement_prediction,
                "optimal_rank": p.optimal_rank,
                "user_timezone": p.user_timezone,
                "error_message": p.error_message,
            }
            for p in scheduled
        ]
    finally:
        pass


@router.post("/schedule")
async def schedule_post(
    request: PublishRequest,
    scheduled_time: datetime.datetime,
    parallel_allowed: bool = False,
    user_timezone: str = "UTC",
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    credits_cost: int = Depends(credits_required("social_publish")),
):
    """
    Schedules a video for later publishing.
    """
    try:
        prediction = smart_scheduler.predict_engagement(
            str(current_user.id), scheduled_time
        )
        await credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action="social_publish",
            db=db,
            description=f"Scheduled post for {request.platform}",
        )

        content_id = str(uuid.uuid4())
        metadata = await base_optimization_service.generate_viral_package(
            content_id, request.niche, request.platform
        )

        new_schedule = ScheduledPostDB(
            video_path=request.video_path,
            platform=request.platform,
            scheduled_time=scheduled_time,
            status=ContentPublishStatus.PENDING,
            parallel_allowed=parallel_allowed,
            user_timezone=user_timezone,
            engagement_prediction=prediction,
            metadata_json=metadata.dict() if hasattr(metadata, "dict") else metadata,
            account_id=request.account_id,
            user_id=current_user.id,
        )
        db.add(new_schedule)
        await db.commit()
        return success_response(
            data={"status": "success", "message": f"Scheduled for {scheduled_time}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Schedule post failed: {e}")
        raise HTTPException(status_code=503, detail="Publishing service unavailable")


@router.delete("/schedule/{schedule_id}")
async def cancel_scheduled_post(
    schedule_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """Cancel a scheduled post before it publishes."""
    try:
        stmt = select(ScheduledPostDB).where(
            ScheduledPostDB.id == schedule_id,
            ScheduledPostDB.user_id == current_user.id,
        )
        result = await db.execute(stmt)
        scheduled = result.scalar_one_or_none()

        if not scheduled:
            raise HTTPException(status_code=404, detail="Scheduled post not found")

        await db.delete(scheduled)
        await db.commit()

        return success_response(
            data={"status": "cancelled", "message": "Scheduled post cancelled"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Cancel scheduled post failed: {e}")
        raise HTTPException(status_code=503, detail="Failed to cancel scheduled post")


@router.get("/schedule/suggested-times")
async def get_suggested_times(
    count: int = Query(3, ge=1, le=10),
    current_user: UserDB = Depends(get_current_user),
):
    """Returns AI-suggested optimal posting windows."""
    try:
        suggestions = smart_scheduler.calculate_n_optimal_windows(
            str(current_user.id), count
        )
        return {"suggestions": suggestions}
    except Exception as e:
        logger.exception(f"Error getting suggested times: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to calculate optimal windows"
        )
