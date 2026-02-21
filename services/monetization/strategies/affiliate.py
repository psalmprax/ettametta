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
        options = [
            f"Check the link in bio for the best {niche} deal!",
            f"Ready to level up your {niche}? Link in bio.",
            f"Limited time offer on {niche} gear. See the link below."
        ]
        return random.choice(options)
