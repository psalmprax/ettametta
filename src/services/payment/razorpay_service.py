"""
Razorpay Payment Service for ettametta Subscriptions
"""

import razorpay
import logging
import asyncio
from typing import Any
from datetime import datetime
from sqlalchemy import select
from src.api.utils.database import async_session_factory

logger = logging.getLogger(__name__)

# Maps Razorpay plan IDs to SubscriptionTier enum values.
RAZORPAY_TIER_MAP = {
    "free": "FREE",
    "creator": "BASIC",
    "empire": "PREMIUM",
    "sovereign": "SOVEREIGN",
    "studio": "STUDIO",
}

# Subscription tiers (mirrors stripe_service.py)
RAZORPAY_SUBSCRIPTION_TIERS = {
    "free": {
        "name": "Free",
        "plan_id": None,
        "features": ["Basic discovery", "1 video/day"],
        "limit_videos": 1,
    },
    "creator": {
        "name": "Creator",
        "plan_id": "plan_creator_monthly",
        "price_cents": 2900,
        "features": ["Transformation pipeline", "5 videos/day", "Priority support"],
        "limit_videos": 5,
    },
    "empire": {
        "name": "Empire",
        "plan_id": "plan_empire_monthly",
        "price_cents": 9900,
        "features": ["100 videos/month", "Lite4K Synthesis ONLY", "Priority GPU"],
        "limit_videos": 100,
    },
    "sovereign": {
        "name": "Sovereign",
        "plan_id": "plan_sovereign_monthly",
        "price_cents": 14900,
        "features": ["Sovereign LTX-Video", "500 videos/month", "Private GPU Node"],
        "limit_videos": 500,
    },
    "studio": {
        "name": "Studio",
        "plan_id": "plan_studio_monthly",
        "price_cents": 29900,
        "features": ["Runway/Pika/Wan2.2", "1000 videos/month", "Studio Quality"],
        "limit_videos": 1000,
    },
}


