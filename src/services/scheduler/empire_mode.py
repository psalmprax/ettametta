import logging
import json
from typing import Any
from src.api.config import settings

class EmpireModeScheduler:
    def __init__(self):
        self._client = None
        self.model = "llama-3.3-70b-versatile"

    @property
    def client(self):
        """Lazy-initialize the Groq client to prevent crash on import when GROQ_API_KEY is missing."""
        if self._client is None:
            if not settings.GROQ_API_KEY:
                raise RuntimeError(
                    "GROQ_API_KEY is not configured — EmpireModeScheduler requires a valid Groq key"
                )
            from groq import AsyncGroq
            self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        return self._client

    async def clone_strategy(self, base_script: dict[str, Any], target_niche: str) -> dict[str, Any]:
        """
        Re-spins a successful script for a new niche to avoid duplicate content flags.
        """
        prompt = f"""
        Adapt the following viral script for a new niche: {target_niche}.
        
        ORIGINAL SCRIPT:
        {json.dumps(base_script, indent=2)}
        
        REQUIREMENTS:
        - Rewrite the HOOK to fit the new niche.
        - Adapt the body text to use niche-specific terminology.
        - Change visual cues to match the new niche.
        - Maintain the exact same structural flow and timing.
        
        OUTPUT FORMAT (JSON ONLY):
        (Same structure as the input script)
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at content diversification. Output JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logging.exception(f"[EmpireModeScheduler] Cloning Error: {e}")
            return base_script

base_scheduler_service = EmpireModeScheduler()
