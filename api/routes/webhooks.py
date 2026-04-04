"""
Webhooks API Routes for Viral Forge
Handles callbacks from YouTube, TikTok, and other platforms with proper security
"""

from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any
from api.utils.database import SessionLocal
from api.utils.models import PublishedContentDB, WebhookEventDB
from datetime import datetime
import hashlib
import hmac
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _verify_signature(payload: bytes, signature: Optional[str], secret: str) -> bool:
    """Verify webhook signature using HMAC-SHA256"""
    if not signature:
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def _check_idempotency(db, event_type: str, external_id: str, platform: str) -> bool:
    """Check if this event was already processed"""
    existing = (
        db.query(WebhookEventDB)
        .filter(
            WebhookEventDB.event_type == event_type,
            WebhookEventDB.external_id == external_id,
            WebhookEventDB.platform == platform,
            WebhookEventDB.processed_at.isnot(None),
        )
        .first()
    )
    return existing is not None


def _record_event(db, event_type: str, external_id: str, platform: str, payload: dict):
    """Record webhook event for idempotency"""
    event = WebhookEventDB(
        event_type=event_type,
        external_id=external_id,
        platform=platform,
        payload_json=json.dumps(payload),
        processed_at=datetime.utcnow(),
    )
    db.add(event)


# === YouTube Webhooks ===


class YouTubeWebhookPayload(BaseModel):
    video_id: str
    status: str  # processing, ready, failed
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    error_message: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ["processing", "ready", "failed"]:
            raise ValueError("Status must be processing, ready, or failed")
        return v


@router.post("/youtube/upload-status")
async def youtube_upload_status(
    payload: YouTubeWebhookPayload,
    request: Request,
    x_youtube_signature: Optional[str] = Header(None, alias="X-Youtube-Signature"),
):
    """
    Receive upload status updates from YouTube
    Requires signature verification if configured
    """
    from api.config import settings

    body = await request.body()

    if settings.YOUTUBE_WEBHOOK_SECRET:
        if not _verify_signature(
            body, x_youtube_signature, settings.YOUTUBE_WEBHOOK_SECRET
        ):
            logger.warning("[Webhooks] YouTube signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")

    db = SessionLocal()
    try:
        if _check_idempotency(db, "youtube_upload_status", payload.video_id, "youtube"):
            logger.info(
                f"[Webhooks] YouTube event {payload.video_id} already processed (idempotency)"
            )
            return {"status": "already_processed", "message": "Event already handled"}

        content = (
            db.query(PublishedContentDB)
            .filter(PublishedContentDB.external_video_id == payload.video_id)
            .first()
        )

        if not content and payload.title:
            content = (
                db.query(PublishedContentDB)
                .filter(PublishedContentDB.title.ilike(f"%{payload.title}%"))
                .first()
            )

        if content:
            old_status = content.status

            if payload.status == "ready":
                content.status = "published"
                content.published_at = datetime.utcnow()
            elif payload.status == "failed":
                content.status = "failed"

            if payload.thumbnail_url:
                content.thumbnail_url = payload.thumbnail_url

            metadata = content.metadata or {}
            metadata["youtube_status"] = payload.status
            metadata["youtube_duration"] = payload.duration
            if payload.error_message:
                metadata["youtube_error"] = payload.error_message
            if payload.description:
                metadata["youtube_description"] = payload.description
            content.metadata = metadata

            _record_event(
                db,
                "youtube_upload_status",
                payload.video_id,
                "youtube",
                payload.model_dump(),
            )
            db.commit()

            logger.info(
                f"[Webhooks] YouTube video {payload.video_id} status: {old_status} -> {content.status}"
            )
            return {
                "status": "success",
                "message": f"Updated video {payload.video_id} to {payload.status}",
            }

        logger.warning(f"[Webhooks] YouTube video {payload.video_id} not found")
        return {"status": "not_found", "message": "Video not found"}

    except Exception as e:
        db.rollback()
        logger.error(f"[Webhooks] YouTube webhook error: {e}")
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

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ["uploaded", "processing", "published", "failed"]:
            raise ValueError("Invalid status")
        return v


