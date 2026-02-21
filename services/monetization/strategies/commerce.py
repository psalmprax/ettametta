import logging
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy
from ..commerce_service import base_commerce_service

logger = logging.getLogger(__name__)


class CommerceStrategy(BaseMonetizationStrategy):
    def __init__(self):
        self.commerce = base_commerce_service

    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        """
        Get commerce/affiliate products for the given niche.
        In production, this should query Shopify or affiliate networks.
        """
        products = await self.commerce.get_relevant_products(niche)
        if not products:
            logger.warning(f"[CommerceStrategy] No products found for niche: {niche}. Configure Shopify credentials or affiliate links.")
            return []
        return products

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generate a call-to-action for commerce products.
        In production, this should use an LLM to generate contextually relevant CTAs
        based on actual product data.
        """
        products = await self.get_assets(niche)
        
        if products:
            chosen = products[0]  # Use first product
            product_url = chosen.get("url", "")
            product_name = chosen.get("name", f"{niche} product")
        else:
            product_url = ""
            product_name = f"{niche} product"
        
        if product_url:
            return f"Shop {product_name}: {product_url}"
        return f"Check out {niche} products - link in bio!"
