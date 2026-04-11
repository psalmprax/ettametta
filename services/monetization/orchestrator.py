import logging
from typing import List, Dict, Any, Optional
from api.utils.database import async_session_factory
from sqlalchemy import select
from api.utils.models import SystemSettings
from .strategies.commerce import CommerceStrategy
from .strategies.affiliate import AffiliateStrategy
from .strategies.lead_gen import LeadGenStrategy
from .strategies.digital_product import DigitalProductStrategy
from .strategies.membership import MembershipStrategy
from .strategies.course import CourseStrategy
from .strategies.sponsorship import SponsorshipStrategy
from .strategies.crypto import CryptoStrategy

class MonetizationOrchestrator:
    def __init__(self):
        self.strategies = {
            "commerce": CommerceStrategy(),
            "affiliate": AffiliateStrategy(),
            "lead_gen": LeadGenStrategy(),
            "digital_product": DigitalProductStrategy(),
            "membership": MembershipStrategy(),
            "course": CourseStrategy(),
            "sponsorship": SponsorshipStrategy(),
            "crypto": CryptoStrategy()
        }
        self.logger = logging.getLogger("MonetizationOrchestrator")

    async def get_active_strategy(self) -> Any:
        async with async_session_factory() as db:
            stmt = select(SystemSettings).where(SystemSettings.key == "active_monetization_strategy")
            result = await db.execute(stmt)
            setting = result.scalar_one_or_none()
            strategy_key = setting.value if setting else "commerce"
            
            if strategy_key not in self.strategies:
                self.logger.warning(f"Unknown strategy key: {strategy_key}. Falling back to commerce.")
                return self.strategies["commerce"]
            
            return self.strategies[strategy_key]

    async def should_monetize(self, viral_score: int = 0) -> bool:
        async with async_session_factory() as db:
            stmt = select(SystemSettings).where(SystemSettings.key == "monetization_mode")
            result = await db.execute(stmt)
            setting = result.scalar_one_or_none()
            mode = setting.value if setting else "selective"
            
            if mode == "all":
                return True
            
            # Selective mode: Only monetize high-potential content
            return viral_score >= 85

    async def get_monetization_assets(self, niche: str, viral_score: int = 0) -> List[Dict[str, Any]]:
        if not await self.should_monetize(viral_score):
            return []
        strategy = await self.get_active_strategy()
        return await strategy.get_assets(niche)

    async def get_monetization_cta(self, niche: str, context: str, viral_score: int = 0) -> str:
        if not await self.should_monetize(viral_score):
            return ""
        strategy = await self.get_active_strategy()
        return await strategy.generate_cta(niche, context)

base_monetization_orchestrator = MonetizationOrchestrator()
