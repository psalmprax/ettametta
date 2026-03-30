"""
Webhooks API Routes for Viral Forge
Handles callbacks from YouTube, TikTok, and other platforms
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from api.utils.database import SessionLocal
from api.utils.models import VideoJobDB, PublishedContentDB
from datetime import datetime
import logging

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# === YouTube Webhooks ===

class YouTubeWebhookPayload(BaseModel):
    video_id: str
    status: str  # processing, ready, failed
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    error_message: Optional[str] = None


@router.post("/youtube/upload-status")
async def youtube_upload_status(
    payload: YouTubeWebhookPayload,
    request: Request
):
    """
    Receive upload status updates from YouTube
    Called by YouTube's pubhubsubbub or video processing callbacks
    """
    db = SessionLocal()
    try:
        # Find the published content by video_id or external_id
        content = db.query(PublishedContentDB).filter(
            PublishedContentDB.external_video_id == payload.video_id
        ).first()
        
        if not content:
            # Also try to find by title match
            content = db.query(PublishedContentDB).filter(
                PublishedContentDB.title.ilike(f"%{payload.title}%") if payload.title else False
            ).first()
        
        if content:
            # Update status based on YouTube response
            if payload.status == "ready":
                content.status = "published"
                content.published_at = datetime.utcnow()
            elif payload.status == "failed":
                content.status = "failed"
            
            # Update metadata if provided
            if payload.thumbnail_url:
                content.thumbnail_url = payload.thumbnail_url
            
            # Store additional metadata
            metadata = content.metadata or {}
            metadata["youtube_status"] = payload.status
            metadata["youtube_duration"] = payload.duration
            if payload.error_message:
                metadata["youtube_error"] = payload.error_message
            content.metadata = metadata
            
            db.commit()
            
            return {"status": "success", "message": f"Updated video {payload.video_id} status to {payload.status}"}
        
        return {"status": "not_found", "message": "Video not found"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# === TikTok Webhooks ===

class TikTokWebhookPayload(BaseModel):
    video_id: str
    status: str  # uploaded, processing, published, failed
    share_url: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    error_message: Optional[str] = None


@router.post("/tiktok/upload-status")
async def tiktok_upload_status(
    payload: TikTokWebhookPayload,
    request: Request
):
    """
    Receive upload status updates from TikTok
    """
    db = SessionLocal()
    try:
        content = db.query(PublishedContentDB).filter(
            PublishedContentDB.external_video_id == payload.video_id
        ).first()
        
        if not content:
            content = db.query(PublishedContentDB).filter(
                PublishedContentDB.platform == "tiktok"
            ).order_by(PublishedContentDB.created_at.desc()).first()
        
        if content:
            if payload.status == "published":
                content.status = "published"
                content.published_at = datetime.utcnow()
            elif payload.status == "failed":
                content.status = "failed"
            
            if payload.share_url:
                content.url = payload.share_url
            
            # Update metrics
            metrics = content.metrics or {}
            if payload.view_count is not None:
                metrics["views"] = payload.view_count
            if payload.like_count is not None:
                metrics["likes"] = payload.like_count
            if payload.comment_count is not None:
                metrics["comments"] = payload.comment_count
            
            # Store TikTok-specific metadata
            metadata = content.metadata or {}
            metadata["tiktok_status"] = payload.status
            if payload.error_message:
                metadata["tiktok_error"] = payload.error_message
            content.metadata = metadata
            
            db.commit()
            
            return {"status": "success", "message": f"Updated TikTok video {payload.video_id} status to {payload.status}"}
        
        return {"status": "not_found", "message": "Video not found"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# === Generic Platform Webhook ===

class GenericPlatformWebhookPayload(BaseModel):
    platform: str  # youtube, tiktok, instagram, etc.
    external_id: str
    status: str
    metadata: Optional[Dict[str, Any]] = None


@router.post("/platform-status")
async def generic_platform_status(
    payload: GenericPlatformWebhookPayload,
    request: Request
):
    """
    Generic webhook for any platform status updates
    """
    db = SessionLocal()
    try:
        content = db.query(PublishedContentDB).filter(
            PublishedContentDB.external_video_id == payload.external_id,
            PublishedContentDB.platform == payload.platform
        ).first()
        
        if content:
            if payload.status in ["published", "ready", "success"]:
                content.status = "published"
                content.published_at = datetime.utcnow()
            elif payload.status in ["failed", "error"]:
                content.status = "failed"
            
            # Merge metadata
            if payload.metadata:
                existing_metadata = content.metadata or {}
                existing_metadata.update(payload.metadata)
                content.metadata = existing_metadata
            
            db.commit()
            
            return {"status": "success", "message": f"Updated {payload.platform} video status"}
        
        return {"status": "not_found", "message": "Video not found"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# === Webhook Verification ===

@router.get("/verify")
async def verify_webhook(request: Request):
    """
    Verify webhook endpoint is active
    """
    return {
        "status": "active",
        "endpoints": {
            "youtube": "/webhooks/youtube/upload-status",
            "tiktok": "/webhooks/tiktok/upload-status",
            "generic": "/webhooks/platform-status"
        }
    }
