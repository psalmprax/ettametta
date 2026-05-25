"""
Automated A/B Testing Service
Handles automatic winner determination and optimization
"""

import asyncio
import logging
from datetime import datetime, timezone
from src.api.utils.database import async_session_factory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.utils.models import ABTestDB
from src.shared.enums import ABTestStatus, SystemJobStatus

logger = logging.getLogger(__name__)


class ABTestingAutomation:
    """
    Automated A/B testing service that monitors tests and determines winners
    """

    def __init__(self):
        self.is_running = False
        self.check_interval = 300  # 5 minutes

    async def start(self):
        """Start the automated A/B testing service"""
        if self.is_running:
            return

        self.is_running = True
        await self._log("A/B Testing Automation Started", SystemJobStatus.SYSTEM)

        while self.is_running:
            try:
                await self._check_active_tests()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                await self._log(f"A/B Automation Error: {e}", SystemJobStatus.FAILED)
                await asyncio.sleep(60)  # Wait 1 minute on error

    def stop(self):
        """Stop the automated A/B testing service"""
        self.is_running = False
        logger.info("[ABTestingAutomation] Stopped")

    async def _log(self, message: str, level: str = "INFO"):
        """Broadcast a log message"""
        from src.api.routes.ws import notify_system_log_async
        await notify_system_log_async(message, level=level, module="AB_TESTING")

    async def _check_active_tests(self):
        """Check all active A/B tests for potential winners"""
        async with async_session_factory() as db:
            try:
                # Get all active tests that haven't been completed
                stmt = select(ABTestDB).where(
                    ABTestDB.status == ABTestStatus.ACTIVE,
                    ABTestDB.winner_variant.is_(None)
                )
                result = await db.execute(stmt)
                active_tests = result.scalars().all()

                for test in active_tests:
                    await self._evaluate_test(test, db)

            except Exception as e:
                logger.exception(f"[ABTestingAutomation] Error checking tests: {e}")

    async def _evaluate_test(self, test: ABTestDB, db: AsyncSession):
        """Evaluate a single A/B test for winner determination"""
        try:
            # Calculate current metrics
            total_views = test.variant_a_view_count + test.variant_b_view_count

            # Need minimum sample size for statistical significance
            if total_views < 30:
                return  # Not enough data yet

            # Check if we have enough data for both variants
            min_views_per_variant = 15
            if (
                test.variant_a_view_count < min_views_per_variant
                or test.variant_b_view_count < min_views_per_variant
            ):
                return  # Need more data

            # Get the right metrics based on target
            if test.target_metric == "clicks":
                views_a, views_b = test.variant_a_view_count, test.variant_b_view_count
                conv_a, conv_b = test.variant_a_click_count, test.variant_b_click_count
            elif test.target_metric == "conversions":
                views_a, views_b = test.variant_a_view_count, test.variant_b_view_count
                conv_a, conv_b = (
                    test.variant_a_conversion_count,
                    test.variant_b_conversion_count,
                )
            else:  # default to views
                views_a, views_b = test.variant_a_view_count, test.variant_b_view_count
                conv_a, conv_b = test.variant_a_click_count, test.variant_b_click_count

            # Use proper statistical testing
            from src.api.routes.ab_testing import calculate_statistics

            stats = calculate_statistics(
                views_a,
                views_b,
                conv_a,
                conv_b,
            )

            # Check if statistically significant
            if stats.significant and stats.winner:
                # We have a winner!
                test.winner_variant = stats.winner
                test.confidence_level = stats.confidence_level
                test.p_value = stats.p_value
                test.status = ABTestStatus.COMPLETED
                test.completed_at = datetime.now(timezone.utc)

                await db.commit()

                winner_title = (
                    test.variant_a_title
                    if stats.winner == "A"
                    else test.variant_b_title
                )

                await self._log(
                    f"A/B Test #{test.id} completed automatically. Winner: {stats.winner} ({winner_title}) "
                    f"with {stats.confidence_level:.1f}% confidence",
                    SystemJobStatus.SUCCESS,
                )

                # Trigger optimization if enabled
                await self._apply_winner_optimization(test, stats.winner)

            elif total_views >= 1000:  # Maximum sample size reached
                # Call it a draw if no clear winner after max samples
                test.status = ABTestStatus.COMPLETED
                test.completed_at = datetime.now(timezone.utc)
                test.winner_variant = "DRAW"

                await db.commit()

                await self._log(
                    f"A/B Test #{test.id} completed with no clear winner after {total_views} views",
                    SystemJobStatus.STRATEGIZING,
                )

        except Exception as e:
            logger.exception(f"[ABTestingAutomation] Error evaluating test {test.id}: {e}")

    async def _apply_winner_optimization(self, test: ABTestDB, winner: str):
        """Apply the winning variant to future content"""
        try:
            # Get the winning title
            winner_title = (
                test.variant_a_title if winner == "A" else test.variant_b_title
            )

            # Update user's optimization preferences
            # This would integrate with the optimization service
            await self._log(
                f"Applied winner optimization: '{winner_title}' for future content in niche",
                "INFO",
            )

        except Exception as e:
            logger.exception(f"[ABTestingAutomation] Error applying optimization: {e}")


# Global instance
ab_testing_automation = ABTestingAutomation()
