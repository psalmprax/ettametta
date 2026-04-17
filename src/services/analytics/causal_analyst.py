import json
import logging
import numpy as np
from typing import Any
from groq import AsyncGroq
from src.api.config import settings

logger = logging.getLogger("CausalAnalyst")

class CausalAnalyst:
    """
    10/10 Reflex: The Ground-Truth Reflection Engine.
    Analyzes the 'Regret' between prediction and reality.
    """
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def analyze_regret(self, predicted_curve: list[dict], actual_curve: list[dict], blueprint: dict[str, Any]) -> dict[str, Any]:
        """Identifies the 'Why' behind prediction errors."""
        
        # 1. Calculate the Delta
        pred_vals = [p["retention"] for p in predicted_curve]
        act_vals = [a["retention"] for a in actual_curve]
        
        # Trim or pad to match lengths
        min_len = min(len(pred_vals), len(act_vals))
        pred_vals = np.array(pred_vals[:min_len])
        act_vals = np.array(act_vals[:min_len])
        
        errors = act_vals - pred_vals
        max_error_idx = np.argmin(errors) # Most negative error = most overestimated
        error_time = max_error_idx * 5
        
        logger.info(f"📉 [Causal] Detected max drop-off error at {error_time}s")
        
        # 2. AI Reflection on the Error
        prompt = f"""
        You are the Causal Attribution Engine. You are analyzing why a video performed differently than predicted.
        
        NARRATIVE BLUEPRINT:
        {json.dumps(blueprint, indent=2)}
        
        PREDICTION ERROR:
        - At {error_time} seconds, the video performed {abs(errors[max_error_idx]):.2f} worse than predicted.
        - The intended emotion was: {self._get_emotion_at(blueprint, error_time)}
        
        TASK:
        Identify the 'Causal Reason' for this failure. Was it 'Hook Latency', 'Confusing Setup', 'Boring Middle', or 'Payoff Failure'?
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "causal_reason": "Brief technical label",
            "explanation": "Why did humans leave here?",
            "narrative_fix": "How to fix this in future blueprints",
            "impact_score": 0.85
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Causal ML Analyst specializing in human attention behavior."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result["timestamp_sec"] = error_time
            result["error_magnitude"] = float(abs(errors[max_error_idx]))
            
            logger.info(f"🧠 [Causal] Lessons crystallized: {result['causal_reason']}")
            return result
        except Exception as e:
            logger.error(f"[Causal] Reflection Failed: {e}")
            return {"causal_reason": "Unknown", "explanation": "System error during reflection."}

    def _get_emotion_at(self, blueprint: dict[str, Any], t: int) -> str:
        for arc in blueprint.get("emotional_arc", []):
            if arc["time_start"] <= t <= arc["time_end"]:
                return arc["emotion"]
        return "Unknown"

base_causal_analyst = CausalAnalyst()
