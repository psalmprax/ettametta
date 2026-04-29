from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.api.utils.database import get_db
from src.shared.enums import SystemJobStatus, CreditAction
from src.api.utils.models import VideoJobDB
from src.api.routes.auth import get_current_user
from src.api.utils.user_models import UserDB, SubscriptionTier
from src.api.utils.subscription import (
    subscription_required,
    daily_limit_reached,
    engine_access_required,
    credits_required,
    check_daily_limit,
)
from src.services.video_engine.job_service import get_video_job_service, VideoJobService
from src.services.video_engine.tasks import generate_video_task, generate_story_task
from src.services.script_generator.service import base_script_generator
from src.services.decision_engine.hook_validator import base_hook_validator
from src.services.voiceover.service import base_voiceover_service
from src.services.stock_media.service import base_stock_media_service
from src.services.multiplatform.translator import base_global_adapter
from src.services.nexus_engine.auto_creator import base_auto_creator
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
    engine: str = "veo3"
    style: str = "Cinematic"
    aspect_ratio: str = "9:16"
    custom_image_uri: str | None = None
    num_variants: int = 1  # Standard 4.1: Growth Loop Scaling
    variant_strategy: str = "hook_variation"


class StoryRequest(BaseModel):
    prompt: str
    engine: str = "veo3"
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

        # Logic for engine-to-action mapping
        # Since engine_config is missing, we implement a resilient fallback here
        ENGINE_TO_ACTION = {
            "veo3": CreditAction.VIDEO_GENERATE,
            "flux": CreditAction.IMAGE_GENERATE,
            "kling": CreditAction.VIDEO_GENERATE_PREMIUM,
            "luma": CreditAction.VIDEO_GENERATE_PREMIUM,
        }
        
        def get_credit_action(engine_name: str) -> CreditAction:
            return ENGINE_TO_ACTION.get(engine_name, CreditAction.VIDEO_GENERATE)
            
        action = get_credit_action(body.engine)
        credits_cost = await credits_required(action)(current_user, db)

        # --- ELITE GROWTH LOOP: MULTI-VARIANT GENERATION ---
        num_variants = body.num_variants if body.num_variants > 0 else 1
        variant_strategy = body.variant_strategy or "hook_variation"

        # 0. Generate Variant Prompts (Standard 4.1)
        variant_prompts = [{"modified_prompt": body.prompt, "variant_name": "Original"}]
        if num_variants > 1:
            from src.services.optimization.variant_generator import (
                base_variant_generator,
            )

            variant_prompts = await base_variant_generator.generate_variant_prompts(
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

        # 1. Dispatch Tasks for each variant
        for i, variant in enumerate(variant_prompts):
            try:
                task = generate_video_task.delay(
                    prompt=variant.get("modified_prompt", body.prompt),
                    engine=body.engine,
                    style=variant.get("suggested_style", body.style),
                    aspect_ratio=body.aspect_ratio,
                    user_id=current_user.id,
                    custom_image_uri=body.custom_image_uri,
                    parent_id=parent_job_id,
                    variant_index=i,
                    request_id=get_request_id(),
                )
                task_ids.append(task.id)

                # 2. Consume Credits for each variant
                success, msg = await credit_service.consume_credits(
                    user_id=current_user.id,
                    amount=credits_cost,
                    action=action,
                    db=db,
                    reference_id=task.id,
                )

                if not success:
                    # Partial failure - stop and revoke
                    from src.api.utils.celery import celery_app

                    celery_app.control.revoke(task.id, terminate=True)
                    logger.warning(f"Credit failure for variant {i}: {msg}")
                    break

                # 3. Create Job for each variant
                new_job = VideoJobDB(
                    id=task.id,
                    title=f"Variant {i}: {variant.get('variant_name', 'Default')}",
                    status=SystemJobStatus.QUEUED,
                    progress=0,
                    source_uri="Generation Prompt",
                    job_metadata={
                        "prompt": variant.get("modified_prompt", body.prompt),
                        "engine": body.engine,
                        "style": variant.get("suggested_style", body.style),
                        "parent_id": parent_job_id,
                        "variant_index": i,
                        "variant_logic": variant.get("logic", "N/A"),
                        "hook_text": variant.get("hook_text", "N/A"),
                    },
                    user_id=current_user.id,
                )
                db.add(new_job)

            except Exception as task_err:
                logger.error(f"Variant generation task failure: {task_err}")

        await db.commit()

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

        # 1. Dispatch Task
        task = generate_story_task.delay(
            prompt=body.prompt,
            engine=body.engine,
            style=body.style,
            user_id=current_user.id,
            request_id=get_request_id(),
        )

        # 2. Consume Credits (Hardened: await and reference_id)
        success, msg = await credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action=CreditAction.STORYTELLING,
            db=db,
            reference_id=task.id,
        )

        if not success:
            from src.api.utils.celery import celery_app

            celery_app.control.revoke(task.id, terminate=True)
            raise HTTPException(status_code=402, detail=f"Credit failure: {msg}")

        # 3. Job Entry
        new_job = VideoJobDB(
            id=task.id,
            title=f"Storytelling - {body.style}",
            status=SystemJobStatus.QUEUED,
            job_metadata={
                "prompt": body.prompt,
                "engine": body.engine,
                "style": body.style,
            },
            user_id=current_user.id,
        )
        db.add(new_job)
        await db.commit()

        await audit_service.log(
            action=CreditAction.STORY_GENERATE_START,
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=task.id,
            db=db,
        )

        return success_response(
            data={"message": "Storytelling started", "task_id": task.id}
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
                engine=params.get("engine", "veo3"),
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
                engine=params.get("engine", "veo3"),
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

        return {
            "message": "Job retry initiated",
            "original_job_id": job_id,
            "new_task_id": task.id,
        }

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
        return handle_exception(e)
