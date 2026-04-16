from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from api.utils.database import get_db
from api.utils.models import VideoJobDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB, SubscriptionTier
from api.utils.subscription import (
    subscription_required,
    check_daily_limit,
    engine_access_required,
    credits_required,
)
from services.video_engine.tasks import generate_video_task, generate_story_task
from services.video_engine.synthesis_service import generative_service
from services.payment.credit_service import credit_service
from api.utils.limiter import limiter
from api.utils.audit_service import audit_service
import logging

router = APIRouter(prefix="/video", tags=["Video Generation"])
logger = logging.getLogger(__name__)


class GenerationRequest(BaseModel):
    prompt: str
    engine: str = "veo3"
    style: str = "Cinematic"
    aspect_ratio: str = "9:16"
    custom_image_url: Optional[str] = None


class StoryRequest(BaseModel):
    prompt: str
    engine: str = "veo3"
    style: str = "Cinematic"


@router.post("/generate")
@limiter.limit("5/minute")
async def generate_single_video(
    request: Request,
    body: GenerationRequest,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Hardened AI video synthesis endpoint with atomic credit flow.
    """
    try:
        await engine_access_required(body.engine)(current_user)
        await check_daily_limit(current_user, db)

        from api.config.engine_config import (
            ENGINE_TO_ACTION,
            get_credit_action,
            DEFAULT_ENGINE,
            is_free_engine,
            is_premium_engine,
        )

        # Get credit action for the engine
        action = get_credit_action(body.engine)
        credits_cost = await credits_required(action)(current_user, db)

        # 1. Dispatch Task first
        try:
            task = generate_video_task.delay(
                prompt=body.prompt,
                engine=body.engine,
                style=body.style,
                aspect_ratio=body.aspect_ratio,
                user_id=current_user.id,
                custom_image_url=body.custom_image_url,
            )
        except Exception as task_err:
            logger.error(f"Generation task failure: {task_err}")
            raise HTTPException(status_code=503, detail="Generation queue unavailable")

        # 2. Consume Credits
        success, msg = await credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action=action,
            db=db,
            reference_id=task.id,
        )

        if not success:
            from api.utils.celery import celery_app

            celery_app.control.revoke(task.id, terminate=True)
            raise HTTPException(status_code=402, detail=f"Credit failure: {msg}")

        # 3. Create Job
        new_job = VideoJobDB(
            id=task.id,
            title=f"AI Synthesis - {body.engine}",
            status="Queued",
            progress=0,
            input_url="Generation Prompt",
            user_id=current_user.id,
        )
        db.add(new_job)
        await db.commit()

        await audit_service.log(
            action="VIDEO_GENERATE_START",
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=task.id,
            details={"engine": body.engine, "style": body.style},
            db=db,
        )

        return {"message": "Generation started", "task_id": task.id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"video_generate.py: Error: {e}")
        raise HTTPException(status_code=500, detail="Generation failed")


@router.post("/generate-story")
async def start_story_generation(
    request: Request,
    body: StoryRequest,
    current_user: UserDB = Depends(subscription_required(SubscriptionTier.BASIC)),
    credits_cost: int = Depends(credits_required("storytelling")),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers a multi-scene storytelling narrative task.
    """
    try:
        await check_daily_limit(current_user, db)

        # 1. Dispatch Task
        task = generate_story_task.delay(
            prompt=body.prompt,
            engine=body.engine,
            style=body.style,
            user_id=current_user.id,
        )

        # 2. Consume Credits (Hardened: await and reference_id)
        success, msg = await credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action="storytelling",
            db=db,
            reference_id=task.id,
        )

        if not success:
            from api.utils.celery import celery_app

            celery_app.control.revoke(task.id, terminate=True)
            raise HTTPException(status_code=402, detail=f"Credit failure: {msg}")

        # 3. Job Entry
        new_job = VideoJobDB(
            id=task.id,
            title=f"Storytelling - {body.style}",
            status="Queued",
            user_id=current_user.id,
        )
        db.add(new_job)
        await db.commit()

        await audit_service.log(
            action="STORY_GENERATE_START",
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=task.id,
            db=db,
        )

        return {"message": "Storytelling started", "task_id": task.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Story generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry/{task_id}")
@limiter.limit("10/minute")
async def retry_failed_job(
    request: Request,
    task_id: str,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retry a failed video generation job.
    Validates that the job belongs to the user and is in a failed state.
    """
    try:
        # Find the job
        from api.utils.models import VideoJobDB
        from sqlalchemy import select

        stmt = select(VideoJobDB).where(
            VideoJobDB.id == task_id, VideoJobDB.user_id == current_user.id
        )
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if job can be retried
        if not job.status.startswith("Failed"):
            raise HTTPException(
                status_code=400,
                detail=f"Job is not in a failed state (current: {job.status})",
            )

        # Check for retry limits (simple check - could be enhanced)
        if job.error_message and "max retries" in job.error_message.lower():
            raise HTTPException(
                status_code=400, detail="Job has exceeded maximum retry attempts"
            )

        # Determine which task type to retry
        if "AI Synthesis" in job.title:
            # Retry generate_video_task
            from services.video_engine.tasks import generate_video_task

            # We need to extract parameters from the job or use defaults
            # For now, use basic retry with stored parameters if available
            # This is a simplified version - in production, store task args
            task = generate_video_task.delay(
                prompt="Retried synthesis",  # Would need to store original prompt
                engine="veo3",
                style="Cinematic",
                aspect_ratio="9:16",
                user_id=current_user.id,
            )
        elif "Storytelling" in job.title:
            # Retry generate_story_task
            from services.video_engine.tasks import generate_story_task

            task = generate_story_task.delay(
                prompt="Retried story",
                engine="veo3",
                style="Cinematic",
                user_id=current_user.id,
            )
        else:
            # Retry download_and_process_task
            from services.video_engine.tasks import download_and_process_task

            task = download_and_process_task.delay(
                source_url=job.input_url,
                niche="general",  # Would need to store original niche
                platform="YouTube Shorts",
                preview_only=False,
            )

        # Update job status
        job.status = "Queued"
        job.progress = 0
        job.error_message = None
        await db.commit()

        await audit_service.log(
            action="VIDEO_JOB_RETRY",
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=task_id,
            details={"new_task_id": task.id},
            db=db,
        )

        return {
            "message": "Job retry initiated",
            "original_task_id": task_id,
            "new_task_id": task.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job retry failed: {e}")
        raise HTTPException(status_code=500, detail="Retry failed")


@router.get("/{job_id}/preview")
async def get_video_preview(
    job_id: str,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get video preview information including public URL and status.
    """
    try:
        stmt = select(VideoJobDB).where(
            VideoJobDB.id == job_id, VideoJobDB.user_id == current_user.id
        )
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Video job not found")

        return {
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "public_url": job.output_path,
            "title": job.title,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video preview failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video preview")


@router.get("/jobs")
async def list_video_jobs(
    page: int = 1,
    limit: int = 10,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of user's video generation jobs.
    """
    try:
        if page < 1:
            page = 1
        if limit < 1 or limit > 50:
            limit = 10

        offset = (page - 1) * limit

        stmt = (
            select(VideoJobDB)
            .where(VideoJobDB.user_id == current_user.id)
            .order_by(VideoJobDB.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(stmt)
        jobs = result.scalars().all()

        # Get total count for pagination info
        count_stmt = select(VideoJobDB).where(VideoJobDB.user_id == current_user.id)
        count_result = await db.execute(count_stmt)
        total_jobs = len(count_result.scalars().all())

        return {
            "jobs": [
                {
                    "job_id": job.id,
                    "status": job.status,
                    "progress": job.progress,
                    "public_url": job.output_path,
                    "title": job.title,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                }
                for job in jobs
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_jobs,
                "pages": (total_jobs + limit - 1) // limit,
            },
        }
    except Exception as e:
        logger.error(f"Video jobs listing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list video jobs")
