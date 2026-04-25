import logging
import random
from typing import Any
from sqlalchemy import select
from .base import BaseMonetizationStrategy
from src.api.utils.database import async_session_factory
from src.api.utils.models import MembershipPlanDB, SystemSettings

logger = logging.getLogger(__name__)

class MembershipStrategy(BaseMonetizationStrategy):
    """
    Patreon/Membership strategy - Recurring revenue through supporter tiers
    """
    
    async def get_assets(self, niche: str) -> list[dict[str, Any]]:
        """
        Fetches membership tiers from database configuration.
        Returns available membership programs for the given niche.
        """
        async with async_session_factory() as db:
            try:
                # First try to get specific plans for the niche
                stmt = select(MembershipPlanDB).where(MembershipPlanDB.niche == niche)
                result = await db.execute(stmt)
                plans = result.scalars().all()
                
                if plans:
                    return [{
                        "id": str(plan.id),
                        "name": plan.name,
                        "url": plan.sign_up_url,
                        "cta_text": plan.cta_text or "Join Now",
                        "price": str(plan.monthly_price),
                        "source": "membership"
                    } for plan in plans]

                # Fallback to general platform URL setting
                setting_stmt = select(SystemSettings).where(
                    SystemSettings.key == "membership_platform_url"
                )
                setting_result = await db.execute(setting_stmt)
                setting = setting_result.scalar_one_or_none()
                platform_url = setting.value if setting else None
                
                if not platform_url:
                    logger.warning(f"[MembershipStrategy] No membership platform configured.")
                    return []
                
                return [
                    {
                        "id": "gen_tier_1",
                        "name": "General Supporter",
                        "url": platform_url,
                        "price": "$5",
                        "source": "membership"
                    }
                ]
            except Exception as e:
                logger.error(f"[MembershipStrategy] Error: {e}")
                return []

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generates a call to action for membership/support.
        """
        assets = await self.get_assets(niche)
        
        if not assets:
            return ""
        
        platform_url = assets[0].get("url", "")
        
        options = [
            f"Support my work! Join the inner circle: \n🔗 {platform_url}",
            f"Want exclusive content and early access? Become a supporter: \n🔗 {platform_url}",
            f"Help me keep creating! Join my membership program: \n🔗 {platform_url}",
            f"Support the channel! Get perks and exclusive content: \n🔗 {platform_url}"
        ]
        return random.choice(options)
