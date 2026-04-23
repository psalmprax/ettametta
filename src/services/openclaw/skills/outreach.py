import logging
import requests
from src.api.config import settings
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class OutreachSkill(OpenClawBaseSkill):
    def __init__(self):
        super().__init__()
        # We will interact with the local OpenClaw broadcast endpoint
        # OpenClaw service runs on port 3001 by default
        openclaw_port = getattr(settings, "OPENCLAW_PORT", 3001)
        self.broadcast_url = f"http://localhost:{openclaw_port}/broadcast"

    def execute(
        self,
        action: str = "send",
        target_identifier: str = "",
        message: str = "",
        channel: str = "email",
        **kwargs,
    ) -> str:
        """
        Standardized mission execution.
        Routes to the correct adapter based on the channel.
        """
        target = target_identifier or kwargs.get("target_identifier")
        msg = message or kwargs.get("message")
        chnl = (channel or kwargs.get("channel") or "email").lower()

        if not target or not msg:
            return "⚠️ Outreach failed: Missing target_identifier or message"

        if chnl == "whatsapp":
            return self.send_whatsapp_message(target, msg)
        elif chnl in ["social", "instagram", "twitter", "x"]:
            return self.send_social_dm(target, msg, platform=chnl)
        return self.send_outreach_message(target, msg)

    def send_outreach_message(self, target_identifier: str, message: str) -> str:
        """
        Commands the core system to dispatch an outbound email/broadcast message.
        """
        try:
            payload = {
                "user_ids": [target_identifier],
                "message": message,
                "channel": "email",
            }
            response = requests.post(
                self.broadcast_url,
                json=payload,
                headers=self._get_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                return f"✅ **Outreach Dispatched**:\nEmail message sent to `{target_identifier}`."
            else:
                return f"⚠️ **Outreach Failed**: System returned status {response.status_code}."

        except Exception as e:
            self.logger.error(f"Outreach Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

    def send_whatsapp_message(self, target_identifier: str, message: str) -> str:
        """
        Commands the core system to dispatch a WhatsApp message.
        """
        try:
            payload = {
                "user_ids": [target_identifier],
                "message": message,
                "channel": "whatsapp",
            }
            response = requests.post(
                self.broadcast_url,
                json=payload,
                headers=self._get_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                return f"✅ **WhatsApp Dispatched**:\nMessage sent to `{target_identifier}`."
            else:
                return f"⚠️ **WhatsApp Failed**: System returned status {response.status_code}."
        except Exception as e:
            self.logger.error(f"WhatsApp Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

    def send_social_dm(
        self, target_identifier: str, message: str, platform: str
    ) -> str:
        """
        Commands the core system to dispatch a Social DM.
        """
        try:
            payload = {
                "user_ids": [target_identifier],
                "message": message,
                "channel": platform,
            }
            response = requests.post(
                self.broadcast_url,
                json=payload,
                headers=self._get_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                return f"✅ **Social DM Dispatched**:\n{platform.title()} message sent to `{target_identifier}`."
            else:
                return f"⚠️ **Social DM Failed**: System returned status {response.status_code}."
        except Exception as e:
            self.logger.error(f"Social DM Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"


outreach_skill = OutreachSkill()
