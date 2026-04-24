from fastapi import HTTPException, status, Depends
from src.api.utils.database import get_db
from src.api.utils.user_models import UserDB, UserRole, SubscriptionTier
from src.api.routes.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from functools import wraps
from src.shared.enums import CreditAction


def subscription_required(required_tier: SubscriptionTier):
    """
    Dependency to enforce a minimum subscription tier.
    """

    async def dependency(current_user: UserDB = Depends(get_current_user)):
        # Tier hierarchy check
        tier_values = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.PREMIUM: 2,
            SubscriptionTier.SOVEREIGN: 3,
            SubscriptionTier.STUDIO: 4,
        }

        user_tier_val = tier_values.get(current_user.subscription, 0)
        required_tier_val = tier_values.get(required_tier, 0)

        if user_tier_val < required_tier_val:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Subscription upgrade required. This feature requires {required_tier.value} tier or higher.",
            )
        return current_user

    return dependency


async def check_daily_limit(current_user: UserDB, db_session: AsyncSession):
    """
    Checks if the user has exceeded their daily video generation limit.
    """
    from src.api.utils.models import VideoJobDB
    from datetime import datetime, timedelta
    from sqlalchemy import select, func

    # Define limits (Daily for Free/Creator, Monthly for others)
    LIMITS = {
        SubscriptionTier.FREE: {"quota": 1, "window": "day"},
        SubscriptionTier.BASIC: {"quota": 3, "window": "day"},
        SubscriptionTier.PREMIUM: {"quota": 90, "window": "month"},
        SubscriptionTier.SOVEREIGN: {"quota": 120, "window": "month"},
        SubscriptionTier.STUDIO: {"quota": 200, "window": "month"},
    }

    config = LIMITS.get(current_user.subscription, {"quota": 1, "window": "day"})
    quota = config["quota"]

    # Calculate window start
    if config["window"] == "month":
        lookback = datetime.utcnow() - timedelta(days=30)
    else:
        lookback = datetime.utcnow() - timedelta(days=1)

    # Async-compatible count query
    result = await db_session.execute(
        select(func.count(VideoJobDB.id)).where(
            VideoJobDB.user_id == current_user.id, VideoJobDB.created_at >= lookback
        )
    )
    job_count = result.scalar()

    if job_count >= quota:
        window_name = "monthly" if config["window"] == "month" else "daily"
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"{window_name.capitalize()} limit reached for {get_subscription_tier_value(current_user)} tier ({quota} videos/{config['window']}).",
        )


def daily_limit_reached():
    """
    FastAPI dependency to enforce daily limits.
    """

    async def dependency(
        current_user: UserDB = Depends(get_current_user),
        db=Depends(get_db),
    ):
        await check_daily_limit(current_user, db)
        return current_user

    return dependency


def engine_access_required(engine: str):
    """
    Dependency to check if a user has access to a specific AI engine.
    """

    async def dependency(current_user: UserDB = Depends(get_current_user)):
        tier_values = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.PREMIUM: 2,
            SubscriptionTier.SOVEREIGN: 3,
            SubscriptionTier.STUDIO: 4,
        }

        # Engine-to-Tier Mapping
        engine_map = {
            "lite4k": SubscriptionTier.PREMIUM,
            "ltx-video": SubscriptionTier.SOVEREIGN,
            "hunyuan": SubscriptionTier.SOVEREIGN,
            "mochi": SubscriptionTier.SOVEREIGN,
            "cogvideo": SubscriptionTier.SOVEREIGN,
            "wan": SubscriptionTier.SOVEREIGN,
            "veo3": SubscriptionTier.STUDIO,
            "wan2.2": SubscriptionTier.STUDIO,
            # Free tier engines (browser automation)
            "kling": SubscriptionTier.FREE,
            "pika": SubscriptionTier.FREE,
            "runway": SubscriptionTier.FREE,
            "leonardo": SubscriptionTier.FREE,
            "frameloop": SubscriptionTier.FREE,
            "wavespeed": SubscriptionTier.FREE,
            "ltx": SubscriptionTier.FREE,
            "videoany": SubscriptionTier.FREE,
            "vidu": SubscriptionTier.FREE,
            "hailuo": SubscriptionTier.FREE,
            "seedance": SubscriptionTier.FREE,
            "heygen": SubscriptionTier.FREE,
            "pixverse": SubscriptionTier.FREE,
            "haiper": SubscriptionTier.FREE,
            "luma": SubscriptionTier.FREE,
            "leiapix": SubscriptionTier.FREE,
            "kaiber": SubscriptionTier.FREE,
            "fliki": SubscriptionTier.FREE,
            "invideo": SubscriptionTier.FREE,
            "morph": SubscriptionTier.FREE,
            "genmo": SubscriptionTier.FREE,
            # Mid tier
            "zsky-wan": SubscriptionTier.FREE,
        }

        required_tier = engine_map.get(engine, SubscriptionTier.STUDIO)
        user_tier_val = tier_values.get(current_user.subscription, 0)
        required_tier_val = tier_values.get(required_tier, 4)

        if user_tier_val < required_tier_val:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Subscription upgrade required. The '{engine}' engine requires {required_tier.value} tier.",
            )
        return current_user

    return dependency


def credits_required(action: CreditAction | str):
    """
    Dependency to check and consume credits for an action.
    Accepts CreditAction enum or string for backward compatibility.
    """

    async def dependency(
        current_user: UserDB = Depends(get_current_user),
        db=Depends(get_db),
    ):
        from src.services.payment.credit_service import credit_service

        # Convert to string if CreditAction enum
        action_str = action.value if isinstance(action, CreditAction) else action
        tier = get_subscription_tier_value(current_user)
        cost = credit_service.get_action_cost(action_str, tier)

        if not await credit_service.has_sufficient_credits(current_user.id, cost, db):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Need {cost} credits for {action_str.replace('_', ' ')}.",
            )

        return cost

    return dependency


async def get_user_subscription_tier(user: UserDB, db: AsyncSession) -> str:
    """
    Get user's current subscription tier as a string.
    """
    # Simply use the enum's value
    return get_subscription_tier_value(user)


def get_subscription_tier_value(user) -> str:
    """
    Safely get subscription tier value from user object.
    Handles both SubscriptionTier enum and None cases.
    """
    if user is None:
        return "free"
    if user.subscription is None:
        return "free"
    # Handle SubscriptionTier enum - has .value attribute
    if hasattr(user.subscription, "value"):
        return user.subscription.value
    # Handle string subscription directly
    if isinstance(user.subscription, str):
        return user.subscription
    # Fallback to string conversion
    return str(user.subscription)


def get_provider_quota_info(engine: str) -> dict:
    """
    Get quota information for a specific AI video engine.
    """
    quota_mapping = {
        "veo3": {"daily_limit": 5, "premium": True, "provider": "Google"},
        "runway": {"daily_limit": 5, "premium": True, "provider": "RunwayML"},
        "pika": {"daily_limit": 10, "premium": True, "provider": "Pika Labs"},
        "ltx-video": {"daily_limit": 20, "premium": False, "provider": "Lightbox"},
        "hunyuan": {"daily_limit": 15, "premium": False, "provider": "Tencent"},
    }
    return quota_mapping.get(
        engine, {"daily_limit": 10, "premium": False, "provider": "Default"}
    )
