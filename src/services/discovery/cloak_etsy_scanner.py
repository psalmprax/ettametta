"""
Cloak-Backed Etsy Scanner

Uses CloakBrowser stealth engine for Etsy product research.
Extracts product data: titles, prices, sales, reviews, shop names.
"""

import datetime
import logging
from typing import Optional

from .scanner_base import DiscoveryScannerBase
from .models import ContentCandidate
from .cloak_scanner import CloakBrowserScanner

logger = logging.getLogger(__name__)


class CloakEtsyScanner(DiscoveryScannerBase):
    """Etsy product scanner backed by CloakBrowser stealth engine."""

    def __init__(self, scraper_url: str = "http://cloakbrowser:8010"):
        self.cloak_engine = CloakBrowserScanner(
            scraper_url=scraper_url, platform="etsy"
        )

    async def scan_trends(
        self,
        niche: str,
        published_after: Optional[datetime.datetime] = None,
        region: Optional[str] = None,
        **kwargs,
    ) -> list[ContentCandidate]:
        try:
            results = await self.cloak_engine.scan_platform(
                "etsy", niche, region=region
            )
            if results:
                logger.info(
                    f"[CloakEtsy] Stealth scan returned {len(results)} products for '{niche}'"
                )
                return results
        except Exception as e:
            logger.warning(f"[CloakEtsy] Stealth scan failed: {e}")

        return []

    async def scan_products(
        self,
        niche: str,
        region: Optional[str] = None,
        max_results: int = 20,
    ) -> list[ContentCandidate]:
        """Scan Etsy for products in a specific niche."""
        return await self.scan_trends(niche, region=region)

    async def close(self):
        await self.cloak_engine.close()
