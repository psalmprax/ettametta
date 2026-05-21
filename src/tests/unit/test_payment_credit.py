import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import stripe
from datetime import datetime, timezone

from src.api.utils.database import AsyncSessionLocal
from src.api.utils.user_models import UserDB, SubscriptionTier
from src.api.utils.credit_models import UserCreditDB, CreditTransactionDB
from src.services.payment.credit_service import CreditService
from src.services.payment.stripe_service import PaymentService, SUBSCRIPTION_TIERS
from src.api.config import settings


class StripeMockObject(dict):
    """Mock object that supports both dict-like and attribute-like access."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


@pytest.mark.asyncio
async def test_get_or_create_user_credits(test_db):
    """Verify that a user credit entry is created if it does not exist."""
    service = CreditService()
    user_id = "test_user_123"

    async with AsyncSessionLocal() as db:
        # Check initial state (should not exist in DB)
        from sqlalchemy import select
        res = await db.execute(select(UserCreditDB).where(UserCreditDB.user_id == user_id))
        assert res.scalar_one_or_none() is None

        # Fetch using service
        user_credits = await service.get_user_credits(user_id, db)
        assert user_credits.user_id == user_id
        assert user_credits.balance == 0
        assert user_credits.lifetime_spent == 0

        # Fetch again to verify it exists now
        res = await db.execute(select(UserCreditDB).where(UserCreditDB.user_id == user_id))
        assert res.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_credit_operations(test_db):
    """Verify get_balance, add_credits, and consume_credits."""
    service = CreditService()
    user_id = "test_user_456"

    async with AsyncSessionLocal() as db:
        # Initial balance
        balance = await service.get_balance(user_id, db)
        assert balance == 0

        # Add credits (purchase)
        success = await service.add_credits(
            user_id=user_id,
            amount=100,
            transaction_type="purchase",
            db=db,
            description="Purchased 100 credits",
            auto_commit=False
        )
        assert success is True
        await db.commit()

    async with AsyncSessionLocal() as db:
        # Verify balance updated
        assert await service.get_balance(user_id, db) == 100
        assert await service.has_sufficient_credits(user_id, 50, db) is True
        assert await service.has_sufficient_credits(user_id, 150, db) is False

        # Consume credits success
        ok, msg = await service.consume_credits(
            user_id=user_id,
            amount=40,
            action="video_generation_ltx",
            db=db,
            auto_commit=False
        )
        assert ok is True
        assert "consumed successfully" in msg
        await db.commit()

    async with AsyncSessionLocal() as db:
        # Verify deducted balance
        assert await service.get_balance(user_id, db) == 60

        # Consume credits failure (insufficient)
        ok, msg = await service.consume_credits(
            user_id=user_id,
            amount=70,
            action="video_generation_hunyuan",
            db=db,
            auto_commit=False
        )
        assert ok is False
        assert "Insufficient credits" in msg


@pytest.mark.asyncio
async def test_stripe_create_customer():
    """Verify Stripe customer creation helper."""
    service = PaymentService(stripe_api_key="sk_test_mock")
    
    mock_customer = MagicMock()
    mock_customer.id = "cus_mock123"
    mock_customer.email = "test@example.com"
    
    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = mock_customer
        
        res = await service.create_customer(email="test@example.com", user_id="user_abc")
        assert res["stripe_customer_id"] == "cus_mock123"
        assert res["email"] == "test@example.com"
        mock_to_thread.assert_called_once()


@pytest.mark.asyncio
async def test_stripe_create_subscription():
    """Verify Stripe checkout session creation for subscriptions."""
    service = PaymentService(stripe_api_key="sk_test_mock")
    
    mock_session = MagicMock()
    mock_session.id = "sess_mock123"
    mock_session.url = "https://checkout.stripe.com/pay/sess_mock123"
    
    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread, \
         patch.object(settings, "PRODUCTION_DOMAIN", "https://ettametta.com"):
        mock_to_thread.return_value = mock_session
        
        res = await service.create_subscription(
            stripe_customer_id="cus_mock123",
            tier="sovereign"
        )
        assert res["session_id"] == "sess_mock123"
        assert res["url"] == "https://checkout.stripe.com/pay/sess_mock123"


@pytest.mark.asyncio
async def test_stripe_get_and_cancel_subscription():
    """Verify retrieval and cancellation logic for Stripe subscriptions."""
    service = PaymentService(stripe_api_key="sk_test_mock")
    
    mock_sub = MagicMock()
    mock_sub.id = "sub_mock123"
    mock_sub.status = "active"
    mock_sub.current_period_end = 1716298800
    mock_sub.cancel_at = 1716298800
    mock_sub.metadata = {"tier": "sovereign"}
    
    with patch("stripe.Subscription.retrieve", return_value=mock_sub), \
         patch("stripe.Subscription.modify", return_value=mock_sub):
        
        # Test retrieve
        get_res = await service.get_subscription("sub_mock123")
        assert get_res["id"] == "sub_mock123"
        assert get_res["status"] == "active"
        assert get_res["tier"] == "sovereign"
        
        # Test cancel
        cancel_res = await service.cancel_subscription("sub_mock123")
        assert cancel_res["id"] == "sub_mock123"
        assert cancel_res["status"] == "active"


@pytest.mark.asyncio
async def test_stripe_webhook_checkout_completed(test_db):
    """Verify webhook handling for checkout.session.completed."""
    service = PaymentService(stripe_api_key="sk_test_mock")
    
    user_id = "user_webhook_123"
    stripe_customer_id = "cus_webhook_123"
    
    # Pre-populate user in db
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="web@example.com",
            stripe_customer_id=stripe_customer_id,
            subscription=SubscriptionTier.FREE
        )
        db.add(user)
        await db.commit()

    # Define mock event payload
    stripe_event = StripeMockObject({
        "type": "checkout.session.completed",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": "cs_test_completed",
                "customer": stripe_customer_id,
                "subscription": "sub_active_123",
                "metadata": StripeMockObject({
                    "tier": "sovereign"
                })
            })
        })
    })
    
    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        res = await service.handle_webhook(
            payload=b"raw_payload",
            signature="sig",
            webhook_secret="secret"
        )
        assert res["status"] == "processed"
        assert res["event"] == "checkout.session.completed"

    # Verify user's subscription tier was upgraded in database
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_updated = res_db.scalar_one()
        assert user_updated.subscription == SubscriptionTier.SOVEREIGN
        assert user_updated.stripe_subscription_id == "sub_active_123"


@pytest.mark.asyncio
async def test_stripe_webhook_subscription_deleted(test_db):
    """Verify webhook handling for customer.subscription.deleted."""
    service = PaymentService(stripe_api_key="sk_test_mock")
    
    user_id = "user_webhook_456"
    stripe_sub_id = "sub_deleted_123"
    
    # Pre-populate active subscriber in db
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="web_sub@example.com",
            stripe_subscription_id=stripe_sub_id,
            subscription=SubscriptionTier.SOVEREIGN
        )
        db.add(user)
        await db.commit()

    # Define mock event payload
    stripe_event = StripeMockObject({
        "type": "customer.subscription.deleted",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": stripe_sub_id
            })
        })
    })
    
    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        res = await service.handle_webhook(
            payload=b"raw_payload",
            signature="sig",
            webhook_secret="secret"
        )
        assert res["status"] == "processed"

    # Verify user was downgraded to FREE tier
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_updated = res_db.scalar_one()
        assert user_updated.subscription == SubscriptionTier.FREE
        assert user_updated.stripe_subscription_id is None
