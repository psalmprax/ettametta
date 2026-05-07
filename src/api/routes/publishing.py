"""
Publishing API Routes
=====================
Endpoints for publishing videos to social media platforms.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Any

from src.api.routes.auth import get_current_user
from src.api.utils.models import UserDB
from src.api.utils.api_responses import success_response
from src.services.publishing.service import base_publishing_service

router = APIRouter(prefix="/publish", tags=["Publishing"])


class PublishRequest(BaseModel):
    platform: str  # 'youtube', 'tiktok'
    video_path: str  # Path to existing video or job_id
    title: str
    description: str = ""
    tags: list[str] = []
    privacy: str = "private"  # 'public', 'private', 'unlisted'


@router.post("/video")
async def publish_video(
    request: PublishRequest,
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Publish a video to a social media platform.
    
    Requires OAuth connection to the platform (configured in settings).
    """
    try:
        result = await base_publishing_service.publish_to_platform(
            platform=request.platform,
            video_path=request.video_path,
            metadata={
                "title": request.title,
                "description": request.description,
                "tags": request.tags,
                "privacy": request.privacy
            }
        )
        return success_response(data=result)
    except NotImplementedError:
        raise HTTPException(status_code=501, detail=f"{request.platform} publishing not yet implemented")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{platform}")
async def get_publishing_status(
    platform: str,
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Check if a platform is connected and ready for publishing.
    """
    # Mock implementation - would check OAuth tokens in DB
    is_connected = platform == "youtube"  # Assume YouTube is connected for demo
    
    return success_response(data={
        "platform": platform,
        "connected": is_connected,
        "status": "ready" if is_connected else "disconnected"
    })
