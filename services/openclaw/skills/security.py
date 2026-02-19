import requests
import logging
from config import settings

logger = logging.getLogger(__name__)

class SecuritySkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}/security"

    def panic_lockdown(self) -> str:
        """
        Triggers a security audit and lockdown.
        """
        try:
            # Trigger Audit
            response = requests.post(f"{self.api_url}/scan", timeout=10)
            
            if response.status_code == 200:
                return "🚨 **PANIC MODE ACTIVATED** 🚨\n• Security Audit: Started\n• System Lockdown: Initiated\n• Posting: Paused"
            else:
                return f"⚠️ **Lockdown Failed**: {response.status_code}"
                
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

security_skill = SecuritySkill()
