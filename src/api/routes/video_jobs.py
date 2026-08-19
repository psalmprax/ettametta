from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.utils.database import get_db
from src.shared.enums import SystemJobStatus, CreditAction
from src.api.utils.models import VideoJobDB, AuditLogDB
from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB, UserRole
from src.api.utils.audit_service import audit_service
from src.services.payment.credit_service import credit_service
from src.services.video_engine.job_service import get_video_job_service, VideoJobService
from src.api.utils.tracing import get_request_id
from datetime import datetime, timedelta, timezone
from src.api.utils.api_responses import success_response
import logging

router = APIRouter(prefix="/video/jobs", tags=["Video Jobs"])
logger = logging.getLogger(__name__)

GENERATION_PROMPT = "Generation Prompt"
NARRATIVE_PROMPT = "Narrative Prompt"


@router.get(
    "/",
    responses={
        500: {"description": "Database error retrieving jobs"},
    },
)
async def list_jobs(
    current_user: Annotated[UserDB, Depends(get_current_user)],
    job_service: Annotated[VideoJobService, Depends(get_video_job_service)],
):
    """
    Lists all video processing jobs from the database for the current current_user.
    """
    try:
        include_all = current_user.role == UserRole.ADMIN
        jobs, _ = await job_service.get_user_jobs(
            user_id=current_user.id,
            limit=100,  # sensible default for listing
            include_all=include_all,
        )
        return success_response(data=jobs)
    except Exception as e:
        logger.exception(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail="Database error retrieving jobs")


@router.post(
    "/{job_id}/abort",
    responses={
        404: {"description": "Job not found or unauthorized"},
        500: {"description": "Database error aborting job"},
    },
)
async def abort_job(
    job_id: str,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    job_service: Annotated[VideoJobService, Depends(get_video_job_service)],
):
    """
    Abort a running video processing job.
    """
    try:
        success = await job_service.abort_job(
            job_id=job_id,
            user_id=current_user.id,
            user_role=current_user.role,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Job not found or unauthorized")

        return success_response(
            data={
                "status": SystemJobStatus.ABORTED.value,
                "message": f"Job {job_id} revoked.",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error aborting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error aborting job")


@router.get(
    "/metadata/{job_id}",
    responses={
        404: {"description": "Job not found"},
        500: {"description": "Database error fetching metadata"},
    },
)
async def get_job_details(
    job_id: str,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    job_service: Annotated[VideoJobService, Depends(get_video_job_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get comprehensive metadata for a video generation task.
    Includes model used, provider, cost, and generation details.
    """
    try:
        # Get job via service (handles both Video and Nexus)
        job = await job_service.get_job_by_id(job_id, current_user.id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get audit logs for this task
        stmt_audit = (
            select(AuditLogDB)
            .where(
                AuditLogDB.resource_id == job_id, AuditLogDB.resource_type == "VIDEO"
            )
            .order_by(AuditLogDB.created_at.desc())
        )

        result_audit = await db.execute(stmt_audit)
        audit_logs = result_audit.scalars().all()

        # Extract metadata from audit logs
        metadata = {
            "job_id": job_id,
            "title": job["title"],
            "status": job["status"],
            "progress": job["progress"],
            "created_at": job["created_at"].isoformat(),
            "updated_at": job["updated_at"].isoformat(),
            "input_prompt": job["source_uri"]
            if job["source_uri"] not in [GENERATION_PROMPT, NARRATIVE_PROMPT, "Cinema Mode / Studio"]
            else None,
            "output_path": job["output_path"],
            "generation_details": {},
            "cost_info": {},
            "engine": job.get("engine", "unknown")
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

        # Simple cost mapping (consistent with original)
        cost_mapping = {

            "runway": {"credits": 30, "cost_usd": 3.00, "category": "premium"},
            "pika": {"credits": 30, "cost_usd": 3.00, "category": "premium"},
            "ltx-video": {"credits": 10, "cost_usd": 1.00, "category": "local"},
            "hunyuan": {"credits": 15, "cost_usd": 1.50, "category": "local"},
            # Local GPU inference engines
            "mochi": {"credits": 15, "cost_usd": 1.50, "category": "local"},
            "wan": {"credits": 15, "cost_usd": 1.50, "category": "local"},
            "cogvideo": {"credits": 20, "cost_usd": 2.00, "category": "local"},
            "zeroscope": {"credits": 10, "cost_usd": 1.00, "category": "local"},
            "animatediff": {"credits": 15, "cost_usd": 1.50, "category": "local"},
            # Zero-API-key engine
            "lite4k": {"credits": 5, "cost_usd": 0.50, "category": "local"},
            # Free daily credit APIs
            "zsky": {"credits": 0, "cost_usd": 0.00, "category": "free"},
            "stability": {"credits": 0, "cost_usd": 0.00, "category": "free"},
            # Paid API
            "replicate": {"credits": 5, "cost_usd": 0.50, "category": "standard"},
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
        logger.exception(f"Error fetching metadata for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error fetching metadata")


@router.post(
    "/{job_id}/retry",
    responses={
        400: {"description": "Job cannot be retried or missing parameters"},
        403: {"description": "Not authorized"},
        404: {"description": "Job not found"},
        500: {"description": "Database error retrying job"},
    },
)
async def retry_job(
    job_id: str,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Retry a failed video processing job.
    """
    from src.services.video_engine.tasks import (
        download_and_process_task,
        generate_video_task,
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
        if job.source_uri not in [GENERATION_PROMPT, NARRATIVE_PROMPT]:
            task = download_and_process_task.delay(
                source_uri=job.source_uri,
                niche=job.title.split(" - ")[-1]
                if " - " in job.title
                else "Motivation",
                platform="YouTube Shorts",
                style="Default",
                quality_tier="standard",
                user_id=current_user.id,
                request_id=get_request_id(),
            )
        elif job.source_uri == GENERATION_PROMPT:
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
                    engine=details.get("engine", "ltx-video"),
                    style=details.get("style", "Cinematic"),
                    aspect_ratio="9:16",
                    user_id=current_user.id,
                    request_id=get_request_id(),
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
            action=CreditAction.VIDEO_JOB_RETRY,
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
        logger.exception(f"Retry failed for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error retrying job")


@router.get(
    "/quotas",
    responses={
        500: {"description": "Database error fetching quotas"},
    },
)
async def get_video_quotas(
    current_user: Annotated[UserDB, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get current current_user's video generation quotas and usage.
    """
    from src.api.utils.subscription import get_user_subscription_tier

    try:
        tier = get_user_subscription_tier(current_user)
        today_start = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time())

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
        logger.exception(f"Quota fetch failed for {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Database error fetching quotas")
