import os
import json
import logging
import time
from typing import Any
from services.llm.intelligence_hub import base_intelligence_hub
from api.config import settings
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

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
            result = await base_intelligence_hub.chat(
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
        niche: str, 
        duration_sec: int = 60, 
        style: str = "story",
        clips: list[dict] = None,
        session_id: str | None = None
    ) -> dict[str, Any]:
        """
        Generates a structured script for a faceless video with Asset-Aware Narration.
        """
        # 1. Fetch crystallized winning patterns from Hermes
        hermes_context = ""
        try:
            from services.hermes.service import base_hermes_service
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

        # 3. Build the mission prompt with Asset-Aware Discovery
        prompt = f"""
        You are a Viral Narrator. Your mission is to narrate the transitions and relationships between specific video clips to create a cohesive {duration_sec}-second video.
        
        TOPIC: {topic}
        NICHE: {niche}
        STYLE: {style}
        
        {f"⚡ WINNING PATTERNS (Crystallized from viral hits):" if hermes_context else ""}
        {hermes_context}

        {f"🎬 ASSET CONTEXT (Use these clips):" if asset_context else ""}
        {asset_context}

        REQUIREMENTS:
        1. NARRATE THE RELATIONSHIPS: Don't just talk about the topic. Explain how one clip builds on the next.
        2. ASSET BINDING: For every segment, specify which 'target_clip_id' from the assets above you are talking about.
        3. HOOK (0-5 sec): Use the most high-impact asset.
        4. MID-CONTENT ENGAGEMENT: Call to action at 50% mark.
        5. B-ROLL CUES: Description of visual overlays.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "title": "Viral title idea",
            "segments": [
                {{
                    "type": "hook | content | engagement | cta",
                    "text": "The script text here",
                    "visual_cue": "Visual description",
                    "target_clip_id": "The ID from the asset context if applicable",
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
            result = await base_intelligence_hub.chat(
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

base_script_generator = ScriptGenerator()
