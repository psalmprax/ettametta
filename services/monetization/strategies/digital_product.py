import logging
import random
from typing import List, Dict, Any
from sqlalchemy import or_
from .base import BaseMonetizationStrategy
from api.utils.database import SessionLocal
from api.utils.models import AffiliateLinkDB

logger = logging.getLogger(__name__)

DIGITAL_PRODUCT_KEYWORDS = ["course", "ebook", "template", "guide", "pdf", "download"]


class DigitalProductStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        """
        Get digital product assets for the given niche.
        Queries AffiliateLinkDB for links matching the niche OR whose
        product_name contains common digital-product keywords.
        """
        db = SessionLocal()
        try:
            keyword_filters = [
                AffiliateLinkDB.product_name.ilike(f"%{kw}%")
                for kw in DIGITAL_PRODUCT_KEYWORDS
            ]

            links = (
                db.query(AffiliateLinkDB)
                .filter(
                    AffiliateLinkDB.niche == niche,
                    or_(*keyword_filters),
                )
                .all()
            )

            if not links:
                logger.warning(
                    f"[DigitalProductStrategy] No digital products found for niche: {niche}. "
                    "Add products with names containing 'course', 'ebook', 'template', 'guide', 'pdf', or 'download'."
                )
                return []

            return [
                {
                    "id": str(l.id),
                    "name": l.product_name,
                    "url": l.link,
                    "cta_text": l.cta_text or "",
                    "source": "digital_product_db",
                }
                for l in links
            ]
        finally:
            db.close()

    async def generate_cta(self, niche: str, context: str) -> str:
        """Generate a call-to-action for digital products found in the database."""
        assets = await self.get_assets(niche)

        if not assets:
            return (
                f"No digital products configured for '{niche}' yet. "
                "Add products to the database (e.g. courses, ebooks, templates) "
                "to enable digital product monetization."
            )

        chosen = random.choice(assets)
        product_name = chosen.get("name", "digital resource")
        product_url = chosen.get("url", "")
        custom_cta = chosen.get("cta_text", "")

        if custom_cta:
            return f"{custom_cta}\n🔗 {product_url}"

        options = [
            f"Want to go deeper with {niche}? Grab my {product_name} here:\n🔗 {product_url}",
            f"Level up your {niche} skills with this {product_name}:\n🔗 {product_url}",
            f"My {product_name} is now available! Start mastering {niche} today:\n🔗 {product_url}",
            f"Don't just watch — take action. Get the {product_name}:\n🔗 {product_url}",
        ]
        return random.choice(options)
