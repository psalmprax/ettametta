import logging
import json
from typing import List, Dict, Any, Optional
from groq import AsyncGroq
from api.config import settings
from services.voiceover.service import base_voiceover_service

class GlobalReachAdapter:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def translate_metadata(self, title: str, description: str, tags: List[str], target_lang: str) -> Dict[str, Any]:
        """
        Translates video metadata using Groq/LLM.
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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a native {target_lang} viral marketing expert. Output JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logging.error(f"[GlobalReachAdapter] Translation Error: {e}")
            return {
                "title": title,
                "description": description,
                "tags": tags,
                "error": str(e)
            }

    async def translate_script_segments(self, segments: List[Dict[str, Any]], target_lang: str) -> List[Dict[str, Any]]:
        """
        Translates a list of script segments for dubbing/subtitles.
        """
        prompt = f"""
        Translate these video script segments into {target_lang}.
        Keep the timing and tone consistent with the original.
        
        SEGMENTS:
        {json.dumps(segments, indent=2)}
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "segments": [ ... translated segments ... ]
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a native {target_lang} scriptwriter. Output JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            translated_data = json.loads(content)
            return translated_data.get("segments", segments)
        except Exception as e:
            logging.error(f"[GlobalReachAdapter] Script Translation Error: {e}")
            return segments

base_global_adapter = GlobalReachAdapter()
