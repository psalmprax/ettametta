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
    from pathlib import Path
    token_file = Path(f"data/storage/tokens/{platform}_{current_user.id}.json")
    
    # Check for real token file
    is_connected = token_file.exists()
    
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
    if platform not in ["tiktok", "instagram"]:
        raise HTTPException(status_code=400, detail="Test login only supported for tiktok and instagram")
    
    if not PLAYWRIGHT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Playwright automation not available")
    
    try:
        # Import the publisher skill
        from src.services.openclaw.skills.social_publisher import base_playwright_publisher
        
        # Start browser and navigate to login page
        browser = await base_playwright_publisher._start_browser()
        context = await browser.new_context(
            viewport={'width': 1080, 'height': 1920},
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1'
        )
        page = await context.new_page()
        
        if platform == "tiktok":
            await page.goto('https://www.tiktok.com/login')
        elif platform == "instagram":
            await page.goto('https://www.instagram.com/accounts/login/')
        
        # Wait for user to log in manually (max 2 minutes)
        await page.wait_for_timeout(120000)
        
        # Check if logged in by looking for profile elements
        is_logged_in = False
        if platform == "tiktok":
            # Check for profile avatar or upload button
            is_logged_in = await page.query_selector('div[data-e2e="user-profile"]') is not None
        elif platform == "instagram":
            # Check for home icon or profile picture
            is_logged_in = await page.query_selector('svg[aria-label="Home"]') is not None
        
        if is_logged_in:
            # Save cookies
            cookies = await context.cookies()
            await base_playwright_publisher._save_session(platform, current_user.id, cookies)
            await context.close()
            
            return success_response(data={
                "platform": platform,
                "status": "success",
                "message": f"Successfully logged in to {platform}. Session saved for automated posting."
            })
        else:
            await context.close()
            raise HTTPException(status_code=400, detail=f"Login not detected. Please ensure you are fully logged in.")
            
    except Exception as e:
        logger.error(f"Test login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test login failed: {str(e)}")
