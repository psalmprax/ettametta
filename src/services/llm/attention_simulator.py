import logging
import random
from typing import Any

logger = logging.getLogger("AttentionSimulator")

class AttentionSimulator:
    """
    10/10 Pre-Viz: Simulates how human attention will decay over the Story Blueprint.
    Allows for 'Narrative Pruning' before compute is wasted on rendering.
    """

    def simulate_retention(self, blueprint: dict[str, Any]) -> dict[str, Any]:
        """Heuristic-based Attention Flow Simulation (CPU Optimized)"""

        logger.info("[NRM] Simulating Attention Flow for Blueprint...")

        # 1. Structural Scoring
        has_hook = any(e['action'].lower() == "hook" for e in blueprint.get("emotional_arc", []))
        has_conflict = blueprint.get("narrative_conflict") is not None
        gap_count = len(blueprint.get("curiosity_gaps", []))

        score = 0
        if has_hook: score += 40
        if has_conflict: score += 30
        score += min(30, gap_count * 10)

        # 2. Simulated Curve (Internal Model Prediction)
        # 1.0 at 0s, decaying based on score
        decay_rate = 0.05 if score > 80 else 0.12 # Higher score = lower decay

        curve = []
        current = 1.0
        for t in range(0, 61, 5):
            current = max(0.2, current - (decay_rate * random.uniform(0.5, 1.5)))
            # Spike at curiosity payoffs
            for gap in blueprint.get("curiosity_gaps", []):
                if t == gap.get("payoff_time"):
                    current = min(1.0, current + 0.15)
            curve.append({"time": t, "retention": round(current, 2)})

        prediction = {
            "narrative_score": score,
            "predicted_retention_p50": curve[len(curve)//2]["retention"],
            "retention_curve": curve,
            "verdict": "PROCEED" if score >= 70 else "REGENERATE"
        }

        logger.info(f"📊 [NRM] Simulation Verdict: {prediction['verdict']} (Score: {score})")
        return prediction

base_attention_simulator_service = AttentionSimulator()
