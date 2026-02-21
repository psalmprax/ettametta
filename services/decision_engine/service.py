import json
import logging
from typing import Dict, Any, List, Optional
from groq import AsyncGroq
from api.config import settings
from api.utils.vault import get_secret
from pydantic import BaseModel

class VideoStrategy(BaseModel):
    speed_range: List[float] = [0.98, 1.02]
    jitter_intensity: float = 1.0
    recommended_filters: List[str] = []
    hook_points: List[List[float]] = [] # [ [start, end], [start, end] ]
    b_roll_keywords: List[str] = []
    vibe: str = "Neutral"
    explanation: str = ""

class StrategyService:
    def __init__(self):
        self.api_key = get_secret("groq_api_key")
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"

    async def generate_visual_strategy(self, transcript: List[Dict], niche: str, style: str = "Default") -> VideoStrategy:
        """
        Analyzes transcript content and user-selected style to decide on video editing parameters.
        """
        full_text = " ".join([s.get("text", "") for s in transcript])
        
        prompt = f"""
        You are an elite AI Video Editor. Analyze the following video transcript, niche, and user-selected STYLE to decide the visual strategy.
        
        NICHE: {niche}
        SELECTED STYLE: {style}
        TRANSCRIPT: "{full_text[:2000]}"
        
        DECISION CRITERIA:
        1. STYLE OVERRIDE: If the user selected a specific style (e.g., 'Cinematic'), prioritize its parameters over the niche defaults.
        2. SPEED: High energy needs 1.02-1.1x speed ramping. Relaxed needs 0.95-1.0x.
        3. JITTER: Intense/Action needs 2.0-3.0 intensity. Calm needs 0.0-0.5.
        4. FILTERS: 'f6' (Speed Ramping), 'f7' (Cinematic Overlays), 'f8' (Dynamic Jitter).
        5. HOOKS: Identify 1-3 specific segments (start/end in seconds) that are the most viral, emotional, or high-energy parts of the transcript.
        6. B-ROLL: Provide 3-5 search keywords for stock footage (e.g., 'dark forest', 'police siren', 'cryptic symbols') that match the transcript's vibe.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "speed_range": [min, max],
            "jitter_intensity": float,
            "recommended_filters": ["f6", "f7", "f8"],
            "hook_points": [[start, end], ...],
            "b_roll_keywords": ["keyword1", "keyword2"],
            "vibe": "Energetic" | "Calm" | "Educational" | "Dramatic",
            "explanation": "Why this strategy?"
        }}
        """

        try:
            if not self.api_key or self.api_key == "your_key_here":
                return VideoStrategy()

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a professional social media editor. The user wants a '{style}' aesthetic. Output JSON."},
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
