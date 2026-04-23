"""
opencli-rs API Routes — Per-User Chrome Session Management
==========================================================

Endpoints for users to connect/manage their opencli-rs platform sessions.
Each user provides their own Chrome cookies via the opencli Chrome extension.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Any
from src.api.routes.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.api.utils.models import OpenCLISessionDB
from src.shared.enums import SessionStatus
from src.api.config import settings
from src.services.opencli.service import opencli_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/opencli", tags=["opencli"])


class CookieUpload(BaseModel):
    platform: str
    cookies: str


class PostRequest(BaseModel):
    platform: str
    content: str
    media_url: str | None = None


class InteractRequest(BaseModel):
    platform: str
    action: str  # like, follow, comment, retweet, upvote
    content_url: str


class SearchRequest(BaseModel):
    platform: str
    query: str
    limit: int = 20


# ─── Platform Discovery ────────────────────────────────────────────────


@router.get("/platforms")
async def list_supported_platforms():
    """list all platforms supported by opencli-rs with their capabilities."""
    if not await opencli_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="opencli-rs is not available. Install with: cargo install opencli-rs",
        )
    return await opencli_service.get_supported_platforms()


# ─── Session Management ────────────────────────────────────────────────


@router.get("/sessions")
async def get_my_sessions(
    current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get all platform session statuses for the current user."""
    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    status_data = await opencli_service.get_user_platforms_status(current_user.id)

    # Sync with DB
    try:
        for session_info in status_data["sessions"]:
            stmt = select(OpenCLISessionDB).where(
                OpenCLISessionDB.user_id == current_user.id,
                OpenCLISessionDB.platform == session_info["platform"],
            )
            result = await db.execute(stmt)
            db_session = result.scalar_one_or_none()
    finally:
        pass

    return status_data


