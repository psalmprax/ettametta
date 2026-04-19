import logging
import random
from typing import Any
from datetime import datetime


from services.base_agent import BaseEttamettaAgent

class AlgorithmSentinel(BaseEttamettaAgent):
    """
    Monitors platform performance shifts and suggests pivots.
    Currently uses probabilistic modeling based on recent viral trends.
    """

    def __init__(self):
        super().__init__(agent_name="SENTINEL")

    async def get_sync_status(self) -> dict[str, Any]:
        """
        Returns the 'Algorithm Sync' score and potential risks.
        Tries to generate real-time metrics, falling back to probabilistic models on error.
        """
        try:
            import json
            prompt = """
            Analyze the current macro social media algorithm trends (TikTok, YouTube Shorts).
            Output JSON strictly with these keys: 
            - "score" (integer 0-100 indicating stability)
            - "status" ("NOMINAL", "WARNING", or "NEUTRAL")
            - "recommendations" (list of 3 string tips for hook/pacing shifts)
            """
            response_content = await self._call_llm(
                prompt=prompt,
                response_format="json_object"
            )

            data = json.loads(response_content)

            return {
                "score": data.get("score", 85),
                "status": data.get("status", "NOMINAL"),
                "last_shift_detected": datetime.utcnow().isoformat(),
                "recommendations": data.get("recommendations", []),
            }
        except Exception as e:
            await self._log(f"Failed to fetch dynamic sentinel data: {e}. Using fallback.", "ERROR")

        # Hardened: No fallback to mock/random data.
        return {
            "score": 0,
            "status": "UNKNOWN",
            "last_shift_detected": datetime.utcnow().isoformat(),
            "recommendations": [],
        }


base_algorithm_sentinel = AlgorithmSentinel()
