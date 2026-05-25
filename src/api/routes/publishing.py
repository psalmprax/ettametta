"""
Publishing API Routes
=====================
Endpoints for publishing videos to social media platforms.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

from src.api.utils.auth import get_current_user
from src.api.utils.models import UserDB
from src.api.utils.api_responses import success_response
from src.services.publishing.service import base_publishing_service
from src.services.optimization.auth import token_manager

router = APIRouter(prefix="/publish", tags=["Publishing"])


class PublishRequest(BaseModel):
    platform: str  # 'youtube', 'tiktok', 'instagram'
    video_path: str  # Path to existing video or job_id
    title: str
    description: str = ""
    tags: list[str] = []
    privacy: str = "private"  # 'public', 'private', 'unlisted'
    use_automation: bool = False  # Use Playwright for TikTok/Instagram


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
            user_id=current_user.id,  # Pass real user ID
            platform=request.platform,
            video_path=request.video_path,
            metadata={
                "title": request.title,
                "description": request.description,
                "tags": request.tags,
                "privacy": request.privacy
            },
            use_automation=request.use_automation  # Pass automation flag
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
    Check if a platform is connected and ready for publishing by verifying stored tokens.
    """
    platform_key = platform.lower()
    is_connected = await token_manager.get_token(platform_key, user_id=current_user.id) is not None
    
    return success_response(data={
        "platform": platform,
        "connected": is_connected,
        "status": "ready" if is_connected else "disconnected",
        "message": f"{platform} account {'connected' if is_connected else 'not linked'}"
    })


@router.post("/test-login")
async def test_login(
    platform: str,
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Trigger a manual login flow for TikTok/Instagram to save session cookies.
    Opens a browser window for the user to log in once.
    After successful login, cookies are saved for future automated posts.
    """
    raise HTTPException(
        status_code=410,
        detail=(
            "Browser-based login capture is disabled because it required handling "
            "session cookies in an unsafe server-side browser flow. Use the OAuth "
            "routes under /api/v1/publish/auth/{platform} instead."
        ),
    )


@router.get("/auth/{platform}")
async def init_oauth_auth(
    platform: str,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Initiate OAuth flow for connecting social media accounts.
    Supported platforms: instagram, x (twitter), linkedin, facebook
    """
    supported_platforms = ["youtube", "tiktok", "instagram", "x", "twitter", "linkedin", "facebook"]
    
    if platform.lower() not in supported_platforms:
        raise HTTPException(status_code=400, detail=f"Platform '{platform}' not supported for OAuth")
    
    return success_response(data={
        "platform": platform,
        "status": "oauth_required",
        "auth_url": f"/api/v1/publish/auth/{platform.lower()}",
        "message": f"Start the OAuth flow at /api/v1/publish/auth/{platform.lower()}.",
    })
