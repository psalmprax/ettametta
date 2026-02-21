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
            SubscriptionTier.PREMIUM: 2
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
    
    # Define limits per tier
    LIMITS = {
        SubscriptionTier.FREE: 3,
        SubscriptionTier.BASIC: 20,
        SubscriptionTier.PREMIUM: 1000 # Effectively unlimited
    }
    
    tier_limit = LIMITS.get(current_user.subscription, 3)
    
    # Count jobs in the last 24 hours
    since_24h = datetime.utcnow() - timedelta(days=1)
    job_count = db_session.query(VideoJobDB).filter(
        VideoJobDB.user_id == current_user.id,
        VideoJobDB.created_at >= since_24h
    ).count()
    
    if job_count >= tier_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit reached for {current_user.subscription.value} tier ({tier_limit} videos/day)."
        )
