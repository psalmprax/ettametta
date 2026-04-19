import logging
from typing import Any
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

    async def _execute_with_failover(self, method_name: str, *args, **kwargs) -> Any:
        """
        Executes a strategy method with automatic failover if the primary strategy fails or its circuit is open.
        """
        primary = await self.get_active_strategy()
        
        # Try primary first if circuit is CLOSED/HALF_OPEN
        if not primary.circuit_breaker.is_open():
            try:
                method = getattr(primary, method_name)
                result = await method(*args, **kwargs)
                if result: # Consider empty result as candidate for failover in some cases
                    primary.circuit_breaker.record_success()
                    return result
            except Exception as e:
                self.logger.error(f"[Monetization] Primary strategy failed: {e}")
                primary.circuit_breaker.record_failure()
        
        # Failover Loop: Try all other strategies
        self.logger.warning("[Monetization] Primary strategy unusable. Primary failover initiated...")
        for name, strategy in self.strategies.items():
            if strategy == primary:
                continue
            
            if not strategy.circuit_breaker.is_open():
                try:
                    self.logger.info(f"[Monetization] Trying failover strategy: {name}")
                    method = getattr(strategy, method_name)
                    result = await method(*args, **kwargs)
                    if result:
                        strategy.circuit_breaker.record_success()
                        return result
                except Exception as e:
                    self.logger.error(f"[Monetization] Failover strategy {name} failed: {e}")
                    strategy.circuit_breaker.record_failure()
        
        return "" if method_name == "generate_cta" else []

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

    async def get_monetization_assets(self, niche: str, viral_score: int = 0) -> list[dict[str, Any]]:
        if not await self.should_monetize(viral_score):
            return []
        return await self._execute_with_failover("get_assets", niche)

    async def get_monetization_cta(self, niche: str, context: str, viral_score: int = 0) -> str:
        if not await self.should_monetize(viral_score):
            return ""
        return await self._execute_with_failover("generate_cta", niche, context)

base_monetization_orchestrator = MonetizationOrchestrator()
