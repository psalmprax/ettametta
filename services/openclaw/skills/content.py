import requests
import logging
from config import settings
from typing import Optional

logger = logging.getLogger(__name__)

class ContentSkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}/video"

    def create_content(self, input_url: str, niche: str = "Motivation", platform: str = "YouTube Shorts") -> str:
        """
        Triggers a new video transformation job.
        """
        try:
            payload = {
                "input_url": input_url,
                "niche": niche,
                "platform": platform
            }
            
            response = requests.post(f"{self.api_url}/transform", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id")
                return f"🎬 **Production Started!**\nJob ID: `{task_id}`\nNiche: {niche}\nTarget: {platform}"
            else:
                return f"⚠️ **Creation Failed**: server returned {response.status_code}"
                
        except Exception as e:
            logger.error(f"Content Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

content_skill = ContentSkill()
