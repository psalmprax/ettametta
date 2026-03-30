from fastapi import HTTPException, status, Depends
from api.utils.user_models import UserDB, SubscriptionTier
from api.routes.auth import get_current_user
from functools import wraps

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
            SubscriptionTier.STUDIO: 4
        }

        
        user_tier_val = tier_values.get(current_user.subscription, 0)
        required_tier_val = tier_values.get(required_tier, 0)
        
        if user_tier_val < required_tier_val:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Subscription upgrade required. This feature requires {required_tier.value} tier or higher."
            )
        return current_user
    return dependency

async def check_daily_limit(current_user: UserDB, db_session):
    """
    Checks if the user has exceeded their daily video generation limit.
    """
    from api.utils.models import VideoJobDB
    from datetime import datetime, timedelta
    
    # Define limits (Daily for Free/Creator, Monthly for others)
    LIMITS = {
        SubscriptionTier.FREE: {"quota": 1, "window": "day"},
        SubscriptionTier.BASIC: {"quota": 3, "window": "day"},
        SubscriptionTier.PREMIUM: {"quota": 90, "window": "month"},
        SubscriptionTier.SOVEREIGN: {"quota": 120, "window": "month"},
        SubscriptionTier.STUDIO: {"quota": 200, "window": "month"}
    }
    
    config = LIMITS.get(current_user.subscription, {"quota": 1, "window": "day"})
    quota = config["quota"]
    
    # Calculate window start
    if config["window"] == "month":
        lookback = datetime.utcnow() - timedelta(days=30)
    else:
        lookback = datetime.utcnow() - timedelta(days=1)
        
    job_count = db_session.query(VideoJobDB).filter(
        VideoJobDB.user_id == current_user.id,
        VideoJobDB.created_at >= lookback
    ).count()
    
    if job_count >= quota:
        window_name = "monthly" if config["window"] == "month" else "daily"
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"{window_name.capitalize()} limit reached for {current_user.subscription.value} tier ({quota} videos/{config['window']})."
        )

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
            SubscriptionTier.STUDIO: 4
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
            "runway": SubscriptionTier.STUDIO,
            "pika": SubscriptionTier.STUDIO
        }
        
        required_tier = engine_map.get(engine, SubscriptionTier.STUDIO)
        user_tier_val = tier_values.get(current_user.subscription, 0)
        required_tier_val = tier_values.get(required_tier, 4)
        
        if user_tier_val < required_tier_val:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Subscription upgrade required. The '{engine}' engine requires {required_tier.value} tier."
            )
        return current_user
    return dependency

def credits_required(action: str):
    """
    Dependency to check and consume credits for an action.
    """
    async def dependency(current_user: UserDB = Depends(get_current_user)):
        from services.payment.credit_service import credit_service
        
        tier = current_user.subscription.value if current_user.subscription else "free"
        cost = credit_service.get_action_cost(action, tier)
        
        if not credit_service.has_sufficient_credits(current_user.id, cost):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Need {cost} credits for {action.replace('_', ' ')}."
            )
        
        # Note: We don't consume yet, the route should do it to avoid consuming when validation fails
        # but we provide the cost in the return for the route to use
        return cost
    return dependency
