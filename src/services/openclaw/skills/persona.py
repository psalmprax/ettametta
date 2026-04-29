import logging
import requests
from typing import Any
from .base_skill import OpenClawBaseSkill
from src.api.config import settings

logger = logging.getLogger(__name__)


class PersonaSkill(OpenClawBaseSkill):
    """
    Persona Skill for OpenClaw agents.
    Manages autonomous character behaviors and interaction styles via API.
    """

    def execute(
        self,
        action: str = "generate",
        persona_id: int = None,
        topic: str = "general chat",
        **kwargs,
    ) -> str:
        """
        Persona Skill for OpenClaw agents.
        Manages autonomous character behaviors and interaction styles via API.
        """
        pid = persona_id or kwargs.get("persona_id")
        if not pid:
            return "⚠️ Persona generation failed: Missing persona_id"

        try:
            payload = {"persona_id": int(pid), "topic": topic}

            # Use API_URL from settings instead of hardcoded localhost
            url = f"{settings.API_URL}/persona/generate"
            response = requests.post(
                url, json=payload, headers=self._get_headers(), timeout=30
            )

            if response.status_code == 200:
                raw_data = response.json()
                data = (
                    raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data
                )
                video_uri = data.get("video_uri", "No URL returned")
                return f"👤 **Persona Animated!**\nVideo generated successfully.\nLink: {video_uri}"
            else:
                return f"⚠️ Persona generation failed. Ensure your Persona is registered in the Dashboard."
        except Exception as e:
            logger.error(f"Persona Skill Error: {e}")
            return f"⚠️ Persona System Error: {str(e)}"


persona_skill = PersonaSkill()
