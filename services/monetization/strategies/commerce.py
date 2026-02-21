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
        products = await self.get_assets(niche)
        
        if products:
            chosen = random.choice(products)
            product_url = chosen.get("url", "https://linkin.bio/ettametta")
            product_name = chosen.get("name", f"{niche} gear")
        else:
            product_url = "https://linkin.bio/ettametta"
            product_name = f"{niche} gear"
            
        options = [
            f"Grab this {product_name} essential before it's gone! \n🛒 Shop here: {product_url}",
            f"Boost your {niche} game today. Get your {product_name} below. \n🛒 {product_url}",
            f"Official {niche} merch just dropped: {product_name}. \n🛒 Get yours: {product_url}"
        ]
        return random.choice(options)
