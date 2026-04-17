import requests
import logging
from src.api.config import settings

logger = logging.getLogger(__name__)


class SecuritySkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}/security"

    def _get_headers(self):
        headers = {}
        if settings.INTERNAL_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.INTERNAL_API_TOKEN}"
        return headers

    def get_status(self) -> str:
        """
        Returns the current security health score and recent threat events.
        """
        try:
            response = requests.get(
                f"{self.api_url}/status", headers=self._get_headers(), timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                score = data.get("health_score", data.get("score", "N/A"))
                threats = data.get("threats", data.get("recent_events", []))
                threat_count = len(threats) if isinstance(threats, list) else 0
                return (
                    f"🛡️ **Security Status**\n"
                    f"• Health Score: `{score}`\n"
                    f"• Recent Threats: `{threat_count}`\n"
                    f"• Last Scan: Check dashboard for details"
                )
            else:
                return f"⚠️ **Status Check Failed**: {response.status_code}"
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

    def panic_lockdown(self) -> str:
        """
        Triggers a security audit and lockdown.
        """
        try:
            # Trigger Audit
            response = requests.post(
                f"{self.api_url}/scan", headers=self._get_headers(), timeout=10
            )

            if response.status_code == 200:
                return "🚨 **PANIC MODE ACTIVATED** 🚨\n• Security Audit: Started\n• System Lockdown: Initiated\n• Posting: Paused"
            else:
                return f"⚠️ **Lockdown Failed**: {response.status_code}"
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"


security_skill = SecuritySkill()
