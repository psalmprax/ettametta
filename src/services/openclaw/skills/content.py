from src.api.config import settings
import requests
import logging
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class ContentSkill(OpenClawBaseSkill):
    def __init__(self):
        super().__init__()
        self.api_url = f"{settings.API_URL}/video"

    def execute(
        self,
        action: str = "transform",
        source_url: str = "",
        prompt: str = "",
        engine: str = "veo3",
        niche: str = "Motivation",
        platform: str = "YouTube Shorts",
        **kwargs,
    ) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        return self.create_content(
            action=action,
            source_url=source_url or kwargs.get("input_url", ""),
            prompt=prompt,
            engine=engine,
            niche=niche,
            platform=platform,
        )


    def create_content(
        self,
        action: str = "transform",
        source_url: str = "",
        prompt: str = "",
        engine: str = "veo3",
        niche: str = "Motivation",
        platform: str = "YouTube Shorts",
    ) -> str:
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
                    "aspect_ratio": "9:16"
                    if "Shorts" in platform or "TikTok" in platform
                    else "16:9",
                }
                msg_prefix = "🎬 **AI Generation Started!**\nPrompt"
                msg_body = prompt
            elif action == "story":
                endpoint = f"{self.api_url}/generate-story"
                payload = {"prompt": prompt, "engine": engine, "style": "Cinematic"}
                msg_prefix = "📖 **Story Generation Started!**\nPrompt"
                msg_body = prompt
            else:  # default to transform
                endpoint = f"{self.api_url}/transform"
                payload = {
                    "source_url": source_url,
                    "niche": niche,
                    "platform": platform,
                }
                msg_prefix = "🎬 **Production Started!**\nNiche"
                msg_body = niche

            response = requests.post(
                endpoint, json=payload, headers=self._get_headers(), timeout=10
            )

            if response.status_code == 200:
                raw_data = response.json()
                data = (
                    raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data
                )
                task_id = (
                    data.get("task_id", data.get("job_id", "Unknown"))
                    if isinstance(data, dict)
                    else "Unknown"
                )
                return f"{msg_prefix}: {msg_body}\nJob ID: `{task_id}`"
            else:
                return f"⚠️ **Creation Failed**: server returned {response.status_code}"

        except Exception as e:
            logger.error(f"Content Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"


content_skill = ContentSkill()
