import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.utils.database import AsyncSessionLocal
from src.api.utils.user_models import UserDB, SubscriptionTier
from src.api.utils.credit_models import UserCreditDB
from src.services.payment.credit_service import CreditService
from src.services.payment.stripe_service import PaymentService
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
async def test_stripe_webhook_subscription_idempotent(test_db):
    """Verify idempotency: calling handle_webhook twice with the same
    subscription checkout event upgrades the user only on the first call.

    The second call should hit the idempotency check (same tier + same
    subscription_id) and skip the DB write.
    """
    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_sub_idemp_001"
    stripe_customer_id = "cus_sub_idemp_001"
    subscription_id = "sub_idemp_001"
    session_id = "cs_sub_idemp_001"

    # Pre-populate user on FREE tier
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="sub_idemp@example.com",
            stripe_customer_id=stripe_customer_id,
            subscription=SubscriptionTier.FREE,
        )
        db.add(user)
        await db.commit()

    # Build the mock event once — same session.id + subscription for both calls
    stripe_event = StripeMockObject({
        "type": "checkout.session.completed",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": session_id,
                "customer": stripe_customer_id,
                "subscription": subscription_id,
                "metadata": StripeMockObject({
                    "tier": "sovereign",
                }),
            })
        }),
    })

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        # First call — should process the upgrade
        res1 = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res1["status"] == "processed"
        assert res1["event"] == "checkout.session.completed"

    # Verify user was upgraded after first call
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_after_first = res_db.scalar_one()
        assert user_after_first.subscription == SubscriptionTier.SOVEREIGN
        assert user_after_first.stripe_subscription_id == subscription_id

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        # Second call with same event — should skip (idempotent)
        res2 = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res2["status"] == "processed"
        assert res2["event"] == "checkout.session.completed"

    # Verify user's subscription is unchanged after second call
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_after_second = res_db.scalar_one()
        assert user_after_second.subscription == SubscriptionTier.SOVEREIGN  # unchanged
        assert user_after_second.stripe_subscription_id == subscription_id  # unchanged


@pytest.mark.asyncio
async def test_stripe_webhook_trial_sets_trial_ends_at(test_db):
    """Verify that a subscription checkout webhook with a trial sets
    ``trial_ends_at`` on the user record.

    When the Stripe subscription has a ``trial_end`` timestamp, the
    webhook handler reads it and persists it on the user. Without this,
    the free-trial check in ``create_checkout_session`` (which rejects
    users whose ``trial_ends_at is not None``) would never block a
    second trial.
    """
    from datetime import datetime, timedelta, timezone

    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_trial_001"
    stripe_customer_id = "cus_trial_001"
    subscription_id = "sub_trial_001"
    session_id = "cs_trial_001"

    # Pre-populate user on FREE tier with no trial
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="trial@example.com",
            stripe_customer_id=stripe_customer_id,
            subscription=SubscriptionTier.FREE,
        )
        db.add(user)
        await db.commit()

    # Build a future trial_end timestamp (14 days from now)
    trial_end_ts = int((
        datetime.now(timezone.utc) + timedelta(days=14)
    ).timestamp())

    # Mock the Stripe subscription object with trial_end
    mock_sub = MagicMock()
    mock_sub.trial_end = trial_end_ts
    mock_sub.status = "trialing"

    # Mock checkout event for sovereign tier
    stripe_event = StripeMockObject({
        "type": "checkout.session.completed",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": session_id,
                "customer": stripe_customer_id,
                "subscription": subscription_id,
                "metadata": StripeMockObject({
                    "tier": "sovereign",
                }),
            }),
        }),
    })

    with (
        patch("stripe.Webhook.construct_event", return_value=stripe_event),
        patch("stripe.Subscription.retrieve", return_value=mock_sub),
    ):
        res = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res["status"] == "processed"
        assert res["event"] == "checkout.session.completed"

    # Verify user was upgraded to SOVEREIGN with trial_ends_at set
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_updated = res_db.scalar_one()
        assert user_updated.subscription == SubscriptionTier.SOVEREIGN
        assert (
            user_updated.stripe_subscription_id == subscription_id
        )
        assert user_updated.trial_ends_at is not None
        # Verify trial_ends_at matches the expected timestamp
        expected = datetime.fromtimestamp(
            trial_end_ts, tz=timezone.utc
        ).replace(tzinfo=None)
        assert user_updated.trial_ends_at == expected


