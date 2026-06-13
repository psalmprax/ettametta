"""
Stripe Payment Service for ettametta Subscriptions
"""

import stripe
import logging
import asyncio
from typing import Any
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from src.api.utils.database import async_session_factory

logger = logging.getLogger(__name__)

# Maps Stripe metadata tier names to SubscriptionTier enum values.
# Stripe uses "creator" / "empire" / "sovereign" / "studio" in metadata,
# but SubscriptionTier uses BASIC / PREMIUM / SOVEREIGN / STUDIO.
STRIPE_TIER_MAP = {
    "free": "FREE",
    "creator": "BASIC",
    "empire": "PREMIUM",
    "sovereign": "SOVEREIGN",
    "studio": "STUDIO",
}

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
        "features": ["Runway/Pika/Wan2.2", "1000 videos/month", "Studio Quality"],
        "limit_videos": 1000,
    },
}


class PaymentService:
    """Stripe payment integration for subscriptions"""

    def __init__(self, stripe_api_key: str | None = None):
        self.stripe_api_key = stripe_api_key

    def _ensure_api_key(self) -> str:
        """Resolve and verify Stripe API key dynamically."""
        if not self.stripe_api_key:
            from src.api.config import settings
            self.stripe_api_key = settings.STRIPE_SECRET_KEY
        if not self.stripe_api_key:
            raise ValueError(
                "Stripe is not configured. Please set STRIPE_SECRET_KEY in environment."
            )
        stripe.api_key = self.stripe_api_key
        return self.stripe_api_key

    async def create_customer(
        self, email: str, user_id: str, idempotency_key: str = None
    ) -> dict[str, Any]:
        """Create a Stripe customer for a user"""
        self._ensure_api_key()
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
            logger.exception(f"[PaymentService] Failed to create customer: {e}")
            raise

    async def create_subscription(
        self,
        stripe_customer_id: str,
        tier: str,
        success_url: str = None,
        cancel_url: str = None,
        idempotency_key: str = None,
        trial_period_days: int = 0,
    ) -> dict[str, Any]:
        """Create a checkout session for subscription

        Args:
            trial_period_days: Number of days for free trial (0 = no trial).
                               When > 0, the subscription will start in
                               ``trialing`` status and the user won't be
                               charged until the trial ends.
        """
        self._ensure_api_key()
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
            if trial_period_days > 0:
                session_params["trial_period_days"] = trial_period_days
                session_params["payment_method_collection"] = "if_required"

            session = await asyncio.to_thread(
                stripe.checkout.Session.create, **session_params
            )
            logger.info(
                f"[PaymentService] Created checkout session {session.id} for tier {tier}"
                + (f" with {trial_period_days}-day trial" if trial_period_days > 0 else "")
            )
            return {
                "session_id": session.id,
                "url": session.url,
            }
        except stripe.error.StripeError as e:
            logger.exception(f"[PaymentService] Failed to create subscription: {e}")
            raise

    async def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Get subscription details from Stripe"""
        self._ensure_api_key()
        try:
            sub = await asyncio.to_thread(stripe.Subscription.retrieve, subscription_id)
            return {
                "id": sub.id,
                "status": sub.status,
                "current_period_end": datetime.fromtimestamp(sub.current_period_end),
                "tier": sub.metadata.get("tier", "unknown"),
            }
        except stripe.error.StripeError as e:
            logger.exception(f"[PaymentService] Failed to get subscription: {e}")
            raise

    async def cancel_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Cancel a subscription at period end"""
        self._ensure_api_key()
        try:
            sub = await asyncio.to_thread(
                stripe.Subscription.modify, subscription_id, cancel_at_period_end=True
            )
            logger.info(f"[PaymentService] Cancelled subscription {subscription_id}")
            return {
                "id": sub.id,
                "status": sub.status,
                "cancel_at": datetime.fromtimestamp(sub.cancel_at),
            }
        except stripe.error.StripeError as e:
            logger.exception(f"[PaymentService] Failed to cancel subscription: {e}")
            raise

    async def handle_webhook(
        self, payload: bytes, signature: str, webhook_secret: str
    ) -> dict[str, Any]:
        """Handle Stripe webhook events"""
        self._ensure_api_key()

        try:
            # construct_event is relatively fast but handles signature verification
            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
        except ValueError as e:
            logger.exception(f"[PaymentService] Invalid payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.exception(f"[PaymentService] Invalid signature: {e}")
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
                    from src.api.utils.credit_models import CreditTransactionDB

                    async with async_session_factory() as db:
                        # Idempotency check: skip if this session was already processed
                        dup_stmt = select(CreditTransactionDB).where(
                            CreditTransactionDB.user_id == user_id,
                            CreditTransactionDB.reference_id == session.id,
                            CreditTransactionDB.transaction_type == "purchase",
                        )
                        existing = await db.execute(dup_stmt)
                        if existing.scalar_one_or_none():
                            logger.info(
                                f"[PaymentService] Credit purchase for session {session.id} "
                                f"already processed — skipping"
                            )
                            # Track skip event
                            from src.api.utils.models import WebhookEventDB
                            db.add(WebhookEventDB(
                                event_type="checkout.session.completed",
                                platform="stripe",
                                external_id=session.id,
                                payload_json={"result": "skipped", "reason": "idempotency", "subtype": "credit_purchase"},
                                processed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                            ))
                            await db.commit()
                        else:
                            await credit_service.add_credits(
                                user_id=user_id,
                                amount=credits,
                                transaction_type="purchase",
                                db=db,
                                reference_id=session.id,
                                description=f"Credit purchase via Stripe (session: {session.id})",
                            )
                            # Track processed event
                            from src.api.utils.models import WebhookEventDB
                            db.add(WebhookEventDB(
                                event_type="checkout.session.completed",
                                platform="stripe",
                                external_id=session.id,
                                payload_json={"result": "processed", "subtype": "credit_purchase"},
                                processed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                            ))
                            await db.commit()
                            logger.info(
                                f"[PaymentService] Added {credits} credits to user {user_id}"
                            )
                return {
                    "status": "processed",
                    "event": "checkout.session.completed",
                    "type": "credit_purchase",
                }

            # Handle subscription checkout
            tier_key = metadata.get("tier", "free")
            tier_enum_name = STRIPE_TIER_MAP.get(tier_key, "FREE")
            subscription_id = session.get("subscription")
            new_tier = getattr(
                SubscriptionTier, tier_enum_name, SubscriptionTier.FREE
            )

            # Retrieve subscription from Stripe to check trial status
            trial_ends_at = None
            if subscription_id:
                try:
                    sub = await asyncio.to_thread(
                        stripe.Subscription.retrieve, subscription_id
                    )
                    if sub.trial_end:
                        trial_ends_at = datetime.fromtimestamp(
                            sub.trial_end, tz=timezone.utc
                        ).replace(tzinfo=None)
                except stripe.error.StripeError:
                    logger.warning(
                        f"[PaymentService] Could not retrieve subscription {subscription_id} "
                        f"for trial info"
                    )

            async with async_session_factory() as db:
                stmt = select(UserDB).where(UserDB.stripe_customer_id == customer_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                        # Idempotency check: skip if tier and subscription_id are unchanged
                        if (
                            user.subscription == new_tier
                            and user.stripe_subscription_id == subscription_id
                        ):
                            logger.info(
                                f"[PaymentService] Subscription for session {session.id} "
                                f"already processed — skipping"
                            )
                            # Track skip event
                            from src.api.utils.models import WebhookEventDB
                            db.add(WebhookEventDB(
                                event_type="checkout.session.completed",
                                platform="stripe",
                                external_id=session.id,
                                payload_json={"result": "skipped", "reason": "idempotency", "subtype": "subscription_checkout"},
                                processed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                            ))
                            await db.commit()
                        else:
                            user.subscription = new_tier
                            user.stripe_subscription_id = subscription_id
                            if trial_ends_at:
                                user.trial_ends_at = trial_ends_at
                            await db.commit()
                            # Track processed event
                            from src.api.utils.models import WebhookEventDB
                            db.add(WebhookEventDB(
                                event_type="checkout.session.completed",
                                platform="stripe",
                                external_id=session.id,
                                payload_json={"result": "processed", "subtype": "subscription_checkout"},
                                processed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                            ))
                            await db.commit()
                            logger.info(
                                f"[PaymentService] Updated user {user.id} to tier {tier_enum_name}"
                                + (f" (trial until {trial_ends_at})" if trial_ends_at else "")
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
                    # NOTE: intentionally NOT clearing trial_ends_at here so the user
                    # cannot re-use the free trial after it expires or is canceled.
                    await db.commit()
                    logger.info(f"[PaymentService] Reset user {user.id} to FREE tier")

                    # Create in-app notification
                    from src.api.utils.models import UserNotificationDB
                    notification = UserNotificationDB(
                        user_id=user.id,
                        type="billing",
                        title="Subscription Cancelled",
                        message="Your subscription has been cancelled and you have been downgraded to the Free tier.",
                        link="/settings?tab=billing",
                    )
                    db.add(notification)
                    await db.commit()
                    logger.info(
                        f"[PaymentService] Created cancellation notification for user {user.id}"
                    )

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
                        tier_key = subscription.metadata.get("tier", "free")
                        tier_enum_name = STRIPE_TIER_MAP.get(tier_key, "FREE")
                        tier_info = SUBSCRIPTION_TIERS.get(tier_key, {})
                        tier_display = tier_info.get("name", tier_enum_name.title())
                        try:
                            user.subscription = getattr(
                                SubscriptionTier, tier_enum_name, SubscriptionTier.FREE
                            )
                            # Trial → paid transition: clear trial tracking;
                            # user is now a normal subscriber.
                            user.trial_ends_at = None
                            await db.commit()
                            # Create in-app notification for upgrade/change
                            from src.api.utils.models import UserNotificationDB
                            notification = UserNotificationDB(
                                user_id=user.id,
                                type="billing",
                                title="Subscription Updated",
                                message=f"Your subscription has been updated to the {tier_display} tier.",
                                link="/settings?tab=billing",
                            )
                            db.add(notification)
                            await db.commit()
                            logger.info(
                                f"[PaymentService] Updated user {user.id} to tier {tier_enum_name}"
                            )
                        except ValueError:
                            logger.warning(
                                f"[PaymentService] Unknown tier {tier_key}, keeping current"
                            )
                    elif subscription.status in ["canceled", "past_due", "unpaid"]:
                        # Downgrade to free
                        user.subscription = SubscriptionTier.FREE
                        user.stripe_subscription_id = None
                        user.trial_ends_at = None
                        await db.commit()
                        # Create in-app notification for downgrade
                        from src.api.utils.models import UserNotificationDB
                        reason_map = {"canceled": "cancellation", "past_due": "non-payment", "unpaid": "non-payment"}
                        reason = reason_map.get(subscription.status, subscription.status)
                        notification = UserNotificationDB(
                            user_id=user.id,
                            type="billing",
                            title="Subscription Downgraded",
                            message=f"Your subscription has been downgraded to Free due to {reason}.",
                            link="/settings?tab=billing",
                        )
                        db.add(notification)
                        await db.commit()
                        logger.info(
                            f"[PaymentService] Downgraded user {user.id} to FREE due to {subscription.status}"
                        )

            return {"status": "processed", "event": "customer.subscription.updated"}

        elif event["type"] == "invoice.payment_succeeded":
            # Log successful renewals for observability and track as renewal event
            invoice = event["data"]["object"]
            subscription_id = invoice.get("subscription")
            amount_paid = invoice.get("amount_paid", 0)
            logger.info(
                f"[PaymentService] Payment succeeded for invoice: {invoice.id} "
                f"(subscription: {subscription_id}, amount: ${amount_paid / 100:.2f})"
            )

            async with async_session_factory() as db:
                customer_id = invoice.get("customer")
                stmt = select(UserDB).where(UserDB.stripe_customer_id == customer_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    logger.info(
                        f"[PaymentService] User {user.id} subscription renewed successfully"
                    )
                    # Create in-app notification for successful renewal
                    from src.api.utils.models import UserNotificationDB
                    amount_dollars = f"${amount_paid / 100:.2f}"
                    notification = UserNotificationDB(
                        user_id=user.id,
                        type="billing",
                        title="Subscription Renewed",
                        message=f"Your subscription has been renewed successfully ({amount_dollars}).",
                        link="/settings?tab=billing",
                    )
                    db.add(notification)
                    logger.info(
                        f"[PaymentService] Created renewal notification for user {user.id}"
                    )

                # Track renewal event in WebhookEventDB for billing dashboard
                from src.api.utils.models import WebhookEventDB
                db.add(WebhookEventDB(
                    event_type="invoice.payment_succeeded",
                    platform="stripe",
                    external_id=invoice.id,
                    payload_json={
                        "result": "renewal",
                        "subtype": "subscription_renewal",
                        "subscription_id": subscription_id,
                        "amount_cents": amount_paid,
                    },
                    processed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                ))
                await db.commit()

            return {"status": "processed", "event": "invoice.payment_succeeded"}

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
                    from src.api.utils.models import UserNotificationDB
                    invoice_amount = invoice.get("amount_due", 0)
                    amount_part = f"of ${invoice_amount / 100:.2f} " if invoice_amount else ""
                    notification = UserNotificationDB(
                        user_id=user.id,
                        type="billing",
                        title="Payment Failed",
                        message=f"Your recent payment {amount_part}failed. Please update your payment method to avoid service interruption.",
                        link="/settings?tab=billing",
                    )
                    db.add(notification)
                    await db.commit()
                    logger.warning(
                        f"[PaymentService] User {user.id} has failed payment — created notification"
                    )

            return {"status": "processed", "event": "invoice.payment_failed"}

        else:
            logger.warning(f"[PaymentService] Unhandled event type: {event['type']}")
            return {"status": "ignored", "event": event["type"]}


# Initialize base service singleton (lazy loaded)
base_stripe_service = PaymentService()


# Keep get_payment_service for backward compatibility
def get_payment_service() -> PaymentService:
    base_stripe_service._ensure_api_key()
    return base_stripe_service

