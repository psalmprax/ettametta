import logging
import random
from typing import List, Dict, Any
from sqlalchemy import select
from .base import BaseMonetizationStrategy
from api.utils.database import async_session_factory
from api.utils.models import DigitalProductDB

logger = logging.getLogger(__name__)

class DigitalProductStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        """
        Get digital product assets for the given niche from DigitalProductDB.
        """
        async with async_session_factory() as db:
            try:
                stmt = select(DigitalProductDB).where(DigitalProductDB.niche == niche)
                result = await db.execute(stmt)
                products = result.scalars().all()
                
                return [{
                    "id": str(product.id),
                    "name": product.name,
                    "url": product.purchase_url,
                    "price": str(product.price),
                    "source": "digital_product"
                } for product in products]
            except Exception as e:
                logger.error(f"[DigitalProductStrategy] Error fetching assets: {e}")
                return []

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