class RazorpayService:
    """Razorpay payment integration for subscriptions"""

    def __init__(
        self,
        key_id: str | None = None,
        key_secret: str | None = None,
    ):
        self._key_id = key_id
        self._key_secret = key_secret
        self._client: razorpay.Client | None = None

    def _ensure_client(self) -> razorpay.Client:
        """Resolve and create Razorpay client dynamically."""
        if self._client:
            return self._client

        if not self._key_id or not self._key_secret:
            from src.api.config import settings
            self._key_id = self._key_id or settings.RAZORPAY_KEY_ID
            self._key_secret = self._key_secret or settings.RAZORPAY_KEY_SECRET

        if not self._key_id or not self._key_secret:
            raise ValueError(
                "Razorpay is not configured. Set RAZORPAY_KEY_ID and "
                "RAZORPAY_KEY_SECRET in environment."
            )

        self._client = razorpay.Client(auth=(self._key_id, self._key_secret))
        return self._client

    async def create_order(
        self,
        amount_cents: int,
        currency: str = "INR",
        receipt: str | None = None,
        notes: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a Razorpay order for one-time payment.

        Args:
            amount_cents: Amount in smallest currency unit (paise for INR).
            currency: ISO 4217 currency code.
            receipt: Optional receipt id for internal tracking.
            notes: Optional key-value metadata.
        """
        client = self._ensure_client()
        payload: dict[str, Any] = {
            "amount": amount_cents,
            "currency": currency,
            "receipt": receipt or f"order_{int(datetime.now().timestamp())}",
        }
        if notes:
            payload["notes"] = notes

        try:
            order = await asyncio.to_thread(client.order.create, payload)
            logger.info(f"[RazorpayService] Created order {order['id']} ({currency} {amount_cents})")
            return {
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "status": order["status"],
            }
        except Exception as e:
            logger.exception(f"[RazorpayService] Failed to create order: {e}")
            raise

    async def verify_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify a Razorpay payment signature.

        Returns True if the signature is valid, False otherwise.
        """
        client = self._ensure_client()
        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                }
            )
            logger.info(
                f"[RazorpayService] Payment verified for order {razorpay_order_id}, "
                f"payment {razorpay_payment_id}"
            )
            return True
        except Exception as e:
            logger.exception(
                f"[RazorpayService] Payment verification failed for order "
                f"{razorpay_order_id}: {e}"
            )
            return False

    async def create_subscription(
        self,
        tier: str,
        customer_id: str,
        start_at: int | None = None,
        notes: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a Razorpay subscription.

        Args:
            tier: Subscription tier key (creator, empire, sovereign, studio).
            customer_id: Razorpay customer ID.
            start_at: Unix timestamp for subscription start (None = immediate).
            notes: Optional key-value metadata.
        """
        tier_info = RAZORPAY_SUBSCRIPTION_TIERS.get(tier)
        if not tier_info or not tier_info.get("plan_id"):
            raise ValueError(f"Invalid tier: {tier}")

        client = self._ensure_client()
        payload: dict[str, Any] = {
            "plan_id": tier_info["plan_id"],
            "customer_id": customer_id,
            "total_count": 12,  # 12 monthly renewals
        }
        if start_at:
            payload["start_at"] = start_at
        if notes:
            payload["notes"] = notes

        try:
            subscription = await asyncio.to_thread(
                client.subscription.create, payload
            )
            logger.info(
                f"[RazorpayService] Created subscription {subscription['id']} "
                f"for tier {tier}"
            )
            return {
                "subscription_id": subscription["id"],
                "plan_id": subscription["plan_id"],
                "status": subscription["status"],
            }
        except Exception as e:
            logger.exception(f"[RazorpayService] Failed to create subscription: {e}")
            raise

    async def cancel_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Cancel a Razorpay subscription at period end."""
        client = self._ensure_client()
        try:
            subscription = await asyncio.to_thread(
                client.subscription.cancel,
                subscription_id,
                {"cancel_at_cycle_end": 1},
            )
            logger.info(f"[RazorpayService] Cancelled subscription {subscription_id}")
            return {
                "id": subscription["id"],
                "status": subscription["status"],
            }
        except Exception as e:
            logger.exception(
                f"[RazorpayService] Failed to cancel subscription {subscription_id}: {e}"
            )
            raise

    async def fetch_customer(self, customer_id: str) -> dict[str, Any]:
        """Fetch a Razorpay customer by ID."""
        client = self._ensure_client()
        try:
            customer = await asyncio.to_thread(
                client.customer.fetch, customer_id
            )
            return {
                "id": customer["id"],
                "name": customer.get("name"),
                "email": customer.get("email"),
                "contact": customer.get("contact"),
            }
        except Exception as e:
            logger.exception(f"[RazorpayService] Failed to fetch customer {customer_id}: {e}")
            raise

    async def create_customer(
        self, email: str, name: str | None = None, contact: str | None = None
    ) -> dict[str, Any]:
        """Create a Razorpay customer."""
        client = self._ensure_client()
        payload: dict[str, Any] = {"email": email}
        if name:
            payload["name"] = name
        if contact:
            payload["contact"] = contact

        try:
            customer = await asyncio.to_thread(
                client.customer.create, payload
            )
            logger.info(
                f"[RazorpayService] Created customer {customer['id']} for {email}"
            )
            return {
                "customer_id": customer["id"],
                "email": customer.get("email"),
                "name": customer.get("name"),
            }
        except Exception as e:
            logger.exception(f"[RazorpayService] Failed to create customer: {e}")
            raise

    async def handle_webhook(
        self, payload: dict[str, Any], signature: str
    ) -> dict[str, Any]:
        """Handle Razorpay webhook events.

        Verify the webhook signature and dispatch to appropriate handler.
        """
        client = self._ensure_client()
        try:
            client.utility.verify_webhook_signature(
                str(payload), signature, self._key_secret
            )
        except Exception as e:
            logger.exception(f"[RazorpayService] Invalid webhook signature: {e}")
            raise

        event = payload.get("event", "")
        entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})

        if event == "subscription.activated":
            return await self._handle_subscription_activated(entity)
        elif event == "subscription.cancelled":
            return await self._handle_subscription_cancelled(entity)
        elif event == "subscription.charged":
            return await self._handle_subscription_charged(entity)
        elif event == "payment.captured":
            return await self._handle_payment_captured(
                payload.get("payload", {}).get("payment", {}).get("entity", {})
            )
        else:
            logger.warning(f"[RazorpayService] Unhandled event: {event}")
            return {"status": "ignored", "event": event}

    async def _handle_subscription_activated(self, entity: dict) -> dict[str, Any]:
        from src.api.utils.user_models import UserDB, SubscriptionTier

        subscription_id = entity.get("id")
        notes = entity.get("notes", {})
        tier_key = notes.get("tier", "free")
        tier_enum_name = RAZORPAY_TIER_MAP.get(tier_key, "FREE")

        async with async_session_factory() as db:
            stmt = select(UserDB).where(
                UserDB.stripe_subscription_id == subscription_id
            )
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                user.subscription = getattr(
                    SubscriptionTier, tier_enum_name, SubscriptionTier.FREE
                )
                await db.commit()
                logger.info(
                    f"[RazorpayService] Activated subscription {subscription_id} "
                    f"for user {user.id} → tier {tier_enum_name}"
                )
        return {"status": "processed", "event": "subscription.activated"}

    async def _handle_subscription_cancelled(self, entity: dict) -> dict[str, Any]:
        from src.api.utils.user_models import UserDB, SubscriptionTier

        subscription_id = entity.get("id")

        async with async_session_factory() as db:
            stmt = select(UserDB).where(
                UserDB.stripe_subscription_id == subscription_id
            )
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                user.subscription = SubscriptionTier.FREE
                user.stripe_subscription_id = None
                await db.commit()
                logger.info(
                    f"[RazorpayService] Cancelled subscription {subscription_id}, "
                    f"reset user {user.id} to FREE"
                )
        return {"status": "processed", "event": "subscription.cancelled"}

    async def _handle_subscription_charged(self, entity: dict) -> dict[str, Any]:
        subscription_id = entity.get("id")
        logger.info(
            f"[RazorpayService] Subscription charged: {subscription_id}"
        )
        return {"status": "processed", "event": "subscription.charged"}

    async def _handle_payment_captured(self, entity: dict) -> dict[str, Any]:
        payment_id = entity.get("id")
        amount = entity.get("amount", 0)
        logger.info(
            f"[RazorpayService] Payment captured: {payment_id} ({amount})"
        )
        return {"status": "processed", "event": "payment.captured"}


# Initialize base service singleton (lazy loaded)
base_razorpay_service = RazorpayService()


def get_razorpay_service() -> RazorpayService:
    base_razorpay_service._ensure_client()
    return base_razorpay_service