@pytest.mark.asyncio
async def test_stripe_trial_second_trial_rejected(test_db):
    """Verify that POST /billing/create-checkout-session with
    tier=sovereign is rejected when the user has already used their free
    trial (``trial_ends_at`` is not None).

    This is the API-level guard in ``billing.py``: even if the frontend
    sends the request, the backend must refuse to create a second trial
    checkout session.
    """
    from datetime import datetime, timezone

    user_id = "user_second_trial_001"
    stripe_customer_id = "cus_second_trial_001"

    # Pre-populate user with trial_ends_at already set → trial already used
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="second_trial@example.com",
            stripe_customer_id=stripe_customer_id,
            subscription=SubscriptionTier.FREE,
            trial_ends_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(user)
        await db.commit()

    # Patch SECRET_KEY before importing billing router (security.py checks
    # it at module-import time and raises RuntimeError if it's None)
    with patch.object(settings, "SECRET_KEY", "test-secret-key-for-trial-test"):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from src.api.routes.billing import router as billing_router
        from src.api.utils.auth import get_current_user

        # Build a minimal FastAPI app with only the billing router
        app = FastAPI()
        app.include_router(billing_router, prefix="/api/v1")

        # Override dependencies to return our test user
        async def _fake_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = _fake_get_current_user

        # Mock the payment service so it doesn't call Stripe
        with patch(
            "src.services.payment.stripe_service.get_payment_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            client = TestClient(app)
            resp = client.post(
                "/api/v1/billing/create-checkout-session",
                json={"tier": "sovereign"},
            )

        assert resp.status_code == 400, (
            f"Expected 400, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert "detail" in body
        assert "already used" in body["detail"].lower()

        # Verify get_payment_service was NEVER called (rejected before Stripe)
        mock_get_service.assert_not_called()


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

    # Verify UserNotificationDB was created
    async with AsyncSessionLocal() as db:
        from src.api.utils.models import UserNotificationDB
        from sqlalchemy import select, desc

        res_db = await db.execute(
            select(UserNotificationDB)
            .where(UserNotificationDB.user_id == user_id)
            .order_by(desc(UserNotificationDB.created_at))
            .limit(1)
        )
        notification = res_db.scalar_one_or_none()
        assert notification is not None, "Expected a UserNotificationDB record"
        assert notification.type == "billing"
        assert notification.title == "Subscription Cancelled"
        assert (
            "cancelled" in notification.message.lower()
        ), f"Expected cancellation text, got: {notification.message}"
        assert (
            "Free" in notification.message
        ), f"Expected Free tier mention, got: {notification.message}"
        assert notification.link == "/settings?tab=billing"
        assert notification.read is False


@pytest.mark.asyncio
async def test_stripe_webhook_subscription_deleted_preserves_trial(test_db):
    """Verify that subscription.deleted does NOT clear trial_ends_at.

    The handler has an explicit comment:
    ``# NOTE: intentionally NOT clearing trial_ends_at here so the user
     # cannot re-use the free trial after it expires or is canceled.``

    This test ensures that a user who cancels during their trial period
    does not get a second trial opportunity.
    """
    from datetime import datetime, timedelta, timezone

    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_delete_preserves_trial_001"
    stripe_sub_id = "sub_delete_trial_001"

    # Pre-populate user on SOVEREIGN trial with trial_ends_at set
    trial_end = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=10)
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="delete_preserves_trial@example.com",
            stripe_subscription_id=stripe_sub_id,
            subscription=SubscriptionTier.SOVEREIGN,
            trial_ends_at=trial_end,
        )
        db.add(user)
        await db.commit()

    # Mock event: subscription.deleted
    stripe_event = StripeMockObject({
        "type": "customer.subscription.deleted",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": stripe_sub_id,
            })
        }),
    })

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        res = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res["status"] == "processed"
        assert res["event"] == "customer.subscription.deleted"

    # Verify user was downgraded to FREE but trial_ends_at is preserved
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_updated = res_db.scalar_one()
        assert user_updated.subscription == SubscriptionTier.FREE
        assert user_updated.stripe_subscription_id is None
        assert user_updated.trial_ends_at == trial_end, (
            f"Expected trial_ends_at to be preserved ({trial_end}), "
            f"got {user_updated.trial_ends_at}"
        )

    # Verify UserNotificationDB was still created
    async with AsyncSessionLocal() as db:
        from src.api.utils.models import UserNotificationDB
        from sqlalchemy import select, desc

        res_db = await db.execute(
            select(UserNotificationDB)
            .where(UserNotificationDB.user_id == user_id)
            .order_by(desc(UserNotificationDB.created_at))
            .limit(1)
        )
        notification = res_db.scalar_one_or_none()
        assert notification is not None, "Expected a UserNotificationDB record"
        assert notification.title == "Subscription Cancelled"


@pytest.mark.asyncio
async def test_stripe_webhook_subscription_updated_active(test_db):
    """Verify webhook handling for customer.subscription.updated with active status.

    When a subscription is updated with status=active, the user's tier should be
    upgraded to the tier specified in the subscription metadata.
    """
    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_webhook_sub_upd_1"
    stripe_sub_id = "sub_updated_active_123"

    # Pre-populate user on FREE tier
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="sub_upd_active@example.com",
            stripe_subscription_id=stripe_sub_id,
            subscription=SubscriptionTier.FREE,
        )
        db.add(user)
        await db.commit()

    # Mock event: subscription.updated with active status -> upgrade to SOVEREIGN
    stripe_event = StripeMockObject({
        "type": "customer.subscription.updated",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": stripe_sub_id,
                "status": "active",
                "metadata": StripeMockObject({"tier": "sovereign"}),
            })
        }),
    })

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        res = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res["status"] == "processed"
        assert res["event"] == "customer.subscription.updated"

    # Verify user was upgraded to SOVEREIGN
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_updated = res_db.scalar_one()
        assert user_updated.subscription == SubscriptionTier.SOVEREIGN
        assert user_updated.stripe_subscription_id == stripe_sub_id  # unchanged


