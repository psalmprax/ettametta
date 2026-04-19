import logging
import random
from typing import Any
from .base import BaseMonetizationStrategy
from api.utils.models import SystemSettings

class SponsorshipStrategy(BaseMonetizationStrategy):
    """
    Sponsorship strategy - Brand deals and sponsored content
    """
    
    async def get_assets(self, niche: str) -> list[dict[str, Any]]:
        """
        Fetches brand partners from database configuration.
        """
        from sqlalchemy import select
        from api.utils.database import async_session_factory
        
        async with async_session_factory() as db:
            stmt = select(SystemSettings).filter(SystemSettings.key == "brand_partners")
            result = await db.execute(stmt)
            setting = result.scalar_one_or_none()
            
            brand_partners_str = setting.value if setting else ""
            brand_partners = [b.strip() for b in brand_partners_str.split(",") if b.strip()]
            
            # Get contact email
            stmt_email = select(SystemSettings).filter(SystemSettings.key == "contact_email")
            result_email = await db.execute(stmt_email)
            setting_email = result_email.scalar_one_or_none()
            contact_email = setting_email.value if setting_email else "support@ettametta.ai"

            if not brand_partners:
                logging.warning(f"[SponsorshipStrategy] No brand partners configured. Set 'brand_partners' in settings.")
                return []
            
            # Return brand partnerships as assets
            assets = []
            for i, brand in enumerate(brand_partners[:5], 1):  # Limit to 5 brands
                assets.append({
                    "id": f"sponsor_{i}",
                    "name": brand.strip(),
                    "url": "", # Hardened: Do not generate fake URLs based on name.
                    "contact": contact_email,
                    "type": "sponsorship",
                    "source": "sponsorship"
                })
            
            return assets

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generates a call to action for sponsorships.
        """
        assets = await self.get_assets(niche)
        
        if assets:
            brand_name = assets[0].get("name", "our sponsors")
        else:
            brand_name = "amazing brands"
        
        options = [
            f"Huge thanks to {brand_name} for sponsoring this video! Check them out!",
            f"Proud to partner with {brand_name} - they make this content possible!",
            f"Shoutout to {brand_name} for supporting the channel!",
            f"{brand_name} - thanks for making this content happen!"
        ]
        return random.choice(options)
