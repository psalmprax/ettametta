"""
Cloak-Backed Reddit Scanner

Uses CloakBrowser stealth engine as primary scraper with the existing
httpx-based RedditScanner as fallback when the scraper service is unavailable.
"""

import datetime
import logging
from typing import Optional

from .scanner_base import DiscoveryScannerBase
from .models import ContentCandidate
from .cloak_scanner import CloakBrowserScanner
from .reddit_scanner import RedditScanner

logger = logging.getLogger(__name__)


class CloakRedditScanner(DiscoveryScannerBase):
    """Reddit scanner backed by CloakBrowser stealth engine with httpx fallback."""

    def __init__(self, scraper_url: str = "http://cloakbrowser:8010"):
        self.cloak_engine = CloakBrowserScanner(
            scraper_url=scraper_url, platform="reddit"
        )
        self.fallback_scanner = RedditScanner()

    async def scan_trends(
        self,
        niche: str,
        published_after: Optional[datetime.datetime] = None,
        region: Optional[str] = None,
        **kwargs,
    ) -> list[ContentCandidate]:
        # 1. Try CloakBrowser first (stealth Playwright)
        try:
            results = await self.cloak_engine.scan_platform(
                "reddit", niche, published_after=published_after, region=region
            )
            if results:
                logger.info(
                    f"[CloakReddit] Stealth scan returned {len(results)} candidates for '{niche}'"
                )
                return results
        except Exception as e:
            logger.warning(f"[CloakReddit] Stealth scan failed: {e}")

        # 2. Fall back to existing HTTP scraper
        logger.info(f"[CloakReddit] Falling back to httpx scraper for '{niche}'")
        return await self.fallback_scanner.scan_trends(
            niche, published_after=published_after, region=region
        )

    async def close(self):
        await self.cloak_engine.close()
