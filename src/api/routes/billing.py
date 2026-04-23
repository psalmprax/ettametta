"""
Billing API Routes for ettametta
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from src.api.utils.user_models import UserDB
from src.api.routes.auth import get_current_user
from src.api.utils.database import get_db
from src.api.utils.subscription import get_subscription_tier_value
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.api.config import settings
from src.api.utils.api_responses import success_response, handle_exception

router = APIRouter(prefix="/billing", tags=["Billing"])


class CreateCheckoutRequest(BaseModel):
    tier: str  # "creator" or "empire"


class SubscriptionResponse(BaseModel):
    tier: str
    status: str
    current_period_end: str | None = None


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe checkout session for subscription"""
    from src.services.payment.stripe_service import (
        get_payment_service,
        SUBSCRIPTION_TIERS,
    )

    # Validate tier
    if request.tier not in SUBSCRIPTION_TIERS:
        raise HTTPException(status_code=400, detail="Invalid tier")

    tier_info = SUBSCRIPTION_TIERS[request.tier]
    if not tier_info.get("price_id"):
        raise HTTPException(status_code=400, detail="Tier not available for purchase")

    # Get or create Stripe customer
    try:
        # Check if user has stripe_customer_id
        stripe_customer_id = getattr(current_user, "stripe_customer_id", None)

        # Get payment service instance (reuse throughout function)
        payment_service = get_payment_service()

        if not stripe_customer_id:
            # Create Stripe customer
            customer = await payment_service.create_customer(
                email=current_user.email, user_id=current_user.id
            )
            stripe_customer_id = customer["stripe_customer_id"]

            # Save stripe_customer_id to user record
            current_user.stripe_customer_id = stripe_customer_id
            await db.commit()

        # Create checkout session
        result = await payment_service.create_subscription(
            stripe_customer_id=stripe_customer_id, tier=request.tier
        )
        return success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        return handle_exception(e)


@router.get("/subscription")
async def get_subscription(
    current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get current user's subscription status"""
    from src.services.payment.stripe_service import (
        get_payment_service,
        SUBSCRIPTION_TIERS,
    )

    try:
        stmt = select(UserDB).where(UserDB.id == current_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        tier = get_subscription_tier_value(user)
        tier_info = SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS["free"])

        # If user has a stripe subscription, get live status
        if user.stripe_subscription_id:
            try:
                payment_service = get_payment_service()
                sub_info = await payment_service.get_subscription(
                    user.stripe_subscription_id
                )
                return success_response(
                    data={
                        "tier": tier,
                        "status": sub_info.get("status", "active"),
                        "current_period_end": sub_info.get("current_period_end"),
                        "features": tier_info.get("features", []),
                        "stripe_subscription_id": user.stripe_subscription_id,
                    }
                )
            except Exception as e:
                # If Stripe call fails, return DB status
                pass

        return success_response(
            data={
                "tier": tier,
                "status": "active",
                "features": tier_info.get("features", []),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return handle_exception(e)


@router.post("/cancel")
async def cancel_subscription(
    current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Cancel current subscription"""
    from src.services.payment.stripe_service import get_payment_service

    try:
        stmt = select(UserDB).where(UserDB.id == current_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.stripe_subscription_id:
            raise HTTPException(
                status_code=400, detail="No active subscription to cancel"
            )

        # Cancel in Stripe
        payment_service = get_payment_service()
        result = await payment_service.cancel_subscription(user.stripe_subscription_id)

        # Note: User stays on paid tier until period ends
        # The webhook will handle the actual downgrade when period ends

        return success_response(
            data={
                "status": "cancellation_scheduled",
                "cancels_at": result.get("cancel_at"),
                "message": "Subscription will be cancelled at the end of the billing period",
            }
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        return handle_exception(e)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    from src.services.payment.stripe_service import get_payment_service

    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhook not configured")

    try:
        payment_service = get_payment_service()
        result = await payment_service.handle_webhook(
            payload=payload,
            signature=signature,
            webhook_secret=settings.STRIPE_WEBHOOK_SECRET,
        )
        return success_response(data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")
