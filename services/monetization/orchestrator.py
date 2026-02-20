import logging
from typing import List, Dict, Any, Optional
from api.utils.database import SessionLocal
from api.utils.models import SystemSettings
from .strategies.commerce import CommerceStrategy
from .strategies.affiliate import AffiliateStrategy
from .strategies.lead_gen import LeadGenStrategy
from .strategies.digital_product import DigitalProductStrategy

class MonetizationOrchestrator:
    def __init__(self):
        self.strategies = {
            "commerce": CommerceStrategy(),
            "affiliate": AffiliateStrategy(),
            "lead_gen": LeadGenStrategy(),
            "digital_product": DigitalProductStrategy()
        }
        self.logger = logging.getLogger("MonetizationOrchestrator")

    async def get_active_strategy(self) -> Any:
        db = SessionLocal()
        try:
            setting = db.query(SystemSettings).filter(SystemSettings.key == "active_monetization_strategy").first()
            strategy_key = setting.value if setting else "commerce"
            
            if strategy_key not in self.strategies:
                self.logger.warning(f"Unknown strategy key: {strategy_key}. Falling back to commerce.")
                return self.strategies["commerce"]
            
            return self.strategies[strategy_key]
        finally:
            db.close()

    async def should_monetize(self, viral_score: int = 0) -> bool:
        db = SessionLocal()
        try:
            setting = db.query(SystemSettings).filter(SystemSettings.key == "monetization_mode").first()
            mode = setting.value if setting else "selective"
            
            if mode == "all":
                return True
            
            # Selective mode: Only monetize high-potential content
            return viral_score >= 85
        finally:
            db.close()

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
