from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from api.utils.database import get_db
from shared.enums import SystemJobStatus
from api.utils.models import VideoJobDB, AuditLogDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB, UserRole
from api.utils.audit_service import audit_service
from services.payment.credit_service import credit_service
from datetime import datetime, timedelta
from api.utils.api_responses import success_response
import logging

router = APIRouter(prefix="/video/jobs", tags=["Video Jobs"])
logger = logging.getLogger(__name__)


@router.get("/")
async def list_jobs(
    current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Lists all video processing jobs from the database for the current user.
    """
    try:
        if current_user.role == UserRole.ADMIN:
            stmt = select(VideoJobDB).order_by(VideoJobDB.created_at.desc())
        else:
            stmt = (
                select(VideoJobDB)
                .where(VideoJobDB.user_id == current_user.id)
                .order_by(VideoJobDB.created_at.desc())
            )

        result = await db.execute(stmt)
        jobs = result.scalars().all()
        return success_response(data=jobs)
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve jobs.")


@router.post("/{job_id}/abort")
async def abort_job(
    job_id: str,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Abort a running video processing job.
    """
    from api.utils.celery import celery_app
    from api.routes.ws import notify_job_update_sync

    try:
        stmt = select(VideoJobDB).where(VideoJobDB.id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if current_user.role != UserRole.ADMIN and job.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        celery_app.control.revoke(job_id, terminate=True)
        job.status = SystemJobStatus.ABORTED
        await db.commit()

        notify_job_update_sync(
            {
                "id": job_id,
                "status": SystemJobStatus.ABORTED.value,
                "progress": job.progress,
                "output_path": job.output_path,
            }
        )

        return success_response(
            data={
                "status": SystemJobStatus.ABORTED.value,
                "message": f"Job {job_id} revoked.",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error aborting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to abort job.")


@router.get("/metadata/{task_id}")
async def get_job_details(
    task_id: str,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive metadata for a video generation task.
    Includes model used, provider, cost, and generation details.
    """
    try:
        # Get video job
        stmt = select(VideoJobDB).where(
            VideoJobDB.id == task_id, VideoJobDB.user_id == current_user.id
        )
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Video job not found")

        # Get audit logs for this task
        stmt_audit = (
            select(AuditLogDB)
            .where(
                AuditLogDB.resource_id == task_id, AuditLogDB.resource_type == "VIDEO"
            )
            .order_by(AuditLogDB.created_at.desc())
        )

        result_audit = await db.execute(stmt_audit)
        audit_logs = result_audit.scalars().all()

        # Extract metadata from audit logs
        metadata = {
            "task_id": task_id,
            "title": job.title,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "input_prompt": job.source_url
            if job.source_url not in ["Generation Prompt", "Narrative Prompt"]
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
        from api.utils.subscription import get_provider_quota_info

        # Simple cost mapping (consistent with original)
        cost_mapping = {
            "veo3": {"credits": 25, "cost_usd": 2.50, "category": "premium"},
            "runway": {"credits": 30, "cost_usd": 3.00, "category": "premium"},
            "pika": {"credits": 30, "cost_usd": 3.00, "category": "premium"},
            "ltx-video": {"credits": 10, "cost_usd": 1.00, "category": "local"},
            "hunyuan": {"credits": 15, "cost_usd": 1.50, "category": "local"},
        }

        cost_info = cost_mapping.get(
            engine, {"credits": 10, "cost_usd": 1.00, "category": "standard"}
        )
        metadata["cost_info"] = {
            "credits_used": cost_info["credits"],
            "estimated_cost_usd": cost_info["cost_usd"],
            "category": cost_info["category"],
        }

        return success_response(data=metadata)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metadata for {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metadata")


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: str,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retry a failed video processing job.
    """
    from services.video_engine.tasks import (
        download_and_process_task,
        generate_video_task,
        generate_story_task,
    )

    try:
        stmt = select(VideoJobDB).where(VideoJobDB.id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # User isolation
        if current_user.role != UserRole.ADMIN and job.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        if job.status not in [SystemJobStatus.FAILED, SystemJobStatus.ABORTED]:
            raise HTTPException(
                status_code=400, detail=f"Job {job.status} cannot be retried"
            )

        # Retry logic based on job type
        task = None
        if job.source_url not in ["Generation Prompt", "Narrative Prompt"]:
            task = download_and_process_task.delay(
                source_url=job.source_url,
                niche=job.title.split(" - ")[-1]
                if " - " in job.title
                else "Motivation",
                platform="YouTube Shorts",
                style="Default",
                quality_tier="standard",
            )
        elif job.source_url == "Generation Prompt":
            stmt_audit = select(AuditLogDB).where(
                AuditLogDB.resource_id == job_id,
                AuditLogDB.action == "VIDEO_GENERATE_START",
            )
            audit_result = await db.execute(stmt_audit)
            audit_log = audit_result.scalar_one_or_none()

            if audit_log and audit_log.details:
                details = audit_log.details
                task = generate_video_task.delay(
                    prompt=job.title.split(" - ")[-1],
                    engine=details.get("engine", "veo3"),
                    style=details.get("style", "Cinematic"),
                    aspect_ratio="9:16",
                    user_id=current_user.id,
                )

        if not task:
            raise HTTPException(
                status_code=400,
                detail="Cannot determine job type or missing parameters",
            )

        # Update job
        old_task_id = job.id
        job.id = task.id
        job.status = SystemJobStatus.QUEUED
        job.progress = 0
        job.output_path = None
        await db.commit()

        # Audit log
        await audit_service.log(
            action="VIDEO_JOB_RETRY",
            user_id=current_user.id,
            resource_type="VIDEO",
            resource_id=task.id,
            details={"original_job_id": old_task_id},
            db=db,
        )

        return success_response(
            data={"message": "Job retry initiated", "new_task_id": task.id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry failed for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quotas")
async def get_video_quotas(
    current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get current user's video generation quotas and usage.
    """
    from api.utils.subscription import get_user_subscription_tier

    try:
        tier = await get_user_subscription_tier(current_user, db)
        today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())

        stmt = select(func.count(VideoJobDB.id)).where(
            VideoJobDB.user_id == current_user.id,
            VideoJobDB.created_at >= today_start,
            VideoJobDB.status.in_(
                [
                    SystemJobStatus.COMPLETED,
                    SystemJobStatus.SYNTHESIZING,
                    SystemJobStatus.RENDERING,
                ]
            ),
        )
        result = await db.execute(stmt)
        video_count = result.scalar()

        tier_limits = {
            "free": {"daily_videos": 5, "monthly_credits": 0},
            "basic": {"daily_videos": 20, "monthly_credits": 50},
            "premium": {"daily_videos": 1000, "monthly_credits": 200},
        }
        limits = tier_limits.get(tier, tier_limits["free"])

        # Credit balance (Async call)
        credit_balance = await credit_service.get_user_credits(current_user.id, db)

        return success_response(
            data={
                "subscription_tier": tier,
                "daily_limit": limits["daily_videos"],
                "daily_used": video_count,
                "current_credit_balance": credit_balance.balance
                if credit_balance
                else 0,
                "reset_time": (today_start + timedelta(days=1)).isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Quota fetch failed for {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch quotas")
