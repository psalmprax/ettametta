import json
import logging
from typing import Any
import os
from src.services.llm.intelligence_hub import base_intelligence_service

logger = logging.getLogger("NarrativePlanner")

class NarrativePlanner:
    """
    10/10 Intelligence: The Narrative Reasoning Model (NRM).
    Decomposes topics into story-driven components before editing begins.
    """
    def __init__(self):
        # We now use the unified IntelligenceHub for multi-provider resilience
        pass

    async def plan_story(self, topic: str, niche: str, duration_sec: int = 60, session_id: str | None = None, feedback: str | None = None) -> dict[str, Any]:
        """Creates a high-level Narrative Blueprint for the attention economy."""
        
        logger.info(f"🧠 [NRM] Designing Narrative Blueprint for: {topic}")
        
        feedback_clause = f"\nPREVIOUS FEEDBACK: {feedback}\nPlease address these issues in the new version." if feedback else ""

        prompt = f"""
        You are the Narrative Reasoning Model (NRM). Your task is to design a high-retention 'Story Blueprint' for a {duration_sec}-second video.
        
        TOPIC: {topic}
        NICHE: {niche}
        {feedback_clause}
        
        TARGET QUALITY: ELITE (95%+ Attention Score)
        
        CRITICAL REQUIREMENTS:
        1. HOOK: Must be visceral and immediate (Time 0-5s).
        2. CONFLICT: Establish a high-stakes tension early.
        3. CURIOSITY GAPS: You MUST include at least 3 distinct 'Curiosity Gaps' with clear payoff timestamps to maximize retention.
        
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
                {{"gap": "Question 1", "payoff_time": 15}},
                {{"gap": "Question 2", "payoff_time": 35}},
                {{"gap": "Question 3", "payoff_time": 55}}
            ],
            "visual_direction": "The overall cinematic style"
        }}
        """
        
        try:
            result = await base_intelligence_service.chat(
                prompt=prompt,
                system_prompt="You are a Story-Driven Attention Optimization Engine. Return ONLY valid JSON. Focus on maximizing Curiosity Gaps.",
                session_id=session_id,
                json_mode=True
            )
            
            blueprint = json.loads(result["response"])
            logger.info(f"✨ [NRM] Narrative Blueprint Crystallized via {result['provider'].upper()}.")
            return blueprint

        except Exception as e:
            logger.error(f"[NRM] Blueprint Generation Failed: {e}")
            return self._get_fallback_blueprint(topic)

    def _get_fallback_blueprint(self, topic: str) -> dict[str, Any]:
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

base_narrative_planner_service = NarrativePlanner()
