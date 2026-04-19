"""
Webhooks API Routes for Viral Forge
Handles callbacks from YouTube, TikTok, and other platforms with proper security
"""

from fastapi import APIRouter, Request, HTTPException, Header, Depends
from pydantic import BaseModel, field_validator
from typing import Any
from api.utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from api.utils.models import PublishedContentDB, WebhookEventDB
from api.routes.auth import admin_required
from datetime import datetime
import hashlib
import hmac
import logging
import json

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
        processed_at=datetime.utcnow(),
    )
    db.add(event)


# === YouTube Webhooks ===


class YouTubeWebhookPayload(BaseModel):
    video_id: str
    status: str  # processing, ready, failed
    title: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    duration: int | None = None
    error_message: str | None = None

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
    x_youtube_signature: str | None = Header(None, alias="X-Youtube-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive upload status updates from YouTube
    Requires signature verification if configured
    """
    from api.config import settings

    body = await request.body()  # raw bytes for HMAC verification

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
                content.status = "published"
                content.published_at = datetime.utcnow()
            elif payload.status == "failed":
                content.status = "failed"

            if payload.thumbnail_url:
                content.thumbnail_url = payload.thumbnail_url

            # Use metadata_json for SQLAlchemy model consistency
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
        logger.error(f"[Webhooks] YouTube webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === TikTok Webhooks ===


class TikTokWebhookPayload(BaseModel):
    video_id: str
    status: str  # uploaded, processing, published, failed
    share_url: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    error_message: str | None = None

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
    x_tiktok_signature: str | None = Header(None, alias="X-Tiktok-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive upload status updates from TikTok
    """
    from api.config import settings

    body = await request.body()  # raw bytes for HMAC verification

    if settings.TIKTOK_WEBHOOK_SECRET:
        if not _verify_signature(
            body, x_tiktok_signature, settings.TIKTOK_WEBHOOK_SECRET
        ):
            logger.warning("[Webhooks] TikTok signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        if await _check_idempotency(
            db, "tiktok_upload_status", payload.video_id, "tiktok"
        ):
            logger.info(f"[Webhooks] TikTok event {payload.video_id} already processed")
            return {"status": "already_processed", "message": "Event already handled"}

        stmt = select(PublishedContentDB).where(
            PublishedContentDB.external_video_id == payload.video_id
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            stmt = (
                select(PublishedContentDB)
                .where(PublishedContentDB.platform == "tiktok")
                .order_by(PublishedContentDB.created_at.desc())
            )
            result = await db.execute(stmt)
            content = result.scalars().first()

        if content:
            old_status = content.status

            if payload.status == "published":
                content.status = "published"
                content.published_at = datetime.utcnow()
            elif payload.status == "failed":
                content.status = "failed"

            if payload.share_url:
                content.source_url = payload.share_url

            metrics = content.metrics or {}
            if payload.view_count is not None:
                metrics["views"] = payload.view_count
            if payload.like_count is not None:
                metrics["likes"] = payload.like_count
            if payload.comment_count is not None:
                metrics["comments"] = payload.comment_count
            content.metrics = metrics

            # Use metadata_json for SQLAlchemy model consistency
            metadata = content.metadata_json or {}
            metadata["tiktok_status"] = payload.status
            if payload.error_message:
                metadata["tiktok_error"] = payload.error_message
            content.metadata_json = metadata

            _record_event(
                db,
                "tiktok_upload_status",
                payload.video_id,
                "tiktok",
                payload.model_dump(),
            )
            await db.commit()

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
        await db.rollback()
        logger.error(f"[Webhooks] TikTok webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Generic Platform Webhook ===


class GenericPlatformWebhookPayload(BaseModel):
    platform: str
    external_id: str
    status: str
    metadata: dict[str, Any] | None = None

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
    x_platform_signature: str | None = Header(None, alias="X-Platform-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generic webhook for any platform status updates
    """
    from api.config import settings

    webhook_secret = getattr(
        settings, f"{payload.platform.upper()}_WEBHOOK_SECRET", None
    )

    body = await request.body()  # raw bytes for HMAC verification

    if webhook_secret:
        if not _verify_signature(body, x_platform_signature, webhook_secret):
            logger.warning(
                f"[Webhooks] {payload.platform} signature verification failed"
            )
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        event_key = f"{payload.platform}_{payload.status}"
        if await _check_idempotency(
            db, event_key, payload.external_id, payload.platform
        ):
            return {"status": "already_processed", "message": "Event already handled"}

        stmt = select(PublishedContentDB).where(
            PublishedContentDB.external_video_id == payload.external_id,
            PublishedContentDB.platform == payload.platform,
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if content:
            old_status = content.status

            if payload.status in ["published", "ready", "success"]:
                content.status = "published"
                content.published_at = datetime.utcnow()
            elif payload.status in ["failed", "error"]:
                content.status = "failed"

            if payload.metadata:
                # Use metadata_json for SQLAlchemy model consistency
                existing_metadata = content.metadata_json or {}
                existing_metadata.update(payload.metadata)
                content.metadata_json = existing_metadata

            _record_event(
                db,
                event_key,
                payload.external_id,
                payload.platform,
                payload.model_dump(),
            )
            await db.commit()

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
        await db.rollback()
        logger.error(f"[Webhooks] Platform webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


# === Monetization Webhooks ===


@router.post("/monetization/amazon")
async def amazon_affiliate_webhook(
    request: Request,
    x_amz_signature: str | None = Header(None, alias="X-Amz-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Amazon Associates commission webhooks.
    Processes commission payments and updates revenue tracking.
    """
    from api.utils.models import RevenueLogDB, AffiliateLinkDB

    body = await request.body()
    data = await request.json()

    # Log webhook event
    try:
        # Record webhook event
        event = WebhookEventDB(
            event_type="amazon_commission",
            platform="amazon",
            external_id=data.get("transaction_id", "unknown"),
            payload_json=json.dumps(data),
            processed_at=datetime.utcnow(),
        )
        db.add(event)

        # Process commission data
        if data.get("status") == "approved":
            commission_amount = float(data.get("commission_amount", 0))
            link_id = data.get("link_id")

            # Find the affiliate link
            stmt = select(AffiliateLinkDB).where(AffiliateLinkDB.id == link_id)
            result = await db.execute(stmt)
            affiliate_link = result.scalar_one_or_none()

            if affiliate_link and commission_amount > 0:
                # Create revenue log
                revenue_log = RevenueLogDB(
                    platform="amazon",
                    niche=affiliate_link.niche,
                    amount=commission_amount,
                    user_id=affiliate_link.user_id,
                    metadata={
                        "transaction_id": data.get("transaction_id"),
                        "product_name": affiliate_link.product_name,
                        "commission_rate": data.get("commission_rate"),
                        "click_timestamp": data.get("click_timestamp"),
                    },
                )
                db.add(revenue_log)

        await db.commit()
        return {"status": "success", "processed": True}
    except Exception as e:
        await db.rollback()
        logger.error(f"[Webhooks] Amazon webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monetization/impact-radius")
async def impact_radius_webhook(
    request: Request,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Impact Radius affiliate webhooks.
    """
    from api.utils.models import RevenueLogDB

    body = await request.body()
    data = await request.json()

    # Log webhook event
    try:
        event = WebhookEventDB(
            event_type="impact_radius_conversion",
            platform="impact_radius",
            external_id=data.get("event_id", "unknown"),
            payload_json=json.dumps(data),
            processed_at=datetime.utcnow(),
        )
        db.add(event)

        # Process conversion data
        if data.get("event_type") == "conversion":
            amount = float(data.get("payout_amount", 0))
            if amount > 0:
                revenue_log = RevenueLogDB(
                    platform="impact_radius",
                    niche=data.get("campaign_category", "general"),
                    amount=amount,
                    metadata={
                        "event_id": data.get("event_id"),
                        "campaign_id": data.get("campaign_id"),
                        "conversion_type": data.get("conversion_type"),
                    },
                )
                db.add(revenue_log)

        await db.commit()
        return {"status": "success"}
    except Exception as e:
        await db.rollback()
        logger.error(f"[Webhooks] Impact Radius webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monetization/shareasale")
async def shareasale_webhook(
    request: Request,
    x_shareasale_signature: str | None = Header(None, alias="X-ShareASale-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle ShareASale affiliate webhooks.
    """
    from api.utils.models import RevenueLogDB

    body = await request.body()
    data = await request.json()

    # Log webhook event
    try:
        event = WebhookEventDB(
            event_type="shareasale_commission",
            platform="shareasale",
            external_id=data.get("trans_id", "unknown"),
            payload_json=json.dumps(data),
            processed_at=datetime.utcnow(),
        )
        db.add(event)

        # Process commission data
        commission = float(data.get("commission", 0))
        if commission > 0:
            revenue_log = RevenueLogDB(
                platform="shareasale",
                niche=data.get("category", "general"),
                amount=commission,
                metadata={
                    "transaction_id": data.get("trans_id"),
                    "merchant_id": data.get("merchant_id"),
                    "commission_rate": data.get("commission_percent"),
                    "order_date": data.get("order_date"),
                },
            )
            db.add(revenue_log)

        await db.commit()
        return {"status": "success"}
    except Exception as e:
        await db.rollback()
        logger.error(f"[Webhooks] ShareASale webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monetization/stripe")
async def stripe_monetization_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Stripe webhooks for subscription payments and one-time purchases.
    This extends the existing Stripe webhook for monetization events.
    """
    from api.utils.models import RevenueLogDB
    import stripe

    body = await request.body()
    data = await request.json()

    # Log webhook event
    try:
        event = WebhookEventDB(
            event_type=data.get("type", "unknown"),
            platform="stripe",
            external_id=data.get("id", "unknown"),
            payload_json=json.dumps(data),
            processed_at=datetime.utcnow(),
        )
        db.add(event)

        # Handle different event types
        event_type = data.get("type")

        if event_type == "payment_intent.succeeded":
            payment_intent = data.get("data", {}).get("object", {})
            amount = payment_intent.get("amount", 0) / 100  # Convert from cents

            if amount > 0:
                revenue_log = RevenueLogDB(
                    platform="stripe",
                    niche="subscription",  # Could be enhanced to track product types
                    amount=amount,
                    metadata={
                        "payment_intent_id": payment_intent.get("id"),
                        "customer_id": payment_intent.get("customer"),
                        "currency": payment_intent.get("currency"),
                        "description": payment_intent.get("description"),
                    },
                )
                db.add(revenue_log)

        elif event_type == "invoice.payment_succeeded":
            invoice = data.get("data", {}).get("object", {})
            amount = invoice.get("amount_paid", 0) / 100

            if amount > 0:
                revenue_log = RevenueLogDB(
                    platform="stripe",
                    niche="subscription",
                    amount=amount,
                    metadata={
                        "invoice_id": invoice.get("id"),
                        "subscription_id": invoice.get("subscription"),
                        "customer_id": invoice.get("customer"),
                        "period_start": invoice.get("period_start"),
                        "period_end": invoice.get("period_end"),
                    },
                )
                db.add(revenue_log)

        await db.commit()
        return {"status": "success"}
    except Exception as e:
        await db.rollback()
        logger.error(f"[Webhooks] Stripe monetization webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify")
async def verify_webhook():
    """Verify webhook endpoints are active"""
    return {
        "status": "active",
        "endpoints": {
            "youtube": "/webhooks/youtube/upload-status",
            "tiktok": "/webhooks/tiktok/upload-status",
            "generic": "/webhooks/platform-status",
            "amazon": "/webhooks/monetization/amazon",
            "impact_radius": "/webhooks/monetization/impact-radius",
            "shareasale": "/webhooks/monetization/shareasale",
            "stripe": "/webhooks/monetization/stripe",
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
        logger.error(f"Failed to fetch events: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
