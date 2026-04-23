"""
Analytics Bridge for Ettametta Ascension
=========================================

The 'Ascension' tier ingestion port for real-world performance metrics.
This service closes the loop by feeding post-production results back into 
the Hermes Reflection Engine.
"""

import logging
from typing import Any
from src.services.hermes.service import base_hermes_service
from src.services.analytics.training_pipeline import base_training_pipeline
from src.services.optimization.oracle_predictor import base_neural_oracle
from src.services.analytics.ledger import base_performance_ledger

logger = logging.getLogger(__name__)

class AnalyticsBridge:
    """
    Ingests metrics from TikTok, YouTube, and IG.
    Triggers evolutionary learning loops.
    """

    async def ingest_performance(self, video_id: str, metrics: dict[str, Any], production_data: dict[str, Any]):
        """
        Ingest performance metrics and trigger reflection if thresholds are met.
        
        metrics: {
            "views": int,
            "retention_p50": float (0-1),
            "shares": int,
            "ctr": float
        }
        """
        logger.info(f"📊 [Analytics] Ingesting performance for {video_id}: {metrics.get('views')} views")
        
        # 1. Store the feedback in a local log (optional/database in production)
        # For now, we trigger Hermes directly
        
        # 2. Trigger Hermes Reflection Loop (Heuristic Crystallization)
        skill = await base_hermes_service.reflect_and_crystallize(
            job_data={**production_data, "job_id": video_id},
            metrics=metrics
        )
        
        # 3. Trigger Oracle Training Loop (Statistical Retraining)
        fusion_plan = production_data.get("fusion_plan", {})
        if fusion_plan:
            base_training_pipeline.record_sample(fusion_plan, metrics)
            
            # 4. Final Scientific Step: Update Performance Ledger
            # Compare the Oracle's prediction with reality
            predicted = production_data.get("predicted_retention", 0.5)
            actual = metrics.get("retention_p50", metrics.get("views", 0) / 10000)
            
            base_performance_ledger.log_entry(
                video_id=video_id,
                predicted=predicted,
                actual=actual,
                model_mae=base_neural_oracle.accuracy_log[-1] if base_neural_oracle.accuracy_log else 1.0
            )

        if skill:
            logger.info(f"🧬 [Evolution] System evolved based on {video_id} success: {skill.get('skill_name')}")
            return {"status": "evolved", "skill": skill}
            
        return {"status": "recorded"}

# Singleton Instance
base_analytics_bridge = AnalyticsBridge()
