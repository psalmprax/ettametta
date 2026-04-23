import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.utils.database import async_session_factory
from src.api.utils.models import VideoJobDB, PerformanceSnapshotDB, PublishedContentDB
from src.services.optimization.youtube_publisher import base_youtube_publisher
from typing import Any

logger = logging.getLogger(__name__)

class FlywheelService:
    """
    The 'Find Winners Fast' Flywheel.
    Automates the Kill & Scale loop:
    - Prunes underperforming variants.
    - Iterates on winners.
    """

    def __init__(self):
        # Weighting from growth MVP spec
        self.WEIGHT_CTR = 0.4
        self.WEIGHT_RETENTION = 0.4
        self.WEIGHT_WATCH_TIME = 0.2

    async def calculate_engagement_score(self, ctr: float, retention: float, watch_time_sec: float) -> float:
        """
        Calculates the 10/10 growth score.
        score = (CTR * 0.4) + (retention * 0.4) + (watch_time * 0.2)
        """
        # Normalize watch time (assuming 60s max for Shorts)
        normalized_watch_time = min(watch_time_sec / 60.0, 1.0)
        return (ctr * self.WEIGHT_CTR) + (retention * self.WEIGHT_RETENTION) + (normalized_watch_time * self.WEIGHT_WATCH_TIME)

    async def run_evolution_cycle(self, parent_job_id: str):
        """
        1. Fetches metrics for all variants of a parent job.
        2. Scores them.
        3. Kills bottom 70%.
        4. Returns the winner metadata for next-gen generation.
        """
        logger.info(f"🔄 [Flywheel] Starting evolution cycle for Parent: {parent_job_id}")

        async with async_session_factory() as db:
            # 1. Get all variants
            stmt = select(VideoJobDB).where(
                VideoJobDB.job_metadata["parent_id"].astext == parent_job_id
            )
            result = await db.execute(stmt)
            variants = result.scalars().all()

            if not variants:
                logger.warning(f"No variants found for {parent_job_id}")
                return

            scored_variants = []

            for variant in variants:
                # 2. Fetch latest metrics (Mocked for now until Analytics API integrated)
                # In production, this would call base_youtube_publisher.get_advanced_metrics
                metrics = await self._fetch_variant_metrics(variant.id)
                
                score = await self.calculate_engagement_score(
                    ctr=metrics.get("ctr", 0.0),
                    retention=metrics.get("retention", 0.0),
                    watch_time_sec=metrics.get("watch_time_sec", 0.0)
                )

                scored_variants.append({
                    "job_id": variant.id,
                    "score": score,
                    "metrics": metrics,
                    "metadata": variant.job_metadata
                })

            # 3. Sort and Rank
            scored_variants.sort(key=lambda x: x["score"], reverse=True)
            
            winner = scored_variants[0]
            logger.info(f"🏆 [Flywheel] Winner identified: {winner['job_id']} (Score: {winner['score']:.2f})")

            # 4. 'Kill' underperformers (Mark as ARCHIVED or lower priority)
            if len(scored_variants) > 1:
                prune_count = int(len(scored_variants) * 0.7)
                losers = scored_variants[-prune_count:]
                for loser in losers:
                    logger.info(f"💀 [Flywheel] Pruning underperformer: {loser['job_id']} (Score: {loser['score']:.2f})")
                    # Logic to stop promotion or unpublish if required

            return winner

    async def _fetch_variant_metrics(self, job_id: str) -> dict[str, Any]:
        """
        Bridge to YouTube Analytics API.
        Currently returns simulated data based on view counts.
        """
        # TODO: Replace with real YouTube Analytics API call
        # For now, simulate higher CTR for variant 0 to show it works
        import random
        return {
            "ctr": random.uniform(0.02, 0.15),
            "retention": random.uniform(0.3, 0.8),
            "watch_time_sec": random.uniform(10, 45)
        }

base_flywheel_service = FlywheelService()
