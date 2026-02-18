import os
import json
import logging
from typing import Dict, Any, List
from groq import AsyncGroq
from api.config import settings

class ScriptGenerator:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def generate_script(self, topic: str, niche: str, duration_sec: int = 60, style: str = "story") -> Dict[str, Any]:
        """
        Generates a structured script for a faceless video.
        """
        prompt = f"""
        You are an expert viral content strategist specializing in no-face monetization (faceless videos).
        Generate a compelling {duration_sec}-second video script for the following:
        
        Topic: {topic}
        Niche: {niche}
        Style: {style}
        
        STRUCTURE REQUIREMENTS:
        1. HOOK (0-5 sec): High-impact, pattern-interrupting opening that stops the scroll.
        2. BODY (5-{duration_sec-5} sec): Engaging, fast-paced content breakdown. Use clear, punchy sentences.
        3. CTA ({duration_sec-5} to end): Clear call to action (e.g., Follow for more, Check link in bio).
        4. B-ROLL CUES: Suggest specific visual cues for each segment.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "title": "Viral title idea",
            "segments": [
                {{
                    "type": "hook",
                    "text": "The script text here",
                    "visual_cue": "Description of what to show on screen",
                    "duration": 5
                }},
                ...
            ],
            "hashtags": ["#tag1", "#tag2"]
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You output valid JSON for video scripts."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logging.error(f"Script Generation Error: {e}")
            return {
                "error": str(e),
                "title": f"Failed to generate script for {topic}",
                "segments": []
            }

base_script_generator = ScriptGenerator()
