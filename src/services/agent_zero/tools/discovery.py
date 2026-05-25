import requests
import logging
from typing import Any
from src.services.openclaw.config import settings

logger = logging.getLogger(__name__)

class DiscoveryTool:
    """
    Standardized Tool for Agent Zero to access the ettametta Discovery Engine.
    """
    def __init__(self):
        self.api_url = f"{settings.API_URL}/discovery"

    def run(self, niche: str, limit: int = 5) -> dict[str, Any]:
        """
        Searches for trending niches across multi-platform scanners.
        """
        try:
            payload = {"query": niche, "platform": "all", "limit": limit}
            response = requests.get(f"{self.api_url}/search", params=payload, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}", "detail": response.text}
                
        except Exception as e:
            logger.exception(f"DiscoveryTool Error: {e}")
            return {"error": str(e)}

discovery_tool = DiscoveryTool()
