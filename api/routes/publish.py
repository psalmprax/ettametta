from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.responses import RedirectResponse
from typing import List, Optional
from services.optimization.service import base_optimization_service
from services.optimization.youtube_publisher import base_youtube_publisher
from services.optimization.models import PostMetadata
from services.optimization.auth import token_manager
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
from api.config import settings
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
# from api.utils.user_models import UserDB # Deprecated import
from api.utils.database import SessionLocal
from api.utils.models import SocialAccount, PublishedContentDB
import datetime

router = APIRouter(prefix="/publish", tags=["Publishing"])

# OAuth Scopes for YouTube
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

@router.get("/auth/youtube")
async def auth_youtube():
    """
    Starts the YouTube OAuth flow.
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=YOUTUBE_SCOPES
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    authorization_url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true")
    return RedirectResponse(authorization_url)

@router.get("/auth/youtube/callback")
async def auth_youtube_callback(code: str, state: str):
    """
    Handles the YouTube OAuth callback.
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=YOUTUBE_SCOPES
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    token_manager.store_token("youtube", {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_type": "Bearer",
        "expires_in": credentials.expiry.replace(tzinfo=datetime.timezone.utc).timestamp() - datetime.datetime.now(datetime.timezone.utc).timestamp() if credentials.expiry else 3600
    })
    
    return {"status": "success", "message": "YouTube authenticated successfully"}

@router.get("/accounts")
async def list_accounts(current_user: UserDB = Depends(get_current_user)):
    db = SessionLocal()
    try:
        query = db.query(SocialAccount)
        if current_user.role != "admin":
            query = query.filter(SocialAccount.user_id == current_user.id)
        accounts = query.all()
        return [{"id": a.id, "platform": a.platform, "username": a.username, "updated_at": a.updated_at} for a in accounts]
    finally:
        db.close()