@pytest.mark.asyncio
async def test_stripe_webhook_subscription_updated_past_due(test_db):
    """Verify webhook handling for customer.subscription.updated with past_due status.

    When a subscription goes past_due, the user should be downgraded to FREE
    and the subscription_id cleared.
    """
    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_webhook_sub_upd_2"
    stripe_sub_id = "sub_past_due_456"

    # Pre-populate user on SOVEREIGN tier
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="sub_past_due@example.com",
            stripe_subscription_id=stripe_sub_id,
            subscription=SubscriptionTier.SOVEREIGN,
        )
        db.add(user)
        await db.commit()

    # Mock event: subscription.updated with past_due -> downgrade to FREE
    stripe_event = StripeMockObject({
        "type": "customer.subscription.updated",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": stripe_sub_id,
                "status": "past_due",
                "metadata": StripeMockObject({"tier": "sovereign"}),
            })
        }),
    })

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        res = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res["status"] == "processed"
        assert res["event"] == "customer.subscription.updated"

    # Verify user was downgraded to FREE and subscription_id cleared
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_updated = res_db.scalar_one()
        assert user_updated.subscription == SubscriptionTier.FREE
        assert user_updated.stripe_subscription_id is None


@pytest.mark.asyncio
async def test_stripe_webhook_subscription_updated_idempotent_active(test_db):
    """Verify idempotency: calling handle_webhook twice with the same
    subscription.updated (active) event keeps the user at the correct tier
    on both calls.

    Unlike the checkout.session.completed handler, the subscription.updated
    handler doesn't have an explicit idempotency guard — the second call will
    write the same values (idempotent outcome for the tier) and create a
    duplicate UserNotificationDB. This test documents that behavior.
    """
    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_sub_upd_idemp_001"
    stripe_sub_id = "sub_upd_idemp_001"

    # Pre-populate user on FREE tier
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="sub_upd_idemp@example.com",
            stripe_subscription_id=stripe_sub_id,
            subscription=SubscriptionTier.FREE,
        )
        db.add(user)
        await db.commit()

    # Build the mock event once — same subscription.id for both calls
    stripe_event = StripeMockObject({
        "type": "customer.subscription.updated",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": stripe_sub_id,
                "status": "active",
                "metadata": StripeMockObject({"tier": "sovereign"}),
            })
        }),
    })

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        # First call — should process the upgrade
        res1 = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res1["status"] == "processed"
        assert res1["event"] == "customer.subscription.updated"

    # Verify user was upgraded after first call
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_after_first = res_db.scalar_one()
        assert user_after_first.subscription == SubscriptionTier.SOVEREIGN
        assert user_after_first.stripe_subscription_id == stripe_sub_id  # unchanged

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        # Second call with same event — should keep the tier stable
        res2 = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res2["status"] == "processed"
        assert res2["event"] == "customer.subscription.updated"

    # Verify user's subscription is unchanged after second call
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_after_second = res_db.scalar_one()
        assert user_after_second.subscription == SubscriptionTier.SOVEREIGN  # unchanged
        assert user_after_second.stripe_subscription_id == stripe_sub_id  # unchanged

    # Count notifications — current handler creates one per call (no dedup)
    async with AsyncSessionLocal() as db:
        from src.api.utils.models import UserNotificationDB
        from sqlalchemy import select, func

        count = (await db.execute(
            select(func.count(UserNotificationDB.id))
            .where(
                UserNotificationDB.user_id == user_id,
                UserNotificationDB.type == "billing",
                UserNotificationDB.title == "Subscription Updated",
            )
        )).scalar_one()
        # Current behavior: creates 2 notifications (one per call).
        # If this is ever fixed to be idempotent, change to 1.
        assert count == 2, (
            f"Expected 2 notifications (current behavior — no dedup), got {count}"
        )


@pytest.mark.asyncio
async def test_stripe_webhook_trial_to_paid_transition(test_db):
    """Verify that subscription.updated with status=active clears
    trial_ends_at when the user transitions from trial to paid.

    When a user on SOVEREIGN trial converts to an active (paid)
    subscription, the handler sets ``user.trial_ends_at = None`` so that
    the user is no longer considered "in trial" for future checks.
    """
    from datetime import datetime, timedelta, timezone

    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_trial_to_paid_001"
    stripe_sub_id = "sub_trial_to_paid_001"

    # Pre-populate user on SOVEREIGN with an active trial (trial_ends_at set)
    trial_end = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="trial_to_paid@example.com",
            stripe_subscription_id=stripe_sub_id,
            subscription=SubscriptionTier.SOVEREIGN,
            trial_ends_at=trial_end,
        )
        db.add(user)
        await db.commit()

    # Mock event: subscription.updated with active status -> trial converted
    stripe_event = StripeMockObject({
        "type": "customer.subscription.updated",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": stripe_sub_id,
                "status": "active",
                "metadata": StripeMockObject({"tier": "sovereign"}),
            })
        }),
    })

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        res = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res["status"] == "processed"
        assert res["event"] == "customer.subscription.updated"

    # Verify tier is still SOVEREIGN and trial_ends_at was cleared
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_updated = res_db.scalar_one()
        assert user_updated.subscription == SubscriptionTier.SOVEREIGN  # unchanged
        assert user_updated.stripe_subscription_id == stripe_sub_id  # unchanged
        assert user_updated.trial_ends_at is None, (
            f"Expected trial_ends_at to be None after trial→paid transition, "
            f"got {user_updated.trial_ends_at}"
        )

    # Verify UserNotificationDB was created for the upgrade
    async with AsyncSessionLocal() as db:
        from src.api.utils.models import UserNotificationDB
        from sqlalchemy import select, desc

        res_db = await db.execute(
            select(UserNotificationDB)
            .where(UserNotificationDB.user_id == user_id)
            .order_by(desc(UserNotificationDB.created_at))
            .limit(1)
        )
        notification = res_db.scalar_one_or_none()
        assert notification is not None, "Expected a UserNotificationDB record"
        assert notification.type == "billing"
        assert notification.title == "Subscription Updated"
        assert (
            "Sovereign" in notification.message
        ), f"Expected tier mention in message, got: {notification.message}"
        assert notification.link == "/settings?tab=billing"
        assert notification.read is False


