"""
Performance Ledger: The Truth Layer (10/10)
=========================================

Persistent log of Predicted vs Actual retention to prove 
the system's learning maturity.
"""

import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceLedger:
    def __init__(self, ledger_path: str = "data/analytics/performance_ledger.json"):
        self.ledger_path = ledger_path
        os.makedirs(os.path.dirname(ledger_path), exist_ok=True)

    def log_entry(self, video_id: str, predicted: float, actual: float, model_mae: float, niche: str = "general"):
        """Record the delta between hope and reality"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "video_id": video_id,
            "niche": niche,
            "predicted_retention": round(predicted, 4),
            "actual_retention": round(actual, 4),
            "error": round(abs(predicted - actual), 4),
            "model_confidence_mae": round(model_mae, 4)
        }
        
        try:
            entries = []
            if os.path.exists(self.ledger_path):
                with open(self.ledger_path, 'r') as f:
                    try:
                        entries = json.load(f)
                    except json.JSONDecodeError:
                        entries = []
            
            entries.append(entry)
            
            with open(self.ledger_path, 'w') as f:
                json.dump(entries, f, indent=4)
                
            logger.info(f"📗 [Ledger] Logged {video_id} ({niche}): Err={entry['error']:.4f}")
        except Exception as e:
            logger.exception(f"Ledger log failed: {e}")

    def get_accuracy_report(self) -> dict:
        """Dashboard Report: How honest is the system?"""
        if not os.path.exists(self.ledger_path):
            return {"accuracy": "no_data", "raw_entries": []}
            
        try:
            with open(self.ledger_path, 'r') as f:
                entries = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"accuracy": "no_data", "raw_entries": []}
        
        if not entries: return {"accuracy": "no_data", "raw_entries": []}
        
        avg_err = sum(e["error"] for e in entries) / len(entries)
        return {
            "avg_prediction_error": round(avg_err, 4),
            "total_verified_posts": len(entries),
            "system_honesty_level": f"{max(0, 100 - (avg_err * 100)):.1f}%",
            "raw_entries": entries
        }

# Singleton Instance
base_ledger_service = PerformanceLedger()
