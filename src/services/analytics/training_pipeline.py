"""
Training Pipeline for Oracle Retraining (True 10/10)
===================================================

Aggregates real-world feedback and triggers the Oracle's 
Machine Learning training loop.
"""

import json
import os
import logging
from typing import Any
from services.optimization.oracle_predictor import base_neural_oracle

logger = logging.getLogger(__name__)

class TrainingPipeline:
    def __init__(self, data_path: str = "data/training/samples.jsonl"):
        self.data_path = data_path
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        self.batch_threshold = 10 # Retrain every 10 samples

    def record_sample(self, fusion_plan: dict, metrics: dict[str, Any]):
        """Records a new training sample: [Features -> Metric]"""
        features = base_neural_oracle.extract_features(fusion_plan)
        # Use retention_p50 as the gold-standard metric for content quality
        metric = metrics.get("retention_p50", metrics.get("views", 0) / 10000) # Fallback to normalized views
        
        sample = {
            "features": features.tolist(),
            "metric": float(metric)
        }
        
        with open(self.data_path, "a") as f:
            f.write(json.dumps(sample) + "\n")
            
        logger.info(f"💾 [Pipeline] New training sample recorded. Total samples check...")
        
        # Check if we should retrain
        self._check_and_trigger_retraining()

    def _check_and_trigger_retraining(self):
        """Triggers Oracle retraining if enough data has been collected"""
        try:
            with open(self.data_path, "r") as f:
                lines = f.readlines()
            
            if len(lines) >= self.batch_threshold:
                logger.info(f"🔄 [Pipeline] Batch threshold ({self.batch_threshold}) met. Triggering Oracle Retraining...")
                samples = [json.loads(line) for line in lines]
                base_neural_oracle.train_on_batch(samples)
                
                # Move samples to archive or clear (for simple loop)
                # os.remove(self.data_path) 
        except Exception as e:
            logger.error(f"Training check failed: {e}")

# Singleton Instance
base_training_pipeline = TrainingPipeline()
