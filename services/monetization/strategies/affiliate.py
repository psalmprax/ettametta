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
                # Mock high-converting affiliate links if None found
                return [{
                    "id": f"aff_{random.randint(100, 999)}",
                    "name": f"Top {niche} Tool (Affiliate)",
                    "url": "https://amzn.to/mock-affiliate-link",
                    "price": "$29.99",
                    "source": "Amazon/ClickBank"
                }]
            
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
