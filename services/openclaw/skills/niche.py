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

    def trigger_auto_merch(self, trend_topic: str) -> str:
        """
        Triggers the Reverse Monetization pipeline for a detected trend.
        Calls /monetization/auto-merch on the backend.
        """
        try:
            # Note: We need the full base URL since monetization is on a different route prefix
            api_url = settings.API_URL
            payload = {"trend_topic": trend_topic}
            response = requests.post(f"{api_url}/monetization/auto-merch", json=payload, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                product = data.get("product", {})
                return f"👕 **Auto-Merch Success!**\nTrend: {trend_topic}\nProduct: {product.get('name')}\nPrice: {product.get('price')}\nStore Link: {product.get('url')}"
            else:
                return f"⚠️ **Auto-Merch Failed**: server returned {response.status_code}"
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

niche_skill = NicheSkill()
