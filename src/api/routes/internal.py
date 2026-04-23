from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.utils.database import get_db
from src.api.utils.models import VideoJobDB
from src.api.config import settings
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
    db: AsyncSession = Depends(get_db)
):
    """Allows internal services to register jobs without direct DB access."""
    new_job = VideoJobDB(
        id=body.id,
        title=body.title,
        user_id=body.user_id,
        status=SystemJobStatus.QUEUED,
        metadata=body.metadata or {}
    )
    db.add(new_job)
    await db.commit()
    return {"status": "ok", "job_id": body.id}

@router.patch("/jobs/{job_id}", dependencies=[Depends(verify_internal_token)])
async def update_internal_job(
    job_id: str,
    body: InternalJobUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Atomic update for job status from internal workers."""
    from sqlalchemy import select
    stmt = select(VideoJobDB).where(VideoJobDB.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if body.status:
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
        notify_job_update_sync({
            "id": job_id,
            "status": job.status,
            "progress": job.progress,
            "output_path": job.output_path
        })
    except Exception as e:
        logger.warning(f"WS notification failed: {e}")
        
    return {"status": "ok"}
