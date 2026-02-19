import requests
import logging
from config import settings

logger = logging.getLogger(__name__)

class SystemSkill:
    def __init__(self):
        self.api_url = settings.API_URL

    def check_health(self) -> str:
        """
        Checks the health of the platform services.
        """
        try:
            # Check API Health
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                return "✅ **System Status**: All systems operational. API is healthy."
            else:
                return f"⚠️ **System Alert**: API returned status {response.status_code}."
        except Exception as e:
            return f"❌ **Critical Error**: Unable to contact API. {str(e)}"

system_skill = SystemSkill()
