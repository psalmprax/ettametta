import time
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

from src.api.utils.resilience import CircuitBreaker

class BaseMonetizationStrategy(ABC):
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()

    @abstractmethod
    async def get_assets(self, niche: str) -> list[dict[str, Any]]:
        """
        Fetches relevant products, links, or lead magnets for the given niche.
        """
        pass

    @abstractmethod
    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generates a conversion-optimized call to action.
        """
        pass
