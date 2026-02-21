import requests
import logging
from config import settings
from typing import Optional

logger = logging.getLogger(__name__)

class NoFaceSkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}/no-face"

    def generate_script(self, topic: str) -> str:
        """
        Triggers text-based script generation for a given topic.
        """
        try:
            payload = {"topic": topic}
            response = requests.post(f"{self.api_url}/generate-script", json=payload, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                script = data.get("script", "No script returned")
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
            payload = {"hook_text": f"Crazy fact about {topic}"} # Simplified payload for validation
            response = requests.post(f"{self.api_url}/validate-hook", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("score", 0)
                feedback = data.get("feedback", "")
                return f"🪝 **Hook Analysis for '{topic}'**:\nExpected Score: {score}/100\nFeedback: {feedback}"
            else:
                return f"⚠️ **Hook Generation Failed**: {response.status_code}"
                
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

noface_skill = NoFaceSkill()
