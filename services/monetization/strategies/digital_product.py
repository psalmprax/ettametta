import logging
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy

logger = logging.getLogger(__name__)


class DigitalProductStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        """
        Get digital product assets for the given niche.
        In production, this should query a database of digital products or
        integrate with a platform like Gumroad, Shopify, or a custom store.
        """
        logger.warning(f"[DigitalProductStrategy] No digital products configured for niche: {niche}. Configure products in the database.")
        # Return empty list instead of mock data
        return []

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generate a call-to-action for digital products.
        In production, this should use an LLM to generate contextually relevant CTAs.
        """
        logger.warning(f"[DigitalProductStrategy] No CTA template configured for niche: {niche}")
        # Return a generic CTA instead of random mock options
        return f"Check out our {niche} resources - link in bio!"
