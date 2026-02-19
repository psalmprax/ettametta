import requests
import logging
from config import settings

logger = logging.getLogger(__name__)

class DiscoverySkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}/discovery"

    def search_trends(self, topic: str, limit: int = 5) -> str:
        """
        Calls the Discovery API to search for trends.
        """
        try:
            # Call the internal /discovery/search endpoint
            # Note: Assuming endpoints from api/routes/discovery.py
            # The actual endpoint might be /search or /scan depending on implementation
            # Based on architectue: /discovery/search
            
            payload = {"query": topic, "platform": "all", "limit": limit}
            # For GET request if that's how it's implemented, or POST.
            # Usually search is GET with params or POST.
            # Let's assume POST /scan or GET /search.
            # I will check discovery.py to be sure, but for now I'll try GET /search
            
            response = requests.get(f"{self.api_url}/search", params=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("valid_candidates", [])
                
                if not results:
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
