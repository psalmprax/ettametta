import random
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy

class LeadGenStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        # Mocking lead magnets for the niche
        return [{
            "id": f"lead_{random.randint(100, 999)}",
            "name": f"FREE {niche} Growth Blueprint (PDF)",
            "url": "https://ettametta.ai/magnets/growth-blueprint",
            "price": "FREE",
            "source": "lead_gen_hub"
        }]

    async def generate_cta(self, niche: str, context: str) -> str:
        options = [
            f"Get my FREE {niche} secrets at the link in bio!",
            f"Stop failing at {niche}. Download my free guide below.",
            f"The ultimate {niche} checklist is now FREE. Grab it in bio."
        ]
        return random.choice(options)
