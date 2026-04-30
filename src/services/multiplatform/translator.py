import logging
import json
from typing import Any
from src.services.llm.intelligence_hub import base_intelligence_service
from src.services.voiceover.service import base_voiceover_service

class GlobalReachAdapter:
    def __init__(self):
        self.logger = logging.getLogger("GlobalReachAdapter")

    async def translate_metadata(self, title: str, description: str, tags: list[str], target_lang: str) -> dict[str, Any]:
        """
        Translates video metadata using IntelligenceHub.
        """
        prompt = f"""
        Translate the following video metadata into {target_lang}.
        Maintain the viral, high-impact tone. Use natural local idioms.
        
        TITLE: {title}
        DESCRIPTION: {description}
        TAGS: {", ".join(tags)}
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "title": "Translated title",
            "description": "Translated description",
            "tags": ["tag1", "tag2"]
        }}
        """
        
        try:
            result = await base_intelligence_service.chat(
                prompt=prompt,
                system_prompt=f"You are a native {target_lang} viral marketing expert. Output JSON.",
                json_mode=True,
                complexity="medium"
            )
            
            content = result["response"]
            return json.loads(content)
        except Exception as e:
            self.logger.error(f"[GlobalReachAdapter] Translation Error: {e}")
            return {
                "title": title,
                "description": description,
                "tags": tags,
                "error": str(e)
            }

    async def translate_script_segments(self, segments: list[dict[str, Any]], target_lang: str) -> list[dict[str, Any]]:
        """
        Translates a list of script segments for dubbing/subtitles.
        """
        prompt = f"""
        Translate these video script segments into {target_lang}.
        
        CRITICAL RULES:
        1. Keep the EXACT same JSON structure and ALL keys (type, text, visual_cue, visual_style, tone, pattern_interrupt, duration).
        2. ONLY translate the content of the "text" and "visual_cue" fields.
        3. Do NOT change the number of segments.
        
        SEGMENTS TO TRANSLATE:
        {json.dumps(segments, indent=2)}
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "segments": [ ... translated segments ... ]
        }}
        """
        
        try:
            result = await base_intelligence_service.chat(
                prompt=prompt,
                system_prompt=f"You are a native {target_lang} scriptwriter. You translate video scripts while preserving all metadata. Output JSON.",
                json_mode=True,
                complexity="medium"
            )
            
            content = result["response"]
            translated_data = json.loads(content)
            
            # Safety Check: Handle both { "segments": [...] } and direct [...] formats
            if isinstance(translated_data, list):
                return translated_data
            if isinstance(translated_data, dict):
                return translated_data.get("segments", segments)
            
            return segments
        except Exception as e:
            self.logger.error(f"[GlobalReachAdapter] Script Translation Error: {e}")
            return segments

base_multiplatform_service = GlobalReachAdapter()
