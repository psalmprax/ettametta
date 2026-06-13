from typing import Any
from src.api.utils.credit_models import (
    UserCreditDB,
    CreditTransactionDB,
    CreditPackageDB,
    ReferralDB,
)
from src.api.utils.user_models import UserDB
from src.api.utils.subscription import get_subscription_tier_value
from datetime import datetime, timezone
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.shared.enums import ReferralStatus

logger = logging.getLogger(__name__)


def utc_now():
    """Get current UTC datetime (naive for PostgreSQL compatibility)"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CreditService:
    """Service for managing user credits"""

    # Default credit costs for actions
    DEFAULT_COSTS = {
        "video_generation_ltx": 10,
        "video_generation_hunyuan": 15,
        "video_generation_runway": 30,
        # Local GPU inference engines
        "video_generation_mochi": 15,
        "video_generation_wan": 15,
        "video_generation_cogvideo": 20,
        "video_generation_zeroscope": 10,
        "video_generation_animatediff": 15,
        # Zero-API-key engine (image-gen + FFmpeg parallax)
        "video_generation_lite4k": 5,
        # Free daily credit providers
        "video_generation_free": 0,
        "video_generation_zsky": 0,
        "video_generation_stability": 0,
        # Replicate paid models ($0.01-0.72 per video - cheapest!)
        "video_generation_replicate": 5,
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

    # Subscription monthly credits - must match SubscriptionTier enum values
    SUBSCRIPTION_CREDITS = {
        "free": 0,
        "basic": 50,
        "premium": 200,
        "sovereign": 500,
        "studio": 1000,
    }

    async def get_user_credits(self, user_id: str, db) -> UserCreditDB:
        """Get or create user's credit balance"""
        from sqlalchemy import select

        result = await db.execute(
            select(UserCreditDB).where(UserCreditDB.user_id == user_id)
        )
        user_credits = result.scalar_one_or_none()

        if not user_credits:
            user_credits = UserCreditDB(
                user_id=user_id,
                balance=0,
                lifetime_purchased=0,
                lifetime_earned=0,
                lifetime_spent=0,
            )
            db.add(user_credits)
            await db.flush()
            await db.refresh(user_credits)

        return user_credits

    async def get_balance(self, user_id: str, db) -> int:
        """Get user's credit balance"""
        user_credits = await self.get_user_credits(user_id, db)
        return user_credits.balance

    async def has_sufficient_credits(self, user_id: str, amount: int, db) -> bool:
        """Check if user has enough credits"""
        balance = await self.get_balance(user_id, db)
        return balance >= amount

    async def consume_credits(
        self,
        user_id: str,
        amount: int,
        action: str,
        db: AsyncSession,
        reference_id: str | None = None,
        auto_commit: bool = True,
        description: str | None = None,
    ) -> tuple[bool, str]:
        """
        Attempt to consume credits for an action.
        Returns (success, message)
        """
        from sqlalchemy import select

        try:
            # Use SELECT FOR UPDATE to lock the row and prevent race conditions
            result = await db.execute(
                select(UserCreditDB)
                .where(UserCreditDB.user_id == user_id)
                .with_for_update()
            )
            user_credits = result.scalar_one_or_none()

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
                description=description or f"Action: {action}",
                reference_id=reference_id,
            )
            db.add(transaction)
            
            if auto_commit:
                await db.commit()
            else:
                await db.flush()

            logger.info(
                f"[CreditService] User {user_id} spent {amount} credits for {action}"
            )
            return True, "Credits consumed successfully"

        except Exception as e:
            await db.rollback()
            logger.exception(f"[CreditService] Error consuming credits: {e}")
            return False, str(e)

    async def add_credits(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        db: AsyncSession,
        description: str | None = None,
        reference_id: str | None = None,
        auto_commit: bool = True,
    ) -> bool:
        """Add credits to user's balance"""
        try:
            user_credits = await self.get_user_credits(user_id, db)
            user_credits.balance += amount
            user_credits.updated_at = utc_now()

            if transaction_type == "purchase":
                user_credits.lifetime_purchased += amount
            elif transaction_type == "earned":
                user_credits.lifetime_earned += amount

            transaction = CreditTransactionDB(
                user_id=user_id,
                amount=amount,
                balance_after=user_credits.balance,
                transaction_type=transaction_type,
                description=description,
                reference_id=reference_id,
            )
            db.add(transaction)
            
            if auto_commit:
                await db.commit()
            else:
                await db.flush()
                
            return True
        except Exception as e:
            await db.rollback()
            logger.exception(f"[CreditService] Error adding credits: {e}")
            return False

    async def get_transaction_history(
        self, user_id: str, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get user's credit transaction history"""
        stmt = (
            select(CreditTransactionDB)
            .where(CreditTransactionDB.user_id == user_id)
            .order_by(CreditTransactionDB.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(stmt)
        transactions = result.scalars().all()
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

    async def get_credit_packages(self, db: AsyncSession) -> list[dict[str, Any]]:
        """Get available credit packages for purchase"""
        stmt = (
            select(CreditPackageDB)
            .where(CreditPackageDB.is_active)
            .order_by(CreditPackageDB.price_cents.asc())
        )
        result = await db.execute(stmt)
        packages = result.scalars().all()

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

    # === Referral System ===

    async def generate_referral_code(self, user_id: str, db: AsyncSession) -> str:
        """Generate a unique referral code for user"""
        try:
            # Check if user already has a code
            stmt = select(ReferralDB).where(ReferralDB.referrer_id == user_id)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                return existing.referral_code

            # Generate new code
            code = f"ET{uuid.uuid4().hex[:8].upper()}"
            referral = ReferralDB(
                referrer_id=user_id, referral_code=code, status=ReferralStatus.PENDING.value
            )
            db.add(referral)
            await db.commit()

            return code
        except Exception as e:
            await db.rollback()
            logger.exception(f"[CreditService] Error generating referral code: {e}")
            raise

    async def get_referral_code(self, user_id: str, db: AsyncSession) -> str:
        """Get user's referral code"""
        stmt = select(ReferralDB).where(ReferralDB.referrer_id == user_id)
        result = await db.execute(stmt)
        referral = result.scalar_one_or_none()

        if referral:
            return referral.referral_code

        return await self.generate_referral_code(user_id, db)

    async def apply_referral_code(
        self, referrer_id: str, referral_code: str, db: AsyncSession
    ) -> tuple[bool, str]:
        """Apply a referral code (when new user signs up)"""
        try:
            stmt = select(ReferralDB).where(
                ReferralDB.referral_code == referral_code.upper()
            )
            result = await db.execute(stmt)
            referral = result.scalar_one_or_none()

            if not referral:
                return False, "Invalid referral code"

            if referral.status != ReferralStatus.PENDING.value:
                return False, "Referral code already used"

            if referral.referrer_id == referrer_id:
                return False, "Cannot refer yourself"

            referral.referred_id = referrer_id
            referral.status = ReferralStatus.COMPLETED.value

            REWARD_CREDITS = 50
            referral.reward_credits = REWARD_CREDITS

            await self.add_credits(
                referral.referrer_id,
                REWARD_CREDITS,
                "earned",
                db,
                f"Referral bonus - {referral_code}",
                auto_commit=False,
            )

            await db.commit()
            return True, f"Referral applied! You earned {REWARD_CREDITS} bonus credits"

        except Exception as e:
            await db.rollback()
            logger.exception(f"[CreditService] Error applying referral: {e}")
            return False, str(e)

    async def get_referrals(
        self, user_id: str, db: AsyncSession
    ) -> list[dict[str, Any]]:
        """Get user's referrals"""
        stmt = select(ReferralDB).where(ReferralDB.referrer_id == user_id)
        result = await db.execute(stmt)
        referrals = result.scalars().all()

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

    async def get_referral_stats(self, user_id: str, db: AsyncSession) -> dict:
        """Get user's referral statistics"""
        stmt = select(ReferralDB).where(ReferralDB.referrer_id == user_id)
        result = await db.execute(stmt)
        referrals = result.scalars().all()

        total_referrals = len(referrals)
        completed = sum(1 for r in referrals if r.status == "completed")
        total_earned = sum(r.reward_credits for r in referrals)

        return {
            "total_referrals": total_referrals,
            "completed_referrals": completed,
            "pending_referrals": total_referrals - completed,
            "total_credits_earned": total_earned,
        }

    # === Usage Breakdown ===

    async def get_usage_breakdown(
        self, user_id: str, db: AsyncSession, month: str | None = None
    ) -> dict:
        """
        Get per-action credit spending breakdown for a calendar month.

        Parameters
        ----------
        user_id : str
            The user to query.
        db : AsyncSession
            Database session.
        month : str | None
            Optional month in ``YYYY-MM`` format (e.g. ``"2026-05"``).
            Defaults to the current calendar month.

        Returns
        -------
        dict
            ``{"total_spent": int, "by_action": {str: int}, "action_count": int}``
        """
        if month:
            try:
                year, mon = month.split("-")
                month_start = datetime(
                    int(year), int(mon), 1, tzinfo=timezone.utc
                ).replace(tzinfo=None)
            except (ValueError, IndexError):
                raise ValueError(
                    f"Invalid month format: '{month}'. Expected YYYY-MM (e.g. '2026-05')."
                )
            # Start of the *next* month for the upper bound
            if int(mon) == 12:
                next_month_start = datetime(
                    int(year) + 1, 1, 1, tzinfo=timezone.utc
                ).replace(tzinfo=None)
            else:
                next_month_start = datetime(
                    int(year), int(mon) + 1, 1, tzinfo=timezone.utc
                ).replace(tzinfo=None)
        else:
            now = utc_now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month_start = None  # no upper bound — all transactions from month_start onward

        conditions = [
            CreditTransactionDB.user_id == user_id,
            CreditTransactionDB.transaction_type == "spent",
            CreditTransactionDB.created_at >= month_start,
        ]
        if next_month_start:
            conditions.append(CreditTransactionDB.created_at < next_month_start)

        stmt = (
            select(CreditTransactionDB)
            .where(*conditions)
            .order_by(CreditTransactionDB.created_at.desc())
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        # Parse action from description — descriptions follow the pattern
        # "Action: {action_name}" or a custom message.
        by_action: dict[str, int] = {}
        total_spent = 0
        ACTION_PREFIX = "Action: "

        for row in rows:
            amount = abs(row.amount)  # amount is negative for spends
            action = "unknown"
            if row.description and row.description.startswith(ACTION_PREFIX):
                action = row.description[len(ACTION_PREFIX):]
            by_action[action] = by_action.get(action, 0) + amount
            total_spent += amount

        return {
            "total_spent": total_spent,
            "by_action": dict(sorted(by_action.items(), key=lambda x: -x[1])),
            "action_count": len(by_action),
        }

    # === Credit Costs ===

    def get_action_cost(self, action: str, tier: str = "free") -> int:
        """Get credit cost for an action (may vary by tier)"""
        base_cost = self.DEFAULT_COSTS.get(action, 10)

        # Apply tier discounts - must match SubscriptionTier enum values
        tier_discounts = {
            "basic": 0.1,  # 10% off
            "premium": 0.2,  # 20% off
            "sovereign": 0.3,  # 30% off
            "studio": 0.5,  # 50% off
        }

        discount = tier_discounts.get(tier, 0)
        return max(1, int(base_cost * (1 - discount)))

    async def check_and_consume(
        self, user_id: str, action: str, db: AsyncSession, reference_id: str = None
    ) -> tuple[bool, str]:
        """Check if user can afford action and consume credits"""
        # Get user's tier
        stmt = select(UserDB).where(UserDB.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return False, "User not found"

        tier = get_subscription_tier_value(user)
        cost = self.get_action_cost(action, tier)

        if not await self.has_sufficient_credits(user_id, cost, db):
            balance = await self.get_balance(user_id, db)
            return (
                False,
                f"Insufficient credits. Need {cost}, have {balance}",
            )

        return await self.consume_credits(user_id, cost, action, db, reference_id)


# Initialize service
base_credit_service = CreditService()
credit_service = base_credit_service

