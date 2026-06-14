"""
Periodic Celery tasks for the payment/credit system.

Currently includes:
- ``grant_monthly_subscription_credits`` — runs daily, grants monthly credits
  to every paid-tier user who hasn't yet received them in the current calendar month.
"""

from src.api.utils.celery import celery_app
from src.services.payment.credit_service import base_credit_service
from src.api.utils.database import async_session_factory
from src.api.utils.user_models import UserDB, SubscriptionTier
from src.api.utils.credit_models import CreditTransactionDB
from sqlalchemy import select, and_
from datetime import datetime, timezone
import asyncio
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="payment.monthly_credits")
def grant_monthly_subscription_credits():
    """
    Grant monthly subscription credits to all users on paid tiers.

    The task runs on a daily Celery beat schedule.  It skips any user who
    already received credits in the current calendar month (detected by
    scanning ``CreditTransactionDB`` for a matching bonus transaction).

    Credits amounts are defined in
    :attr:`CreditService.SUBSCRIPTION_CREDITS`:

        - ``basic``: 50
        - ``premium``: 200
        - ``sovereign``: 500
        - ``studio``: 1000
    """

    async def _run():
        async with async_session_factory() as db:
            # All users currently on a paid tier
            stmt = select(UserDB).where(
                UserDB.subscription.in_(
                    [
                        SubscriptionTier.BASIC,
                        SubscriptionTier.PREMIUM,
                        SubscriptionTier.SOVEREIGN,
                        SubscriptionTier.STUDIO,
                    ]
                )
            )
            result = await db.execute(stmt)
            users = result.scalars().all()

            now = datetime.now(timezone.utc).replace(tzinfo=None)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            granted = 0
            skipped = 0
            errors = 0

            for user in users:
                try:
                    # De-duplicate: skip if already granted this calendar month
                    dup_stmt = select(CreditTransactionDB).where(
                        and_(
                            CreditTransactionDB.user_id == user.id,
                            CreditTransactionDB.transaction_type == "bonus",
                            CreditTransactionDB.description
                            == "Monthly subscription credit grant",
                            CreditTransactionDB.created_at >= month_start,
                        )
                    )
                    existing = await db.execute(dup_stmt)
                    if existing.scalar_one_or_none():
                        skipped += 1
                        continue

                    tier_key = (
                        user.subscription.value
                        if hasattr(user.subscription, "value")
                        else str(user.subscription)
                    )
                    amount = base_credit_service.SUBSCRIPTION_CREDITS.get(tier_key, 0)
                    if amount <= 0:
                        skipped += 1
                        continue

                    ok = await base_credit_service.add_credits(
                        user_id=user.id,
                        amount=amount,
                        transaction_type="bonus",
                        db=db,
                        description="Monthly subscription credit grant",
                        auto_commit=True,
                    )

                    if ok:
                        granted += 1
                        logger.info(
                            "[Monthly Credits] Granted %d credits to user %s "
                            "(tier=%s)",
                            amount,
                            user.id,
                            tier_key,
                        )
                    else:
                        errors += 1
                        logger.error(
                            "[Monthly Credits] add_credits returned False for user %s",
                            user.id,
                        )

                except Exception:
                    errors += 1
                    logger.exception(
                        "[Monthly Credits] Error processing user %s", user.id
                    )

            await db.commit()

            logger.info(
                "[Monthly Credits] Complete: %d granted, %d skipped, %d errors",
                granted,
                skipped,
                errors,
            )

            return {
                "status": "success",
                "granted": granted,
                "skipped": skipped,
                "errors": errors,
            }

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.exception("[Monthly Credits] Task failed: %s", e)
        return {"status": "error", "error": str(e)}
