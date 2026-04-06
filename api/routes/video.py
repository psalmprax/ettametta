from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from api.utils.database import SessionLocal
from api.utils.models import VideoJobDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB, SubscriptionTier
from api.utils.subscription import (
    subscription_required,
    check_daily_limit,
    engine_access_required,
    credits_required,
)
from services.video_engine.tasks import (
    download_and_process_task,
    generate_video_task,
    generate_story_task,
)
from services.video_engine.synthesis_service import generative_service
from services.payment.credit_service import credit_service
from api.utils.limiter import limiter
from api.utils.audit_service import audit_service
from fastapi import Request
import logging

router = APIRouter(prefix="/video", tags=["Video Engine"])


class TransformationRequest(BaseModel):
    input_url: str
    niche: str = "Motivation"
    platform: str = "YouTube Shorts"
    style: Optional[str] = "Default"
    quality_tier: Optional[str] = "standard"  # standard, enhanced, premium
    generate_thumbnail: Optional[bool] = False
    sound_design: Optional[bool] = False
    motion_graphics: Optional[bool] = False


class GenerationRequest(BaseModel):
    prompt: str
    engine: str = "veo3"  # veo3, wan2.2, custom_image, zsky, kling, pixverse, replicate, stability, runway, pika, ltx-video, hunyuan, mochi, cogvideo
    style: str = "Cinematic"
    aspect_ratio: str = "9:16"
    custom_image_url: Optional[str] = None  # For custom image input


class StoryRequest(BaseModel):
    prompt: str
    engine: str = "veo3"
    style: str = "Cinematic"


