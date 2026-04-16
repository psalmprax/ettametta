import requests
import logging
from typing import Dict, Any, List
from services.openclaw.config import settings

logger = logging.getLogger(__name__)

class AffiliateTool:
    """
    Standardized Tool for Agent Zero to manage affiliate links and monetization.
    """
    def __init__(self):
        self.api_url = f"{settings.API_URL}/monetization"

    def recommend_links(self, niche: str, script_text: str) -> Dict[str, Any]:
        """
        Recommends high-converting products/links based on video script.
        """
        try:
            payload = {"niche": niche, "script_text": script_text}
            response = requests.post(f"{self.api_url}/recommend-links", json=payload, timeout=20)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}", "detail": response.text}
                
        except Exception as e:
            logger.error(f"AffiliateTool Recommend Error: {e}")
            return {"error": str(e)}

    def create_link(self, product_name: str, niche: str, link: str, cta_text: str = "Check link in bio") -> Dict[str, Any]:
        """
        Registers a new affiliate link in the database.
        """
        try:
            payload = {
                "product_name": product_name,
                "niche": niche,
                "link": link,
                "cta_text": cta_text
            }
            response = requests.post(f"{self.api_url}/links", json=payload, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}", "detail": response.text}
                
        except Exception as e:
            logger.error(f"AffiliateTool Create Error: {e}")
            return {"error": str(e)}

affiliate_tool = AffiliateTool()
