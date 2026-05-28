import requests
import logging
from src.api.config import settings
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class NicheSkill(OpenClawBaseSkill):
    def __init__(self):
        super().__init__()
        self.api_url = f"{settings.API_URL}/api/v1/discovery"

    def execute(self, action: str = "trends", niche: str = "general", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if action == "add":
            return self.add_niche_scan(niche)
        elif action == "trends":
            return self.get_niche_trends(niche)
        elif action == "auto_merch":
            return self.trigger_auto_merch(kwargs.get("niche", niche))

        return f"⚠️ Unknown niche action: {action}"


    def add_niche_scan(self, niche: str) -> str:
        """
        Triggers a deep scan for a new niche.
        """
        try:
            payload = {"niches": [niche]}
            response = requests.post(
                f"{self.api_url}/scan",
                json=payload,
                headers=self._get_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                return (
                    f"🎯 **Niche Added**: '{niche}' is now being scanned by the swarm."
                )
            else:
                return f"⚠️ **Scan Request Failed**: {response.status_code}"

        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

    def get_niche_trends(self, niche: str) -> str:
        """
        Gets specific trends for a niche.
        """
        try:
            response = requests.get(
                f"{self.api_url}/niche-trends/{niche}",
                headers=self._get_headers(),
                timeout=10,
            )
            if response.status_code == 200:
                raw_data = response.json()
                data = (
                    raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data
                )
                keywords = ", ".join(data.get("top_keywords", [])[:5])
                return f"📈 **Trends for {niche}**:\nKeywords: {keywords}\nEngagement Score: {data.get('avg_engagement_score', 0)}"
            else:
                return f"⚠️ **Fetch Failed**: {response.status_code}"
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

    def trigger_auto_merch(self, niche: str) -> str:
        """
        Triggers the Reverse Monetization pipeline for a detected trend.
        Calls /monetization/auto-merch on the backend.
        """
        try:
            # Note: We need the full base URL since monetization is on a different route prefix
            api_url = f"{settings.API_URL}/api/v1"
            payload = {"niche": niche}
            response = requests.post(
                f"{api_url}/monetization/auto-merch",
                json=payload,
                headers=self._get_headers(),
                timeout=20,
            )

            if response.status_code == 200:
                raw_data = response.json()
                data = (
                    raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data
                )
                product = data.get("product", {}) if isinstance(data, dict) else {}
                return f"👕 **Auto-Merch Success!**\nTrend: {niche}\nProduct: {product.get('name')}\nPrice: {product.get('price')}\nStore Link: {product.get('url')}"
            else:
                return (
                    f"⚠️ **Auto-Merch Failed**: server returned {response.status_code}"
                )
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"


niche_skill = NicheSkill()