@router.delete("/account/{account_id}")
async def delete_account(account_id: int, current_user: UserDB = Depends(get_current_user)):
    db = SessionLocal()
    try:
        account = db.query(SocialAccount).filter(SocialAccount.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Isolation check
        if account.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to delete this account")
            
        db.delete(account)
        db.commit()
        return {"status": "success", "message": "Account unlinked"}
    finally:
        db.close()

# TikTok OAuth
@router.get("/auth/tiktok")
async def auth_tiktok():
    """
    Starts the TikTok OAuth flow.
    """
    client_key = settings.TIKTOK_CLIENT_KEY
    redirect_uri = settings.TIKTOK_REDIRECT_URI
    scope = "video.upload,user.info.basic"
    # Basic validation to prevent crashing if keys are missing
    import urllib.parse
    import secrets
    
    # State parameter for CSRF protection
    state = secrets.token_urlsafe(16)
    
    params = {
        "client_key": client_key,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state
    }
    
    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://www.tiktok.com/v2/auth/authorize?{query_string}"
    return RedirectResponse(auth_url)

@router.get("/auth/tiktok/callback")
async def auth_tiktok_callback(code: str):
    """
    Handles the TikTok OAuth callback and exchanges code for a real token.
    """
    import httpx
    
    # TikTok Token Exchange URL (v2)
    # Note: TikTok uses a specific content-type and parameters
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    
    data = {
        "client_key": settings.TIKTOK_CLIENT_KEY,
        "client_secret": settings.TIKTOK_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.TIKTOK_REDIRECT_URI
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            token_data = response.json()
            
            if response.status_code != 200 or "access_token" not in token_data:
                raise HTTPException(status_code=400, detail=f"TikTok Auth Failed: {token_data.get('error_description', 'Unknown error')}")
            
            # Extract common fields
            # v2 response usually includes access_token, refresh_token, open_id, scope, expires_in
            token_manager.store_token("tiktok", {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "open_id": token_data.get("open_id"),
                "expires_in": token_data.get("expires_in", 3600),
                "scope": token_data.get("scope")
            })
            
            return {"status": "success", "message": "TikTok authenticated successfully"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")

class PublishRequest(BaseModel):
    video_path: str
    niche: str
    platform: str = "YouTube Shorts"
    account_id: Optional[int] = None
    inject_monetization: bool = False
    # A/B Testing Fields
    variant_b_title: Optional[str] = None
    variant_b_description: Optional[str] = None

@router.post("/package")
async def generate_package(niche: str, platform: str = "YouTube Shorts"):
    try:
        package = await base_optimization_service.generate_viral_package("dummy_id", niche, platform)
        return package
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_publish_history(current_user: UserDB = Depends(get_current_user)):
    db = SessionLocal()
    try:
        query = db.query(PublishedContentDB)
        if current_user.role != "admin":
            query = query.filter(PublishedContentDB.user_id == current_user.id)
            
        history = query.order_by(PublishedContentDB.published_at.desc()).all()
        return history
    finally:
        db.close()

@router.post("/schedule")
async def schedule_post(request: PublishRequest, scheduled_time: datetime.datetime, current_user: UserDB = Depends(get_current_user)):
    """
    Schedules a video for later publishing.
    """
    from api.utils.database import SessionLocal
    from api.utils.models import ScheduledPostDB
    db = SessionLocal()
    try:
        # Re-use viral package generation for consistency
        metadata = await base_optimization_service.generate_viral_package("dummy_id", request.niche, request.platform)
        
        new_schedule = ScheduledPostDB(
            video_path=request.video_path,
            platform=request.platform,
            scheduled_time=scheduled_time,
            status="PENDING",
            metadata_json=metadata.dict(),
            account_id=request.account_id,
            user_id=current_user.id
        )
        db.add(new_schedule)
        db.commit()
        return {"status": "success", "message": f"Scheduled for {scheduled_time}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/post")
async def publish_video(request: PublishRequest, current_user: UserDB = Depends(get_current_user)):
    from api.utils.database import SessionLocal
    from api.utils.models import PublishedContentDB, ABTestDB
    db = SessionLocal()
    try:
        # 1. Generate SEO package
        metadata = await base_optimization_service.generate_viral_package("dummy_id", request.niche, request.platform)
        
        # 2. Affiliate Injection
        if request.inject_monetization:
            from api.utils.models import AffiliateLinkDB
            # Fetch most recent link for this niche
            aff_link = db.query(AffiliateLinkDB).filter(AffiliateLinkDB.niche == request.niche).order_by(AffiliateLinkDB.created_at.desc()).first()
            if aff_link:
                injection_text = f"\n\n🔥 {aff_link.cta_text or 'Check this out'}: {aff_link.link}"
                metadata.description += injection_text
                print(f"[Monetization] Injected link: {aff_link.product_name}")
        
        # 3. Upload (Using Variant A Title as default)
        url = None
        if request.platform == "YouTube Shorts":
            url = await base_youtube_publisher.upload_video(request.video_path, metadata, account_id=request.account_id)
        elif request.platform == "TikTok":
            from services.optimization.tiktok_publisher import base_tiktok_publisher
            url = await base_tiktok_publisher.upload_video(request.video_path, metadata, account_id=request.account_id)
        else:
            raise HTTPException(status_code=400, detail="Platform not supported yet")
            
        # 4. Record History
        new_post = PublishedContentDB(
            title=metadata.title or "Viral Post",
            platform=request.platform,
            status="Published" if url else "Failed",
            url=url,
            account_id=request.account_id,
            user_id=current_user.id,
            niche=request.niche
        )
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        
        # 5. Initialize A/B Test if requested
        if request.variant_b_title:
            new_test = ABTestDB(
                content_id=str(new_post.id),
                variant_a_title=metadata.title,
                variant_b_title=request.variant_b_title
            )
            db.add(new_test)
            db.commit()
            print(f"[A/B Testing] Initialized test for post {new_post.id}")

        return {"status": "success", "url": url, "metadata": metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
