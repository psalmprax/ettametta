"""
Autonomous Video Remix API Routes
==================================
Endpoints for AI-driven autonomous video creation from discovered viral content.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.api_responses import success_response
from src.services.video_engine.autonomous_remixer import base_autonomous_remixer

router = APIRouter(prefix="/video/autonomous", tags=["Autonomous Video"])


class RemixRequest(BaseModel):
    topic: str
    niche: str | None = None  # Auto-detected if not provided
    style: str = "dynamic"  # dynamic, aggressive, smooth, asmr
    duration_seconds: int = 60
    voice_id: str | None = None


@router.post("/remix")
async def autonomous_video_remix(
    request: RemixRequest,
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Fully autonomous video creation from discovered viral content.

    Pipeline:
    1. Discovers viral videos matching topic/niche from 15+ platforms
    2. Downloads and analyzes videos for best segments
    3. Generates script matching the clips
    4. Extracts and fuses clips with transitions
    5. Adds AI voiceover synced to visuals
    6. Burns in captions
    7. Renders final polished video

    No human intervention required - completely autonomous.
    """
    try:
        result = await base_autonomous_remixer.create_remix_video(
            topic=request.topic,
            niche=request.niche,
            style=request.style,
            duration_seconds=request.duration_seconds,
            voice_id=request.voice_id,
        )
        return success_response(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Remix failed: {str(e)}")


@router.get("/remix/{job_id}/status")
async def get_remix_status(
    job_id: str,
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Check status of a remix job with real-time progress updates.
    Returns progress percentage and current step.
    """
    try:
        status = await base_autonomous_remixer.get_job_status(job_id)

        if not status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return success_response(data=status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
