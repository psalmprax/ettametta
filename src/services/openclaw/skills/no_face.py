from api.config import settings
import requests
import logging
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class NoFaceSkill(OpenClawBaseSkill):
    def __init__(self):
        super().__init__()
        self.api_url = f"{settings.API_URL}/no-face"

    def execute(
        self, action: str = "script", topic: str = "General advice", **kwargs
    ) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if action == "hook":
            return self.generate_hook(topic)
        return self.generate_script(topic)


    def generate_script(self, topic: str) -> str:
        """
        Triggers text-based script generation for a given topic.
        """
        try:
            payload = {"topic": topic}
            response = requests.post(
                f"{self.api_url}/generate-script",
                json=payload,
                headers=self._get_headers(),
                timeout=20,
            )

            if response.status_code == 200:
                raw_data = response.json()
                data = (
                    raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data
                )
                script = (
                    data.get("script", "No script returned")
                    if isinstance(data, dict)
                    else "No script returned"
                )
                # Telegram has message length limits, so we truncate if necessary
                if len(script) > 3000:
                    script = script[:3000] + "...\n[Script truncated]"
                return f"📝 **Viral Script Generated for '{topic}'**:\n\n{script}"
            else:
                return f"⚠️ **Script Generation Failed**: server returned {response.status_code}"

        except Exception as e:
            logger.error(f"NoFace Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

    def generate_hook(self, topic: str) -> str:
        """
        Generates and validates a viral hook for a topic.
        """
        try:
            payload = {"topic": topic, "hook": topic}
            response = requests.post(
                f"{self.api_url}/validate-hook",
                json=payload,
                headers=self._get_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                raw_data = response.json()
                data = (
                    raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data
                )
                score = data.get("score", 0) if isinstance(data, dict) else 0
                feedback = data.get("feedback", "") if isinstance(data, dict) else ""
                return f"🪝 **Hook Analysis for '{topic}'**:\nExpected Score: {score}/100\nFeedback: {feedback}"
            else:
                return f"⚠️ **Hook Generation Failed**: {response.status_code}"

        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"


noface_skill = NoFaceSkill()