@router.post("/transform")
@limiter.limit("10/minute")  # Technical burst protection
async def start_transformation(
    request: Request,
    body: TransformationRequest,
    current_user: UserDB = Depends(get_current_user),
    credits_cost: int = Depends(credits_required("video_transformation")),
):
    """
    Triggers a background Celery task to download, process, and upload a video.
    """
    db = SessionLocal()
    try:
        # Enforce daily generation limits
        await check_daily_limit(current_user, db)

        # Consume credits
        credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action="video_transformation",
            description=f"Video transformation: {body.input_url}",
        )

        task = download_and_process_task.delay(
            source_url=body.input_url,
            niche=body.niche,
            platform=body.platform,
            style=body.style,
            quality_tier=body.quality_tier,
            sound_design=body.sound_design or False,
            motion_graphics=body.motion_graphics or False,
        )

        # Create Job Entry in Database
        new_job = VideoJobDB(
            id=task.id,
            title=f"Viral Transform - {body.niche}",
            status="Queued",
            progress=0,
            input_url=body.input_url,
            user_id=current_user.id,
        )
        db.add(new_job)
        db.commit()

        audit_service.log(
            action="VIDEO_TRANSFORM_START",
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=task.id,
            details={"input_url": body.input_url, "niche": body.niche},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            db=db,
        )

        return {
            "message": "Transformation started in background",
            "task_id": task.id,
            "status": "Queued",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/jobs")
async def list_jobs(current_user: UserDB = Depends(get_current_user)):
    """
    Lists all video processing jobs from the database for the current user.
    """
    db = SessionLocal()
    try:
        # User isolation: Only see their own jobs unless admin
        query = db.query(VideoJobDB)
        if current_user.role != "admin":
            query = query.filter(VideoJobDB.user_id == current_user.id)

        jobs = query.order_by(VideoJobDB.created_at.desc()).all()
        return jobs
    finally:
        db.close()


@router.post("/jobs/{job_id}/abort")
async def abort_job(job_id: str, current_user: UserDB = Depends(get_current_user)):
    """
    Abort a running video processing job.
    Revokes the Celery task and updates job status.
    """
    from api.utils.celery import celery_app

    db = SessionLocal()
    try:
        job = db.query(VideoJobDB).filter(VideoJobDB.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # User isolation
        if current_user.role != "admin" and job.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to abort this job"
            )

        # Revoke Celery Task
        celery_app.control.revoke(job_id, terminate=True)

        # Update Database
        job.status = "Aborted"
        db.commit()

        # Notify Dashboard via WebSocket
        from api.routes.ws import notify_job_update_sync

        notify_job_update_sync(
            {
                "id": job_id,
                "status": "Aborted",
                "progress": job.progress,
                "output_path": job.output_path,
            }
        )

        return {
            "status": "Aborted",
            "message": f"Job {job_id} revocation signal transmitted.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


class TestDriveRequest(BaseModel):
    niche: str
    style: Optional[str] = "Default"


@router.post("/test-drive")
async def test_drive(
    request: TestDriveRequest, current_user: UserDB = Depends(get_current_user)
):
    """
    Identifies the top viral candidate for a niche and triggers a preview-only transformation.
    """
    from services.discovery.service import base_discovery_service
    from api.utils.models import ContentCandidateDB

    db = SessionLocal()
    try:
        # Enforce daily generation limits
        await check_daily_limit(current_user, db)

        # 1. Find top candidate with strict guardrails
        # - Must have a thumbnail
        # - Must have a niche
        # - Order by viral score
        candidate = (
            db.query(ContentCandidateDB)
            .filter(
                ContentCandidateDB.niche == request.niche,
                ContentCandidateDB.thumbnail_url.isnot(None),
                ContentCandidateDB.thumbnail_url != "",
            )
            .order_by(ContentCandidateDB.viral_score.desc())
            .first()
        )

        if not candidate:
            # Try a quick scan if none found
            logging.info(
                f"[TestDrive] No valid candidates with thumbnails found for {request.niche}. Triggering scan..."
            )
            trends = await base_discovery_service.find_trending_content(
                request.niche, horizon="30d"
            )
            if trends:
                candidate = (
                    db.query(ContentCandidateDB)
                    .filter(
                        ContentCandidateDB.niche == request.niche,
                        ContentCandidateDB.thumbnail_url.isnot(None),
                        ContentCandidateDB.thumbnail_url != "",
                    )
                    .order_by(ContentCandidateDB.viral_score.desc())
                    .first()
                )

        if not candidate:
            raise HTTPException(
                status_code=404,
                detail=f"No high-quality video candidates with thumbnails found for {request.niche}. Please try again in a few minutes after the scanners update.",
            )

        # 2. Trigger Preview Task
        task = download_and_process_task.delay(
            source_url=candidate.url,
            niche=request.niche,
            platform="YouTube Shorts",  # Default format for test drive
            preview_only=True,
            style=request.style,
        )

        # 3. Create Job Entry
        new_job = VideoJobDB(
            id=task.id,
            title=f"Test Drive - {request.niche}",
            status="Queued",
            progress=0,
            input_url=candidate.url,
            user_id=current_user.id,
        )
        db.add(new_job)
        db.commit()

        return {
            "message": "Test Drive started",
            "task_id": task.id,
            "candidate": {
                "id": candidate.id,
                "title": candidate.title,
                "url": candidate.url,
            },
        }
    except Exception as e:
        import traceback

        logging.error(f"[TestDrive] Error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/generate")
@limiter.limit("5/minute")
async def generate_single_video(
    request: Request,
    body: GenerationRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Triggers an AI video synthesis task. Restricted by engine tiers.
    """
    db = SessionLocal()
    try:
        # 0. Tier Gating Logic via Standard Dependency
        await engine_access_required(body.engine)(current_user)

        # Enforce daily limits
        await check_daily_limit(current_user, db)

        # Credit Consumption Logic
        engine_to_action = {
            "ltx-video": "video_generation_ltx",
            "hunyuan": "video_generation_hunyuan",
            "veo3": "video_generation_veo3",
            "runway": "video_generation_runway",
            "pika": "video_generation_runway",
            "lite4k": "video_generation_ltx",
            "mochi": "video_generation_hunyuan",
            "cogvideo": "video_generation_hunyuan",
            "wan": "video_generation_hunyuan",
            "wan2.2": "video_generation_hunyuan",
            # Free daily providers
            "zsky": "video_generation_free",
            "kling": "video_generation_free",
            "pixverse": "video_generation_free",
            "replicate": "video_generation_free",
            "stability": "video_generation_free",
        }

        action = engine_to_action.get(body.engine, "video_generation_ltx")

        # Check and consume credits using dependency helper logic
        credits_cost = await credits_required(action)(current_user)

        # Consume credits
        success, msg = credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action=action,
            description=f"Video generation: {body.engine} - {body.prompt[:50]}...",
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process payment: {msg}",
            )

        # 1. Trigger Synthesis Task (Service handles internal optimization per engine)
        task = generate_video_task.delay(
            prompt=body.prompt,
            engine=body.engine,
            style=body.style,
            aspect_ratio=body.aspect_ratio,
            user_id=current_user.id,
            custom_image_url=body.custom_image_url,
        )

        # We can still show the user what it *will* look like
        preview_prompt = generative_service.optimize_prompt(
            body.prompt, body.style, body.engine
        )

        # 3. Create Job Entry
        new_job = VideoJobDB(
            id=task.id,
            title=f"AI Synthesis - {body.engine}",
            status="Queued",
            progress=0,
            input_url="Generation Prompt",
            user_id=current_user.id,
        )
        db.add(new_job)
        db.commit()

        audit_service.log(
            action="VIDEO_GENERATE_START",
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=task.id,
            details={"engine": body.engine, "style": body.style},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            db=db,
        )

        return {
            "message": "Generation started",
            "task_id": task.id,
            "optimized_prompt_preview": preview_prompt,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/generate-story")
async def start_story_generation(
    request: Request,
    body: StoryRequest,
    current_user: UserDB = Depends(subscription_required(SubscriptionTier.BASIC)),
    credits_cost: int = Depends(credits_required("storytelling")),
):
    """
    Triggers a multi-scene storytelling narrative task. Restricted to BASIC tier and above.
    """
    db = SessionLocal()
    try:
        # Enforce daily limits
        await check_daily_limit(current_user, db)

        # Consume credits
        credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action="storytelling",
            description=f"Storytelling narrative: {body.prompt[:50]}...",
        )

        task = generate_story_task.delay(
            prompt=body.prompt,
            engine=body.engine,
            style=body.style,
            user_id=current_user.id,
        )

        new_job = VideoJobDB(
            id=task.id,
            title=f"Storytelling - {request.style}",
            status="Queued",
            progress=0,
            input_url="Narrative Prompt",
            user_id=current_user.id,
        )
        db.add(new_job)
        db.commit()

        audit_service.log(
            action="STORY_GENERATE_START",
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=task.id,
            details={"engine": body.engine, "style": body.style},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            db=db,
        )

        return {"message": "Storytelling narrative started", "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
