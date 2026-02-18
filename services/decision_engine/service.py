import json
import logging
from typing import Dict, Any, List, Optional
from groq import AsyncGroq
from api.config import settings
from pydantic import BaseModel

class VideoStrategy(BaseModel):
    speed_range: List[float] = [0.98, 1.02]
    jitter_intensity: float = 1.0
    recommended_filters: List[str] = []
    vibe: str = "Neutral"
    explanation: str = ""

class StrategyService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def generate_visual_strategy(self, transcript: List[Dict], niche: str) -> VideoStrategy:
        """
        Analyzes transcript content to decide on video editing parameters.
        """
        full_text = " ".join([s.get("text", "") for s in transcript])
        
        prompt = f"""
        You are an elite AI Video Editor. Analyze the following video transcript and niche to decide the visual strategy.
        
        NICHE: {niche}
        TRANSCRIPT: "{full_text[:2000]}"
        
        DECISION CRITERIA:
        1. SPEED: High energy needs 1.02-1.1x speed ramping. Relaxed needs 0.95-1.0x.
        2. JITTER: Intense/Action needs 2.0-3.0 intensity. Calm needs 0.0-0.5.
        3. FILTERS: 
           - 'f6' (Speed Ramping): Good for high energy.
           - 'f7' (Cinematic Overlays): Good for moody/emotional content.
           - 'f8' (Dynamic Jitter): Good for raw/vlog feel.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "speed_range": [min, max],
            "jitter_intensity": float,
            "recommended_filters": ["f6", "f7", "f8"],
            "vibe": "Energetic" | "Calm" | "Educational" | "Dramatic",
            "explanation": "Why this strategy?"
        }}
        """

        try:
            if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_key_here":
                return VideoStrategy()

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional social media editor. Output JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            return VideoStrategy(**data)
        except Exception as e:
            logging.error(f"[StrategyService] Error: {e}")
            return VideoStrategy()

base_strategy_service = StrategyService()
