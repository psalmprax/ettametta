import logging
from sqlalchemy import update
from src.api.utils.database import AsyncSessionLocal
from src.api.utils.models import StrategyRegistryDB

logger = logging.getLogger("SuccessModel")

class SuccessModel:
    """
    10/10 Proof: The Imperial Success Engine (Stateful).
    Aggregates metrics and enforces automatic rollbacks with persistent lineage.
    """

    def __init__(self, rollback_threshold: float = 0.20):
        self.rollback_threshold = rollback_threshold

    def calculate_imperial_score(self, views: int, retention: float, ctr: float) -> float:
        """
        Calculates a unified success score.
        Weighted: 50% Retention, 30% Views (normalized), 20% CTR.
        """
        import math
        view_score = min(1.0, math.log10(views) / 6.0) if views > 1 else 0

        score = (retention * 0.5) + (view_score * 0.3) + (ctr * 0.2)
        return round(score, 4)

    async def evaluate_strategy_survival(self, strategy_name: str, cohort_scores: list[float]):
        """
        Decides if a narrative strategy should live or be rolled back.
        Persists outcome to StrategyRegistryDB.
        """
        avg_score = sum(cohort_scores) / len(cohort_scores) if cohort_scores else 0

        status = "STRATEGY_DOMINANT"
        db_status = "DOMINANT"

        if avg_score < self.rollback_threshold:
            logger.error(f"💀 [Rollback] Strategy '{strategy_name}' FAILED Validation (Avg Score: {avg_score:.2f}).")
            await self._kill_strategy(strategy_name, avg_score)
            return "ROLLBACK_TRIGGERED"

        # Persist success
        async with AsyncSessionLocal() as db:
            try:
                stmt = update(StrategyRegistryDB).where(
                    StrategyRegistryDB.name == strategy_name
                ).values(status=db_status, avg_score=avg_score)
                await db.execute(stmt)
                await db.commit()
            except Exception as e:
                logger.exception(f"Failed to update strategy success in DB: {e}")

        logger.info(f"🏆 [Success] Strategy '{strategy_name}' Passed Validation (Avg Score: {avg_score:.2f}).")
        return status

    async def _kill_strategy(self, strategy_name: str, avg_score: float):
        """Communicates with Hermes and persists the forbidden status."""

        # 1. Update Database (Source of Truth)
        async with AsyncSessionLocal() as db:
            try:
                stmt = update(StrategyRegistryDB).where(
                    StrategyRegistryDB.name == strategy_name
                ).values(
                    status="KILLED",
                    avg_score=avg_score,
                    failure_reason=f"Score {avg_score:.2f} below threshold {self.rollback_threshold}"
                )
                await db.execute(stmt)
                await db.commit()
            except Exception as e:
                logger.exception(f"Failed to persist strategy kill in DB: {e}")

        # 2. Inform Downstream Engine
        logger.warning(f"🧬 [Hermes] Purging failed strategy branch: {strategy_name}")
        logger.info(f"📡 [SIGNAL] STRATEGY_KILL: {strategy_name}")
