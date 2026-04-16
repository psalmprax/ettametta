import json
import logging
from typing import Dict, Any, List
from groq import AsyncGroq
from api.config import settings

class HookValidator:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def validate_hook(self, hook_text: str) -> Dict[str, Any]:
        """
        Analyzes a script hook and provides a 'Kill-Switch' score + alternatives.
        """
        prompt = f"""
        Analyze the following video hook for its viral potential in a faceless/no-face video format.
        
        HOOK TEXT: "{hook_text}"
        
        CRITERIA:
        - Pattern Interrupt: Does it grab attention in <1 second?
        - Curiosity Gap: Does it make the viewer want to see the resolution?
        - Clarity: Is it immediately understandable?
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "score": 0-100,
            "analysis": "Brief breakdown of why this score was given",
            "status": "PASS" | "KILL" (KILL if score < 75),
            "alternatives": [
                "High-impact alternative 1",
                "High-impact alternative 2",
                "High-impact alternative 3"
            ]
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a viral retention specialist. Output JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logging.error(f"Hook Validation Error: {e}")
            return {
                "score": 0,
                "analysis": f"Error: {e}",
                "status": "KILL",
                "alternatives": []
            }

base_hook_validator = HookValidator()
