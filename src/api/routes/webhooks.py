"""
Webhooks API Routes for ettametta
Handles callbacks from YouTube, TikTok, and other platforms with proper security
Plus ettametta-native Zapier integration endpoints
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.utils.database import get_db
from sqlalchemy import select, func
from src.api.utils.models import (
    PublishedContentDB,
    VideoJobDB,
    ContentCandidateDB,
    SystemSettings,
    WebhookEventDB,
)
from src.shared.enums import ContentPublishStatus, JobStatus
from src.api.utils.auth import admin_required

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _verify_signature(payload: bytes, signature: str | None, secret: str) -> bool:
    """Verify webhook signature using HMAC-SHA256"""
    if not signature:
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


async def _check_idempotency(
    db: AsyncSession, event_type: str, external_id: str, platform: str
) -> bool:
    """Check if this event was already processed"""
    stmt = select(WebhookEventDB).where(
        WebhookEventDB.event_type == event_type,
        WebhookEventDB.external_id == external_id,
        WebhookEventDB.platform == platform,
        WebhookEventDB.processed_at.isnot(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


def _record_event(
    db: AsyncSession, event_type: str, external_id: str, platform: str, payload: dict
):
    """Record webhook event for idempotency"""
    event = WebhookEventDB(
        event_type=event_type,
        external_id=external_id,
        platform=platform,
        payload_json=json.dumps(payload),
        processed_at=datetime.now(timezone.utc),
    )
    db.add(event)


# === YouTube Webhooks ===


class YouTubeWebhookPayload(BaseModel):
    video_id: str
    status: str = Field(..., description="processing, ready, failed")
    title: str | None = None
    description: str | None = None
    thumbnail_uri: str | None = None
    duration: int | None = None
    error_message: str | None = None

    @classmethod
    def validate_status(cls, v):
        if v not in ["processing", "ready", "failed"]:
            raise ValueError("Status must be processing, ready, or failed")
        return v


# Apply validator after class creation
YouTubeWebhookPayload.model_validate = lambda cls, v, *args, **kwargs: \
    cls.validate_status(v) or super().__call__(v, *args, **kwargs) if hasattr(super(), '__call__') else v


# Re-apply the validator properly
def _validate_youtube_status(v):
    if v not in ["processing", "ready", "failed"]:
        raise ValueError("Status must be processing, ready, or failed")
    return v


class YouTubeWebhookPayload(BaseModel):
    video_id: str
    status: str = Field(..., description="processing, ready, failed")
    title: str | None = None
    description: str | None = None
    thumbnail_uri: str | None = None
    duration: int | None = None
    error_message: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ["processing", "ready", "failed"]:
            raise ValueError("Status must be processing, ready, or failed")
        return v


# === Core Webhooks ===


@router.post("/youtube/upload-status")
async def youtube_upload_status(
    payload: YouTubeWebhookPayload,
    request: Request,
    x_youtube_signature: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive upload status updates from YouTube
    Requires signature verification if configured
    """
    from src.api.config import settings

    body = await request.body()

    if settings.YOUTUBE_WEBHOOK_SECRET:
        if not _verify_signature(
            body, x_youtube_signature, settings.YOUTUBE_WEBHOOK_SECRET
        ):
            logger.warning("[Webhooks] YouTube signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        if await _check_idempotency(
            db, "youtube_upload_status", payload.video_id, "youtube"
        ):
            logger.info(
                f"[Webhooks] YouTube event {payload.video_id} already processed (idempotency)"
            )
            return {"status": "already_processed", "message": "Event already handled"}

        stmt = select(PublishedContentDB).where(
            PublishedContentDB.external_video_id == payload.video_id
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content and payload.title:
            stmt = select(PublishedContentDB).where(
                PublishedContentDB.title.ilike(f"%{payload.title}%")
            )
            result = await db.execute(stmt)
            content = result.scalar_one_or_none()

        if content:
            old_status = content.status

            if payload.status == "ready":
                content.status = ContentPublishStatus.PUBLISHED
                content.published_at = datetime.now(timezone.utc)
            elif payload.status == "failed":
                content.status = ContentPublishStatus.FAILED

            if payload.thumbnail_uri:
                content.thumbnail_uri = payload.thumbnail_uri

            metadata = content.metadata_json or {}
            metadata["youtube_status"] = payload.status
            metadata["youtube_duration"] = payload.duration
            if payload.error_message:
                metadata["youtube_error"] = payload.error_message
            if payload.description:
                metadata["youtube_description"] = payload.description
            content.metadata_json = metadata

            _record_event(
                db,
                "youtube_upload_status",
                payload.video_id,
                "youtube",
                payload.model_dump(),
            )
            await db.commit()

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
        await db.rollback()
        logger.exception(f"[Webhooks] YouTube webhook error: {e}")
        raise HTTPException(status_code=503, detail="Webhook processing failed")


@router.get("/verify")
async def verify_webhook():
    """Verify webhook endpoints are active"""
    return {
        "status": "active",
        "endpoints": {
            "youtube": "/webhooks/youtube/upload-status",
            "ettametta_discovery": "/webhooks/ettametta/discovery-trigger",
            "ettametta_video": "/webhooks/ettametta/video-edit",
            "ettametta_metrics": "/webhooks/ettametta/metrics-export",
        },
        "security": {
            "signature_verification": "Configure webhook secrets for each platform",
            "idempotency": "Enabled for duplicate event prevention",
        },
    }


@router.get("/events")
async def get_webhook_events(
    platform: str | None = None,
    limit: int = 20,
    offset: int = 0,
    admin=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Get recent webhook events (admin only)"""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    try:
        stmt = select(WebhookEventDB)
        if platform:
            stmt = stmt.where(WebhookEventDB.platform == platform.lower())

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        res_count = await db.execute(count_stmt)
        total = res_count.scalar() or 0

        # Results
        stmt = (
            stmt.order_by(WebhookEventDB.created_at.desc()).offset(offset).limit(limit)
        )
        result = await db.execute(stmt)
        events = result.scalars().all()

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
    except Exception as e:
        logger.exception(f"Failed to fetch events: {e}")
        raise HTTPException(status_code=503, detail="Webhook processing failed")
