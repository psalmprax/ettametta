"""
Credit System API Routes for Viral Forge
Provides credit management, packages, purchases, and referral system
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from services.payment.credit_service import credit_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credits", tags=["Credits & Billing"])

DEFAULT_PACKAGES = [
    {"id": 1, "name": "Starter", "credits": 50, "price_cents": 499, "features": []},
    {
        "id": 2,
        "name": "Pro",
        "credits": 200,
        "price_cents": 1499,
        "features": ["10% bonus"],
    },
    {
        "id": 3,
        "name": "Enterprise",
        "credits": 1000,
        "price_cents": 4999,
        "features": ["25% bonus", "Priority support"],
    },
    {
        "id": 4,
        "name": "Scale",
        "credits": 2500,
        "price_cents": 9999,
        "features": ["35% bonus", "Priority support", "API access"],
    },
]

PACKAGE_IDS = {p["id"] for p in DEFAULT_PACKAGES}


class PurchaseCreditsRequest(BaseModel):
    package_id: int


class ApplyReferralRequest(BaseModel):
    referral_code: str


class CreditCostRequest(BaseModel):
    action: str


def _get_packages() -> List[dict]:
    """Get packages from DB or return defaults"""
    packages = credit_service.get_credit_packages()
    return packages if packages else DEFAULT_PACKAGES


def _get_package_by_id(package_id: int) -> Optional[dict]:
    """Get package by ID with validation"""
    packages = _get_packages()
    return next((p for p in packages if p["id"] == package_id), None)


# === Credit Balance & History ===


@router.get("/balance")
async def get_credit_balance(current_user: UserDB = Depends(get_current_user)):
    """Get user's current credit balance"""
    balance = credit_service.get_balance(current_user.id)
    return {"balance": balance, "user_id": current_user.id}


@router.get("/transactions")
async def get_transaction_history(
    limit: int = 50, offset: int = 0, current_user: UserDB = Depends(get_current_user)
):
    """Get credit transaction history with pagination"""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    transactions = credit_service.get_transaction_history(
        current_user.id, limit=limit, offset=offset
    )
    return {
        "transactions": transactions,
        "count": len(transactions),
        "limit": limit,
        "offset": offset,
    }


# === Credit Packages ===
@router.get("/packages")
async def get_credit_packages():
    """Get available credit packages for purchase"""
    packages = _get_packages()
    return {"packages": packages, "count": len(packages)}


# === Credit Purchase ===
@router.post("/purchase")
async def purchase_credits(
    request: PurchaseCreditsRequest, current_user: UserDB = Depends(get_current_user)
):
    """Purchase credits - creates Stripe checkout session"""
    from services.payment.stripe_service import get_payment_service
    from api.config import settings
    import uuid

    package = _get_package_by_id(request.package_id)
    if not package:
        available_ids = [p["id"] for p in _get_packages()]
        raise HTTPException(
            status_code=404,
            detail=f"Package {request.package_id} not found. Available IDs: {available_ids}",
        )

    try:
        payment_service = get_payment_service()
    except ValueError as e:
        logger.error(f"[Credits] Stripe not configured: {e}")
        raise HTTPException(
            status_code=503,
            detail="Payment service unavailable. Please contact support.",
        )

    stripe_customer_id = getattr(current_user, "stripe_customer_id", None)

    if not stripe_customer_id:
        try:
            customer = await payment_service.create_customer(
                email=current_user.email,
                user_id=current_user.id,
                idempotency_key=f"customer_{current_user.id}_{uuid.uuid4().hex[:8]}",
            )
            stripe_customer_id = customer["stripe_customer_id"]

            from api.utils.database import SessionLocal

            db = SessionLocal()
            try:
                from api.utils.user_models import UserDB as UserDBModel

                db_user = (
                    db.query(UserDBModel)
                    .filter(UserDBModel.id == current_user.id)
                    .first()
                )
                if db_user:
                    db_user.stripe_customer_id = stripe_customer_id
                    db.commit()
            except Exception as e:
                logger.error(f"[Credits] Failed to update Stripe customer ID: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[Credits] Failed to create Stripe customer: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize payment. Please try again.",
            )

    success_url = f"{settings.PRODUCTION_DOMAIN}/settings?tab=billing&credits_success=true&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = (
        f"{settings.PRODUCTION_DOMAIN}/settings?tab=billing&credits_cancelled=true"
    )

    import stripe
    from api.config import settings

    try:
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{package['name']} Credit Pack - {package['credits']} Credits",
                            "description": f"Viral Forge credit pack: {package['credits']} credits",
                        },
                        "unit_amount": package["price_cents"],
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "type": "credit_purchase",
                "user_id": str(current_user.id),
                "package_id": str(package["id"]),
                "credits": str(package["credits"]),
            },
            idempotency_key=f"credits_{current_user.id}_{package['id']}_{uuid.uuid4().hex[:8]}",
        )

        logger.info(
            f"[Credits] Created checkout session {session.id} for user {current_user.id}"
        )

        return {
            "status": "checkout_created",
            "session_id": session.id,
            "url": session.url,
            "package": package,
        }
    except stripe.error.StripeError as e:
        logger.error(f"[Credits] Stripe error: {e}")
        raise HTTPException(
            status_code=502, detail=f"Payment processing error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[Credits] Purchase failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create checkout session. Please try again.",
        )


# === Credit Costs ===
@router.get("/costs")
async def get_credit_costs(current_user: UserDB = Depends(get_current_user)):
    """Get credit costs for different actions with tier-based pricing"""
    tier = current_user.subscription.value if current_user.subscription else "free"

    costs = {}
    for action, base_cost in credit_service.DEFAULT_COSTS.items():
        costs[action] = {
            "base_cost": base_cost,
            "your_cost": credit_service.get_action_cost(action, tier),
            "tier_discount": f"{int((1 - credit_service.get_action_cost(action, tier) / base_cost) * 100)}%"
            if base_cost > 0
            else "0%",
        }

    return {"tier": tier, "costs": costs}


# === Referral System ===
@router.get("/referral/code")
async def get_referral_code(current_user: UserDB = Depends(get_current_user)):
    """Get user's referral code with share URL"""
    code = credit_service.get_referral_code(current_user.id)
    from api.config import settings

    share_url = f"{settings.PRODUCTION_DOMAIN}/register?ref={code}"

    return {"referral_code": code, "share_url": share_url}


@router.post("/referral/apply")
async def apply_referral_code(
    request: ApplyReferralRequest, current_user: UserDB = Depends(get_current_user)
):
    """Apply a referral code with validation"""
    if not request.referral_code or len(request.referral_code.strip()) < 4:
        raise HTTPException(status_code=400, detail="Invalid referral code")

    success, message = credit_service.apply_referral_code(
        current_user.id, request.referral_code.strip().upper()
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"status": "success", "message": message}


@router.get("/referrals")
async def get_referrals(current_user: UserDB = Depends(get_current_user)):
    """Get user's referrals with stats"""
    referrals = credit_service.get_referrals(current_user.id)
    stats = credit_service.get_referral_stats(current_user.id)
    return {"referrals": referrals, "stats": stats}


@router.get("/referral/stats")
async def get_referral_stats(current_user: UserDB = Depends(get_current_user)):
    """Get referral statistics"""
    return credit_service.get_referral_stats(current_user.id)
