"""
ConsistencySentinel: Autonomous State Enforcement Engine.

Periodically audits Redis↔Postgres consistency and AUTOMATICALLY triggers
RecoveryService when drift is detected. Exposes all audit results as
Prometheus metrics for the Reality Run dashboard.

Evolution: Was a passive logger → Now an active repair enforcer.
"""

import asyncio
import logging
import time
from typing import Any
from sqlalchemy import select
from src.api.utils.database import AsyncSessionLocal
from src.api.utils.models import ExperimentCohortDB
from src.services.distribution.experiment_batcher import base_experiment_service
from src.services.infrastructure.resilience_metrics import (
    state_drift_detected,
    state_repairs_triggered,
    recovery_duration,
    sentinel_audit_pass,
    sentinel_audit_fail,
)

logger = logging.getLogger("ConsistencySentinel")


class DriftReport:
    """Structured representation of a single audit cycle's findings."""

    def __init__(self):
        self.checked_at: float = time.time()
        self.cohorts_checked: int = 0
        self.drifts: list[dict[str, Any]] = []
        self.repair_triggered: bool = False
        self.repair_duration_s: float | None = None

    @property
    def is_clean(self) -> bool:
        return len(self.drifts) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "checked_at": self.checked_at,
            "cohorts_checked": self.cohorts_checked,
            "drift_count": len(self.drifts),
            "drifts": self.drifts,
            "repair_triggered": self.repair_triggered,
            "repair_duration_s": self.repair_duration_s,
            "verdict": "CLEAN" if self.is_clean else "DRIFT_DETECTED",
        }


class ConsistencySentinel:
    """
    The State Enforcement Engine.
    Periodically verifies that Redis 'Hot' state and Postgres 'Truth' are in sync.
    When drift is detected, autonomously triggers RecoveryService to repair it.
    Implements a cooldown to prevent repair thrashing under sustained chaos.
    """

    def __init__(self, check_interval: int = 30, repair_cooldown: int = 60):
        self.check_interval = check_interval
        self.repair_cooldown = repair_cooldown
        self._stop_event = asyncio.Event()
        self._last_repair_time: float = 0.0
        self._audit_history: list[DriftReport] = []
        self._total_repairs: int = 0

    async def start(self):
        """Starts the background auditing + enforcement loop."""
        logger.info(
            "🛡️ [Sentinel] Starting Enforcement Loop "
            f"(Audit: {self.check_interval}s, Repair Cooldown: {self.repair_cooldown}s)"
        )
        while not self._stop_event.is_set():
            try:
                report = await self.audit_experiment_state()
                self._audit_history.append(report)
                # Keep last 100 reports in memory
                if len(self._audit_history) > 100:
                    self._audit_history = self._audit_history[-100:]
            except Exception as e:
                logger.exception(f"[Sentinel] Audit loop error: {e}", exc_info=True)
            await asyncio.sleep(self.check_interval)

    async def audit_experiment_state(self) -> DriftReport:
        """
        Cross-checks participant counts between in-memory cache and Postgres.
        If drift is detected AND cooldown has elapsed, triggers autonomous repair.
        Returns a structured DriftReport.
        """
        report = DriftReport()

        async with AsyncSessionLocal() as db:
            try:
                # 1. Get stats from Postgres (Source of Truth)
                stmt = select(ExperimentCohortDB).where(
                    ExperimentCohortDB.status == "ROLLING_OUT"
                )
                result = await db.execute(stmt)
                db_cohorts = result.scalars().all()
                db_counts = {c.id: len(c.participants) for c in db_cohorts}

                # 2. Get stats from Cache (Hot State)
                cache_counts = {
                    b["batch_id"]: len(b["participants"])
                    for b in base_experiment_service.active_batches
                }

                report.cohorts_checked = len(db_counts)

                # 3. Detect Drift — Missing from cache
                for cohort_id, db_count in db_counts.items():
                    cache_count = cache_counts.get(cohort_id)
                    if cache_count is None:
                        drift_entry = {
                            "cohort_id": cohort_id,
                            "type": "missing_from_cache",
                            "db_count": db_count,
                            "cache_count": None,
                        }
                        report.drifts.append(drift_entry)
                        state_drift_detected.labels(
                            drift_type="missing_from_cache"
                        ).inc()
                        logger.error(
                            f"❌ [Sentinel] DRIFT: Cohort {cohort_id} missing from cache!"
                        )
                    elif cache_count != db_count:
                        drift_entry = {
                            "cohort_id": cohort_id,
                            "type": "count_mismatch",
                            "db_count": db_count,
                            "cache_count": cache_count,
                        }
                        report.drifts.append(drift_entry)
                        state_drift_detected.labels(
                            drift_type="count_mismatch"
                        ).inc()
                        logger.warning(
                            f"⚠️ [Sentinel] DRIFT: Cohort {cohort_id} "
                            f"count mismatch. DB: {db_count}, Cache: {cache_count}"
                        )

                # 4. Update Prometheus audit counters
                if report.is_clean:
                    sentinel_audit_pass.inc()
                    if db_counts:
                        logger.info(
                            "✅ [Sentinel] Audit PASSED. "
                            f"{len(db_counts)} cohorts in sync."
                        )
                else:
                    sentinel_audit_fail.inc()
                    # 5. Autonomous Repair — with cooldown guard
                    await self._attempt_repair(report)

            except Exception as e:
                logger.exception(f"Consistency Audit failed: {e}", exc_info=True)
                sentinel_audit_fail.inc()

        return report

    async def _attempt_repair(self, report: DriftReport):
        """
        Triggers RecoveryService if cooldown has elapsed.
        Prevents repair thrashing under sustained chaos injection.
        """
        now = time.time()
        elapsed = now - self._last_repair_time

        if elapsed < self.repair_cooldown:
            remaining = self.repair_cooldown - elapsed
            logger.info(
                "🕐 [Sentinel] Repair cooldown active. "
                f"Next repair eligible in {remaining:.0f}s"
            )
            return

        logger.warning(
            "🔧 [Sentinel] TRIGGERING AUTONOMOUS REPAIR. "
            f"{len(report.drifts)} drifts detected."
        )

        # Lazy import to avoid circular dependency
        from src.services.infrastructure.recovery_service import base_recovery_service

        repair_start = time.time()
        try:
            await base_recovery_service.sync_all_vitals()
            repair_elapsed = time.time() - repair_start

            report.repair_triggered = True
            report.repair_duration_s = repair_elapsed
            self._last_repair_time = time.time()
            self._total_repairs += 1

            # Prometheus metrics
            state_repairs_triggered.inc()
            recovery_duration.observe(repair_elapsed)

            logger.info(
                f"✅ [Sentinel] Repair Complete in {repair_elapsed:.2f}s. "
                f"Total repairs this session: {self._total_repairs}"
            )
        except Exception as e:
            logger.exception(f"[Sentinel] Repair FAILED: {e}", exc_info=True)

    def get_status(self) -> dict[str, Any]:
        """Returns the current sentinel health summary."""
        recent = self._audit_history[-5:] if self._audit_history else []
        return {
            "running": not self._stop_event.is_set(),
            "check_interval_s": self.check_interval,
            "repair_cooldown_s": self.repair_cooldown,
            "total_repairs": self._total_repairs,
            "last_repair_time": self._last_repair_time,
            "recent_audits": [r.to_dict() for r in recent],
        }

    def stop(self):
        self._stop_event.set()


# Singleton Instance
base_consistency_sentinel = ConsistencySentinel()
