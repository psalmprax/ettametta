import requests
import logging
from api.config import settings
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class SystemSkill(OpenClawBaseSkill):
    def __init__(self):
        super().__init__()
        self.api_url = settings.API_URL

    def execute(self, action: str = "health", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if action == "storage":
            return self.get_storage_status()
        return self.check_health()

    def check_health(self) -> str:
        """
        Checks the health of the platform services.
        """
        try:
            # Check API Health
            response = requests.get(
                f"{self.api_url}/health", headers=self._get_headers(), timeout=5
            )
            if response.status_code == 200:
                return "✅ **System Status**: All systems operational. API is healthy."
            else:
                return (
                    f"⚠️ **System Alert**: API returned status {response.status_code}."
                )
        except Exception as e:
            return f"❌ **Critical Error**: Unable to contact API. {str(e)}"

    def get_storage_status(self) -> str:
        """
        Retrieves video storage usage metrics.
        """
        try:
            response = requests.get(
                f"{self.api_url}/analytics/stats/storage",
                headers=self._get_headers(),
                timeout=5,
            )
            if response.status_code == 200:
                raw_data = response.json()
                data = (
                    raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data
                )
                size = data.get("current_size_gb", 0) if isinstance(data, dict) else 0
                threshold = (
                    data.get("threshold_gb", 140) if isinstance(data, dict) else 140
                )
                usage = data.get("usage_percent", 0) if isinstance(data, dict) else 0
                status = (
                    data.get("status", "Unknown")
                    if isinstance(data, dict)
                    else "Unknown"
                )
                provider = (
                    data.get("provider", "LOCAL") if isinstance(data, dict) else "LOCAL"
                )

                status_emoji = (
                    "✅"
                    if status == "Healthy"
                    else "⚠️"
                    if status == "Warning"
                    else "🚨"
                )

                msg = f"{status_emoji} **Storage Status**: {status}\n\n"
                msg += f"📦 **Total Usage**: {size} GB / {threshold} GB ({usage}%)\n"
                msg += f"☁️ **Provider**: {provider}\n"

                if usage > 90:
                    msg += "\n🛑 **ALERT**: Local storage is nearly full. Archival migration will trigger soon."

                return msg
            else:
                return (
                    f"⚠️ **Storage Alert**: API returned status {response.status_code}."
                )
        except Exception as e:
            return f"❌ **Error fetching storage stats**: {str(e)}"


system_skill = SystemSkill()