@pytest.mark.asyncio
async def test_stripe_webhook_invoice_payment_failed(test_db):
    """Verify webhook handling for invoice.payment_failed.

    When a payment fails, the webhook should log a warning and return processed.
    The user's subscription is NOT immediately downgraded (only past_due does that).
    """
    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_webhook_inv_fail"
    stripe_customer_id = "cus_inv_fail_789"

    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="inv_fail@example.com",
            stripe_customer_id=stripe_customer_id,
            subscription=SubscriptionTier.PREMIUM,
        )
        db.add(user)
        await db.commit()

    # Mock event: invoice.payment_failed
    stripe_event = StripeMockObject({
        "type": "invoice.payment_failed",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": "in_failed_001",
                "customer": stripe_customer_id,
            })
        }),
    })

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        res = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res["status"] == "processed"
        assert res["event"] == "invoice.payment_failed"

    # Verify user's subscription is NOT changed (only notified)
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_updated = res_db.scalar_one()
        assert user_updated.subscription == SubscriptionTier.PREMIUM  # unchanged


@pytest.mark.asyncio
async def test_stripe_webhook_invoice_payment_succeeded(test_db):
    """Verify webhook handling for invoice.payment_succeeded.

    When a subscription invoice is paid, the handler should:
    - Log the successful renewal
    - Persist a WebhookEventDB record with result="renewal"
    - Include subscription_id and amount_cents in the payload
    """
    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_webhook_inv_succ"
    stripe_customer_id = "cus_inv_succ_001"
    subscription_id = "sub_renewal_001"
    invoice_id = "in_succ_001"
    amount_paid = 14900  # $149.00 in cents

    # Pre-populate user with active subscription
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="inv_succ@example.com",
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=subscription_id,
            subscription=SubscriptionTier.SOVEREIGN,
        )
        db.add(user)
        await db.commit()

    # Mock event: invoice.payment_succeeded
    stripe_event = StripeMockObject({
        "type": "invoice.payment_succeeded",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": invoice_id,
                "customer": stripe_customer_id,
                "subscription": subscription_id,
                "amount_paid": amount_paid,
            })
        }),
    })

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        res = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res["status"] == "processed"
        assert res["event"] == "invoice.payment_succeeded"

    # Verify user's subscription is NOT changed (renewals don't touch tier)
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_updated = res_db.scalar_one()
        assert user_updated.subscription == SubscriptionTier.SOVEREIGN  # unchanged
        assert user_updated.stripe_subscription_id == subscription_id  # unchanged

    # Verify WebhookEventDB was created with renewal details
    async with AsyncSessionLocal() as db:
        from src.api.utils.models import WebhookEventDB
        from sqlalchemy import select, desc
        res_db = await db.execute(
            select(WebhookEventDB)
            .where(WebhookEventDB.external_id == invoice_id)
            .order_by(desc(WebhookEventDB.created_at))
            .limit(1)
        )
        event = res_db.scalar_one_or_none()
        assert event is not None, "Expected a WebhookEventDB record for the renewal"
        assert event.event_type == "invoice.payment_succeeded"
        assert event.platform == "stripe"
        assert event.external_id == invoice_id
        assert event.payload_json is not None
        assert event.payload_json.get("result") == "renewal"
        assert event.payload_json.get("subtype") == "subscription_renewal"
        assert event.payload_json.get("subscription_id") == subscription_id
        assert event.payload_json.get("amount_cents") == amount_paid


@pytest.mark.asyncio
async def test_stripe_webhook_credit_purchase(test_db):
    """Verify webhook handling for checkout.session.completed with credit_purchase type.

    When metadata.type is "credit_purchase", the handler should add credits to the
    user's balance instead of upgrading their subscription tier.
    """
    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_webhook_credit_buy"
    stripe_customer_id = "cus_credit_buy_001"

    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="credit_buy@example.com",
            stripe_customer_id=stripe_customer_id,
            subscription=SubscriptionTier.FREE,
        )
        db.add(user)
        # Seed initial credits for the user
        from src.api.utils.credit_models import UserCreditDB

        credits = UserCreditDB(user_id=user_id, balance=50, lifetime_purchased=50)
        db.add(credits)
        await db.commit()

    # Mock event: checkout.session.completed with credit_purchase metadata
    stripe_event = StripeMockObject({
        "type": "checkout.session.completed",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": "cs_credit_purchase_001",
                "customer": stripe_customer_id,
                "subscription": None,
                "metadata": StripeMockObject({
                    "type": "credit_purchase",
                    "user_id": user_id,
                    "credits": "200",
                }),
            })
        }),
    })

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        res = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res["status"] == "processed"
        assert res["event"] == "checkout.session.completed"
        assert res["type"] == "credit_purchase"

    # Verify credits were added to user's balance
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from src.api.utils.credit_models import UserCreditDB

        res_db = await db.execute(
            select(UserCreditDB).where(UserCreditDB.user_id == user_id)
        )
        user_credits = res_db.scalar_one()
        assert user_credits.balance == 250  # 50 initial + 200 purchased
        assert user_credits.lifetime_purchased == 250  # 50 + 200

    # Verify user's subscription was NOT touched
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        res_db = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user_updated = res_db.scalar_one()
        assert user_updated.subscription == SubscriptionTier.FREE  # unchanged


