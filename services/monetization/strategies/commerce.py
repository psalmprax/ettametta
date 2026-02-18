import random
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy
from ..commerce_service import base_commerce_service

class CommerceStrategy(BaseMonetizationStrategy):
    def __init__(self):
        self.commerce = base_commerce_service

    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        products = await self.commerce.get_relevant_products(niche)
        if not products:
            # Fallback mock if nothing in Shopify
            return [{
                "id": f"shop_{random.randint(100, 999)}",
                "name": f"Trending {niche} Product",
                "url": "#",
                "price": "$19.99",
                "source": "shopify_fallback"
            }]
        return products

    async def generate_cta(self, niche: str, context: str) -> str:
        options = [
            f"Grab this {niche} essential before it's gone! Link in bio.",
            f"Boost your {niche} game today. Shop the link below.",
            f"Official {niche} merch just dropped. Get yours at the link in bio."
        ]
        return random.choice(options)
