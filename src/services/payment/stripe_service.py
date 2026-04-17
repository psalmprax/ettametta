"""
Stripe Payment Service for ettametta Subscriptions
"""

import stripe
import logging
import asyncio
from typing import Any
from datetime import datetime
from sqlalchemy import select
from src.api.utils.database import async_session_factory

logger = logging.getLogger(__name__)

# Subscription tiers
SUBSCRIPTION_TIERS = {
    "free": {
        "name": "Free",
        "price_id": None,
        "features": ["Basic discovery", "1 video/day"],
        "limit_videos": 1,
    },
    "creator": {
        "name": "Creator",
        "price_id": "price_creator_monthly",
        "price_cents": 2900,
        "features": ["Transformation pipeline", "5 videos/day", "Priority support"],
        "limit_videos": 5,
    },
    "empire": {
        "name": "Empire",
        "price_id": "price_empire_monthly",
        "price_cents": 9900,
        "features": ["100 videos/month", "Lite4K Synthesis ONLY", "Priority GPU"],
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
        "features": ["Runway/Pika/Veo3/Wan2.2", "1000 videos/month", "Studio Quality"],
        "limit_videos": 1000,
    },
}


class PaymentService:
    """Stripe payment integration for subscriptions"""

    def __init__(self, stripe_api_key: str):
        if not stripe_api_key:
            raise ValueError(
                "Stripe API key not configured. Please set STRIPE_SECRET_KEY."
            )
        stripe.api_key = stripe_api_key

    async def create_customer(
        self, email: str, user_id: int, idempotency_key: str = None
    ) -> dict[str, Any]:
        """Create a Stripe customer for a user"""
        try:
            create_params = {"email": email, "metadata": {"user_id": str(user_id)}}
            if idempotency_key:
                create_params["idempotency_key"] = idempotency_key

            # Stripe Python < 3.0.0 is blocking, use to_thread to keep event loop free
            customer = await asyncio.to_thread(stripe.Customer.create, **create_params)
            logger.info(
                f"[PaymentService] Created Stripe customer {customer.id} for user {user_id}"
            )
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
        cancel_url: str = None,
        idempotency_key: str = None,
    ) -> dict[str, Any]:
        """Create a checkout session for subscription"""
        from src.api.config import settings

        # Use provided URLs or default to production domain settings
        if success_url is None:
            success_url = (
                f"{settings.PRODUCTION_DOMAIN}/settings?tab=billing&success=true"
            )
        if cancel_url is None:
            cancel_url = (
                f"{settings.PRODUCTION_DOMAIN}/settings?tab=billing&cancelled=true"
            )
        tier_info = SUBSCRIPTION_TIERS.get(tier)
        if not tier_info or not tier_info.get("price_id"):
            raise ValueError(f"Invalid tier: {tier}")

        try:
            session_params = {
                "customer": stripe_customer_id,
                "payment_method_types": ["card"],
                "line_items": [
                    {
                        "price": tier_info["price_id"],
                        "quantity": 1,
                    }
                ],
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {"tier": tier},
            }
            if idempotency_key:
                session_params["idempotency_key"] = idempotency_key

            session = await asyncio.to_thread(
                stripe.checkout.Session.create, **session_params
            )
            logger.info(
                f"[PaymentService] Created checkout session {session.id} for tier {tier}"
            )
            return {
                "session_id": session.id,
                "url": session.url,
            }
        except stripe.error.StripeError as e:
            logger.error(f"[PaymentService] Failed to create subscription: {e}")
            raise

    async def get_subscription(self, subscription_id: str) -> dict[str, Any]:
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

    async def cancel_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Cancel a subscription at period end"""
        try:
            sub = stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
            logger.info(f"[PaymentService] Cancelled subscription {subscription_id}")
            return {
                "id": sub.id,
                "status": sub.status,
                "cancel_at": datetime.fromtimestamp(sub.cancel_at),
            }
        except stripe.error.StripeError as e:
            logger.error(f"[PaymentService] Failed to cancel subscription: {e}")
            raise

    async def handle_webhook(
        self, payload: bytes, signature: str, webhook_secret: str
    ) -> dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            # construct_event is relatively fast but handles signature verification
            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
        except ValueError as e:
            logger.error(f"[PaymentService] Invalid payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"[PaymentService] Invalid signature: {e}")
            raise

        from src.api.utils.user_models import UserDB, SubscriptionTier

        # Handle events
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            logger.info(f"[PaymentService] Checkout completed: {session.id}")

            customer_id = session.get("customer")
            metadata = session.get("metadata", {})

            # Handle credit purchases
            if metadata.get("type") == "credit_purchase":
                user_id = metadata.get("user_id")
                credits = int(metadata.get("credits", 0))
                if user_id and credits > 0:
                    from src.services.payment.credit_service import credit_service

                    # Assuming add_credits is now async or we wrap it
                    await credit_service.add_credits(
                        user_id=int(user_id),
                        amount=credits,
                        transaction_type="purchase",
                        description=f"Credit purchase via Stripe (session: {session.id})",
                    )
                    logger.info(
                        f"[PaymentService] Added {credits} credits to user {user_id}"
                    )
                return {
                    "status": "processed",
                    "event": "checkout.session.completed",
                    "type": "credit_purchase",
                }

            # Handle subscription checkout
            tier = metadata.get("tier", "free").upper()
            subscription_id = session.get("subscription")

            async with async_session_factory() as db:
                stmt = select(UserDB).where(UserDB.stripe_customer_id == customer_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    user.subscription = getattr(
                        SubscriptionTier, tier, SubscriptionTier.FREE
                    )
                    user.stripe_subscription_id = subscription_id
                    await db.commit()
                    logger.info(
                        f"[PaymentService] Updated user {user.id} to tier {tier}"
                    )

            return {"status": "processed", "event": "checkout.session.completed"}

        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            logger.info(f"[PaymentService] Subscription cancelled: {subscription.id}")

            async with async_session_factory() as db:
                stmt = select(UserDB).where(
                    UserDB.stripe_subscription_id == subscription.id
                )
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    user.subscription = SubscriptionTier.FREE
                    user.stripe_subscription_id = None
                    await db.commit()
                    logger.info(f"[PaymentService] Reset user {user.id} to FREE tier")

            return {"status": "processed", "event": "customer.subscription.deleted"}

        elif event["type"] == "customer.subscription.updated":
            # Handle upgrades/downgrades that happen outside checkout
            subscription = event["data"]["object"]
            logger.info(f"[PaymentService] Subscription updated: {subscription.id}")

            async with async_session_factory() as db:
                stmt = select(UserDB).where(
                    UserDB.stripe_subscription_id == subscription.id
                )
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    # Check if subscription is still active
                    if subscription.status == "active":
                        # Get the tier from metadata
                        new_tier = subscription.metadata.get("tier", "free").upper()
                        try:
                            user.subscription = getattr(
                                SubscriptionTier, new_tier, SubscriptionTier.FREE
                            )
                            await db.commit()
                            logger.info(
                                f"[PaymentService] Updated user {user.id} to tier {new_tier}"
                            )
                        except ValueError:
                            logger.warning(
                                f"[PaymentService] Unknown tier {new_tier}, keeping current"
                            )
                    elif subscription.status in ["canceled", "past_due", "unpaid"]:
                        # Downgrade to free
                        user.subscription = SubscriptionTier.FREE
                        user.stripe_subscription_id = None
                        await db.commit()
                        logger.info(
                            f"[PaymentService] Downgraded user {user.id} to FREE due to {subscription.status}"
                        )

            return {"status": "processed", "event": "customer.subscription.updated"}

        elif event["type"] == "invoice.payment_failed":
            # Handle failed payments - notify user
            invoice = event["data"]["object"]
            logger.warning(f"[PaymentService] Payment failed for invoice: {invoice.id}")

            async with async_session_factory() as db:
                customer_id = invoice.get("customer")
                stmt = select(UserDB).where(UserDB.stripe_customer_id == customer_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    # Could add notification logic here
                    logger.warning(
                        f"[PaymentService] User {user.id} has failed payment"
                    )

            return {"status": "processed", "event": "invoice.payment_failed"}

        else:
            logger.warning(f"[PaymentService] Unhandled event type: {event['type']}")
            return {"status": "ignored", "event": event["type"]}


# Initialize with API key from settings
def get_payment_service() -> PaymentService:
    from src.api.config import settings

    if not settings.STRIPE_SECRET_KEY:
        raise ValueError(
            "Stripe is not configured. Please set STRIPE_SECRET_KEY in environment."
        )
    return PaymentService(settings.STRIPE_SECRET_KEY)