@router.post("/sessions/connect")
async def connect_platform(
    data: CookieUpload,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload Chrome session cookies for a platform.

    The user gets these cookies from the opencli Chrome extension
    after logging into the platform in their browser.
    """
    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    if not await opencli_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="opencli-rs binary not found. Install with: cargo install opencli-rs",
        )

    platform = data.platform.lower()

    # Save cookies to user's session directory
    saved = await opencli_service.save_user_cookies(
        current_user.id, platform, data.cookies
    )
    if not saved:
        raise HTTPException(
            status_code=400, detail=f"Failed to save cookies for platform: {platform}"
        )

    # Verify the session works
    verification = await opencli_service.verify_user_session(current_user.id, platform)

    # Upsert DB record
    try:
        stmt = select(OpenCLISessionDB).where(
            OpenCLISessionDB.user_id == current_user.id,
            OpenCLISessionDB.platform == platform,
        )
        result = await db.execute(stmt)
        db_session = result.scalar_one_or_none()
        if not db_session:
            db_session = OpenCLISessionDB(
                user_id=current_user.id,
                platform=platform,
            )
            db.add(db_session)

        db_session.status = verification["status"]
        db_session.capabilities = verification.get("capabilities", [])
        db_session.error_message = verification.get("message")
        db_session.last_verified = datetime.utcnow()
        db_session.updated_at = datetime.utcnow()
        await db.commit()
    finally:
        pass

    return {
        "status": verification["status"],
        "platform": platform,
        "capabilities": verification.get("capabilities", []),
        "message": verification.get("message", ""),
    }


@router.post("/sessions/disconnect/{platform}")
async def disconnect_platform(
    platform: str,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove session cookies for a platform."""
    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    platform = platform.lower()
    await opencli_service.disconnect_platform(current_user.id, platform)

    # Update DB
    try:
        stmt = select(OpenCLISessionDB).where(
            OpenCLISessionDB.user_id == current_user.id,
            OpenCLISessionDB.platform == platform,
        )
        result = await db.execute(stmt)
        db_session = result.scalar_one_or_none()
        if db_session:
            db_session.status = SessionStatus.DISCONNECTED
            db_session.updated_at = datetime.utcnow()
            await db.commit()
    finally:
        pass

    return {"status": "disconnected", "platform": platform}


@router.post("/sessions/verify/{platform}")
async def verify_platform_session(
    platform: str,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify if a platform session is still valid."""
    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    platform = platform.lower()
    verification = await opencli_service.verify_user_session(current_user.id, platform)

    # Update DB
    try:
        stmt = select(OpenCLISessionDB).where(
            OpenCLISessionDB.user_id == current_user.id,
            OpenCLISessionDB.platform == platform,
        )
        result = await db.execute(stmt)
        db_session = result.scalar_one_or_none()
        if db_session:
            db_session.status = verification["status"]
            db_session.last_verified = datetime.utcnow()
            db_session.error_message = verification.get("message")
            db_session.updated_at = datetime.utcnow()
            await db.commit()
    finally:
        pass

    return verification


# ─── Platform Actions ──────────────────────────────────────────────────


@router.post("/search")
async def search_platform(
    data: SearchRequest,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search a platform using the user's Chrome session."""
    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    platform = data.platform.lower()
    results = await opencli_service.search_platform(
        current_user.id, platform, data.query, data.limit
    )

    # Update last_used
    try:
        stmt = select(OpenCLISessionDB).where(
            OpenCLISessionDB.user_id == current_user.id,
            OpenCLISessionDB.platform == platform,
        )
        result = await db.execute(stmt)
        db_session = result.scalar_one_or_none()
        if db_session:
            db_session.last_used = datetime.utcnow()
            await db.commit()
    finally:
        pass

    return {"results": results, "platform": platform, "count": len(results)}


@router.get("/feed/{platform}")
async def get_platform_feed(
    platform: str,
    feed_type: str = "feed",
    limit: int = 20,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get feed/trending content from a platform using the user's session.

    feed_type options: feed, trending, hot, top, explore
    """
    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    platform = platform.lower()
    results = await opencli_service.get_platform_feed(
        current_user.id, platform, feed_type, limit
    )

    # Update last_used
    try:
        stmt = select(OpenCLISessionDB).where(
            OpenCLISessionDB.user_id == current_user.id,
            OpenCLISessionDB.platform == platform,
        )
        result = await db.execute(stmt)
        db_session = result.scalar_one_or_none()
        if db_session:
            db_session.last_used = datetime.utcnow()
            await db.commit()
    finally:
        pass

    return {"results": results, "platform": platform, "count": len(results)}


@router.post("/post")
async def post_to_platform(
    data: PostRequest,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Post content to a platform using the user's Chrome session."""
    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    platform = data.platform.lower()

    # Verify session exists
    try:
        stmt = select(OpenCLISessionDB).where(
            OpenCLISessionDB.user_id == current_user.id,
            OpenCLISessionDB.platform == platform,
            OpenCLISessionDB.status == "connected",
        )
        result = await db.execute(stmt)
        db_session = result.scalar_one_or_none()
        if not db_session:
            raise HTTPException(
                status_code=400,
                detail=f"No active session for {platform}. Connect first via /opencli/sessions/connect",
            )
    finally:
        pass

    result = await opencli_service.post_to_platform(
        current_user.id, platform, data.content, data.media_url
    )

    # Update last_used
    try:
        stmt = select(OpenCLISessionDB).where(
            OpenCLISessionDB.user_id == current_user.id,
            OpenCLISessionDB.platform == platform,
        )
        result = await db.execute(stmt)
        db_session = result.scalar_one_or_none()
        if db_session:
            db_session.last_used = datetime.utcnow()
            await db.commit()
    finally:
        pass

    return result


@router.post("/interact")
async def interact_with_content(
    data: InteractRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """Perform an interaction on platform content (like, follow, comment, etc.).

    Uses the user's Chrome session to perform the action.
    """
    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    platform = data.platform.lower()
    result = await opencli_service.interact_with_content(
        current_user.id, platform, data.action, data.content_url
    )

    return result
