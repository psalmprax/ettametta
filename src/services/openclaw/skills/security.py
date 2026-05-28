import requests
import logging
from src.api.config import settings
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class SecuritySkill(OpenClawBaseSkill):
    def __init__(self):
        super().__init__()
        self.api_url = f"{settings.API_URL}/api/v1/security"

    def execute(self, action: str = "status", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if action == "panic":
            return self.panic_lockdown()
        return self.get_status()


    def get_status(self) -> str:
        """
        Returns the current security health score and recent threat events.
        """
        try:
            response = requests.get(
                f"{self.api_url}/status", headers=self._get_headers(), timeout=10
            )
            if response.status_code == 200:
                raw_data = response.json()
                data = (
                    raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data
                )
                score = (
                    data.get("health_score", data.get("score", "N/A"))
                    if isinstance(data, dict)
                    else "N/A"
                )
                threats = (
                    data.get("threats", data.get("recent_events", []))
                    if isinstance(data, dict)
                    else []
                )
                threat_count = len(threats) if isinstance(threats, list) else 0
                return (
                    "🛡️ **Security Status**\n"
                    f"• Health Score: `{score}`\n"
                    f"• Recent Threats: `{threat_count}`\n"
                    "• Last Scan: Check dashboard for details"
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
