from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from src.api.utils.database import get_db
from src.api.utils.models import VideoJobDB
from src.api.config import settings
from src.services.video_engine.job_service import VideoJobService, get_video_job_service
from pydantic import BaseModel
from typing import Any
from src.shared.enums import SystemJobStatus
import logging

router = APIRouter(prefix="/internal", tags=["Internal"])
logger = logging.getLogger(__name__)

INTERNAL_TOKEN_HEADER = APIKeyHeader(name="X-Internal-Token")

async def verify_internal_token(token: str = Security(INTERNAL_TOKEN_HEADER)):
    if token != settings.INTERNAL_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal token"
        )
    return token

class InternalJobCreate(BaseModel):
    id: str
    title: str
    user_id: str
    metadata: dict[str, Any] | None = None

class InternalJobUpdate(BaseModel):
    status: str | None = None
    progress: int | None = None
    output_path: str | None = None
    error_message: str | None = None

@router.post("/jobs", dependencies=[Depends(verify_internal_token)])
async def create_internal_job(
    body: InternalJobCreate,
    job_service: VideoJobService = Depends(get_video_job_service),
):
    """Allows internal services to register jobs without direct DB access."""
    await job_service.create_job(
        user_id=body.user_id,
        title=body.title,
        engine="internal",
        job_id=body.id,
        status=SystemJobStatus.QUEUED,
        extra_metadata=body.metadata,
    )
    return {"status": "ok", "job_id": body.id}

@router.patch("/jobs/{job_id}", dependencies=[Depends(verify_internal_token)])
async def update_internal_job(
    job_id: str,
    body: InternalJobUpdate,
    db=Depends(get_db)
):
    """Atomic update for job status from internal workers."""
    from sqlalchemy import select
    stmt = select(VideoJobDB).where(VideoJobDB.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if body.status:
        if isinstance(body.status, str):
            try:
                job.status = SystemJobStatus(body.status)
            except ValueError:
                try:
                    job.status = SystemJobStatus[body.status.upper()]
                except KeyError:
                    if body.status.upper() == "SYNTHESIS_ACTIVE":
                        job.status = SystemJobStatus.SYNTHESIS_ACTIVE
                    elif body.status.upper() == "SYNTHESIZING":
                        job.status = SystemJobStatus.SYNTHESIZING
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid job status: {body.status}"
                        )
        else:
            job.status = body.status
    if body.progress is not None:
        job.progress = body.progress
    if body.output_path:
        job.output_path = body.output_path
    if body.error_message:
        job.error_message = body.error_message

    await db.commit()

    # Trigger WebSocket notification if needed
    try:
        from src.api.routes.ws import notify_job_update_sync

        ws_status = job.status
        if hasattr(job.status, "value"):
            ws_status = job.status.value

        notify_job_update_sync({
            "id": job_id,
            "status": ws_status,
            "progress": job.progress,
            "output_path": job.output_path,
            "error_message": job.error_message
        })
    except Exception as e:
        logger.warning(f"WS notification failed: {e}")

    return {"status": "ok"}
