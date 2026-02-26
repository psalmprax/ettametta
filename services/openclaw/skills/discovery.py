import requests
import logging
from config import settings

logger = logging.getLogger(__name__)

class DiscoverySkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}/discovery"

    def _get_headers(self):
        headers = {}
        if settings.INTERNAL_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.INTERNAL_API_TOKEN}"
        return headers

    def search_trends(self, topic: str, limit: int = 5) -> str:
        """
        Calls the Discovery API to search for trends.
        """
        try:
            payload = {"q": topic, "platform": "all", "limit": limit}
            response = requests.get(f"{self.api_url}/search", params=payload, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                
                if not isinstance(results, list) or not results:
                    return f"No trends found for '{topic}'."
                
                summary = f"🔎 **Discovery Results for '{topic}':**\n"
                for i, item in enumerate(results[:limit], 1):
                    title = item.get("title", "No Title")
                    score = item.get("score", 0)
                    url = item.get("url", "#")
                    summary += f"{i}. [{title}]({url}) (Score: {score})\n"
                return summary
            else:
                return f"⚠️ API Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            logger.error(f"Discovery Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

discovery_skill = DiscoverySkill()
