import os
import json
import logging
import time
from typing import Dict, Any, List, Optional
from groq import AsyncGroq
from api.config import settings
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures"""
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "CLOSED"

    def is_open(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class ScriptGenerator:
    def __init__(self):
        self.logger = logging.getLogger("ScriptGenerator")
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"
        self.circuit_breaker = CircuitBreaker()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception)),
        reraise=True
    )
    async def _call_ai(self, prompt: str) -> str:
        if self.circuit_breaker.is_open():
            raise Exception("Circuit breaker is OPEN")
        
        groq_key = settings.GROQ_API_KEY
        openai_key = os.getenv("OPENAI_API_KEY")

        providers = []
        if groq_key:
            providers.append(("groq", groq_key, "llama-3.3-70b-versatile", "https://api.groq.com/openai/v1/chat/completions"))
        if openai_key:
            providers.append(("openai", openai_key, "gpt-4o", "https://api.openai.com/v1/chat/completions"))

        import httpx
        for name, key, model, url in providers:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": "You are a Viral Content Narrator. You bridge and narrate relationships between videos for high-retention content. Output JSON ONLY."},
                                {"role": "user", "content": prompt}
                            ],
                            "response_format": {"type": "json_object"},
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        self.circuit_breaker.record_success()
                        return data["choices"][0]["message"]["content"]
                    
                    self.logger.warning(f"  ⚠️ {name.upper()} script generation failed ({resp.status_code}). Checking fallback...")
            except Exception as e:
                self.logger.error(f"  ⚠️ {name.upper()} script generation failed: {str(e)[:50]}")

        self.circuit_breaker.record_failure()
        raise Exception("All AI providers failed for script generation")

    async def generate_script(
        self, 
        topic: str, 
        niche: str, 
        duration_sec: int = 60, 
        style: str = "story",
        clips: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generates a structured script for a faceless video with Asset-Aware Narration.
        """
        # 1. Fetch crystallized winning patterns from Hermes
        hermes_context = ""
        try:
            from services.hermes.service import hermes_service
            skills = hermes_service.get_winning_context(niche)
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

        providers = []
        groq_key = settings.GROQ_API_KEY
        openai_key = os.getenv("OPENAI_API_KEY")
        if groq_key: 
            providers.append(("groq", groq_key, "llama-3.3-70b-versatile", "https://api.groq.com/openai/v1/chat/completions"))
        if openai_key:
            providers.append(("openai", openai_key, "gpt-4o", "https://api.openai.com/v1/chat/completions"))
        
        import httpx
        for name, key, model, url in providers:
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    resp = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 50
                        }
                    )
                    if resp.status_code == 200:
                        return resp.json()["choices"][0]["message"]["content"].strip()
            except Exception:
                continue
        return ""

    def _get_fallback_script(self, topic: str, niche: str, clips: List[Dict] = None) -> Dict[str, Any]:
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