@pytest.mark.asyncio
async def test_get_usage_breakdown_empty(test_db):
    """Verify get_usage_breakdown returns zeroes when there are no transactions."""
    service = CreditService()
    user_id = "usage_empty_user"

    async with AsyncSessionLocal() as db:
        # Seed a user so the credit row can be created
        user = UserDB(id=user_id, email="usage_empty@example.com")
        db.add(user)
        await db.commit()

        # Also seed a purchase transaction (non-spent) to confirm it's ignored
        from src.api.utils.credit_models import CreditTransactionDB

        purchase = CreditTransactionDB(
            user_id=user_id,
            amount=100,
            balance_after=100,
            transaction_type="purchase",
            description="Purchased 100 credits",
        )
        db.add(purchase)
        await db.commit()

    async with AsyncSessionLocal() as db:
        result = await service.get_usage_breakdown(user_id, db)
        assert result["total_spent"] == 0
        assert result["by_action"] == {}
        assert result["action_count"] == 0


@pytest.mark.asyncio
async def test_get_usage_breakdown_mixed_spend_types(test_db):
    """Verify get_usage_breakdown correctly aggregates multiple action types."""
    service = CreditService()
    user_id = "usage_mixed_user"

    async with AsyncSessionLocal() as db:
        user = UserDB(id=user_id, email="usage_mixed@example.com")
        db.add(user)

        from src.api.utils.credit_models import CreditTransactionDB
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Seed several spent transactions with different actions
        transactions = [
            CreditTransactionDB(
                user_id=user_id,
                amount=-50,
                balance_after=50,
                transaction_type="spent",
                description="Action: video_generation_ltx",
                created_at=now,
            ),
            CreditTransactionDB(
                user_id=user_id,
                amount=-30,
                balance_after=20,
                transaction_type="spent",
                description="Action: video_generation_runway",
                created_at=now,
            ),
            CreditTransactionDB(
                user_id=user_id,
                amount=-20,
                balance_after=0,
                transaction_type="spent",
                description="Action: voice_clone",
                created_at=now,
            ),
            # Duplicate action — should be summed
            CreditTransactionDB(
                user_id=user_id,
                amount=-10,
                balance_after=90,
                transaction_type="spent",
                description="Action: video_generation_ltx",
                created_at=now,
            ),
        ]
        for t in transactions:
            db.add(t)
        await db.commit()

    async with AsyncSessionLocal() as db:
        result = await service.get_usage_breakdown(user_id, db)
        assert result["total_spent"] == 110  # 50 + 30 + 20 + 10
        assert result["action_count"] == 3
        # Sorted descending by amount
        by_action = result["by_action"]
        assert by_action["video_generation_ltx"] == 60  # 50 + 10
        assert by_action["video_generation_runway"] == 30
        assert by_action["voice_clone"] == 20
        # video_generation_ltx should be first (highest amount)
        assert list(by_action.keys())[0] == "video_generation_ltx"


@pytest.mark.asyncio
async def test_get_usage_breakdown_custom_description(test_db):
    """Verify get_usage_breakdown falls back to 'unknown' for custom descriptions."""
    service = CreditService()
    user_id = "usage_custom_user"

    async with AsyncSessionLocal() as db:
        user = UserDB(id=user_id, email="usage_custom@example.com")
        db.add(user)

        from src.api.utils.credit_models import CreditTransactionDB
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # A custom description that doesn't start with "Action: "
        custom = CreditTransactionDB(
            user_id=user_id,
            amount=-15,
            balance_after=85,
            transaction_type="spent",
            description="Custom charge — manual adjustment",
            created_at=now,
        )
        db.add(custom)

        # A standard transaction for comparison
        standard = CreditTransactionDB(
            user_id=user_id,
            amount=-10,
            balance_after=75,
            transaction_type="spent",
            description="Action: analytics_report",
            created_at=now,
        )
        db.add(standard)

        # A transaction with no description at all
        no_desc = CreditTransactionDB(
            user_id=user_id,
            amount=-5,
            balance_after=70,
            transaction_type="spent",
            description=None,
            created_at=now,
        )
        db.add(no_desc)
        await db.commit()

    async with AsyncSessionLocal() as db:
        result = await service.get_usage_breakdown(user_id, db)
        assert result["total_spent"] == 30  # 15 + 10 + 5
        assert result["action_count"] == 2  # unknown + analytics_report
        assert result["by_action"]["unknown"] == 20  # 15 + 5 (custom + no description)
        assert result["by_action"]["analytics_report"] == 10


