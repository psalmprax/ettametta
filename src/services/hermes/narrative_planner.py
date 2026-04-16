import json
import logging
from typing import Dict, Any, List, Optional
from groq import AsyncGroq
from api.config import settings

logger = logging.getLogger("NarrativePlanner")

class NarrativePlanner:
    """
    10/10 Intelligence: The Narrative Reasoning Model (NRM).
    Decomposes topics into story-driven components before editing begins.
    """
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def plan_story(self, topic: str, niche: str, duration_sec: int = 60) -> Dict[str, Any]:
        """Creates a high-level Narrative Blueprint for the attention economy."""
        
        logger.info(f"🧠 [NRM] Designing Narrative Blueprint for: {topic}")
        
        prompt = f"""
        You are the Narrative Reasoning Model (NRM). Your task is to design a high-retention 'Story Blueprint' for a {duration_sec}-second video.
        
        TOPIC: {topic}
        NICHE: {niche}
        
        TASK:
        1. DECOMPOSE: Identify the Core Claim, the Conflict, and the Stakes.
        2. EMOTIONAL ARC: Map the intended emotional states over the duration.
        3. ATTENTION TRIGGERS: Identify 3 'Curiosity Gaps' to open and close.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "core_claim": "One sentence summary of the main point",
            "narrative_conflict": "The tension that keeps people watching",
            "stakes": "Why the viewer should care",
            "emotional_arc": [
                {{"time_start": 0, "time_end": 5, "emotion": "Shock/Surprise", "action": "Hook"}},
                {{"time_start": 5, "time_end": 20, "emotion": "Intrigue", "action": "Setup"}},
                {{"time_start": 20, "time_end": 45, "emotion": "Tension/Fear", "action": "Development"}},
                {{"time_start": 45, "time_end": 60, "emotion": "Relief/Clarity", "action": "Resolution"}}
            ],
            "curiosity_gaps": [
                {{"gap": "Question asked", "payoff_time": 45}}
            ],
            "visual_direction": "The overall cinematic style (e.g., 'Aggressive Cuts', 'Documentary', 'Ethereal')"
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Story-Driven Attention Optimization Engine. You prioritize narrative tension over simple facts."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            blueprint = json.loads(response.choices[0].message.content)
            logger.info("✨ [NRM] Narrative Blueprint Crystallized.")
            return blueprint
        except Exception as e:
            logger.error(f"[NRM] Blueprint Generation Failed: {e}")
            return self._get_fallback_blueprint(topic)

    def _get_fallback_blueprint(self, topic: str) -> Dict[str, Any]:
        return {
            "core_claim": f"Why {topic} matters now.",
            "narrative_conflict": "Information vs Ignorance.",
            "stakes": "Staying ahead of the trend.",
            "emotional_arc": [
                {"time_start": 0, "time_end": 10, "emotion": "Curiosity", "action": "Hook"},
                {"time_start": 10, "time_end": 60, "emotion": "Interest", "action": "Context"}
            ],
            "visual_direction": "Professional Cinematic"
        }

base_narrative_planner = NarrativePlanner()
