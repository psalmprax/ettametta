# Databricks notebook source
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select
from src.api.utils.database import get_db
from src.shared.enums import SystemJobStatus, CreditAction
from src.api.utils.models import VideoJobDB
from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB, SubscriptionTier
from src.api.utils.subscription import (
    subscription_required,
    daily_limit_reached,
    engine_access_required,
    credits_required,
)
from src.services.video_engine.job_service import get_video_job_service, VideoJobService
from src.services.video_engine.tasks import generate_video_task, generate_story_task
from src.services.video_engine.engine_config import get_engine_action
from src.api.utils.limiter import limiter
from src.api.utils.audit_service import audit_service
from src.api.utils.api_responses import success_response, handle_exception
from src.services.payment.credit_service import credit_service
import logging
import uuid
from src.api.utils.tracing import get_request_id

router = APIRouter(prefix="/video", tags=["Video Generation"])
logger = logging.getLogger(__name__)


class GenerationRequest(BaseModel):
    prompt: str
    engine: str = "ltx-video"
    style: str = "Cinematic"
    aspect_ratio: str = "9:16"
    custom_image_uri: str | None = None
    num_variants: int = 1  # Standard 4.1: Growth Loop Scaling
    variant_strategy: str = "hook_variation"


class StoryRequest(BaseModel):
    prompt: str
    engine: str = "ltx-video"
    style: str = "Cinematic"