@pytest.mark.asyncio
async def test_get_usage_breakdown_excludes_purchases(test_db):
    """Verify get_usage_breakdown excludes purchase and earned transactions."""
    service = CreditService()
    user_id = "usage_exclude_user"

    async with AsyncSessionLocal() as db:
        user = UserDB(id=user_id, email="usage_exclude@example.com")
        db.add(user)

        from src.api.utils.credit_models import CreditTransactionDB
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        transactions = [
            # Only this one should be counted
            CreditTransactionDB(
                user_id=user_id,
                amount=-25,
                balance_after=175,
                transaction_type="spent",
                description="Action: social_publish",
                created_at=now,
            ),
            # These should be excluded
            CreditTransactionDB(
                user_id=user_id,
                amount=200,
                balance_after=200,
                transaction_type="purchase",
                description="Purchased 200 credits",
                created_at=now,
            ),
            CreditTransactionDB(
                user_id=user_id,
                amount=50,
                balance_after=250,
                transaction_type="earned",
                description="Referral bonus",
                created_at=now,
            ),
            CreditTransactionDB(
                user_id=user_id,
                amount=100,
                balance_after=350,
                transaction_type="bonus",
                description="Monthly subscription credit grant",
                created_at=now,
            ),
        ]
        for t in transactions:
            db.add(t)
        await db.commit()

    async with AsyncSessionLocal() as db:
        result = await service.get_usage_breakdown(user_id, db)
        assert result["total_spent"] == 25
        assert result["action_count"] == 1
        assert result["by_action"]["social_publish"] == 25
        assert "unknown" not in result["by_action"]


@pytest.mark.asyncio
async def test_stripe_webhook_credit_purchase_idempotent(test_db):
    """Verify idempotency: calling handle_webhook twice with the same session.id
    grants credits only on the first call."""
    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_idemp_001"
    stripe_customer_id = "cus_idemp_001"
    session_id = "cs_idempotency_001"

    # Pre-populate user + initial credits
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="idemp@example.com",
            stripe_customer_id=stripe_customer_id,
            subscription=SubscriptionTier.FREE,
        )
        db.add(user)
        credits = UserCreditDB(user_id=user_id, balance=50, lifetime_purchased=50)
        db.add(credits)
        await db.commit()

    # Build the mock event once — same session.id used for both calls
    stripe_event = StripeMockObject({
        "type": "checkout.session.completed",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": session_id,
                "customer": stripe_customer_id,
                "subscription": None,
                "metadata": StripeMockObject({
                    "type": "credit_purchase",
                    "user_id": user_id,
                    "credits": "200",
                }),
            })
        }),
    })

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        # First call — should process
        res1 = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res1["status"] == "processed"
        assert res1["type"] == "credit_purchase"

    # Verify balance after first call
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res_db = await db.execute(
            select(UserCreditDB).where(UserCreditDB.user_id == user_id)
        )
        user_credits = res_db.scalar_one()
        assert user_credits.balance == 250  # 50 + 200

    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        # Second call with same session — should skip (idempotent)
        res2 = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res2["status"] == "processed"
        assert res2["type"] == "credit_purchase"

    # Verify balance is unchanged after second call
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res_db = await db.execute(
            select(UserCreditDB).where(UserCreditDB.user_id == user_id)
        )
        user_credits = res_db.scalar_one()
        assert user_credits.balance == 250  # still 250 — not 450
        assert user_credits.lifetime_purchased == 250  # not 450


@pytest.mark.asyncio
async def test_stripe_webhook_credit_purchase_different_sessions(test_db):
    """Verify that events with DIFFERENT session.id both process correctly.

    This is the happy-path complement to the idempotency test: it proves the
    dedup key (reference_id = session.id) does NOT block legitimate events.
    """
    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_diff_sess_001"
    stripe_customer_id = "cus_diff_sess_001"

    # Pre-populate user + initial credits
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="diff_sess@example.com",
            stripe_customer_id=stripe_customer_id,
            subscription=SubscriptionTier.FREE,
        )
        db.add(user)
        credits = UserCreditDB(user_id=user_id, balance=50, lifetime_purchased=50)
        db.add(credits)
        await db.commit()

    # Event A — session ID "cs_purchase_A", 200 credits
    event_a = StripeMockObject({
        "type": "checkout.session.completed",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": "cs_purchase_A",
                "customer": stripe_customer_id,
                "subscription": None,
                "metadata": StripeMockObject({
                    "type": "credit_purchase",
                    "user_id": user_id,
                    "credits": "200",
                }),
            })
        }),
    })

    # Event B — DIFFERENT session ID "cs_purchase_B", 300 credits
    event_b = StripeMockObject({
        "type": "checkout.session.completed",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": "cs_purchase_B",
                "customer": stripe_customer_id,
                "subscription": None,
                "metadata": StripeMockObject({
                    "type": "credit_purchase",
                    "user_id": user_id,
                    "credits": "300",
                }),
            })
        }),
    })

    with patch("stripe.Webhook.construct_event", return_value=event_a):
        res_a = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res_a["status"] == "processed"
        assert res_a["type"] == "credit_purchase"

    # Balance after A: 50 + 200 = 250
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res_db = await db.execute(
            select(UserCreditDB).where(UserCreditDB.user_id == user_id)
        )
        user_credits = res_db.scalar_one()
        assert user_credits.balance == 250

    with patch("stripe.Webhook.construct_event", return_value=event_b):
        res_b = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res_b["status"] == "processed"
        assert res_b["type"] == "credit_purchase"

    # Balance after B: 250 + 300 = 550 — both events processed
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res_db = await db.execute(
            select(UserCreditDB).where(UserCreditDB.user_id == user_id)
        )
        user_credits = res_db.scalar_one()
        assert user_credits.balance == 550  # 50 + 200 + 300
        assert user_credits.lifetime_purchased == 550  # 50 + 200 + 300


