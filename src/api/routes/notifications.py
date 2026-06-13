"""
Notification Preferences & In-App Notifications
================================================
Endpoints for managing user notification settings (email/telegram) and
for listing / managing in-app notifications surfaced in the frontend
NotificationCenter component.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.utils.database import get_db
from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.api_responses import success_response
from pydantic import BaseModel
from src.services.email.service import base_email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationPreferences(BaseModel):
    email_welcome: bool = True
    email_password_reset: bool = True
    email_notifications: bool = True
    email_marketing: bool = False
    email_product_updates: bool = False
    telegram_notifications: bool = False
    whatsapp_notifications: bool = False


@router.get("/preferences")
async def get_notification_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Get current user's notification preferences."""
    from src.api.utils.models import UserSetting

    preferences = {
        "email_welcome": True,
        "email_password_reset": True,
        "email_notifications": True,
        "email_marketing": False,
        "email_product_updates": False,
        "telegram_notifications": bool(current_user.telegram_chat_id),
        "whatsapp_notifications": bool(current_user.whatsapp_number),
    }

    stmt = select(UserSetting).where(UserSetting.user_id == current_user.id)
    result = await db.execute(stmt)
    user_settings = result.scalars().all()

    for setting in user_settings:
        if setting.key.startswith("notif_"):
            pref_key = setting.key.replace("notif_", "")
            preferences[pref_key] = setting.value.lower() == "true"

    return success_response(data=preferences)


@router.put("/preferences")
async def update_notification_preferences(
    preferences: NotificationPreferences,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Update user's notification preferences."""
    from src.api.utils.models import UserSetting

    pref_dict = preferences.model_dump()
    updated = []

    for key, value in pref_dict.items():
        setting_key = f"notif_{key}"
        stmt = select(UserSetting).where(
            UserSetting.user_id == current_user.id,
            UserSetting.key == setting_key,
        )
        result = await db.execute(stmt)
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = str(value)
        else:
            setting = UserSetting(
                user_id=current_user.id,
                key=setting_key,
                value=str(value),
                category="notifications",
            )
            db.add(setting)
        updated.append(setting_key)

    await db.commit()
    return success_response(data={"updated": updated})


@router.post("/email/subscribe")
async def subscribe_to_marketing(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Subscribe user to marketing emails."""
    if not base_email_service.is_enabled():
        raise HTTPException(status_code=503, detail="Email service not configured")

    success = await base_email_service.subscribe_user(
        current_user.email, tags=["subscriber"]
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to subscribe")

    return success_response(data={"status": "subscribed", "email": current_user.email})


@router.post("/email/unsubscribe")
async def unsubscribe_from_marketing(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Unsubscribe user from marketing emails."""
    if not base_email_service.is_enabled():
        raise HTTPException(status_code=503, detail="Email service not configured")

    success = await base_email_service.unsubscribe_user(current_user.email)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to unsubscribe")

    return success_response(data={"status": "unsubscribed", "email": current_user.email})


@router.get("/")
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """
    List in-app notifications for the current user, newest first.
    Returns up to 50 notifications.
    """
    from src.api.utils.models import UserNotificationDB

    stmt = (
        select(UserNotificationDB)
        .where(UserNotificationDB.user_id == current_user.id)
        .order_by(desc(UserNotificationDB.created_at))
        .limit(50)
    )
    result = await db.execute(stmt)
    notes = result.scalars().all()

    return success_response(
        data=[
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "link": n.link,
                "read": n.read,
                "timestamp": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notes
        ]
    )


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Mark a single notification as read."""
    from src.api.utils.models import UserNotificationDB

    stmt = (
        update(UserNotificationDB)
        .where(
            UserNotificationDB.id == notification_id,
            UserNotificationDB.user_id == current_user.id,
        )
        .values(read=True)
    )
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notification not found")

    return success_response(data={"status": "marked_read"})


@router.put("/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Mark all notifications as read for the current user."""
    from src.api.utils.models import UserNotificationDB

    stmt = (
        update(UserNotificationDB)
        .where(
            UserNotificationDB.user_id == current_user.id,
            UserNotificationDB.read == False,  # noqa: E712
        )
        .values(read=True)
    )
    await db.execute(stmt)
    await db.commit()

    return success_response(data={"status": "all_marked_read"})


@router.get("/unread-count")
async def get_unread_notification_count(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Return the count of unread in-app notifications for the current user.
    Lightweight — avoids fetching the full 50-item list just to show a badge.
    """
    from sqlalchemy import func
    from src.api.utils.models import UserNotificationDB

    stmt = (
        select(func.count())
        .select_from(UserNotificationDB)
        .where(
            UserNotificationDB.user_id == current_user.id,
            UserNotificationDB.read == False,  # noqa: E712
        )
    )
    result = await db.execute(stmt)
    count = result.scalar_one()

    return success_response(data={"unread_count": count})


@router.post("/test-email")
async def send_test_email(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Send a test email to the current user."""
    if not base_email_service.is_enabled():
        raise HTTPException(status_code=503, detail="Email service not configured")

    success = await base_email_service.send_notification_email(
        email=current_user.email,
        subject="Ettametta Test Email",
        message="This is a test email from Ettametta. If you received this, your email configuration is working correctly.",
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send test email")

    return success_response(data={"status": "sent", "email": current_user.email})
