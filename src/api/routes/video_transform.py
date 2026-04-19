from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from api.utils.database import get_db
from shared.enums import SystemJobStatus
from api.utils.models import VideoJobDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from api.utils.subscription import check_daily_limit, credits_required
from services.video_engine.tasks import download_and_process_task
from services.payment.credit_service import credit_service
from api.utils.limiter import limiter
from api.utils.audit_service import audit_service
from api.utils.api_responses import success_response
import logging

router = APIRouter(prefix="/video", tags=["Video Transformation"])
logger = logging.getLogger(__name__)


class TransformationRequest(BaseModel):
    source_url: str
    niche: str = "Motivation"
    platform: str = "YouTube Shorts"
    style: str | None = "Default"
    quality_tier: str | None = "standard"
    generate_thumbnail: bool | None = False
    sound_design: bool | None = False
    motion_graphics: bool | None = False
    analysis_data: dict | None = None


@router.post("/transform")
@limiter.limit("10/minute")
async def start_transformation(
    request: Request,
    body: TransformationRequest,
    current_user: UserDB = Depends(get_current_user),
    credits_cost: int = Depends(credits_required("video_transformation")),
    db: AsyncSession = Depends(get_db),
):
    """
    Hardened transformation endpoint with atomicity between task dispatch and credit consumption.
    """
    try:
        await check_daily_limit(current_user, db)

        # 1. Dispatch Task first (Task Validation)
        try:
            task = download_and_process_task.delay(
                source_url=body.source_url,
                niche=body.niche,
                platform=body.platform,
                style=body.style,
                quality_tier=body.quality_tier,
                sound_design=body.sound_design or False,
                motion_graphics=body.motion_graphics or False,
                analysis_data=body.analysis_data,
            )
            if not task.id:
                raise Exception("Celery task ID generation failed")

        except Exception as task_err:
            logger.error(f"Celery task dispatch failed: {task_err}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Task queue unavailable. Please try again later.",
            )

        # 2. Consume Credits (if task dispatched)
        success, msg = await credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action="video_transformation",
            db=db,
            reference_id=task.id,  # Link directly to task ID
        )

        if not success:
            # ROLLBACK: Revoke the task if credit consumption fails
            from api.utils.celery import celery_app

            celery_app.control.revoke(task.id, terminate=True)
            logger.warning(f"Task {task.id} revoked due to credit failure: {msg}")
            raise HTTPException(
                status_code=402, detail=f"Credit consumption failed: {msg}"
            )

        # 3. Create Job Entry
        new_job = VideoJobDB(
            id=task.id,
            title=f"Viral Transform - {body.niche}",
            status=SystemJobStatus.QUEUED,
            progress=0,
            source_url=body.source_url,
            user_id=current_user.id,
        )
        db.add(new_job)
        await db.commit()

        await audit_service.log(
            action="VIDEO_TRANSFORM_START",
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=task.id,
            details={"source_url": body.source_url, "cost": credits_cost},
            db=db,
        )

        return success_response(data={"message": "Transformation started", "task_id": task.id})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


class TestDriveRequest(BaseModel):
    niche: str
    style: str | None = "Default"


@router.post("/test-drive")
async def test_drive(
    request: TestDriveRequest,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Identifies the top viral candidate and triggers a preview transformation.
    """
    from services.discovery.service import base_discovery_service
    from api.utils.models import ContentCandidateDB

    try:
        await check_daily_limit(current_user, db)

        stmt = (
            select(ContentCandidateDB)
            .where(
                ContentCandidateDB.niche == request.niche,
                ContentCandidateDB.thumbnail_url.isnot(None),
            )
            .order_by(ContentCandidateDB.viral_score.desc())
        )

        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise HTTPException(status_code=404, detail="No viral candidates found")

        task = download_and_process_task.delay(
            source_url=candidate.source_url,
            niche=request.niche,
            platform="YouTube Shorts",
            preview_only=True,
            style=request.style,
        )

        new_job = VideoJobDB(
            id=task.id,
            title=f"Test Drive - {request.niche}",
            status=SystemJobStatus.QUEUED,
            source_url=candidate.source_url,
            user_id=current_user.id,
        )
        db.add(new_job)
        await db.commit()

        return success_response(data={"message": "Test Drive started", "task_id": task.id})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test drive failed: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


@router.post("/auto-insert-links")
async def auto_insert_affiliate_links(
    video_path: str,
    niche: str,
    script_content: str = "",
    current_user: UserDB = Depends(get_current_user),
):
    """
    Automatically inserts affiliate links into video content.
    """
    from services.monetization.service import base_monetization_engine

    try:
        return success_response(
            data=await base_monetization_engine.auto_insert_links(
                video_path, niche, script_content
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