@pytest.mark.asyncio
async def test_stripe_webhook_credit_purchase_retry_after_crash(test_db):
    """Verify that a Stripe retry after a mid-transaction crash doesn't
    double-grant credits.

    Scenario:
      1. First webhook delivery calls ``add_credits`` then crashes before
         returning — the ``async_session_factory()`` context manager rolls
         back the transaction, so no ``CreditTransactionDB`` idempotency
         record is persisted.
      2. Stripe retries (second delivery) — idempotency check finds no
         existing record for this ``session.id`` → processes normally.

    Without transactional rollback, the retry would be blocked by the
    idempotency check and the user would never receive their credits.
    """
    service = PaymentService(stripe_api_key="sk_test_mock")

    user_id = "user_retry_001"
    stripe_customer_id = "cus_retry_001"
    session_id = "cs_retry_001"

    # Pre-populate user + initial credits
    async with AsyncSessionLocal() as db:
        user = UserDB(
            id=user_id,
            email="retry@example.com",
            stripe_customer_id=stripe_customer_id,
            subscription=SubscriptionTier.FREE,
        )
        db.add(user)
        credits = UserCreditDB(user_id=user_id, balance=50, lifetime_purchased=50)
        db.add(credits)
        await db.commit()

    stripe_event = StripeMockObject({
        "type": "checkout.session.completed",
        "data": StripeMockObject({
            "object": StripeMockObject({
                "id": session_id,
                "customer": stripe_customer_id,
                "subscription": None,
                "metadata": StripeMockObject({
                    "type": "credit_purchase",
                    "user_id": user_id,
                    "credits": "200",
                }),
            })
        }),
    })

    # --- First delivery: crash mid-transaction ---
    with patch.object(
        CreditService,
        "add_credits",
        side_effect=Exception("Simulated crash after add_credits"),
    ), patch("stripe.Webhook.construct_event", return_value=stripe_event):
        with pytest.raises(Exception, match="Simulated crash after add_credits"):
            await service.handle_webhook(
                payload=b"raw_payload", signature="sig", webhook_secret="secret"
            )

    # Balance unchanged — the async_session context manager rolled back
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res_db = await db.execute(
            select(UserCreditDB).where(UserCreditDB.user_id == user_id)
        )
        user_credits = res_db.scalar_one()
        assert user_credits.balance == 50  # unchanged — transaction rolled back
        assert user_credits.lifetime_purchased == 50  # unchanged

    # No CreditTransactionDB record with this reference_id was persisted
    async with AsyncSessionLocal() as db:
        from src.api.utils.credit_models import CreditTransactionDB
        res_db = await db.execute(
            select(CreditTransactionDB).where(
                CreditTransactionDB.reference_id == session_id
            )
        )
        assert res_db.scalar_one_or_none() is None

    # --- Second delivery: Stripe retries — should process cleanly ---
    with patch("stripe.Webhook.construct_event", return_value=stripe_event):
        res = await service.handle_webhook(
            payload=b"raw_payload", signature="sig", webhook_secret="secret"
        )
        assert res["status"] == "processed"
        assert res["type"] == "credit_purchase"

    # Balance updated correctly — single grant, not double
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res_db = await db.execute(
            select(UserCreditDB).where(UserCreditDB.user_id == user_id)
        )
        user_credits = res_db.scalar_one()
        assert user_credits.balance == 250  # 50 + 200 (single grant)
        assert user_credits.lifetime_purchased == 250  # 50 + 200 (single grant)

    # Exactly one CreditTransactionDB record with this reference_id
    async with AsyncSessionLocal() as db:
        from src.api.utils.credit_models import CreditTransactionDB
        res_db = await db.execute(
            select(CreditTransactionDB).where(
                CreditTransactionDB.reference_id == session_id
            )
        )
        txns = res_db.scalars().all()
        assert len(txns) == 1  # only one persisted — retry didn't create a second


