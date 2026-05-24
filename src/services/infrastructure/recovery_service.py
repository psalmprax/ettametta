"""
RecoveryService: Runtime-Callable State Reconstruction.

Responsible for reconstructing the system's volatile memory from persistent
sources. Can be called at startup AND at runtime by the ConsistencySentinel
when drift is detected. Records recovery timing via Prometheus.
"""

import asyncio
import logging
import time
from src.services.analytics.drift_detector import base_drift_service
from src.services.distribution.experiment_batcher import base_experiment_service
from src.api.utils.redis import get_redis
from src.services.infrastructure.resilience_metrics import recovery_duration

logger = logging.getLogger("RecoveryService")


class RecoveryService:
    """
    Stateful Recovery & Consistency Engine.
    Reconstructs volatile memory from persistent sources.
    Callable at startup (full sync) and at runtime (repair cycle).
    """

    def __init__(self):
        self._repair_count: int = 0
        self._last_repair_duration: float = 0.0

    async def sync_all_vitals(self):
        """Reconstructs all analytics and experimentation states."""
        logger.info("📡 [Recovery] Initializing Global State Reconstruction...")
        start = time.time()

        # 1. Sync Algorithm Drift History
        await base_drift_service.sync_from_db()

        # 2. Sync Active Experiment Cohorts
        await base_experiment_service.sync_from_db()

        # 3. Rebuild Redis Hot State for Active Batches
        await self._rebuild_redis_hot_state()

        elapsed = time.time() - start
        self._repair_count += 1
        self._last_repair_duration = elapsed

        # Record in Prometheus
        recovery_duration.observe(elapsed)

        logger.info(
            f"✅ [Recovery] Global Consistency Achieved in {elapsed:.2f}s. "
            f"(Repair #{self._repair_count})"
        )

    async def _rebuild_redis_hot_state(self):
        """Ensures Redis 'active_batch' pointers are correct for each strategy."""
        try:
            redis = await get_redis()
            for batch in base_experiment_service.active_batches:
                # Refresh the hot pointer in Redis
                await redis.set(
                    f"active_batch:{batch['strategy']}",
                    batch["batch_id"],
                    ex=86400,
                )
            logger.info(
                "🧠 [Recovery] Redis Hot State reconstructed for "
                f"{len(base_experiment_service.active_batches)} cohorts."
            )
        except Exception as e:
            logger.error(f"Failed to rebuild Redis hot state: {e}")

    def get_status(self):
        """Returns recovery service health info."""
        return {
            "total_repairs": self._repair_count,
            "last_repair_duration_s": round(self._last_repair_duration, 3),
        }


# Singleton Instance
base_recovery_service = RecoveryService()