@router.post("/tiktok/upload-status")
async def tiktok_upload_status(
    payload: TikTokWebhookPayload,
    request: Request,
    x_tiktok_signature: Optional[str] = Header(None, alias="X-Tiktok-Signature"),
):
    """
    Receive upload status updates from TikTok
    """
    from api.config import settings

    body = await request.body()

    if settings.TIKTOK_WEBHOOK_SECRET:
        if not _verify_signature(
            body, x_tiktok_signature, settings.TIKTOK_WEBHOOK_SECRET
        ):
            logger.warning("[Webhooks] TikTok signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")

    db = SessionLocal()
    try:
        if _check_idempotency(db, "tiktok_upload_status", payload.video_id, "tiktok"):
            logger.info(f"[Webhooks] TikTok event {payload.video_id} already processed")
            return {"status": "already_processed", "message": "Event already handled"}

        content = (
            db.query(PublishedContentDB)
            .filter(PublishedContentDB.external_video_id == payload.video_id)
            .first()
        )

        if not content:
            content = (
                db.query(PublishedContentDB)
                .filter(PublishedContentDB.platform == "tiktok")
                .order_by(PublishedContentDB.created_at.desc())
                .first()
            )

        if content:
            old_status = content.status

            if payload.status == "published":
                content.status = "published"
                content.published_at = datetime.utcnow()
            elif payload.status == "failed":
                content.status = "failed"

            if payload.share_url:
                content.url = payload.share_url

            metrics = content.metrics or {}
            if payload.view_count is not None:
                metrics["views"] = payload.view_count
            if payload.like_count is not None:
                metrics["likes"] = payload.like_count
            if payload.comment_count is not None:
                metrics["comments"] = payload.comment_count
            content.metrics = metrics

            metadata = content.metadata or {}
            metadata["tiktok_status"] = payload.status
            if payload.error_message:
                metadata["tiktok_error"] = payload.error_message
            content.metadata = metadata

            _record_event(
                db,
                "tiktok_upload_status",
                payload.video_id,
                "tiktok",
                payload.model_dump(),
            )
            db.commit()

            logger.info(
                f"[Webhooks] TikTok video {payload.video_id} status: {old_status} -> {content.status}"
            )
            return {
                "status": "success",
                "message": f"Updated TikTok video to {payload.status}",
            }

        logger.warning(f"[Webhooks] TikTok video {payload.video_id} not found")
        return {"status": "not_found", "message": "Video not found"}

    except Exception as e:
        db.rollback()
        logger.error(f"[Webhooks] TikTok webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# === Generic Platform Webhook ===


class GenericPlatformWebhookPayload(BaseModel):
    platform: str
    external_id: str
    status: str
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        valid_platforms = [
            "youtube",
            "tiktok",
            "instagram",
            "facebook",
            "linkedin",
            "x",
        ]
        if v.lower() not in valid_platforms:
            raise ValueError(f"Invalid platform. Must be one of: {valid_platforms}")
        return v.lower()


@router.post("/platform-status")
async def generic_platform_status(
    payload: GenericPlatformWebhookPayload,
    request: Request,
    x_platform_signature: Optional[str] = Header(None, alias="X-Platform-Signature"),
):
    """
    Generic webhook for any platform status updates
    """
    from api.config import settings

    webhook_secret = getattr(
        settings, f"{payload.platform.upper()}_WEBHOOK_SECRET", None
    )

    body = await request.body()

    if webhook_secret:
        if not _verify_signature(body, x_platform_signature, webhook_secret):
            logger.warning(
                f"[Webhooks] {payload.platform} signature verification failed"
            )
            raise HTTPException(status_code=401, detail="Invalid signature")

    db = SessionLocal()
    try:
        event_key = f"{payload.platform}_{payload.status}"
        if _check_idempotency(db, event_key, payload.external_id, payload.platform):
            return {"status": "already_processed", "message": "Event already handled"}

        content = (
            db.query(PublishedContentDB)
            .filter(
                PublishedContentDB.external_video_id == payload.external_id,
                PublishedContentDB.platform == payload.platform,
            )
            .first()
        )

        if content:
            old_status = content.status

            if payload.status in ["published", "ready", "success"]:
                content.status = "published"
                content.published_at = datetime.utcnow()
            elif payload.status in ["failed", "error"]:
                content.status = "failed"

            if payload.metadata:
                existing_metadata = content.metadata or {}
                existing_metadata.update(payload.metadata)
                content.metadata = existing_metadata

            _record_event(
                db,
                event_key,
                payload.external_id,
                payload.platform,
                payload.model_dump(),
            )
            db.commit()

            logger.info(
                f"[Webhooks] {payload.platform} video {payload.external_id} status: {old_status} -> {content.status}"
            )
            return {
                "status": "success",
                "message": f"Updated {payload.platform} video status",
            }

        logger.warning(
            f"[Webhooks] {payload.platform} video {payload.external_id} not found"
        )
        return {"status": "not_found", "message": "Video not found"}

    except Exception as e:
        db.rollback()
        logger.error(f"[Webhooks] Platform webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# === Webhook Verification ===


@router.get("/verify")
async def verify_webhook():
    """Verify webhook endpoints are active"""
    return {
        "status": "active",
        "endpoints": {
            "youtube": "/webhooks/youtube/upload-status",
            "tiktok": "/webhooks/tiktok/upload-status",
            "generic": "/webhooks/platform-status",
        },
        "security": {
            "signature_verification": "Configure YOUTUBE_WEBHOOK_SECRET, TIKTOK_WEBHOOK_SECRET",
            "idempotency": "Enabled for duplicate event prevention",
        },
    }


@router.get("/events")
async def get_webhook_events(
    platform: Optional[str] = None, limit: int = 20, offset: int = 0
):
    """Get recent webhook events (admin only in production)"""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    db = SessionLocal()
    try:
        query = db.query(WebhookEventDB)
        if platform:
            query = query.filter(WebhookEventDB.platform == platform.lower())

        total = query.count()
        events = (
            query.order_by(WebhookEventDB.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "events": [
                {
                    "id": e.id,
                    "platform": e.platform,
                    "event_type": e.event_type,
                    "external_id": e.external_id,
                    "processed_at": e.processed_at.isoformat()
                    if e.processed_at
                    else None,
                    "created_at": e.created_at.isoformat(),
                }
                for e in events
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    finally:
        db.close()
