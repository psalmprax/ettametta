import logging
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy

logger = logging.getLogger(__name__)


class LeadGenStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        """
        Get lead magnet assets for the given niche.
        In production, this should query a database of lead magnets or 
        integrate with an email marketing platform (e.g., Mailchimp, ConvertKit).
        """
        logger.warning(f"[LeadGenStrategy] No lead magnets configured for niche: {niche}. Configure lead magnets in the database.")
        # Return empty list instead of mock data
        return []

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generate a call-to-action for lead capture.
        In production, this should use an LLM to generate contextually relevant CTAs.
        """
        logger.warning(f"[LeadGenStrategy] No CTA template configured for niche: {niche}")
        # Return a generic CTA instead of random mock options
        return f"Get started with {niche} - link in bio!"