@router.post("/generate")
@limiter.limit("5/minute")
async def generate_single_video(
    request: Request,
    body: GenerationRequest,
    current_user: UserDB = Depends(daily_limit_reached()),
    db=Depends(get_db),
):
    """
    Hardened AI video synthesis endpoint with atomic credit flow.
    """
    try:
        # Engine access check still manual because it depends on request body
        await engine_access_required(body.engine)(current_user)
        # daily_limit_reached dependency already checked via Depends
        # Engine-specific billing action mapping
        engine_action = get_engine_action(body.engine)
        unit_cost = await credits_required(engine_action)(current_user, db)

        num_variants = body.num_variants if body.num_variants > 0 else 1
        total_credits_cost = unit_cost * num_variants

        if total_credits_cost > 0 and not await credit_service.has_sufficient_credits(
            current_user.id,
            total_credits_cost,
            db,
        ):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Need {total_credits_cost} credits for {num_variants} variant(s) using engine '{body.engine}'.",
            )
        action = engine_action
        credits_cost = unit_cost
        variant_strategy = body.variant_strategy or "hook_variation"
        # --- ELITE GROWTH LOOP: MULTI-VARIANT GENERATION ---
        num_variants = body.num_variants if body.num_variants > 0 else 1
        variant_strategy = body.variant_strategy or "hook_variation"

        # 0. Generate Variant Prompts (Standard 4.1)
        variant_prompts = [{"modified_prompt": body.prompt, "variant_name": "Original"}]
        if num_variants > 1:
            from src.services.optimization.variant_generator import (
                base_variant_service,
            )

            variant_prompts = await base_variant_service.generate_variant_prompts(
                original_prompt=body.prompt,
                count=num_variants,
                strategy=variant_strategy,
                session_id=request.state.request_id
                if hasattr(request.state, "request_id")
                else None,
            )

        # Ensure we have a parent ID for grouping
        parent_job_id = str(uuid.uuid4())
        task_ids = []
        variant_info = []
        job_service: VideoJobService = VideoJobService(db)

        # 1. Consume credits and create job entries first in a single transaction
        try:
            for i, variant in enumerate(variant_prompts):
                task_id = str(uuid.uuid4())
                
                # Consume Credits with auto_commit=False (flushes to session)
                success, msg = await credit_service.consume_credits(
                    user_id=current_user.id,
                    amount=credits_cost,
                    action=action,
                    db=db,
                    reference_id=task_id,
                    auto_commit=False,
                )

                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail=f"Credit failure for variant {i}: {msg}"
                    )

                # Create Job for each variant via service layer
                await job_service.create_job(
                    user_id=current_user.id,
                    title=f"Variant {i}: {variant.get('variant_name', 'Original')}",
                    engine=body.engine,
                    prompt=variant.get("modified_prompt", body.prompt),
                    style=variant.get("suggested_style", body.style),
                    status=SystemJobStatus.QUEUED,
                    job_id=task_id,
                    progress=0,
                    source_uri="Generation Prompt",
                    auto_commit=False,
                    extra_metadata={
                        "parent_id": parent_job_id,
                        "variant_index": i,
                        "variant_logic": variant.get("logic", "N/A"),
                        "hook_text": variant.get("hook_text", "N/A"),
                    },
                )
                variant_info.append((task_id, variant, i))

            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e

        # 2. Dispatch Tasks for each variant only after DB commit succeeded
        for task_id, variant, i in variant_info:
            try:
                generate_video_task.apply_async(
                    kwargs={
                        "prompt": variant.get("modified_prompt", body.prompt),
                        "engine": body.engine,
                        "style": variant.get("suggested_style", body.style),
                        "aspect_ratio": body.aspect_ratio,
                        "user_id": current_user.id,
                        "custom_image_uri": body.custom_image_uri,
                        "parent_id": parent_job_id,
                        "variant_index": i,
                        "request_id": get_request_id(),
                    },
                    task_id=task_id,
                )
                task_ids.append(task_id)
            except Exception as task_err:
                logger.exception(f"Failed to dispatch variant {i} Celery task: {task_err}")
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
                        description=f"Refund: Failed to queue variant {i}",
                        reference_id=task_id,
                        auto_commit=False,
                    )
                    await db.commit()
                except Exception as refund_err:
                    await db.rollback()
                    logger.exception(f"Refund/fail update failed for variant {i}: {refund_err}")

        await audit_service.log(
            action=CreditAction.VIDEO_GENERATE_VARIANTS_START,
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=parent_job_id,
            details={
                "engine": body.engine,
                "count": len(task_ids),
                "strategy": variant_strategy,
            },
            db=db,
        )

        return success_response(
            data={
                "message": f"Started {len(task_ids)} video variants",
                "parent_id": parent_job_id,
                "task_id": task_ids[0] if task_ids else None,
                "task_ids": task_ids,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        return handle_exception(e)


@router.post("/generate-story")
async def start_story_generation(
    request: Request,
    body: StoryRequest,
    current_user: UserDB = Depends(daily_limit_reached()),
    credits_cost: int = Depends(credits_required("storytelling")),
    db=Depends(get_db),
):
    """
    Triggers a multi-scene storytelling narrative task.
    """
    try:
        # Minimum tier check (BASIC for stories)
        await subscription_required(SubscriptionTier.BASIC)(current_user)
        # daily_limit_reached dependency already checked via Depends

        task_id = str(uuid.uuid4())
        job_service: VideoJobService = VideoJobService(db)

        # 1. Consume Credits and save to DB in a single transaction first
        try:
            success, msg = await credit_service.consume_credits(
                user_id=current_user.id,
                amount=credits_cost,
                action=CreditAction.STORYTELLING,
                db=db,
                reference_id=task_id,
                auto_commit=False,
            )

            if not success:
                raise HTTPException(status_code=402, detail=f"Credit failure: {msg}")

            # 2. Job Entry via service layer
            await job_service.create_job(
                user_id=current_user.id,
                title=f"Storytelling - {body.style}",
                engine=body.engine,
                prompt=body.prompt,
                style=body.style,
                status=SystemJobStatus.QUEUED,
                job_id=task_id,
                auto_commit=False,
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e

        # 3. Dispatch Task only after DB commit succeeded
        try:
            generate_story_task.apply_async(
                kwargs={
                    "prompt": body.prompt,
                    "engine": body.engine,
                    "style": body.style,
                    "user_id": current_user.id,
                    "request_id": get_request_id(),
                },
                task_id=task_id,
            )
        except Exception as task_err:
            logger.exception(f"Failed to dispatch storytelling Celery task: {task_err}")
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
                    description="Refund: Failed to queue storytelling task",
                    reference_id=task_id,
                    auto_commit=False,
                )
                await db.commit()
            except Exception as refund_err:
                await db.rollback()
                logger.exception(f"Refund/fail update failed for storytelling task: {refund_err}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Task queue unavailable. Please try again later.",
            )

        await audit_service.log(
            action=CreditAction.STORY_GENERATE_START,
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=task_id,
            db=db,
            data={"message": "Storytelling started", "task_id": task_id},
        )

        return success_response(
            data={"message": "Storytelling started", "task_id": task_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        return handle_exception(e)


@router.post("/retry/{job_id}")
@limiter.limit("10/minute")
async def retry_failed_job(
    request: Request,
    job_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Retry a failed video generation job.
    Validates that the job belongs to the user and is in a failed state.
    """
    try:
        # Find the job
        stmt = select(VideoJobDB).where(
            VideoJobDB.id == job_id, VideoJobDB.user_id == current_user.id
        )
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if job can be retried
        if job.status == SystemJobStatus.FAILED:
            pass  # Continue to retry
        elif isinstance(job.status, str) and job.status.startswith("Failed"):
            pass  # Backward compatibility for string status
        else:
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
        params = job.job_metadata or {}
        if "AI Synthesis" in job.title:
            # Retry generate_video_task
            from src.services.video_engine.tasks import generate_video_task

            task = generate_video_task.delay(
                prompt=params.get("prompt", "Retried synthesis"),
                engine=params.get("engine", "ltx-video"),
                style=params.get("style", "Cinematic"),
                aspect_ratio=params.get("aspect_ratio", "9:16"),
                user_id=current_user.id,
                custom_image_uri=params.get("custom_image_uri"),
                request_id=get_request_id(),
            )
        elif "Storytelling" in job.title:
            # Retry generate_story_task
            from src.services.video_engine.tasks import generate_story_task

            task = generate_story_task.delay(
                prompt=params.get("prompt", "Retried story"),
                engine=params.get("engine", "ltx-video"),
                style=params.get("style", "Cinematic"),
                user_id=current_user.id,
                request_id=get_request_id(),
            )
        else:
            # Retry download_and_process_task
            from src.services.video_engine.tasks import download_and_process_task

            task = download_and_process_task.delay(
                source_uri=job.source_uri,
                niche=params.get("niche", "general"),
                platform="YouTube Shorts",
                preview_only=False,
                user_id=current_user.id,
                request_id=get_request_id(),
            )

        # Update job status
        job.status = SystemJobStatus.QUEUED
        job.progress = 0
        job.error_message = None
        await db.commit()

        await audit_service.log(
            action=CreditAction.VIDEO_JOB_RETRY,
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=job_id,
            details={"new_task_id": task.id},
            db=db,
        )

        return success_response(data={
            "message": "Job retry initiated",
            "original_job_id": job_id,
            "new_task_id": task.id,
        })

    except HTTPException:
        raise
    except Exception as e:
        return handle_exception(e)


@router.get("/{job_id}/preview")
async def get_video_preview(
    job_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
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

        return success_response(data={
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "public_url": job.output_path,
            "title": job.title,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        })
    except HTTPException:
        raise
    except Exception as e:
        return handle_exception(e)


@router.get("/jobs")
async def list_video_jobs(
    page: int = 1,
    limit: int = 10,
    current_user: UserDB = Depends(get_current_user),
    job_service: VideoJobService = Depends(get_video_job_service),
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
        jobs, total_jobs = await job_service.get_user_jobs(
            user_id=current_user.id, limit=limit, offset=offset
        )

        return success_response(data={
            "jobs": [
                {
                    "job_id": job["id"],
                    "status": job["status"],
                    "progress": job["progress"],
                    "public_url": job["output_path"],
                    "title": job["title"],
                    "created_at": job["created_at"],
                    "updated_at": job.get("created_at"),  # Using created_at as updated_at fallback
                }
                for job in jobs
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_jobs,
                "pages": (total_jobs + limit - 1) // limit,
            },

        })


    except Exception as e:        return handle_exception(e)