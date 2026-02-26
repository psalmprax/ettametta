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
