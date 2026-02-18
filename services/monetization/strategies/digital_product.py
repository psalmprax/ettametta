import random
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy

class DigitalProductStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        # Mocking high-margin digital products
        return [{
            "id": f"digi_{random.randint(100, 999)}",
            "name": f"{niche} Neural Accelerator (Course)",
            "url": "https://viralforge.ai/products/neural-accelerator",
            "price": "$197",
            "source": "viral_vault"
        }]

    async def generate_cta(self, niche: str, context: str) -> str:
        options = [
            f"Join the elite 1% of {niche} creators. Access the vault.",
            f"Master {niche} with our Neural Accelerator. Link in bio.",
            f"Why struggle with {niche}? Get the full system below."
        ]
        return random.choice(options)