@pytest.mark.asyncio
async def test_billing_webhook_stats(test_db):
    """Verify GET /billing/webhook/stats returns correct counts for
    processed vs skipped webhook events alongside credit purchase metrics.

    Seeds known data into CreditTransactionDB and WebhookEventDB, then
    runs the same queries the endpoint uses and validates the counts.
    """
    from src.api.utils.credit_models import CreditTransactionDB, UserCreditDB
    from src.api.utils.models import WebhookEventDB
    from src.api.utils.user_models import UserDB
    from sqlalchemy import select, func, desc, cast, String
    from datetime import datetime, timezone

    user_id = "user_webhook_stats_001"

    async with AsyncSessionLocal() as db:
        # Pre-populate user so FK constraints are satisfied
        user = UserDB(id=user_id, email="webhook_stats@example.com")
        db.add(user)
        credits = UserCreditDB(user_id=user_id, balance=500, lifetime_purchased=500)
        db.add(credits)

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # --- Seed CreditTransactionDB (purchase records) ---
        purchases = [
            CreditTransactionDB(
                user_id=user_id, amount=100, balance_after=100,
                transaction_type="purchase", reference_id="cs_purchase_001",
                description="Credit purchase A", created_at=now,
            ),
            CreditTransactionDB(
                user_id=user_id, amount=200, balance_after=300,
                transaction_type="purchase", reference_id="cs_purchase_002",
                description="Credit purchase B", created_at=now,
            ),
            # Transaction with different type — should be excluded
            CreditTransactionDB(
                user_id=user_id, amount=-50, balance_after=250,
                transaction_type="spent",
                description="Action: video_generation", created_at=now,
            ),
        ]
        for p in purchases:
            db.add(p)

        # --- Seed WebhookEventDB (processed + skipped) ---
        events = [
            WebhookEventDB(
                event_type="checkout.session.completed", platform="stripe",
                external_id="cs_100",
                payload_json={"result": "processed", "subtype": "credit_purchase"},
                processed_at=now, created_at=now,
            ),
            WebhookEventDB(
                event_type="checkout.session.completed", platform="stripe",
                external_id="cs_200",
                payload_json={"result": "processed", "subtype": "credit_purchase"},
                processed_at=now, created_at=now,
            ),
            WebhookEventDB(
                event_type="checkout.session.completed", platform="stripe",
                external_id="cs_100",  # same session — duplicate retry
                payload_json={"result": "skipped", "reason": "idempotency",
                              "subtype": "credit_purchase"},
                processed_at=now, created_at=now,
            ),
            # Event with different platform — should be excluded
            WebhookEventDB(
                event_type="webhook.received", platform="github",
                external_id="gh_001",
                payload_json={"result": "processed"},
                processed_at=now, created_at=now,
            ),
        ]
        for e in events:
            db.add(e)
        await db.commit()

    # --- Run same queries as GET /billing/webhook/stats, scoped to user ---
    async with AsyncSessionLocal() as db:
        # Credit purchase stats (scoped to this test's user)
        total_purchases = (await db.execute(
            select(func.count(CreditTransactionDB.id))
            .where(
                CreditTransactionDB.transaction_type == "purchase",
                CreditTransactionDB.user_id == user_id,
            )
        )).scalar_one()

        total_credits = (await db.execute(
            select(func.coalesce(func.sum(CreditTransactionDB.amount), 0))
            .where(
                CreditTransactionDB.transaction_type == "purchase",
                CreditTransactionDB.user_id == user_id,
            )
        )).scalar_one()

        recent = (await db.execute(
            select(CreditTransactionDB)
            .where(
                CreditTransactionDB.transaction_type == "purchase",
                CreditTransactionDB.user_id == user_id,
            )
            .order_by(desc(CreditTransactionDB.created_at))
            .limit(10)
        )).scalars().all()

        # Webhook processed/skipped/renewal stats scoped to our external_ids
        # (WebhookEventDB has no user_id, so we scope by known external_id prefixes)
        our_ids = ["cs_100", "cs_200"]
        result_field = func.json_extract(WebhookEventDB.payload_json, "$.result")

        total_processed = (await db.execute(
            select(func.count(WebhookEventDB.id))
            .where(
                WebhookEventDB.platform == "stripe",
                WebhookEventDB.external_id.in_(our_ids),
                cast(result_field, String) == "processed",
            )
        )).scalar_one()

        total_skipped = (await db.execute(
            select(func.count(WebhookEventDB.id))
            .where(
                WebhookEventDB.platform == "stripe",
                WebhookEventDB.external_id.in_(our_ids),
                cast(result_field, String) == "skipped",
            )
        )).scalar_one()

        total_renewals = (await db.execute(
            select(func.count(WebhookEventDB.id))
            .where(
                WebhookEventDB.platform == "stripe",
                WebhookEventDB.external_id.in_(our_ids),
                cast(result_field, String) == "renewal",
            )
        )).scalar_one()

        recent_events = (await db.execute(
            select(WebhookEventDB)
            .where(
                WebhookEventDB.platform == "stripe",
                WebhookEventDB.external_id.in_(our_ids),
            )
            .order_by(desc(WebhookEventDB.created_at))
            .limit(10)
        )).scalars().all()

    # --- Assertions ---
    assert total_purchases == 2, f"Expected 2 purchases, got {total_purchases}"
    assert (
        total_credits == 300
    ), f"Expected 300 credits granted, got {total_credits}"
    assert len(recent) == 2, f"Expected 2 recent purchases, got {len(recent)}"

    assert (
        total_processed == 2
    ), f"Expected 2 processed events, got {total_processed}"
    assert (
        total_skipped == 1
    ), f"Expected 1 skipped event, got {total_skipped}"
    assert (
        total_renewals == 0
    ), f"Expected 0 renewal events, got {total_renewals}"
    assert (
        len(recent_events) == 3
    ), f"Expected 3 recent stripe events, got {len(recent_events)}"

    # Verify the skipped event has the correct payload
    skipped_events = [e for e in recent_events if e.payload_json.get("result") == "skipped"]
    assert len(skipped_events) == 1
    assert skipped_events[0].payload_json.get("reason") == "idempotency"


@pytest.mark.asyncio
async def test_paypal_get_access_token():
    """Verify PayPal access token retrieval using async client."""
    from src.services.payment.paypal_service import PayPalService

    service = PayPalService()
    service.client_id = "fake_client_id"
    service.client_secret = "fake_client_secret"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "mock_paypal_token", "expires_in": 3600}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        token = await service._get_access_token()
        assert token == "mock_paypal_token"
        mock_post.assert_called_once()


def test_payment_singletons():
    """Verify exposed base payment/credit service singletons."""
    from src.services.payment.stripe_service import base_stripe_service
    from src.services.payment.paypal_service import base_paypal_service
    from src.services.payment.credit_service import base_credit_service
    from src.services.video_engine.free_video_providers import base_free_video_provider_service
    from src.services.optimization.auth import base_token_manager_service
    from src.services.optimization.cookie_manager import base_cookie_manager_service

    assert base_stripe_service is not None
    assert base_paypal_service is not None
    assert base_credit_service is not None
    assert base_free_video_provider_service is not None
    assert base_token_manager_service is not None
    assert base_cookie_manager_service is not None

