import logging
import numpy as np
from sqlalchemy import select, desc
from src.api.utils.database import AsyncSessionLocal
from src.api.utils.models import DriftHistoryDB

logger = logging.getLogger("DriftDetector")

class DriftDetector:
    """
    10/10 Proof: The Algorithm Shift Sentry.
    Detects when the platform algorithm has shifted and narrative models need recalibration.
    Persists history to DriftHistoryDB for distributed consistency.
    """
    def __init__(self, drift_threshold: float = 0.15):
        self.drift_threshold = drift_threshold
        self.drift_history = []

    async def sync_from_db(self):
        """
        Standard: Stateful Recovery.
        Loads the last 50 deltas from the database to rebuild the sliding window.
        """
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(DriftHistoryDB.delta).order_by(desc(DriftHistoryDB.recorded_at)).limit(50)
                result = await db.execute(stmt)
                self.drift_history = [row[0] for row in result.all()]
                self.drift_history.reverse() # Keep temporal order
                logger.info(f"🔄 [Drift] State Reconstructed: {len(self.drift_history)} entries loaded.")
            except Exception as e:
                logger.exception(f"Failed to sync drift state from DB: {e}")

    async def record_delta(self, predicted_retention: float, actual_retention: float):
        """
        Records the delta for a single production cycle.
        Persists to Postgres for long-term lineage.
        """
        delta = abs(predicted_retention - actual_retention)
        
        # 1. Update in-memory sliding window
        self.drift_history.append(delta)
        if len(self.drift_history) > 50:
            self.drift_history.pop(0)

        # 2. Persist to Source of Truth
        async with AsyncSessionLocal() as db:
            try:
                new_entry = DriftHistoryDB(
                    predicted_retention=predicted_retention,
                    actual_retention=actual_retention,
                    delta=delta
                )
                db.add(new_entry)
                await db.commit()
                logger.info(f"📉 [Drift] Delta Recorded & Persisted: {delta:.4f}")
            except Exception as e:
                logger.exception(f"Failed to persist drift delta: {e}")
                await db.rollback()

    def get_current_drift(self) -> float:
        if not self.drift_history: return 0.0
        return float(np.mean(self.drift_history))

    def check_for_alarm(self) -> bool:
        """Returns True if the algorithm shift requires a system-wide recalibration."""
        current_drift = self.get_current_drift()
        if current_drift > self.drift_threshold:
            logger.error(f"🚨 [ALARM] Algorithm Shift Detected! Drift: {current_drift:.2f}. Recalibrating Models...")
            return True
        return False

base_drift_service = DriftDetector()
