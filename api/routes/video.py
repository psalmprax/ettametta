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
            # Replicate paid models (cheap!)
            "replicate_wan": "video_generation_replicate",  # $0.01-0.02 per video
            "replicate_seedance": "video_generation_replicate",  # $0.09-0.72 per video
            "replicate_hailuo": "video_generation_replicate",  # $0.10-0.15 per video
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


@router.get("/metadata/{task_id}")
async def get_video_metadata(
    task_id: str,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Get comprehensive metadata for a video generation task.
    Includes model used, provider, cost, and generation details.
    """
    db = SessionLocal()
    try:
        # Get video job
        job = (
            db.query(VideoJobDB)
            .filter(VideoJobDB.id == task_id, VideoJobDB.user_id == current_user.id)
            .first()
        )

        if not job:
            raise HTTPException(status_code=404, detail="Video job not found")

        # Get audit logs for this task
        from api.utils.models import AuditLogDB

        audit_logs = (
            db.query(AuditLogDB)
            .filter(
                AuditLogDB.resource_id == task_id, AuditLogDB.resource_type == "VIDEO"
            )
            .order_by(AuditLogDB.created_at.desc())
            .all()
        )

        # Extract metadata from audit logs
        metadata = {
            "task_id": task_id,
            "title": job.title,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "input_prompt": job.input_url
            if job.input_url != "Generation Prompt"
            else None,
            "output_path": job.output_path,
            "generation_details": {},
            "cost_info": {},
        }

        # Parse audit log details for generation metadata
        for log in audit_logs:
            if log.action in ["VIDEO_GENERATE_START", "STORY_GENERATE_START"]:
                details = log.details or {}
                metadata["generation_details"] = {
                    "engine": details.get("engine"),
                    "style": details.get("style"),
                    "aspect_ratio": details.get("aspect_ratio"),
                    "custom_image": details.get("custom_image", False),
                    "provider": details.get("provider"),
                    "model": details.get("model"),
                    "cost_credits": details.get("cost"),
                }
                break

        # Calculate cost information
        engine = metadata["generation_details"].get("engine", "unknown")
        cost_mapping = {
            # Free providers
            "zsky": {"credits": 0, "cost_usd": 0.00, "category": "free"},
            "kling": {"credits": 0, "cost_usd": 0.00, "category": "free"},
            "pixverse": {"credits": 0, "cost_usd": 0.00, "category": "free"},
            "replicate": {"credits": 0, "cost_usd": 0.00, "category": "free"},
            # Paid Replicate
            "replicate_wan": {"credits": 5, "cost_usd": 0.10, "category": "cheap"},
            "replicate_seedance": {
                "credits": 5,
                "cost_usd": 2.00,
                "category": "quality",
            },
            "replicate_hailuo": {"credits": 5, "cost_usd": 0.75, "category": "cheap"},
            # Local GPU
            "ltx-video": {"credits": 10, "cost_usd": 1.00, "category": "local"},
            "hunyuan": {"credits": 15, "cost_usd": 1.50, "category": "local"},
            "mochi": {"credits": 15, "cost_usd": 1.50, "category": "local"},
            "wan": {"credits": 15, "cost_usd": 1.50, "category": "local"},
            "wan2.2": {"credits": 15, "cost_usd": 1.50, "category": "local"},
            "cogvideo": {"credits": 15, "cost_usd": 1.50, "category": "local"},
            # Cloud premium
            "veo3": {"credits": 25, "cost_usd": 2.50, "category": "premium"},
            "runway": {"credits": 30, "cost_usd": 3.00, "category": "premium"},
            "pika": {"credits": 30, "cost_usd": 3.00, "category": "premium"},
        }

        cost_info = cost_mapping.get(
            engine, {"credits": 10, "cost_usd": 1.00, "category": "unknown"}
        )
        metadata["cost_info"] = {
            "credits_used": cost_info["credits"],
            "estimated_cost_usd": cost_info["cost_usd"],
            "category": cost_info["category"],
            "provider_quota": get_provider_quota_info(engine),
        }

        return metadata

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


def get_provider_quota_info(engine: str) -> dict:
    """
    Get quota information for a specific engine/provider.
    """
    quota_info = {
        # Free daily providers
        "zsky": {
            "daily_limit": 50,
            "type": "free",
            "resolution": "1080p",
            "max_duration": 10,
        },
        "kling": {
            "daily_limit": 100,
            "type": "free",
            "resolution": "1080p",
            "max_duration": 10,
        },
        "pixverse": {
            "daily_limit": 20,
            "type": "free",
            "resolution": "1080p",
            "max_duration": 8,
        },
        "replicate": {
            "daily_limit": "trial",
            "type": "free",
            "resolution": "720p",
            "max_duration": 10,
        },
        # Paid Replicate models
        "replicate_wan": {
            "daily_limit": "unlimited",
            "type": "paid",
            "cost_per_video": 0.02,
            "resolution": "720p",
            "max_duration": 5,
        },
        "replicate_seedance": {
            "daily_limit": "unlimited",
            "type": "paid",
            "cost_per_video": 0.40,
            "resolution": "1080p",
            "max_duration": 10,
        },
        "replicate_hailuo": {
            "daily_limit": "unlimited",
            "type": "paid",
            "cost_per_video": 0.15,
            "resolution": "720p",
            "max_duration": 6,
        },
        # Local GPU models
        "ltx-video": {
            "daily_limit": "unlimited",
            "type": "local_gpu",
            "credits_per_video": 10,
            "resolution": "720p",
            "max_duration": 10,
        },
        "hunyuan": {
            "daily_limit": "unlimited",
            "type": "local_gpu",
            "credits_per_video": 15,
            "resolution": "1080p",
            "max_duration": 5,
        },
        "mochi": {
            "daily_limit": "unlimited",
            "type": "local_gpu",
            "credits_per_video": 15,
            "resolution": "1080p",
            "max_duration": 5,
        },
        "wan": {
            "daily_limit": "unlimited",
            "type": "local_gpu",
            "credits_per_video": 15,
            "resolution": "720p",
            "max_duration": 5,
        },
        "wan2.2": {
            "daily_limit": "unlimited",
            "type": "local_gpu",
            "credits_per_video": 15,
            "resolution": "720p",
            "max_duration": 5,
        },
        "cogvideo": {
            "daily_limit": "unlimited",
            "type": "local_gpu",
            "credits_per_video": 15,
            "resolution": "1080p",
            "max_duration": 5,
        },
        # Cloud premium
        "veo3": {
            "daily_limit": "unlimited",
            "type": "cloud_premium",
            "credits_per_video": 25,
            "resolution": "1080p",
            "max_duration": 8,
        },
        "runway": {
            "daily_limit": "unlimited",
            "type": "cloud_premium",
            "credits_per_video": 30,
            "resolution": "720p",
            "max_duration": 10,
        },
        "pika": {
            "daily_limit": "unlimited",
            "type": "cloud_premium",
            "credits_per_video": 30,
            "resolution": "720p",
            "max_duration": 8,
        },
    }

    return quota_info.get(engine, {"type": "unknown", "daily_limit": "unknown"})


@router.get("/quotas")
async def get_video_quotas(
    current_user: UserDB = Depends(get_current_user),
):
    """
    Get current user's video generation quotas and usage.
    """
    from datetime import datetime, timedelta
    from api.utils.subscription import get_user_subscription_tier

    db = SessionLocal()
    try:
        # Get user's subscription tier
        tier = await get_user_subscription_tier(current_user, db)

        # Get today's video generation count
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())

        video_count = (
            db.query(VideoJobDB)
            .filter(
                VideoJobDB.user_id == current_user.id,
                VideoJobDB.created_at >= today_start,
                VideoJobDB.status.in_(
                    ["Completed", "Synthesizing", "Rendering"]
                ),  # Count active generations
            )
            .count()
        )

        # Tier-based limits
        tier_limits = {
            "free": {"daily_videos": 5, "monthly_credits": 0},
            "creator": {"daily_videos": 20, "monthly_credits": 50},
            "empire": {
                "daily_videos": 1000,
                "monthly_credits": 200,
            },  # Effectively unlimited
            "sovereign": {"daily_videos": 1000, "monthly_credits": 500},
            "studio": {"daily_videos": 1000, "monthly_credits": 1000},
        }

        limits = tier_limits.get(tier, tier_limits["free"])

        # Get credit balance
        credit_balance = credit_service.get_user_credits(current_user.id)

        return {
            "subscription_tier": tier,
            "daily_limit": limits["daily_videos"],
            "daily_used": video_count,
            "daily_remaining": max(0, limits["daily_videos"] - video_count),
            "monthly_credits_limit": limits["monthly_credits"],
            "current_credit_balance": credit_balance.balance if credit_balance else 0,
            "reset_time": (today_start + timedelta(days=1)).isoformat(),
            "provider_quotas": {
                "free_providers": {
                    "zsky": {"remaining": 50 - video_count, "reset_daily": True},
                    "kling": {"remaining": 100 - video_count, "reset_daily": True},
                    "pixverse": {"remaining": 20 - video_count, "reset_daily": True},
                },
                "paid_providers": {
                    "replicate_wan": {"cost_per_video": 5, "unlimited": True},
                    "replicate_seedance": {"cost_per_video": 5, "unlimited": True},
                    "local_gpu": {"cost_per_video": "10-15", "unlimited": True},
                    "cloud_premium": {"cost_per_video": "25-30", "unlimited": True},
                },
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
