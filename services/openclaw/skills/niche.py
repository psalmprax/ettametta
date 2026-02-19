import requests
import logging
from config import settings

logger = logging.getLogger(__name__)

class NicheSkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}/discovery"

    def add_niche_scan(self, niche: str) -> str:
        """
        Triggers a deep scan for a new niche.
        """
        try:
            payload = {"niches": [niche]}
            response = requests.post(f"{self.api_url}/scan", json=payload, timeout=10)
            
            if response.status_code == 200:
                return f"🎯 **Niche Added**: '{niche}' is now being scanned by the swarm."
            else:
                return f"⚠️ **Scan Request Failed**: {response.status_code}"
                
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

    def get_niche_trends(self, niche: str) -> str:
        """
        Gets specific trends for a niche.
        """
        try:
            response = requests.get(f"{self.api_url}/niche-trends/{niche}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                keywords = ", ".join(data.get("top_keywords", [])[:5])
                return f"📈 **Trends for {niche}**:\nKeywords: {keywords}\nEngagement: {data.get('avg_engagement', 0)}"
            else:
                return f"⚠️ **Fetch Failed**: {response.status_code}"
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

niche_skill = NicheSkill()
