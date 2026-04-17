import logging
import random
from typing import Any
from sqlalchemy import select
from .base import BaseMonetizationStrategy
from src.api.utils.database import async_session_factory
from src.api.utils.models import AffiliateLinkDB

class AffiliateStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche: str) -> list[dict[str, Any]]:
        async with async_session_factory() as db:
            stmt = select(AffiliateLinkDB).where(AffiliateLinkDB.niche == niche)
            result = await db.execute(stmt)
            links = result.scalars().all()
            
            if not links:
                # Return empty list instead of mock data when no affiliate links configured
                logging.warning(f"[AffiliateStrategy] No affiliate links found for niche: {niche}. Configure links in the database.")
                return []
            
            return [{
                "id": str(link.id),
                "name": link.product_name,
                "url": link.link,
                "price": "N/A",
                "source": "affiliate"
            } for link in links]

    async def generate_cta(self, niche: str, context: str) -> str:
        # Fetch the links so we can grab one
        links = await self.get_assets(niche)
        
        # Pick one at random if multiple exist
        if not links:
            logging.warning(f"[AffiliateStrategy] No affiliate links found for niche: {niche}. Configure links in the database.")
            return ""
        
        chosen_link = random.choice(links)
        product_url = chosen_link.get("url", "")
        product_name = chosen_link.get("name", "gear")

        options = [
            f"Check the link in bio for the best {product_name} deal! \n🔗 {product_url}",
            f"Ready to level up your {niche}? Get your {product_name} here: \n🔗 {product_url}",
            f"Limited time offer on {product_name}. See the link below.\n🔗 {product_url}"
        ]
        return random.choice(options)
