"""
Credit System API Routes for Viral Forge
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from services.payment.credit_service import credit_service

router = APIRouter(prefix="/credits", tags=["Credits & Billing"])


class PurchaseCreditsRequest(BaseModel):
    package_id: int


class ApplyReferralRequest(BaseModel):
    referral_code: str


class CreditCostRequest(BaseModel):
    action: str


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
    """Get credit transaction history"""
    transactions = credit_service.get_transaction_history(
        current_user.id, limit=limit, offset=offset
    )

    return {"transactions": transactions, "count": len(transactions)}


# === Credit Packages ===


@router.get("/packages")
async def get_credit_packages():
    """Get available credit packages for purchase"""
    packages = credit_service.get_credit_packages()

    # If no packages in DB, return default packages
    if not packages:
        packages = [
            {
                "id": 1,
                "name": "Starter",
                "credits": 50,
                "price_cents": 499,
                "features": [],
            },
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
        ]

    return {"packages": packages}


@router.post("/purchase")
async def purchase_credits(
    request: PurchaseCreditsRequest, current_user: UserDB = Depends(get_current_user)
):
    """Purchase credits (creates Stripe checkout session)"""
    from services.payment.stripe_service import get_payment_service
    from api.config import settings

    packages = credit_service.get_credit_packages()
    if not packages:
        # Use default packages if none in DB
        packages = [
            {
                "id": 1,
                "name": "Starter",
                "credits": 50,
                "price_cents": 499,
                "features": [],
            },
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
        ]

    package = next((p for p in packages if p["id"] == request.package_id), None)

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    try:
        payment_service = get_payment_service()

        # Ensure user has a Stripe customer ID
        stripe_customer_id = getattr(current_user, "stripe_customer_id", None)
        if not stripe_customer_id:
            customer = await payment_service.create_customer(
                email=current_user.email, user_id=current_user.id
            )
            stripe_customer_id = customer["stripe_customer_id"]
            # Update user record
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
            finally:
                db.close()

        # Create a one-time payment checkout session for credits
        import stripe

        success_url = (
            f"{settings.PRODUCTION_DOMAIN}/settings?tab=billing&credits_success=true"
        )
        cancel_url = (
            f"{settings.PRODUCTION_DOMAIN}/settings?tab=billing&credits_cancelled=true"
        )

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
        )

        return {
            "status": "checkout_created",
            "session_id": session.id,
            "url": session.url,
            "package": package,
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")


# === Credit Costs ===


@router.get("/costs")
async def get_credit_costs(current_user: UserDB = Depends(get_current_user)):
    """Get credit costs for different actions"""
    from services.payment.credit_service import credit_service

    # Get user's tier for discount calculation
    tier = current_user.subscription.value if current_user.subscription else "free"

    costs = {}
    for action, base_cost in credit_service.DEFAULT_COSTS.items():
        costs[action] = {
            "base_cost": base_cost,
            "your_cost": credit_service.get_action_cost(action, tier),
        }

    return {"tier": tier, "costs": costs}


# === Referral System ===


@router.get("/referral/code")
async def get_referral_code(current_user: UserDB = Depends(get_current_user)):
    """Get user's referral code"""
    code = credit_service.get_referral_code(current_user.id)

    return {
        "referral_code": code,
        "share_url": f"https://viralforge.io/register?ref={code}",
    }


@router.post("/referral/apply")
async def apply_referral_code(
    request: ApplyReferralRequest, current_user: UserDB = Depends(get_current_user)
):
    """Apply a referral code"""
    success, message = credit_service.apply_referral_code(
        current_user.id, request.referral_code
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"status": "success", "message": message}


@router.get("/referrals")
async def get_referrals(current_user: UserDB = Depends(get_current_user)):
    """Get user's referrals"""
    referrals = credit_service.get_referrals(current_user.id)
    stats = credit_service.get_referral_stats(current_user.id)

    return {"referrals": referrals, "stats": stats}


@router.get("/referral/stats")
async def get_referral_stats(current_user: UserDB = Depends(get_current_user)):
    """Get referral statistics"""
    stats = credit_service.get_referral_stats(current_user.id)

    return stats
