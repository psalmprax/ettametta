import logging
import json
from typing import List, Dict, Any, Optional
from groq import AsyncGroq
from api.config import settings

from .orchestrator import base_monetization_orchestrator

class MonetizationEngine:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.orchestrator = base_monetization_orchestrator
        self.model = "llama-3.3-70b-versatile"

    async def recommend_products(self, niche: str, script_text: str) -> List[Dict[str, Any]]:
        """
        Delegates product recommendation to the active strategy.
        """
        return await self.orchestrator.get_monetization_assets(niche)

    async def match_viral_to_product(self, niche: str, viral_title: str) -> Optional[Dict[str, Any]]:
        """
        Matches a specific viral trend to the most relevant asset from the active strategy.
        """
        assets = await self.orchestrator.get_monetization_assets(niche)
        if not assets:
            return None
            
        asset_list_str = "\n".join([f"- {p['name']} (ID: {p['id']})" for p in assets])
        
        prompt = f"""
        Given the viral video title: "{viral_title}" 
        Select the MOST RELEVANT monetization asset from the list below.
        
        ASSETS:
        {asset_list_str}
        
        Output ONLY the asset ID in JSON format: {{"asset_id": "ID"}}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            aid = data.get("asset_id")
            return next((p for p in assets if p['id'] == aid), assets[0])
        except Exception as e:
            logging.error(f"[Monetization] Asset Matching Error: {e}")
            return assets[0]

    def calculate_epm(self, revenue: float, views: int) -> float:
        if views == 0:
            return 0.0
        return (revenue / views) * 1000

base_monetization_engine = MonetizationEngine()
