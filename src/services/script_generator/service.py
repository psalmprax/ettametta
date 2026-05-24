import os
import json
import logging
import time
from typing import Any
from src.services.llm.intelligence_hub import base_intelligence_service
from src.api.config import settings
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


NICHE_TAXONOMY = {
    "Motivation": ["success", "habits", "mindset", "discipline", "goals", "productivity", "overcoming", "inspiration", "growth"],
    "Finance": ["money", "investing", "crypto", "stocks", "business", "wealth", "passive income", "financial freedom"],
    "Tech": ["ai", "technology", "coding", "software", "gadgets", "programming", "apps", "innovation"],
    "Health": ["fitness", "diet", "wellness", "exercise", "nutrition", "mental health", "sleep", "weight loss"],
    "Gaming": ["game", "esports", "streaming", "minecraft", "fortnite", "gaming setup", "walkthrough"],
    "Education": ["history", "science", "facts", "learning", "tutorial", "explained", "documentary", "how to"],
    "Social Commentary": ["society", "culture", "politics", "feminism", "equality", "controversy", "debate", "opinion"],
    "Entertainment": ["celebrity", "movies", "music", "viral", "trending", "reaction", "comedy", "funny"],
    "Lifestyle": ["travel", "food", "fashion", "beauty", "home", "diy", "minimalism", "daily routine"],
    "Spirituality": ["meditation", "consciousness", "universe", "law of attraction", "manifestation", "energy", "chakras"]
}


def detect_niche_from_topic(topic: str) -> str:
    """Auto-detect the most relevant niche based on topic keywords."""
    topic_lower = topic.lower()
    best_match = "General"
    best_score = 0
    
    for niche, keywords in NICHE_TAXONOMY.items():
        score = sum(1 for kw in keywords if kw in topic_lower)
        if score > best_score:
            best_score = score
            best_match = niche
    
    return best_match

