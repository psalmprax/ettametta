import logging
import requests
from config import settings

logger = logging.getLogger(__name__)

class OutreachSkill:
    def __init__(self):
        # We will interact with the local OpenClaw broadcast endpoint
        self.broadcast_url = f"http://localhost:{settings.PORT}/broadcast"

    def send_outreach_message(self, target_identifier: str, message: str) -> str:
        """
        Commands the core system to dispatch an outbound message.
        """
        try:
            payload = {
                "user_ids": [target_identifier],
                "message": message
            }
            response = requests.post(self.broadcast_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return f"✅ **Outreach Dispatched**:\nMessage sent to `{target_identifier}`."
            else:
                return f"⚠️ **Outreach Failed**: System returned status {response.status_code}."
                
        except Exception as e:
            logger.error(f"Outreach Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

outreach_skill = OutreachSkill()
