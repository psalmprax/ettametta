import logging
import json
from typing import List, Dict, Any
from groq import AsyncGroq
from api.config import settings

class EmpireModeScheduler:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def clone_strategy(self, base_script: Dict[str, Any], target_niche: str) -> Dict[str, Any]:
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
            logging.error(f"[EmpireModeScheduler] Cloning Error: {e}")
            return base_script

base_empire_scheduler = EmpireModeScheduler()