class ScriptGenerator:
    def __init__(self):
        self.logger = logging.getLogger("ScriptGenerator")
        self.circuit_breaker = self._SimpleCircuitBreaker()

    class _SimpleCircuitBreaker:
        """Lightweight circuit breaker for AI call protection."""
        def __init__(self, failure_threshold: int = 5):
            self._failures = 0
            self._threshold = failure_threshold
        def is_open(self) -> bool:
            return self._failures >= self._threshold
        def record_failure(self):
            self._failures += 1
        def record_success(self):
            self._failures = 0

    async def _call_ai(self, prompt: str, session_id: str | None = None) -> str:
        """Centralized AI call through IntelligenceHub"""
        try:
            result = await base_intelligence_service.chat(
                prompt=prompt,
                system_prompt="You are a Viral Content Narrator. You bridge and narrate relationships between videos for high-retention content. Output JSON ONLY.",
                session_id=session_id,
                json_mode=True
            )
            return result["response"]
        except Exception as e:
            self.logger.error(f"  ⚠️ Hub script generation failed: {str(e)[:50]}")
            raise Exception("IntelligenceHub failed for script generation")

    async def generate_script(
        self, 
        topic: str, 
        niche: str | None = None, 
        duration_sec: int = 60, 
        style: str = "story",
        clips: list[dict] = None,
        session_id: str | None = None
    ) -> dict[str, Any]:
        """
        Generates a structured script for a faceless video with Asset-Aware Narration.
        
        If niche is not provided or is 'General', auto-detects the best niche from the topic.
        """
        # Auto-detect niche if not provided or too generic
        if not niche or niche.lower() in ["general", "auto", ""]:
            niche = detect_niche_from_topic(topic)
            logging.info(f"Auto-detected niche '{niche}' for topic: {topic}")
        
        # 1. Fetch crystallized winning patterns from Hermes
        hermes_context = ""
        try:
            from src.services.hermes.service import base_hermes_service
            skills = base_hermes_service.get_winning_context(niche)
            if skills:
                patterns = [f"- {s['skill_name']}: {s['abstracted_pattern']}" for s in skills]
                hermes_context = "\n".join(patterns)
                self.logger.info(f"💎 [Hermes] Injecting {len(skills)} winning patterns into prompt for {niche}")
        except Exception as e:
            self.logger.warning(f"Could not load Hermes skills: {e}")

        # 2. Build Asset Context (The "Relationships" to narrate)
        asset_context = ""
        if clips:
            asset_context = "AVAILABLE VIDEO ASSETS (The clips you must bridge and narrate):\n"
            for i, clip in enumerate(clips[:6]):
                analysis = clip.get("analysis", {})
                asset_context += f"Clip {i+1}: ID={clip.get('id')}, Title='{clip.get('title')}', Pattern='{analysis.get('content_type')}', Sentiment='{analysis.get('sentiment')}'\n"

        # 3. Build the mission prompt with Dynamism Engine (Tier 10.0 Upgrade)
        style_guidance = {
            "story": "Focus on a 'Character-Climbing' arc. Start with a relatable struggle and end with an unexpected triumph.",
            "educational": "Use the 'Inverted Pyramid' of curiosity. Start with a mind-blowing anomaly and explain the mechanics.",
            "aggressive": "High-velocity delivery. Rapid-fire facts. Use 'Staccato' rhythm in sentences.",
            "asmr": "Sensory-heavy descriptions. Slow pacing. Focus on texture and sound visual cues.",
            "motivation": "Emotional Crescendo. Start with low-energy vulnerability and build to high-energy breakthrough."
        }.get(style.lower(), "Ensure high-retention pacing and viral delivery.")

        prompt = f"""
        You are a Viral Narrative Architect. Your mission is to engineer a high-velocity {duration_sec}-second video script for the {niche} niche.
        
        TOPIC: {topic}
        STYLE: {style}
        GUIDANCE: {style_guidance}
        
        {"⚡ WINNING PATTERNS (Crystallized from viral hits):" if hermes_context else ""}
        {hermes_context}

        {"🎬 ASSET CONTEXT (Available Clips):" if asset_context else ""}
        {asset_context}

        DYNAMISM REQUIREMENTS:
        1. ADAPTIVE STRUCTURE: You are NOT restricted to a fixed segment count. Decide how many beats are needed to maximize retention for a {duration_sec}s video.
        2. EMOTIONAL ARC: Define a 'tone' for every segment (e.g., Suspenseful, Revelation, Hype, Vulnerable).
        3. PATTERN INTERRUPTS: Every 7-10 seconds, inject a visual or narrative pattern interrupt (e.g., a sudden change in angle, a shocking fact, or a sound effect cue).
        4. ASSET BINDING: Use 'target_clip_id' from the assets above to ground your narration in reality.
        5. VISUAL PACING: Provide 'visual_style' hints (e.g., 'Rapid cuts', 'Slow pan', 'Glitch overlay').
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "title": "Aggressive Viral Title",
            "emotional_arc": "The progression of feelings (e.g., Curiosity -> Shock -> FOMO)",
            "segments": [
                {{
                    "type": "hook | insight | build | transition | cta",
                    "tone": "The specific emotion of this beat",
                    "text": "The spoken narration (pacing-optimized)",
                    "visual_cue": "Specific visual description",
                    "visual_style": "How the visual should behave (pacing/effects)",
                    "pattern_interrupt": "Description of the interrupt at this beat",
                    "target_clip_id": "ID from asset context",
                    "duration": 5
                }}
            ],
            "hashtags": ["#tag1", "#tag2"]
        }}
        """
        
        try:
            content = await self._call_ai(prompt)
            data = json.loads(content)
            self.logger.info(f"✨ Asset-Aware script generated for '{topic}'")
            return data
        except Exception as e:
            self.logger.error(f"Script Generation Error: {e}. Using fallback.")
            return self._get_fallback_script(topic, niche, clips)

    async def complete(self, prompt: str, system_prompt: str = "You are a Viral Content Analyst. Respond in plain text.") -> str:
        """Generic AI completion for cross-service intelligence (Tournament Selection, etc)"""
        if self.circuit_breaker.is_open():
            return ""

        try:
            result = await base_intelligence_service.chat(
                prompt=prompt,
                system_prompt=system_prompt
            )
            self.circuit_breaker.record_success()
            return result.get("response", "")
        except Exception as e:
            self.circuit_breaker.record_failure()
            self.logger.warning(f"Complete() failed: {e}")
            return ""


    def _get_fallback_script(self, topic: str, niche: str, clips: list[dict] = None) -> dict[str, Any]:
        """Returns a script that tries to bridge clips if available."""
        clip_ref = clips[0].get("id") if clips else "stock"
        return {
            "title": f"Why {topic} is Trending in {niche}",
            "segments": [
                {
                    "type": "hook",
                    "text": f"Did you know about {topic}? Most people in the {niche} space are missing this.",
                    "visual_cue": f"Stunning graphic related to {topic}",
                    "target_clip_id": clip_ref,
                    "duration": 5
                },
                {
                    "type": "content",
                    "text": f"When it comes to {topic}, the secret is all about timing and execution.",
                    "visual_cue": "Fast-paced B-roll montage",
                    "target_clip_id": clips[1].get("id") if clips and len(clips) > 1 else clip_ref,
                    "duration": 15
                },
                {
                    "type": "engagement",
                    "text": "If you finding this helpful, hit that like button and subscribe for more daily secrets!",
                    "visual_cue": "Like and Subscribe animation",
                    "duration": 5
                },
                {
                    "type": "cta",
                    "text": "The clock is ticking. Check the link in our bio for the full breakdown before it's gone!",
                    "visual_cue": "Arrow pointing to bio link",
                    "duration": 8
                }
            ],
            "hashtags": [f"#{niche.replace(' ', '')}", f"#{topic.replace(' ', '')}", "#viral"]
        }

base_script_service = ScriptGenerator()
