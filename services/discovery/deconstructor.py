import os
from .models import ContentCandidate, ViralPattern
from typing import Optional
import json
from api.utils.os_worker import ai_worker

class PatternDeconstructor:
    def __init__(self):
        self.enabled = os.getenv("USE_OS_MODELS", "true") == "true"

    async def analyze_video_structure(self, transcript: str, metadata: dict) -> ViralPattern:
        """
        Calls Groq API to deconstruct the video into hooks and sentiment.
        """
        from api.config import settings
        if not settings.GROQ_API_KEY:
             return self._fallback_pattern(transcript)

        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        prompt = f"""
        [Ettametta ANALYST]
        Analyze this video for viral potential:
        Transcript: {transcript}
        Metadata: {json.dumps(metadata)}
        
        Return JSON ONLY:
        {{
            "hook_score": 0.0-1.0,
            "retention_estimate": 0.0-1.0,
            "pacing_bpm": int,
            "style_keywords": ["keyword1", "keyword2"],
            "emotional_triggers": ["trigger1", "trigger2"]
        }}
        """
        
        try:
            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are a viral content strategist. Output only JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={{"type": "json_object"}}
            )
            
            res = json.loads(completion.choices[0].message.content)
            return ViralPattern(
                id=f"groq_{metadata.get('id', 'unknown')}",
                hook_score=float(res.get("hook_score", 0.5)),
                retention_estimate=float(res.get("retention_estimate", 0.5)),
                pacing_bpm=int(res.get("pacing_bpm", 120)),
                style_keywords=res.get("style_keywords", []),
                emotional_triggers=res.get("emotional_triggers", [])
            )
        except Exception as e:
            import logging
            logging.error(f"Groq analysis failed: {e}")
            return self._fallback_pattern(transcript)

    def _fallback_pattern(self, transcript: str) -> ViralPattern:
        return ViralPattern(
            id="os_pattern",
            hook_score=0.85,
            retention_estimate=0.70,
            pacing_bpm=110,
            style_keywords=["Open Source", "Local Inference"],
            emotional_triggers=["Authenticity", "Value"]
        )

pattern_deconstructor = PatternDeconstructor()
