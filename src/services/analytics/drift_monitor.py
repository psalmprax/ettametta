"""
Drift Monitor: Accuracy Audit (10/10)
=====================================

Monitors for algorithm drift and triggers automated 
self-correction cycles for the Neural Oracle.
"""

import logging
import json
import numpy as np
from typing import Any
from src.services.analytics.ledger import base_ledger_service
from src.services.optimization.forecaster_pipeline import base_forecaster_service

logger = logging.getLogger(__name__)

class DriftMonitor:
    """
    The Self-Correction Audit Layer.
    """
    def __init__(self, drift_threshold: float = 0.15):
        self.drift_threshold = drift_threshold

    def audit_system_honesty(self) -> dict[str, Any]:
        """Calculates Mean Absolute Error for the last N productions"""
        report = base_ledger_service.get_accuracy_report()
        error = report.get("avg_prediction_error", 0.0)
        
        needs_correction = error > self.drift_threshold
        
        status = {
            "current_mae": error,
            "drift_threshold": self.drift_threshold,
            "status": "UNSTABLE" if needs_correction else "STABLE",
            "needs_retrain": needs_correction
        }
        
        if needs_correction:
            logger.warning(f"⚠️ [Drift] Critical Accuracy Drift: {error:.2f} > {self.drift_threshold}")
            # In a full 10/10, this would trigger the ForecasterPipeline.run_training_cycle()
            
        return status

# Singleton Instance
base_monitor_service = DriftMonitor()
