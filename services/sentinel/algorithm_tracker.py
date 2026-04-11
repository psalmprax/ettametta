import logging
import random
from typing import Dict, Any, List
from datetime import datetime


class AlgorithmSentinel:
    """
    Monitors platform performance shifts and suggests pivots.
    Currently uses probabilistic modeling based on recent viral trends.
    """

    async def get_sync_status(self) -> Dict[str, Any]:
        """
        Returns the 'Algorithm Sync' score and potential risks.
        Tries to generate real-time metrics, falling back to probabilistic models on error.
        """
        try:
            from groq import AsyncGroq
            from api.config import settings
            import json
            import logging
            import asyncio

            if settings.GROQ_API_KEY:
                client = AsyncGroq(api_key=settings.GROQ_API_KEY)
                prompt = """
                Analyze the current macro social media algorithm trends (TikTok, YouTube Shorts).
                Output JSON strictly with these keys: 
                - "score" (integer 0-100 indicating stability)
                - "status" ("NOMINAL", "WARNING", or "NEUTRAL")
                - "recommendations" (list of 3 string tips for hook/pacing shifts)
                """
                chat_completion = await client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    response_format={"type": "json_object"},
                )

                response_str = chat_completion.choices[0].message.content.strip()
                data = json.loads(response_str)

                return {
                    "score": data.get("score", 85),
                    "status": data.get("status", "NOMINAL"),
                    "last_shift_detected": datetime.utcnow().isoformat(),
                    "recommendations": data.get("recommendations", []),
                }
        except Exception as e:
            import logging

            logging.getLogger("AlgorithmSentinel").error(
                f"Failed to fetch dynamic sentinel data: {e}. Using fallback."
            )

        # Hardened: No fallback to mock/random data.
        return {
            "score": 0,
            "status": "UNKNOWN",
            "last_shift_detected": datetime.utcnow().isoformat(),
            "recommendations": [],
        }


base_algorithm_sentinel = AlgorithmSentinel()
