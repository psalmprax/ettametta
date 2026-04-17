from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from src.api.config import settings
from src.api.utils.user_models import SubscriptionTier

def get_user_rate_limit(request: Request) -> str:
    """
    Returns a rate limit string based on the user's subscription tier.
    Falls back to a standard limit if user info isn't available.
    """
    # Note: SlowAPI's key_func usually runs BEFORE dependencies like get_current_user.
    # To do tiered limiting properly, we'd ideally use a header or JWT-based key.
    # For now, we'll return the base limits from settings.
    
    # Check if user is already attached to request (might be if middleware set it)
    user = getattr(request.state, "user", None)
    if not user:
        return f"{settings.LIMIT_FREE}/hour"
    
    tier = getattr(user, "subscription", SubscriptionTier.FREE)
    
    if tier == SubscriptionTier.STUDIO or tier == SubscriptionTier.SOVEREIGN:
        return f"{settings.LIMIT_SOVEREIGN}/hour"
    elif tier == SubscriptionTier.PREMIUM or tier == SubscriptionTier.BASIC:
        return f"{settings.LIMIT_PRO}/hour"
    else:
        return f"{settings.LIMIT_FREE}/hour"

# Initialize global limiter
limiter = Limiter(key_func=get_remote_address)
