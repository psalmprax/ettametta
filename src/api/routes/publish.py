from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.responses import RedirectResponse
from src.services.optimization.service import base_optimization_service
from src.services.optimization.youtube_publisher import base_youtube_publisher
from src.services.optimization.tiktok_publisher import base_tiktok_publisher
from src.services.optimization.models import PostMetadata
from src.services.optimization.auth import token_manager
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
from src.api.config import settings
from src.api.routes.auth import get_current_user
from src.api.utils.vault import get_secret, get_secret_async
from src.api.utils.user_models import UserDB

# from src.api.utils.user_models import UserDB # Deprecated import
from src.api.utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.api.utils.models import SocialAccount, PublishedContentDB
from src.api.utils.subscription import credits_required
from src.services.payment.credit_service import credit_service
import datetime
import uuid
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/publish", tags=["Publishing"])

# Supported Platforms for Publishing
SUPPORTED_PLATFORMS = {
    "youtube": {
        "name": "YouTube",
        "types": ["YouTube Shorts", "YouTube Video"],
        "oauth_provider": "google",
        "max_duration": 60,  # seconds for shorts
        "aspect_ratios": ["9:16", "16:9"],
        "monetization": True,
    },
    "tiktok": {
        "name": "TikTok",
        "types": ["TikTok Video"],
        "oauth_provider": "tiktok",
        "max_duration": 180,
        "aspect_ratios": ["9:16"],
        "monetization": True,
    },
    "instagram": {
        "name": "Instagram",
        "types": ["Instagram Reels", "Instagram Video"],
        "oauth_provider": "facebook",
        "max_duration": 90,
        "aspect_ratios": ["9:16", "1:1", "4:5"],
        "monetization": True,
    },
    "facebook": {
        "name": "Facebook",
        "types": ["Facebook Reels", "Facebook Video"],
        "oauth_provider": "facebook",
        "max_duration": 240,
        "aspect_ratios": ["9:16", "16:9", "1:1"],
        "monetization": True,
    },
    "x": {
        "name": "X (Twitter)",
        "types": ["X Video"],
        "oauth_provider": "twitter",
        "max_duration": 140,
        "aspect_ratios": ["16:9", "1:1"],
        "monetization": True,
    },
    "linkedin": {
        "name": "LinkedIn",
        "types": ["LinkedIn Video"],
        "oauth_provider": "linkedin",
        "max_duration": 600,
        "aspect_ratios": ["16:9", "1:1", "9:16"],
        "monetization": False,
    },
    "snapchat": {
        "name": "Snapchat",
        "types": ["Snapchat Spotlight"],
        "oauth_provider": "snapchat",
        "max_duration": 180,
        "aspect_ratios": ["9:16"],
        "monetization": True,
    },
    "twitch": {
        "name": "Twitch",
        "types": ["Twitch Clip"],
        "oauth_provider": "twitch",
        "max_duration": 60,
        "aspect_ratios": ["16:9"],
        "monetization": True,
    },
}


@router.get("/platforms")
async def get_supported_platforms():
    """Get list of all supported platforms for publishing"""
    return {"platforms": SUPPORTED_PLATFORMS, "count": len(SUPPORTED_PLATFORMS)}


# OAuth Scopes for YouTube
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


