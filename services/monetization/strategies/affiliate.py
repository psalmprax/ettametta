import logging
import random
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy
from api.utils.database import SessionLocal
from api.utils.models import AffiliateLinkDB

class AffiliateStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            links = db.query(AffiliateLinkDB).filter(AffiliateLinkDB.niche == niche).all()
            if not links:
                # Return empty list instead of mock data when no affiliate links configured
                logging.warning(f"[AffiliateStrategy] No affiliate links found for niche: {niche}. Configure links in the database.")
                return []
            
            return [{
                "id": str(l.id),
                "name": l.product_name,
                "url": l.link,
                "price": "N/A",
                "source": "affiliate_db"
            } for l in links]
        finally:
            db.close()

    async def generate_cta(self, niche: str, context: str) -> str:
        # Fetch the links so we can grab one
        links = await self.get_assets(niche)
        
        # Pick one at random if multiple exist
        if links:
            chosen_link = random.choice(links)
            product_url = chosen_link.get("url", "")
            product_name = chosen_link.get("name", "gear")
        else:
            product_url = "https://linkin.bio/ettametta"
            product_name = "gear"

        options = [
            f"Check the link in bio for the best {product_name} deal! \n🔗 {product_url}",
            f"Ready to level up your {niche}? Get your {product_name} here: \n🔗 {product_url}",
            f"Limited time offer on {product_name}. See the link below.\n🔗 {product_url}"
        ]
        return random.choice(options)
