"""
Credit Service for Viral Forge
Handles credit purchases, consumption, and referral rewards
"""

from api.utils.database import SessionLocal
from api.utils.credit_models import (
    UserCreditDB,
    CreditTransactionDB,
    CreditPackageDB,
    ReferralDB,
    CreditUsageRuleDB,
    SubscriptionCreditDB,
)
from api.utils.user_models import UserDB, SubscriptionTier
from datetime import datetime, timedelta, timezone
import uuid
import logging

logger = logging.getLogger(__name__)


def utc_now():
    """Get current UTC datetime consistently"""
    return datetime.now(timezone.utc)


class CreditService:
    """Service for managing user credits"""

    # Default credit costs for actions
    DEFAULT_COSTS = {
        "video_generation_ltx": 10,
        "video_generation_hunyuan": 15,
        "video_generation_veo3": 25,
        "video_generation_runway": 30,
        "video_generation_free": 0,  # Free daily providers (ZSky, Kling, PixVerse, Replicate, Stability)
        "video_generation_replicate": 5,  # Replicate paid models ($0.01-0.72 per video - cheapest!)
        "video_transformation": 5,
        "voice_clone": 20,
        "face_swap": 15,
        "background_removal": 5,
        "sound_design": 8,
        "thumbnail_generation": 2,
        "analytics_report": 1,
        "ai_script": 3,
        "viral_analysis": 2,
        "social_publish": 1,
        "auto_merch": 10,
        "storytelling": 40,
    }

    # Subscription monthly credits
    SUBSCRIPTION_CREDITS = {
        "free": 0,
        "creator": 50,
        "empire": 200,
        "sovereign": 500,
        "studio": 1000,
    }

    def get_user_credits(self, user_id: int) -> UserCreditDB:
        """Get or create user's credit balance"""
        db = SessionLocal()
        try:
            user_credits = (
                db.query(UserCreditDB).filter(UserCreditDB.user_id == user_id).first()
            )

            if not user_credits:
                user_credits = UserCreditDB(
                    user_id=user_id,
                    balance=0,
                    lifetime_purchased=0,
                    lifetime_earned=0,
                    lifetime_spent=0,
                )
                db.add(user_credits)
                db.commit()
                db.refresh(user_credits)

            return user_credits
        finally:
            db.close()

    def get_balance(self, user_id: int) -> int:
        """Get user's credit balance"""
        user_credits = self.get_user_credits(user_id)
        return user_credits.balance

    def has_sufficient_credits(self, user_id: int, amount: int) -> bool:
        """Check if user has enough credits"""
        return self.get_balance(user_id) >= amount

    def consume_credits(
        self, user_id: int, amount: int, action: str, reference_id: str = None
    ) -> tuple[bool, str]:
        """
        Attempt to consume credits for an action.
        Returns (success, message)
        Uses SELECT FOR UPDATE to prevent race conditions.
        """

        db = SessionLocal()
        try:
            # Use SELECT FOR UPDATE to lock the row and prevent race conditions
            user_credits = (
                db.query(UserCreditDB)
                .filter(UserCreditDB.user_id == user_id)
                .with_for_update()
                .first()
            )

            if not user_credits:
                return False, "User credits not found"

            if user_credits.balance < amount:
                return (
                    False,
                    f"Insufficient credits. Need {amount}, have {user_credits.balance}",
                )

            # Deduct credits
            user_credits.balance -= amount
            user_credits.lifetime_spent += amount
                user_credits.updated_at = utc_now()

            # Record transaction
            transaction = CreditTransactionDB(
                user_id=user_id,
                amount=-amount,
                balance_after=user_credits.balance,
                transaction_type="spent",
                description=f"Action: {action}",
                reference_id=reference_id,
            )
            db.add(transaction)
            db.commit()

            logger.info(
                f"[CreditService] User {user_id} spent {amount} credits for {action}"
            )
            return True, "Credits consumed successfully"

        except Exception as e:
            db.rollback()
            logger.error(f"[CreditService] Error consuming credits: {e}")
            return False, str(e)
        finally:
            db.close()

    def add_credits(
        self,
        user_id: int,
        amount: int,
        transaction_type: str,
        description: str = None,
        reference_id: str = None,
    ) -> bool:
        """Add credits to user's balance"""
        db = SessionLocal()
        try:
            user_credits = (
                db.query(UserCreditDB).filter(UserCreditDB.user_id == user_id).first()
            )

            if not user_credits:
                user_credits = UserCreditDB(
                    user_id=user_id,
                    balance=amount,
                    lifetime_purchased=amount if transaction_type == "purchase" else 0,
                    lifetime_earned=amount if transaction_type == "earned" else 0,
                )
                db.add(user_credits)
            else:
                user_credits.balance += amount
            user_credits.updated_at = utc_now()

                if transaction_type == "purchase":
                    user_credits.lifetime_purchased += amount
                elif transaction_type == "earned":
                    user_credits.lifetime_earned += amount

            # Record transaction
            transaction = CreditTransactionDB(
                user_id=user_id,
                amount=amount,
                balance_after=user_credits.balance,
                transaction_type=transaction_type,
                description=description,
                reference_id=reference_id,
            )
            db.add(transaction)
            db.commit()

            logger.info(f"[CreditService] Added {amount} credits to user {user_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"[CreditService] Error adding credits: {e}")
            return False
        finally:
            db.close()

    def get_transaction_history(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list:
        """Get user's credit transaction history"""
        db = SessionLocal()
        try:
            transactions = (
                db.query(CreditTransactionDB)
                .filter(CreditTransactionDB.user_id == user_id)
                .order_by(CreditTransactionDB.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": t.id,
                    "amount": t.amount,
                    "balance_after": t.balance_after,
                    "type": t.transaction_type,
                    "description": t.description,
                    "created_at": t.created_at.isoformat(),
                }
                for t in transactions
            ]
        finally:
            db.close()

    def get_credit_packages(self) -> list:
        """Get available credit packages for purchase"""
        db = SessionLocal()
        try:
            packages = (
                db.query(CreditPackageDB)
                .filter(CreditPackageDB.is_active == True)
                .order_by(CreditPackageDB.price_cents.asc())
                .all()
            )

            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "credits": p.credits,
                    "price_cents": p.price_cents,
                    "features": p.features,
                }
                for p in packages
            ]
        finally:
            db.close()

    # === Referral System ===

    def generate_referral_code(self, user_id: int) -> str:
        """Generate a unique referral code for user"""
        db = SessionLocal()
        try:
            # Check if user already has a code
            existing = (
                db.query(ReferralDB).filter(ReferralDB.referrer_id == user_id).first()
            )

            if existing:
                return existing.referral_code

            # Generate new code
            code = f"VF{uuid.uuid4().hex[:8].upper()}"
            referral = ReferralDB(
                referrer_id=user_id, referral_code=code, status="pending"
            )
            db.add(referral)
            db.commit()

            return code

        finally:
            db.close()

    def get_referral_code(self, user_id: int) -> str:
        """Get user's referral code"""
        db = SessionLocal()
        try:
            referral = (
                db.query(ReferralDB).filter(ReferralDB.referrer_id == user_id).first()
            )

            if referral:
                return referral.referral_code

            return self.generate_referral_code(user_id)
        finally:
            db.close()

    def apply_referral_code(
        self, referrer_id: int, referral_code: str
    ) -> tuple[bool, str]:
        """Apply a referral code (when new user signs up)"""
        db = SessionLocal()
        try:
            # Find the referral by code
            referral = (
                db.query(ReferralDB)
                .filter(ReferralDB.referral_code == referral_code.upper())
                .first()
            )

            if not referral:
                return False, "Invalid referral code"

            if referral.status != "pending":
                return False, "Referral code already used"

            if referral.referrer_id == referrer_id:
                return False, "Cannot refer yourself"

            # Update referral status
            referral.referred_id = referrer_id
            referral.status = "completed"

            # Award credits to referrer
            REWARD_CREDITS = 50
            referral.reward_credits = REWARD_CREDITS

            # Add credits to referrer
            self.add_credits(
                referrer_id,
                REWARD_CREDITS,
                "earned",
                f"Referral bonus - {referral_code}",
            )

            db.commit()

            logger.info(
                f"[CreditService] Referral applied: {referrer_id} used code {referral_code}"
            )
            return True, f"Referral applied! You earned {REWARD_CREDITS} bonus credits"

        except Exception as e:
            db.rollback()
            logger.error(f"[CreditService] Error applying referral: {e}")
            return False, str(e)
        finally:
            db.close()

    def get_referrals(self, user_id: int) -> list:
        """Get user's referrals"""
        db = SessionLocal()
        try:
            referrals = (
                db.query(ReferralDB).filter(ReferralDB.referrer_id == user_id).all()
            )

            return [
                {
                    "id": r.id,
                    "referred_id": r.referred_id,
                    "code": r.referral_code,
                    "status": r.status,
                    "reward_credits": r.reward_credits,
                    "created_at": r.created_at.isoformat(),
                }
                for r in referrals
            ]
        finally:
            db.close()

    def get_referral_stats(self, user_id: int) -> dict:
        """Get user's referral statistics"""
        db = SessionLocal()
        try:
            referrals = (
                db.query(ReferralDB).filter(ReferralDB.referrer_id == user_id).all()
            )

            total_referrals = len(referrals)
            completed = sum(1 for r in referrals if r.status == "completed")
            total_earned = sum(r.reward_credits for r in referrals)

            return {
                "total_referrals": total_referrals,
                "completed_referrals": completed,
                "pending_referrals": total_referrals - completed,
                "total_credits_earned": total_earned,
            }
        finally:
            db.close()

    # === Credit Costs ===

    def get_action_cost(self, action: str, tier: str = "free") -> int:
        """Get credit cost for an action (may vary by tier)"""
        base_cost = self.DEFAULT_COSTS.get(action, 10)

        # Apply tier discounts
        tier_discounts = {
            "creator": 0.1,  # 10% off
            "empire": 0.2,  # 20% off
            "sovereign": 0.3,  # 30% off
            "studio": 0.5,  # 50% off
        }

        discount = tier_discounts.get(tier, 0)
        return max(1, int(base_cost * (1 - discount)))

    def check_and_consume(
        self, user_id: int, action: str, reference_id: str = None
    ) -> tuple[bool, str]:
        """Check if user can afford action and consume credits"""
        # Get user's tier
        db = SessionLocal()
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            tier = user.subscription.value if user.subscription else "free"
        finally:
            db.close()

        cost = self.get_action_cost(action, tier)

        if not self.has_sufficient_credits(user_id, cost):
            return (
                False,
                f"Insufficient credits. Need {cost}, have {self.get_balance(user_id)}",
            )

        return self.consume_credits(user_id, cost, action, reference_id)


# Initialize service
credit_service = CreditService()
