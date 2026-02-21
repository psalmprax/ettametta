import requests
import logging
from config import settings
from typing import Optional

logger = logging.getLogger(__name__)

class ContentSkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}/video"

    def create_content(self, action: str = "transform", input_url: str = "", prompt: str = "", engine: str = "veo3", niche: str = "Motivation", platform: str = "YouTube Shorts") -> str:
        """
        Triggers a new video transformation or generation job based on the action.
        """
        try:
            if action == "generate":
                endpoint = f"{self.api_url}/generate"
                payload = {
                    "prompt": prompt,
                    "engine": engine,
                    "style": "Cinematic",
                    "aspect_ratio": "9:16" if "Shorts" in platform or "TikTok" in platform else "16:9"
                }
                msg_prefix = "🎬 **AI Generation Started!**\nPrompt"
                msg_body = prompt
            elif action == "story":
                endpoint = f"{self.api_url}/generate-story"
                payload = {
                    "prompt": prompt,
                    "engine": engine,
                    "style": "Cinematic"
                }
                msg_prefix = "📖 **Story Generation Started!**\nPrompt"
                msg_body = prompt
            else: # default to transform
                endpoint = f"{self.api_url}/transform"
                payload = {
                    "input_url": input_url,
                    "niche": niche,
                    "platform": platform
                }
                msg_prefix = "🎬 **Production Started!**\nNiche"
                msg_body = niche
            
            response = requests.post(endpoint, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id", data.get("job_id", "Unknown"))
                return f"{msg_prefix}: {msg_body}\nJob ID: `{task_id}`"
            else:
                return f"⚠️ **Creation Failed**: server returned {response.status_code}"
                
        except Exception as e:
            logger.error(f"Content Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

content_skill = ContentSkill()
