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
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You output valid JSON for video scripts."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=30.0
            )
            self.circuit_breaker.record_success()
            return response.choices[0].message.content
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise e

    async def generate_script(self, topic: str, niche: str, duration_sec: int = 60, style: str = "story") -> Dict[str, Any]:
        """
        Generates a structured script for a faceless video with high quality & resilience.
        """
        prompt = f"""
        You are an expert viral content strategist specializing in no-face monetization (faceless videos).
        Generate a compelling {duration_sec}-second video script for the following:
        
        Topic: {topic}
        Niche: {niche}
        Style: {style}
        
        STRUCTURE REQUIREMENTS:
        1. HOOK (0-5 sec): High-impact, pattern-interrupting opening that stops the scroll.
        2. MID-CONTENT ENGAGEMENT (at roughly 50% duration): Explicitly appeal to viewers to LIKE the video and SUBSCRIBE for more {niche} secrets. Explain WHY it helps them (e.g., 'so you never miss a trending update').
        3. BODY: Engaging, fast-paced content breakdown. Use clear, punchy sentences.
        4. FINAL MONETIZATION CTA (last 5-8 seconds): High-urgency, aggressive call to action. Tell them to check the link in the bio NOW for the product/service mentioned. Use scarcity (e.g., 'limited time', 'don't wait').
        5. B-ROLL CUES: Suggest specific visual cues for each segment, including visual "LIKE" and "SUBSCRIBE" animations for the engagement segment.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "title": "Viral title idea",
            "segments": [
                {{
                    "type": "hook | content | engagement | cta",
                    "text": "The script text here",
                    "visual_cue": "Description of what to show on screen",
                    "duration": 5
                }}
            ],
            "hashtags": ["#tag1", "#tag2"]
        }}
        """
        
        try:
            content = await self._call_ai(prompt)
            return json.loads(content)
        except Exception as e:
            self.logger.error(f"Script Generation Error: {e}. Using fallback template.")
            return self._get_fallback_script(topic, niche)

    def _get_fallback_script(self, topic: str, niche: str) -> Dict[str, Any]:
        """Returns a high-quality fallback script if AI fails."""
        return {
            "title": f"Why {topic} is Trending in {niche}",
            "segments": [
                {
                    "type": "hook",
                    "text": f"Did you know about {topic}? Most people in the {niche} space are missing this.",
                    "visual_cue": f"Stunning graphic related to {topic}",
                    "duration": 5
                },
                {
                    "type": "content",
                    "text": f"When it comes to {topic}, the secret is all about timing and execution.",
                    "visual_cue": "Fast-paced B-roll montage",
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
