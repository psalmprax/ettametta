import logging
import random
from typing import List, Optional
from .models import ContentCandidate

class BilibiliScanner:
    def __init__(self):
        self.platform = "Bilibili"

    async def scan_trends(self, niche: str, published_after: Optional[str] = None) -> List[ContentCandidate]:
        """
        Sprints for early trends on Bilibili (China's YouTube alternative).
        Critical for early signal detection in tech, gaming, and animation.
        """
        logging.info(f"[BilibiliScanner] Sourcing global signals for: {niche}")
        
        # Bilibili is a powerhouse for Tech and Animation
        if niche.lower() in ["tech", "gaming", "animation", "future", "ai"]:
            return [
                ContentCandidate(
                    id=f"bili_{random.randint(100,999)}",
                    title=f"Early Global Trend: {niche}",
                    url="https://www.bilibili.com/video/mock",
                    author=f"Bili_Tech_{niche}",
                    view_count=random.randint(20000, 200000),
                    engagement_rate=random.uniform(0.05, 0.12),
                    platform=self.platform,
                    metadata={"coin_count": random.randint(500, 5000)}
                )
            ]
        return []

base_bilibili_scanner = BilibiliScanner()
