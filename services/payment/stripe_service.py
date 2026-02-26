"""
Stripe Payment Service for ettametta Subscriptions
"""
import stripe
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Subscription tiers
SUBSCRIPTION_TIERS = {
    "free": {
        "name": "Free",
        "price_id": None,
        "features": ["Basic discovery", "5 videos/month"],
        "limit_videos": 5,
    },
    "creator": {
        "name": "Creator",
        "price_id": "price_creator_monthly",  # Replace with actual Stripe price ID
        "price_cents": 2900,
        "features": ["Full pipeline", "50 videos/month", "Priority support"],
        "limit_videos": 50,
    },
    "empire": {
        "name": "Empire",
        "price_id": "price_empire_monthly",
        "price_cents": 9900,
        "features": ["Unlimited videos", "Priority GPU", "API access"],
        "limit_videos": 100,
    },
    "sovereign": {
        "name": "Sovereign",
        "price_id": "price_sovereign_monthly",
        "price_cents": 14900,
        "features": ["Sovereign LTX-Video", "500 videos/month", "Private GPU Node"],
        "limit_videos": 500,
    },
    "studio": {
        "name": "Studio",
        "price_id": "price_studio_monthly",
        "price_cents": 29900,
        "features": ["Runway Gen-3 / Pika access", "1000 videos/month", "Studio Quality"],
        "limit_videos": 1000,
    }
}



class PaymentService:
    """Stripe payment integration for subscriptions"""
    
    def __init__(self, stripe_api_key: str):
        if not stripe_api_key:
            raise ValueError("Stripe API key not configured. Please set STRIPE_SECRET_KEY.")
        stripe.api_key = stripe_api_key
    
    async def create_customer(self, email: str, user_id: int) -> Dict[str, Any]:
        """Create a Stripe customer for a user"""
        try:
            customer = stripe.Customer.create(
                email=email,
                metadata={"user_id": str(user_id)}
            )
            logger.info(f"[PaymentService] Created Stripe customer {customer.id} for user {user_id}")
            return {
                "stripe_customer_id": customer.id,
                "email": customer.email,
            }
        except stripe.error.StripeError as e:
            logger.error(f"[PaymentService] Failed to create customer: {e}")
            raise
    
    async def create_subscription(
        self, 
        stripe_customer_id: str, 
        tier: str,
        success_url: str = None,
        cancel_url: str = None
    ) -> Dict[str, Any]:
        """Create a checkout session for subscription"""
        from api.config import settings
        
        # Use provided URLs or default to production domain settings
        if success_url is None:
            success_url = f"{settings.PRODUCTION_DOMAIN}/settings?tab=billing&success=true"
        if cancel_url is None:
            cancel_url = f"{settings.PRODUCTION_DOMAIN}/settings?tab=billing&cancelled=true"
        tier_info = SUBSCRIPTION_TIERS.get(tier)
        if not tier_info or not tier_info.get("price_id"):
            raise ValueError(f"Invalid tier: {tier}")
        
        try:
            session = stripe.checkout.Session.create(
                customer=stripe_customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": tier_info["price_id"],
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"tier": tier}
            )
            logger.info(f"[PaymentService] Created checkout session {session.id} for tier {tier}")
            return {
                "session_id": session.id,
                "url": session.url,
            }
        except stripe.error.StripeError as e:
            logger.error(f"[PaymentService] Failed to create subscription: {e}")
            raise
    
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details from Stripe"""
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": sub.id,
                "status": sub.status,
                "current_period_end": datetime.fromtimestamp(sub.current_period_end),
                "tier": sub.metadata.get("tier", "unknown"),
            }
        except stripe.error.StripeError as e:
            logger.error(f"[PaymentService] Failed to get subscription: {e}")
            raise
    
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription at period end"""
        try:
            sub = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            logger.info(f"[PaymentService] Cancelled subscription {subscription_id}")
            return {
                "id": sub.id,
                "status": sub.status,
                "cancel_at": datetime.fromtimestamp(sub.cancel_at),
            }
        except stripe.error.StripeError as e:
            logger.error(f"[PaymentService] Failed to cancel subscription: {e}")
            raise
    
    async def handle_webhook(self, payload: bytes, signature: str, webhook_secret: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
        except ValueError as e:
            logger.error(f"[PaymentService] Invalid payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"[PaymentService] Invalid signature: {e}")
            raise
        
        # Handle events
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            logger.info(f"[PaymentService] Checkout completed: {session.id}")
            # TODO: Update user subscription in database
            return {"status": "processed", "event": "checkout.session.completed"}
        
        elif event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            logger.info(f"[PaymentService] Subscription updated: {subscription.id}")
            return {"status": "processed", "event": "customer.subscription.updated"}
        
        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            logger.info(f"[PaymentService] Subscription cancelled: {subscription.id}")
            return {"status": "processed", "event": "customer.subscription.deleted"}
        
        else:
            logger.warning(f"[PaymentService] Unhandled event type: {event['type']}")
            return {"status": "ignored", "event": event["type"]}


# Initialize with API key from settings
def get_payment_service() -> PaymentService:
    from api.config import settings
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError("Stripe is not configured. Please set STRIPE_SECRET_KEY in environment.")
    return PaymentService(settings.STRIPE_SECRET_KEY)