@router.get("/auth/youtube")
async def auth_youtube(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the YouTube OAuth flow with user_id state isolation.
    """
    client_id = await get_secret_async("google_client_id")
    client_secret = await get_secret_async("google_client_secret")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400, detail="Google OAuth Credentials not configured in Vault."
        )

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=YOUTUBE_SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_YOUTUBE_REDIRECT_URI

    # Securely encode user_id in the state
    import json
    import base64
    import secrets

    # Generate a manual code_verifier for PKCE pass-through
    code_verifier = secrets.token_urlsafe(64)
    flow.code_verifier = code_verifier

    state_data = {
        "user_id": current_user.id,
        "csrf": uuid.uuid4().hex,
        "code_verifier": code_verifier,
    }
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    authorization_url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", state=state
    )
    return {"url": authorization_url}


@router.get("/auth/youtube/callback")
async def auth_youtube_callback(
    state: str, code: str | None = None, error: str | None = None
):
    """
    Handles the YouTube OAuth callback with user isolation and robust error logging.
    """
    # Decode state to get user_id and code_verifier
    import json
    import base64

    logger.info(
        f"YouTube Callback received: state_len={len(state)}, code_present={bool(code)}, error={error}"
    )

    if error:
        raise HTTPException(status_code=400, detail=f"OAuth Error from Google: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing OAuth code from Google")

    try:
        state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
        user_id = state_data.get("user_id")
        code_verifier = state_data.get("code_verifier")
        logger.info(
            f"Decoded State: user_id={user_id}, has_verifier={bool(code_verifier)}"
        )
    except Exception as e:
        logger.error(f"Failed to decode OAuth state: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # Allow insecure transport for development/local sslip.io setups if using HTTP
    if settings.PRODUCTION_DOMAIN.startswith("http://"):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        logger.warning("OAUTHLIB_INSECURE_TRANSPORT enabled for HTTP session")

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": await get_secret_async("google_client_id"),
                "client_secret": await get_secret_async("google_client_secret"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=YOUTUBE_SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_YOUTUBE_REDIRECT_URI
    logger.info(f"Using Redirect URI for token exchange: {flow.redirect_uri}")

    # Restore the code_verifier for PKCE validation
    if code_verifier:
        flow.code_verifier = code_verifier

    try:
        await asyncio.to_thread(flow.fetch_token, code=code)
    except Exception as e:
        logger.error(f"YouTube Token Exchange Failed: {str(e)}", exc_info=True)
        # Check for specific redirect_uri mismatch in error message
        error_detail = str(e)
        if "redirect_uri_mismatch" in error_detail.lower():
            error_detail = f"Redirect URI Mismatch. Check if {flow.redirect_uri} is registered in Google Cloud Console."

        raise HTTPException(
            status_code=400, detail=f"Token exchange failed: {error_detail}"
        )

    credentials = flow.credentials
    await token_manager.store_token(
        "youtube",
        user_id,
        {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_type": "Bearer",
            "expires_in": credentials.expiry.replace(
                tzinfo=datetime.timezone.utc
            ).timestamp()
            - datetime.datetime.now(datetime.timezone.utc).timestamp()
            if credentials.expiry
            else 3600,
        },
    )

    logger.info(f"Successfully stored YouTube token for user_id={user_id}")

    # Redirect back to the frontend dashboard
    dashboard_url = (
        settings.PRODUCTION_DOMAIN.split("/api/v1")[0].rstrip("/")
        or "http://localhost:7202"
    )
    return RedirectResponse(
        url=f"{dashboard_url}/publishing?success=true&platform=youtube"
    )


@router.get("/accounts")
async def list_accounts(
    current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(SocialAccount)
        if current_user.role != "admin":
            stmt = stmt.where(SocialAccount.user_id == current_user.id)
        result = await db.execute(stmt)
        accounts = result.scalars().all()
        return [
            {
                "id": a.id,
                "platform": a.platform,
                "username": a.username,
                "updated_at": a.updated_at,
            }
            for a in accounts
        ]
    finally:
        pass


@router.delete("/account/{account_id}")
async def delete_account(
    account_id: str,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        stmt = select(SocialAccount).where(SocialAccount.id == account_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Isolation check
        if account.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this account"
            )

        await db.delete(account)
        await db.commit()
        return {"status": "success", "message": "Account unlinked"}
    finally:
        pass


@router.post("/retry/{content_id}")
async def retry_publish(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retry publishing a video that was pending authentication.
    Called after user has authenticated the platform.
    """
    from src.api.utils.models import PublishedContentDB
    from src.services.optimization.service import base_optimization_service

    try:
        # Get the pending content
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.id == content_id,
            PublishedContentDB.user_id == current_user.id,
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        if content.status != "PENDING_AUTH":
            raise HTTPException(
                status_code=400,
                detail=f"Content is not in PENDING_AUTH status. Current: {content.status}",
            )

        # Get metadata
        metadata_dict = content.metadata or {}
        video_path = metadata_dict.get("video_path")
        platform_key = metadata_dict.get("platform_key", content.platform.lower())

        if not video_path:
            raise HTTPException(
                status_code=400, detail="Video path not found in content metadata"
            )

        # Check if now authenticated
        from src.services.optimization.auth import token_manager

        has_auth = (
            await token_manager.get_token(platform_key, user_id=current_user.id)
            is not None
        )

        if not has_auth:
            raise HTTPException(
                status_code=401,
                detail=f"Platform '{platform_key}' still not authenticated. Please authenticate first.",
            )

        # Generate metadata
        metadata = await base_optimization_service.generate_viral_package(
            str(content_id), content.niche, content.platform
        )

        # Upload based on platform
        url = None
        if platform_key == "youtube":
            url = await base_youtube_publisher.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "tiktok":
            from src.services.optimization.tiktok_publisher import base_tiktok_publisher

            url = await base_tiktok_publisher.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "instagram":
            from src.services.optimization.instagram_publisher import (
                base_instagram_publisher,
            )

            url = await base_instagram_publisher.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "facebook":
            from src.services.optimization.facebook_publisher import base_facebook_publisher

            url = await base_facebook_publisher.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "x":
            from src.services.optimization.x_publisher import base_x_publisher

            url = await base_x_publisher.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "linkedin":
            from src.services.optimization.linkedin_publisher import base_linkedin_publisher

            url = await base_linkedin_publisher.upload_video(
                video_path, metadata, user_id=current_user.id
            )

        # Update status
        content.status = "Published" if url else "Failed"
        content.url = url
        content.published_at = datetime.datetime.utcnow() if url else None

        # Clear retention metadata
        metadata_dict.pop("delete_at", None)
        metadata_dict.pop("retention_hours", None)
        metadata_dict.pop("requires_auth", None)
        content.metadata = metadata_dict

        await db.commit()

        return {
            "status": "success" if url else "failed",
            "url": url,
            "message": "Video published successfully"
            if url
            else "Failed to publish video",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        pass


# TikTok OAuth
@router.get("/auth/tiktok")
async def auth_tiktok(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the TikTok OAuth flow with user_id state isolation.
    """
    client_key = await get_secret_async("tiktok_client_key")
    redirect_uri = settings.TIKTOK_REDIRECT_URI

    if not client_key:
        raise HTTPException(
            status_code=400, detail="TikTok Client Key not configured in Vault."
        )

    scope = "video.upload,user.info.basic"
    import urllib.parse
    import secrets
    import base64
    import json

    state_data = {"user_id": current_user.id, "csrf": secrets.token_urlsafe(16)}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    params = {
        "client_key": client_key,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }

    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://www.tiktok.com/v2/auth/authorize?{query_string}"
    return {"url": auth_url}


@router.get("/auth/tiktok/callback")
async def auth_tiktok_callback(code: str, state: str):
    """
    Handles the TikTok OAuth callback and exchanges code for a real token.
    """
    import httpx
    import json
    import base64

    try:
        state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
        user_id = state_data.get("user_id")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    url = "https://open.tiktokapis.com/v2/oauth/token/"

    data = {
        "client_key": await get_secret_async("tiktok_client_key"),
        "client_secret": await get_secret_async("tiktok_client_secret"),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.TIKTOK_REDIRECT_URI,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            token_data = response.json()

            if response.status_code != 200 or "access_token" not in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"TikTok Auth Failed: {token_data.get('error_description', 'Unknown error')}",
                )

            await token_manager.store_token(
                "tiktok",
                user_id,
                {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "open_id": token_data.get("open_id"),
                    "expires_in": token_data.get("expires_in", 3600),
                    "scope": token_data.get("scope"),
                },
            )

            return {
                "status": "success",
                "message": "TikTok authenticated successfully",
                "user_id": user_id,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")


# Instagram/Facebook OAuth (via Meta)
@router.get("/auth/instagram")
async def auth_instagram(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the Instagram/Facebook OAuth flow with user_id state isolation.
    """
    app_id = await get_secret_async("meta_app_id")
    redirect_uri = settings.META_REDIRECT_URI

    if not app_id:
        raise HTTPException(
            status_code=400, detail="Meta App ID not configured in Vault."
        )

    import urllib.parse
    import secrets
    import base64
    import json

    state_data = {"user_id": current_user.id, "csrf": secrets.token_urlsafe(16)}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    # Instagram scope for video upload
    scope = "instagram_basic,instagram_content_publish,pages_read_engagement,pages_manage_posts"

    params = {
        "client_id": app_id,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }

    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://api.instagram.com/oauth/authorize?{query_string}"
    return {"url": auth_url}


@router.get("/auth/instagram/callback")
async def auth_instagram_callback(code: str, state: str):
    """Handles the Instagram OAuth callback"""
    import httpx
    import json
    import base64

    try:
        state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
        user_id = state_data.get("user_id")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    app_id = await get_secret_async("meta_app_id")
    app_secret = await get_secret_async("meta_app_secret")
    redirect_uri = settings.META_REDIRECT_URI

    url = "https://api.instagram.com/oauth/access_token"
    data = {
        "client_id": app_id,
        "client_secret": app_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            token_data = response.json()

            if response.status_code != 200 or "access_token" not in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Instagram Auth Failed: {token_data.get('error_message', 'Unknown error')}",
                )

            await token_manager.store_token(
                "instagram",
                user_id,
                {
                    "access_token": token_data["access_token"],
                    "user_id": token_data.get("user_id"),
                    "expires_in": token_data.get("expires_in", 3600),
                },
            )

            return {
                "status": "success",
                "message": "Instagram authenticated successfully",
                "user_id": user_id,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")


# X (Twitter) OAuth
@router.get("/auth/x")
async def auth_x(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the X (Twitter) OAuth flow with user_id state isolation.
    """
    client_id = await get_secret_async("twitter_client_id")
    redirect_uri = settings.TWITTER_REDIRECT_URI

    if not client_id:
        raise HTTPException(
            status_code=400, detail="Twitter Client ID not configured in Vault."
        )

    import urllib.parse
    import secrets
    import base64
    import json

    state_data = {"user_id": current_user.id, "csrf": secrets.token_urlsafe(16)}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    scope = "tweet.read tweet.write users.read offline.access"

    params = {
        "client_id": client_id,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }

    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://twitter.com/i/oauth2/authorize?{query_string}"
    return {"url": auth_url}


@router.get("/auth/x/callback")
async def auth_x_callback(code: str, state: str):
    """Handles the X (Twitter) OAuth callback"""
    import httpx
    import json
    import base64

    try:
        state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
        user_id = state_data.get("user_id")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    client_id = await get_secret_async("twitter_client_id")
    client_secret = await get_secret_async("twitter_client_secret")
    redirect_uri = settings.TWITTER_REDIRECT_URI

    url = "https://api.twitter.com/2/oauth2/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            token_data = response.json()

            if response.status_code != 200 or "access_token" not in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"X Auth Failed: {token_data.get('error_description', 'Unknown error')}",
                )

            await token_manager.store_token(
                "x",
                user_id,
                {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in", 3600),
                },
            )

            return {
                "status": "success",
                "message": "X authenticated successfully",
                "user_id": user_id,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")


# LinkedIn OAuth
@router.get("/auth/linkedin")
async def auth_linkedin(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the LinkedIn OAuth flow with user_id state isolation.
    """
    client_id = await get_secret_async("linkedin_client_id")
    redirect_uri = settings.LINKEDIN_REDIRECT_URI

    if not client_id:
        raise HTTPException(
            status_code=400, detail="LinkedIn Client ID not configured in Vault."
        )

    import urllib.parse
    import secrets
    import base64
    import json

    state_data = {"user_id": current_user.id, "csrf": secrets.token_urlsafe(16)}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    scope = "r_liteprofile r_emailaddress w_member_social"

    params = {
        "client_id": client_id,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }

    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{query_string}"
    return {"url": auth_url}


@router.get("/auth/linkedin/callback")
async def auth_linkedin_callback(code: str, state: str):
    """Handles the LinkedIn OAuth callback"""
    import httpx
    import json
    import base64

    try:
        state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
        user_id = state_data.get("user_id")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    client_id = get_secret("linkedin_client_id")
    client_secret = get_secret("linkedin_client_secret")
    redirect_uri = settings.LINKEDIN_REDIRECT_URI

    url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            token_data = response.json()

            if response.status_code != 200 or "access_token" not in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"LinkedIn Auth Failed: {token_data.get('error_description', 'Unknown error')}",
                )

            await token_manager.store_token(
                "linkedin",
                user_id,
                {
                    "access_token": token_data["access_token"],
                    "expires_in": token_data.get("expires_in", 3600),
                },
            )

            return {
                "status": "success",
                "message": "LinkedIn authenticated successfully",
                "user_id": user_id,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")


class PublishRequest(BaseModel):
    video_path: str
    niche: str
    platform: str = "YouTube Shorts"
    account_id: int | None = None
    inject_monetization: bool = False
    # A/B Testing Fields
    variant_b_title: str | None = None
    variant_b_description: str | None = None


class MultiPlatformPublishRequest(BaseModel):
    """Request for publishing to multiple platforms at once"""

    video_path: str
    niche: str
    platforms: list[str]  # list of platforms to publish to
    account_id: int | None = None
    inject_monetization: bool = False
    variant_b_title: str | None = None
    variant_b_description: str | None = None


@router.post("/package")
async def generate_package(
    niche: str,
    platform: str = "YouTube Shorts",
    current_user: UserDB = Depends(get_current_user),
):
    try:
        # Use authenticated user's ID
        content_id = str(current_user.id) + "-" + str(uuid.uuid4())[:8]
        package = await base_optimization_service.generate_viral_package(
            content_id, niche, platform
        )
        return package
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comments/{content_id}")
async def get_content_comments(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
):
    """
    Fetch comments for a published post.
    """
    try:
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.id == content_id,
            PublishedContentDB.user_id == current_user.id,
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(status_code=404, detail="Post not found")

        if not content.url:
            raise HTTPException(
                status_code=400, detail="Post has no URL (not published yet)"
            )

        # Extract Platform ID from URL
        platform_id = None
        platform_key = content.platform.lower()

        # YouTube Extraction
        if "youtube.com" in content.url or "youtu.be" in content.url:
            if "youtu.be" in content.url:
                platform_id = content.url.split("/")[-1].split("?")[0]
            else:
                # Handle various YouTube URL formats
                url_parts = content.url.split("/")
                for i, part in enumerate(url_parts):
                    if part == "watch" and i + 1 < len(url_parts):
                        platform_id = url_parts[i + 1].split("&")[0].split("?")[0]
                        break
                    elif (
                        part.startswith("UC") or len(part) == 11
                    ):  # Channel or video ID
                        platform_id = part.split("?")[0]
                        break
            platform_key = "youtube"

        # TikTok Extraction - handle multiple URL formats
        elif "tiktok.com" in content.url:
            url_clean = content.url.split("?")[0]  # Remove query params
            url_parts = url_clean.split("/")

            # Handle different TikTok URL patterns:
            # https://www.tiktok.com/@username/video/1234567890123456789
            # https://vm.tiktok.com/ZTR123abc/
            # https://www.tiktok.com/t/ZTR123abc/
            for part in reversed(url_parts):
                # TikTok video IDs are typically 19 digits long
                if part.isdigit() and len(part) >= 15:
                    platform_id = part
                    break
                # Handle share links like ZTR123abc
                elif len(part) >= 8 and any(c.isalnum() for c in part):
                    platform_id = part
                    break

            platform_key = "tiktok"

        if not platform_id:
            raise HTTPException(
                status_code=400, detail="Could not extract platform ID from URL"
            )

        # Fetch comments from platform
        comments = []

        if platform_key == "tiktok":
            comments = await base_tiktok_publisher.get_comments(
                platform_id, user_id=current_user.id, limit=limit
            )
        elif platform_key == "youtube":
            # YouTube comments would need separate implementation
            comments = []

        return {
            "platform": platform_key,
            "video_id": platform_id,
            "comments": comments,
            "total_count": len(comments),
        }

    finally:
        pass


@router.post("/sync/{content_id}")
async def sync_content_metrics(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Syncs live metrics from the social platform to the database for a specific post.
    """
    try:
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.id == content_id,
            PublishedContentDB.user_id == current_user.id,
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(status_code=404, detail="Post not found")

        if not content.url:
            raise HTTPException(
                status_code=400, detail="Post has no URL (not published yet)"
            )

        # Extract Platform ID from URL
        platform_id = None
        platform_key = content.platform.lower()

        # YouTube Extraction
        if "youtube.com" in content.url or "youtu.be" in content.url:
            if "youtu.be" in content.url:
                platform_id = content.url.split("/")[-1].split("?")[0]
            else:
                # Handle various YouTube URL formats
                url_parts = content.url.split("/")
                for i, part in enumerate(url_parts):
                    if part == "watch" and i + 1 < len(url_parts):
                        platform_id = url_parts[i + 1].split("&")[0].split("?")[0]
                        break
                    elif (
                        part.startswith("UC") or len(part) == 11
                    ):  # Channel or video ID
                        platform_id = part.split("?")[0]
                        break
            platform_key = "youtube"

        # TikTok Extraction - handle multiple URL formats
        elif "tiktok.com" in content.url:
            url_clean = content.url.split("?")[0]  # Remove query params
            url_parts = url_clean.split("/")

            # Handle different TikTok URL patterns:
            # https://www.tiktok.com/@username/video/1234567890123456789
            # https://vm.tiktok.com/ZTR123abc/
            # https://www.tiktok.com/t/ZTR123abc/
            for part in reversed(url_parts):
                # TikTok video IDs are typically 19 digits long
                if part.isdigit() and len(part) >= 15:
                    platform_id = part
                    break
                # Handle share links like ZTR123abc
                elif len(part) >= 8 and any(c.isalnum() for c in part):
                    platform_id = part
                    break

            platform_key = "tiktok"

        if not platform_id:
            raise HTTPException(
                status_code=400, detail="Could not extract platform ID from URL"
            )

        # Fetch metrics from platform
        metrics = {"views": 0, "likes": 0, "comments": 0, "shares": 0}

        if platform_key == "youtube":
            metrics = await base_youtube_publisher.get_metrics(
                platform_id, user_id=current_user.id
            )
        elif platform_key == "tiktok":
            metrics = await base_tiktok_publisher.get_metrics(
                platform_id, user_id=current_user.id
            )

        # Update Database
        old_views = content.view_count or 0
        content.view_count = metrics.get("views", 0)
        content.likes = metrics.get("likes", 0)
        content.comments = metrics.get("comments", 0)
        content.shares = metrics.get("shares", 0)

        # Record A/B test events if this post is part of an A/B test
        from src.api.utils.models import ABTestDB

        stmt_ab = select(ABTestDB).where(ABTestDB.content_id == str(content.id))
        result_ab = await db.execute(stmt_ab)
        ab_test = result_ab.scalar_one_or_none()
        if ab_test and not ab_test.completed_at:
            new_views = max(0, (content.view_count or 0) - old_views)
            if new_views > 0:
                # For now, we'll assume views are split 50/50 between variants
                # In a real implementation, you'd track which variant was actually shown
                variant_a_views = new_views // 2
                variant_b_views = new_views - variant_a_views

                ab_test.variant_a_views = (
                    ab_test.variant_a_views or 0
                ) + variant_a_views
                ab_test.variant_b_views = (
                    ab_test.variant_b_views or 0
                ) + variant_b_views

                # Record conversion events based on engagement
                engagement_score = (
                    (content.likes or 0)
                    + (content.comments or 0)
                    + (content.shares or 0)
                )
                if engagement_score > 0:
                    # Simple heuristic: treat engagement as conversions
                    conversions_a = engagement_score // 2
                    conversions_b = engagement_score - conversions_a
                    ab_test.variant_a_conversions = (
                        ab_test.variant_a_conversions or 0
                    ) + conversions_a
                    ab_test.variant_b_conversions = (
                        ab_test.variant_b_conversions or 0
                    ) + conversions_b

        await db.commit()
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        pass


@router.get("/history")
async def get_publish_history(
    current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(PublishedContentDB)
        if current_user.role != "admin":
            stmt = stmt.where(PublishedContentDB.user_id == current_user.id)

        stmt = stmt.order_by(PublishedContentDB.published_at.desc())
        result = await db.execute(stmt)
        history = result.scalars().all()
        return history
    finally:
        pass


@router.get("/scheduled")
async def get_scheduled_posts(
    current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get scheduled posts waiting for publish."""
    from src.api.utils.models import ScheduledPostDB
    import datetime

    try:
        stmt = select(ScheduledPostDB).where(
            ScheduledPostDB.user_id == current_user.id,
            ScheduledPostDB.scheduled_time > datetime.datetime.utcnow(),
        )
        stmt = stmt.order_by(ScheduledPostDB.scheduled_time.asc())
        result = await db.execute(stmt)
        scheduled = result.scalars().all()
        return [
            {
                "id": p.id,
                "video_path": p.video_path,
                "platform": p.platform,
                "scheduled_time": p.scheduled_time,
                "status": p.status,
                "parallel_allowed": p.parallel_allowed,
                "engagement_prediction": p.engagement_prediction,
                "optimal_rank": p.optimal_rank,
                "user_timezone": p.user_timezone,
                "error_message": p.error_message
            }
            for p in scheduled
        ]
    finally:
        pass



@router.get("/schedule/suggested-times")
async def get_suggested_times(
    count: int = Query(3, ge=1, le=10),
    current_user: UserDB = Depends(get_current_user),
):
    """Returns AI-suggested optimal posting windows."""
    try:
        suggestions = smart_scheduler.calculate_n_optimal_windows(str(current_user.id), count)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error getting suggested times: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate optimal windows")

@router.post("/schedule")
async def schedule_post(
    request: PublishRequest,
    scheduled_time: datetime.datetime,
    parallel_allowed: bool = False,
    user_timezone: str = "UTC",
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    credits_cost: int = Depends(credits_required("social_publish")),
):
    """
    Schedules a video for later publishing.
    """
    from src.api.utils.models import ScheduledPostDB

    try:
        prediction = smart_scheduler.predict_engagement(str(current_user.id), scheduled_time)
        # Consume credits
        await credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action="social_publish",
            db=db,
            description=f"Scheduled post for {request.platform}",
        )
        # Generate metadata for the scheduled post
        content_id = str(uuid.uuid4())
        metadata = await base_optimization_service.generate_viral_package(
            content_id, request.niche, request.platform
        )

        new_schedule = ScheduledPostDB(
            video_path=request.video_path,
            platform=request.platform,
            scheduled_time=scheduled_time,
            status="PENDING",
            parallel_allowed=parallel_allowed,
            user_timezone=user_timezone,
            engagement_prediction=prediction,
            metadata_json=metadata.dict() if hasattr(metadata, "dict") else metadata,
            account_id=request.account_id,
            user_id=current_user.id
        )
            account_id=request.account_id,
            user_id=current_user.id,
        )
        db.add(new_schedule)
        await db.commit()
        return {"status": "success", "message": f"Scheduled for {scheduled_time}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        pass


@router.post("/post")
async def publish_video(
    request: PublishRequest,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    credits_cost: int = Depends(credits_required("social_publish")),
):
    from src.api.utils.models import PublishedContentDB, ABTestDB

    try:
        # Consume credits
        await credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action="social_publish",
            db=db,
            description=f"Direct post to {request.platform}",
        )

        # 1. Generate SEO package
        content_id = str(uuid.uuid4())
        metadata = await base_optimization_service.generate_viral_package(
            content_id, request.niche, request.platform
        )

        # 2. Affiliate Injection
        if request.inject_monetization:
            from src.api.utils.models import AffiliateLinkDB
            from src.services.monetization.service import base_monetization_engine

            # First, try AI-powered recommendations
            try:
                script_text = metadata.description or ""
                recommendations = await base_monetization_engine.recommend_products(
                    request.niche, script_text
                )

                if recommendations:
                    # Use the top AI recommendation
                    top_rec = recommendations[0]
                    injection_text = f"\n\n🔥 {top_rec.get('cta_text', 'Check this out')}: {top_rec.get('link', '')}"
                    metadata.description += injection_text
                    logger.info(
                        f"[Monetization] AI Recommended: {top_rec.get('name', 'Product')}"
                    )
                else:
                    # Fallback to database
                    stmt_aff = (
                        select(AffiliateLinkDB)
                        .where(AffiliateLinkDB.niche == request.niche)
                        .order_by(AffiliateLinkDB.created_at.desc())
                        .limit(1)
                    )
                    res_aff = await db.execute(stmt_aff)
                    aff_link = res_aff.scalar_one_or_none()
                    if aff_link:
                        injection_text = f"\n\n🔥 {aff_link.cta_text or 'Check this out'}: {aff_link.link}"
                        metadata.description += injection_text
                        logger.info(
                            f"[Monetization] Injected link: {aff_link.product_name}"
                        )
            except Exception as e:
                # Fallback to database on any error
                logger.warning(f"[Monetization] AI recommendation failed: {e}")
                stmt_aff = (
                    select(AffiliateLinkDB)
                    .where(AffiliateLinkDB.niche == request.niche)
                    .order_by(AffiliateLinkDB.created_at.desc())
                    .limit(1)
                )
                res_aff = await db.execute(stmt_aff)
                aff_link = res_aff.scalar_one_or_none()
                if aff_link:
                    injection_text = f"\n\n🔥 {aff_link.cta_text or 'Check this out'}: {aff_link.link}"
                    metadata.description += injection_text
                    logger.info(
                        f"[Monetization] Injected link: {aff_link.product_name}"
                    )

        # 3. Upload (Using Variant A Title as default)
        url = None

        # Determine platform type from platform name
        platform_lower = request.platform.lower()

        # Map platform names to platform keys
        platform_map = {
            "youtube shorts": "youtube",
            "youtube video": "youtube",
            "youtube": "youtube",
            "tiktok": "tiktok",
            "tiktok video": "tiktok",
            "instagram reels": "instagram",
            "instagram video": "instagram",
            "instagram": "instagram",
            "facebook reels": "facebook",
            "facebook video": "facebook",
            "facebook": "facebook",
            "x video": "x",
            "x": "x",
            "twitter": "x",
            "linkedin video": "linkedin",
            "linkedin": "linkedin",
            "snapchat spotlight": "snapchat",
            "snapchat": "snapchat",
            "twitch clip": "twitch",
            "twitch": "twitch",
        }

        platform_key = platform_map.get(platform_lower, platform_lower)

        if platform_key not in SUPPORTED_PLATFORMS:
            raise HTTPException(
                status_code=400,
                detail=f"Platform '{request.platform}' not supported. Available: {', '.join(SUPPORTED_PLATFORMS.keys())}",
            )

        platform_info = SUPPORTED_PLATFORMS[platform_key]

        # Check if platform supports monetization
        if request.inject_monetization and not platform_info.get("monetization", False):
            return {
                "status": "warning",
                "message": f"{platform_info['name']} does not support monetization. Publishing without affiliate links.",
                "url": None,
            }

        # === CHECK PLATFORM AUTHENTICATION ===
        from src.services.optimization.auth import token_manager

        has_auth = (
            await token_manager.get_token(
                platform_key, user_id=current_user.id, account_id=request.account_id
            )
            is not None
        )

        retention_hours = 3  # Default retention for pending videos

        if not has_auth:
            # Platform not authenticated - check if monetization is required
            if request.inject_monetization:
                # Monetization requires authentication - store for deletion
                from datetime import datetime, timedelta

                delete_at = datetime.utcnow() + timedelta(hours=retention_hours)

                # Store as pending_auth with auto-deletion
                new_post = PublishedContentDB(
                    title=metadata.title or "Viral Post",
                    platform=request.platform,
                    status="PENDING_AUTH",  # Special status for pending auth
                    url=None,
                    account_id=request.account_id,
                    user_id=current_user.id,
                    niche=request.niche,
                    # Store retention info in metadata
                    metadata={
                        "video_path": request.video_path,
                        "delete_at": delete_at.isoformat(),
                        "retention_hours": retention_hours,
                        "requires_auth": True,
                        "platform_key": platform_key,
                    },
                )
                db.add(new_post)
                await db.commit()

                return {
                    "status": "pending_auth",
                    "message": f"Platform '{platform_info['name']}' not authenticated. Video will be deleted in {retention_hours} hours. Please authenticate to publish with monetization.",
                    "video_id": new_post.id,
                    "delete_at": delete_at.isoformat(),
                    "auth_url": f"/publish/auth/{platform_key}",
                    "requires_auth": True,
                }
            else:
                # No monetization - just fail the upload
                return {
                    "status": "error",
                    "message": f"Platform '{platform_info['name']}' not authenticated. Please authenticate first.",
                    "auth_url": f"/publish/auth/{platform_key}",
                    "requires_auth": True,
                }

        # === AUTHENTICATED - PROCEED WITH UPLOAD ===
        if platform_key == "youtube":
            url = await base_youtube_publisher.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        elif platform_key == "tiktok":
            from src.services.optimization.tiktok_publisher import base_tiktok_publisher

            url = await base_tiktok_publisher.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        elif platform_key == "instagram":
            from src.services.optimization.instagram_publisher import (
                base_instagram_publisher,
            )

            url = await base_instagram_publisher.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        elif platform_key == "facebook":
            from src.services.optimization.facebook_publisher import base_facebook_publisher

            url = await base_facebook_publisher.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        elif platform_key == "x":
            from src.services.optimization.x_publisher import base_x_publisher

            url = await base_x_publisher.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        elif platform_key == "linkedin":
            from src.services.optimization.linkedin_publisher import base_linkedin_publisher

            url = await base_linkedin_publisher.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        else:
            raise HTTPException(
                status_code=501,
                detail=f"Publisher for platform '{platform_key}' is not yet implemented. "
                f"Supported platforms: youtube, tiktok, instagram, facebook, x, linkedin",
            )

        # 4. Record History
        new_post = PublishedContentDB(
            title=metadata.title or "Viral Post",
            platform=request.platform,
            status="Published" if url else "Failed",
            url=url,
            account_id=request.account_id,
            user_id=current_user.id,
            niche=request.niche,
        )
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)

        # 5. Initialize A/B Test if requested
        if request.variant_b_title:
            new_test = ABTestDB(
                content_id=str(new_post.id),
                variant_a_title=metadata.title,
                variant_b_title=request.variant_b_title,
                variant_a_views=0,
                variant_b_views=0,
                variant_a_conversions=0,
                variant_b_conversions=0,
                status="active",
            )
            db.add(new_test)
            await db.commit()
            logger.info(f"[A/B Testing] Initialized test for post {new_post.id}")

            # Record initial view event for variant A (assuming it gets shown first)
            from src.api.routes.ab_testing import router as ab_router
            # We'll use the existing event recording endpoint
            # For now, just initialize the counters - real tracking would need frontend integration

        return {"status": "success", "url": url, "metadata": metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        pass


@router.post("/post-multi")
async def publish_multi_platform(
    request: MultiPlatformPublishRequest,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Publish video to multiple platforms at once.
    - Authenticated platforms will be published immediately
    - Unauthenticated platforms will be stored as PENDING_AUTH (deleted after 3 hours)
    """
    from src.api.utils.models import PublishedContentDB
    from src.services.optimization.service import base_optimization_service
    from src.services.optimization.auth import token_manager

    try:
        results = {"published": [], "pending_auth": [], "failed": []}

        retention_hours = 3

        for platform_name in request.platforms:
            try:
                # Map platform name to key
                platform_lower = platform_name.lower()
                platform_map = {
                    "youtube shorts": "youtube",
                    "youtube video": "youtube",
                    "youtube": "youtube",
                    "tiktok": "tiktok",
                    "tiktok video": "tiktok",
                    "instagram reels": "instagram",
                    "instagram video": "instagram",
                    "instagram": "instagram",
                    "facebook reels": "facebook",
                    "facebook video": "facebook",
                    "facebook": "facebook",
                    "x video": "x",
                    "x": "x",
                    "twitter": "x",
                    "linkedin video": "linkedin",
                    "linkedin": "linkedin",
                    "snapchat spotlight": "snapchat",
                    "snapchat": "snapchat",
                    "twitch clip": "twitch",
                    "twitch": "twitch",
                }
                platform_key = platform_map.get(platform_lower, platform_lower)

                if platform_key not in SUPPORTED_PLATFORMS:
                    results["failed"].append(
                        {"platform": platform_name, "error": "Platform not supported"}
                    )
                    continue

                platform_info = SUPPORTED_PLATFORMS[platform_key]

                # Check authentication
                has_auth = (
                    await token_manager.get_token(platform_key, user_id=current_user.id)
                    is not None
                )

                # Generate metadata for this platform
                content_id = str(uuid.uuid4())
                metadata = await base_optimization_service.generate_viral_package(
                    content_id, request.niche, platform_name
                )

                if has_auth:
                    # Authenticated - try to upload
                    url = None
                    try:
                        if platform_key == "youtube":
                            url = await base_youtube_publisher.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "tiktok":
                            from src.services.optimization.tiktok_publisher import (
                                base_tiktok_publisher,
                            )

                            url = await base_tiktok_publisher.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "instagram":
                            from src.services.optimization.instagram_publisher import (
                                base_instagram_publisher,
                            )

                            url = await base_instagram_publisher.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "facebook":
                            from src.services.optimization.facebook_publisher import (
                                base_facebook_publisher,
                            )

                            url = await base_facebook_publisher.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "x":
                            from src.services.optimization.x_publisher import (
                                base_x_publisher,
                            )

                            url = await base_x_publisher.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "linkedin":
                            from src.services.optimization.linkedin_publisher import (
                                base_linkedin_publisher,
                            )

                            url = await base_linkedin_publisher.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                    except Exception as e:
                        logging.error(
                            f"Multi-platform upload failed for {platform_key}: {e}"
                        )

                    if url:
                        # Record success
                        new_post = PublishedContentDB(
                            title=metadata.title or "Viral Post",
                            platform=platform_name,
                            status="Published",
                            url=url,
                            user_id=current_user.id,
                            niche=request.niche,
                        )
                        db.add(new_post)
                        await db.commit()

                        results["published"].append(
                            {
                                "platform": platform_name,
                                "url": url,
                                "status": "published",
                            }
                        )
                    else:
                        results["failed"].append(
                            {"platform": platform_name, "error": "Upload failed"}
                        )
                else:
                    # Not authenticated - store as pending
                    from datetime import datetime, timedelta

                    delete_at = datetime.utcnow() + timedelta(hours=retention_hours)

                    # Monetization check
                    if request.inject_monetization and not platform_info.get(
                        "monetization", False
                    ):
                        results["failed"].append(
                            {
                                "platform": platform_name,
                                "error": f"{platform_info['name']} does not support monetization",
                            }
                        )
                        continue

                    new_post = PublishedContentDB(
                        title=metadata.title or "Viral Post",
                        platform=platform_name,
                        status="PENDING_AUTH",
                        url=None,
                        user_id=current_user.id,
                        niche=request.niche,
                        metadata={
                            "video_path": request.video_path,
                            "delete_at": delete_at.isoformat(),
                            "retention_hours": retention_hours,
                            "requires_auth": True,
                            "platform_key": platform_key,
                            "inject_monetization": request.inject_monetization,
                        },
                    )
                    db.add(new_post)
                    await db.commit()

                    results["pending_auth"].append(
                        {
                            "platform": platform_name,
                            "video_id": new_post.id,
                            "delete_at": delete_at.isoformat(),
                            "auth_url": f"/publish/auth/{platform_key}",
                        }
                    )

            except Exception as e:
                results["failed"].append({"platform": platform_name, "error": str(e)})

        return {
            "status": "completed",
            "total_platforms": len(request.platforms),
            "published_count": len(results["published"]),
            "pending_count": len(results["pending_auth"]),
            "failed_count": len(results["failed"]),
            "results": results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        pass


# ─── opencli-rs Enhanced Publishing ────────────────────────────────────
# These endpoints allow publishing via the user's own Chrome sessions
# instead of platform OAuth APIs.


class OpenCLIPostRequest(BaseModel):
    platform: str
    content: str
    media_url: str | None = None


@router.post("/opencli/post")
async def opencli_post(
    request: OpenCLIPostRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """Post content to a platform using the user's Chrome session (via opencli-rs).

    This is an alternative to OAuth-based publishing. The user must have
    a connected session for the platform via /opencli/sessions/connect.
    """
    from src.api.config import settings
    from src.services.opencli.service import opencli_service

    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    platform = request.platform.lower()
    result = await opencli_service.post_to_platform(
        current_user.id, platform, request.content, request.media_url
    )

    if result.get("success"):
        # Record in DB
        from src.api.utils.database import async_session_factory

        async with async_session_factory() as db:
            try:
                post = PublishedContentDB(
                    title=request.content[:100],
                    platform=platform,
                    status="Published",
                    url=result.get("url", ""),
                    account_id=0,  # opencli posts don't use OAuth accounts
                    user_id=current_user.id,
                )
                db.add(post)
                await db.commit()
            finally:
                pass

    return result


@router.post("/opencli/post-multi")
async def opencli_post_multi(
    platforms: list[str],
    content: str,
    media_url: str | None = None,
    current_user: UserDB = Depends(get_current_user),
):
    """Post to multiple platforms using the user's Chrome sessions."""
    from src.api.config import settings
    from src.services.opencli.service import opencli_service

    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    import asyncio

    tasks = []
    for platform in platforms:
        tasks.append(
            opencli_service.post_to_platform(
                current_user.id, platform.lower(), content, media_url
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for platform, result in zip(platforms, results):
        if isinstance(result, Exception):
            output.append(
                {"platform": platform, "success": False, "error": str(result)}
            )
        else:
            output.append({"platform": platform, **result})

    return {"results": output}
