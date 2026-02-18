from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseMonetizationStrategy(ABC):
    @abstractmethod
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
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
