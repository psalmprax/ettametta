from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.api.utils.database import get_db
from src.shared.enums import SystemJobStatus
from src.api.utils.models import VideoJobDB
from src.api.routes.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.subscription import check_daily_limit, credits_required
from src.services.video_engine.tasks import download_and_process_task
from src.services.payment.credit_service import credit_service
from src.api.utils.limiter import limiter
from src.api.utils.audit_service import audit_service
from src.api.utils.api_responses import success_response
from src.services.discovery.service import base_discovery_service
from src.api.utils.models import ContentCandidateDB
import logging
import uuid

router = APIRouter(prefix="/video", tags=["Video Transformation"])
logger = logging.getLogger(__name__)


class TransformationRequest(BaseModel):
    source_uri: str
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
    db=Depends(get_db),
):
    """
    Hardened transformation endpoint with atomicity between task dispatch and credit consumption.
    """
    try:
        await check_daily_limit(current_user, db)

        task_id = str(uuid.uuid4())

        # 1. Consume credits and create job entry first in a single transaction
        try:
            # Consume Credits with auto_commit=False (flushes to session)
            success, msg = await credit_service.consume_credits(
                user_id=current_user.id,
                amount=credits_cost,
                action="video_transformation",
                db=db,
                reference_id=task_id,
                auto_commit=False,
            )

            if not success:
                raise HTTPException(
                    status_code=402, detail=f"Credit consumption failed: {msg}"
                )

            # Create Job Entry
            new_job = VideoJobDB(
                id=task_id,
                title=f"Viral Transform - {body.niche}",
                status=SystemJobStatus.QUEUED,
                progress=0,
                source_uri=body.source_uri,
                user_id=current_user.id,
                job_metadata={
                    "niche": body.niche,
                    "platform": body.platform,
                    "style": body.style,
                    "quality_tier": body.quality_tier,
                    "sound_design": body.sound_design,
                    "motion_graphics": body.motion_graphics,
                    "generate_thumbnail": body.generate_thumbnail,
                    "analysis_data": body.analysis_data,
                }
            )
            db.add(new_job)
            await db.commit()

        except Exception as e:
            await db.rollback()
            raise e

        # 2. Dispatch Task only after DB commit succeeded
        try:
            download_and_process_task.apply_async(
                kwargs={
                    "source_uri": body.source_uri,
                    "niche": body.niche,
                    "platform": body.platform,
                    "style": body.style,
                    "quality_tier": body.quality_tier,
                    "sound_design": body.sound_design or False,
                    "motion_graphics": body.motion_graphics or False,
                    "generate_thumbnail": body.generate_thumbnail or False,
                    "analysis_data": body.analysis_data,
                    "user_id": current_user.id,
                },
                task_id=task_id,
            )
        except Exception as task_err:
            logger.error(f"Failed to dispatch transformation Celery task: {task_err}")
            # Compensation workflow: mark job as failed and refund credits
            try:
                stmt = select(VideoJobDB).where(VideoJobDB.id == task_id)
                res = await db.execute(stmt)
                job_to_fail = res.scalar_one_or_none()
                if job_to_fail:
                    job_to_fail.status = SystemJobStatus.FAILED
                    job_to_fail.error_message = f"Enqueuing failed: {task_err}"

                await credit_service.add_credits(
                    user_id=current_user.id,
                    amount=credits_cost,
                    transaction_type="refund",
                    db=db,
                    description="Refund: Failed to queue transformation task",
                    reference_id=task_id,
                    auto_commit=False,
                )
                await db.commit()
            except Exception as refund_err:
                await db.rollback()
                logger.error(f"Refund/fail update failed for transformation task: {refund_err}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Task queue unavailable. Please try again later.",
            )

        await audit_service.log(
            action="VIDEO_TRANSFORM_START",
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=task_id,
            details={"source_uri": body.source_uri, "cost": credits_cost},
            db=db,
        )

        return success_response(
            data={"message": "Transformation started", "task_id": task_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise HTTPException(status_code=503, detail="Video processing unavailable")


class TestDriveRequest(BaseModel):
    niche: str
    style: str | None = "Default"


@router.post("/test-drive")
async def test_drive(
    request: TestDriveRequest,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Identifies the top viral candidate and triggers a preview transformation.
    """
    try:
        await check_daily_limit(current_user, db)

        stmt = (
            select(ContentCandidateDB)
            .where(
                ContentCandidateDB.niche == request.niche,
                ContentCandidateDB.thumbnail_uri.isnot(None),
            )
            .order_by(ContentCandidateDB.viral_score.desc())
        )

        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise HTTPException(status_code=404, detail="No viral candidates found")

        task_id = str(uuid.uuid4())

        # 1. Save job record first in DB
        try:
            new_job = VideoJobDB(
                id=task_id,
                title=f"Test Drive - {request.niche}",
                status=SystemJobStatus.QUEUED,
                source_uri=candidate.source_uri,
                user_id=current_user.id,
                job_metadata={
                    "niche": request.niche,
                    "style": request.style,
                    "preview_only": True,
                    "platform": "YouTube Shorts",
                    "candidate_id": candidate.id
                }
            )
            db.add(new_job)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e

        # 2. Dispatch Task only after DB commit succeeded
        try:
            download_and_process_task.apply_async(
                kwargs={
                    "source_uri": candidate.source_uri,
                    "niche": request.niche,
                    "platform": "YouTube Shorts",
                    "preview_only": True,
                    "style": request.style,
                    "user_id": current_user.id,
                },
                task_id=task_id,
            )
        except Exception as task_err:
            logger.error(f"Failed to dispatch test-drive Celery task: {task_err}")
            try:
                stmt = select(VideoJobDB).where(VideoJobDB.id == task_id)
                res = await db.execute(stmt)
                job_to_fail = res.scalar_one_or_none()
                if job_to_fail:
                    job_to_fail.status = SystemJobStatus.FAILED
                    job_to_fail.error_message = f"Enqueuing failed: {task_err}"
                await db.commit()
            except Exception as update_err:
                await db.rollback()
                logger.error(f"Failed to update job status on test-drive celery dispatch failure: {update_err}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Task queue unavailable. Please try again later.",
            )

        return success_response(
            data={"message": "Test Drive started", "task_id": task_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test drive failed: {e}")
        raise HTTPException(status_code=503, detail="Video processing unavailable")


class AutoLinkRequest(BaseModel):
    job_id: str | None = None
    video_path: str | None = None
    niche: str | None = None
    script_content: str = ""


@router.post("/auto-insert-links")
async def auto_insert_affiliate_links(
    body: AutoLinkRequest,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Automatically inserts affiliate links into video content.
    Consumes job_id to ensure we use the correct processed asset.
    """
    from src.services.monetization.service import base_monetization_service

    try:
        video_path = body.video_path
        niche = body.niche
        script_content = body.script_content

        # 1. If job_id provided, lookup real data
        if body.job_id:
            stmt = select(VideoJobDB).where(VideoJobDB.id == body.job_id)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            
            if job:
                # Use output_path as the video source
                if not job.output_path:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Job {body.job_id} has no output path. Status: {job.status}. Error: {job.error_message}"
                    )
                video_path = job.output_path
                niche = job.job_metadata.get("niche", niche) if job.job_metadata else niche
                # Attempt to find script in metadata
                script_content = job.job_metadata.get("script", script_content) if job.job_metadata else script_content
            else:
                raise HTTPException(status_code=404, detail=f"Job ID {body.job_id} not found")

        if not video_path:
            raise HTTPException(status_code=400, detail="Video path or Job ID with output required")

        return success_response(
            data=await base_monetization_service.plan_monetization_strategy(
                niche or "General", script_content, video_path=video_path
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auto-insert links failed: {e}")
        raise HTTPException(status_code=503, detail="Video processing unavailable")
