"""
CloakBrowser Scanner

A DiscoveryScannerBase subclass that uses the containerized CloakBrowser
service for undetected web scraping of YouTube and other platforms.
Bypasses YouTube API quota limits entirely.
"""

import datetime
import logging
import re
from typing import Optional

import httpx

from .scanner_base import DiscoveryScannerBase
from .models import ContentCandidate

logger = logging.getLogger(__name__)


class CloakBrowserScanner(DiscoveryScannerBase):
    """
    Scanner that delegates to the containerized discovery-scraper service
    powered by CloakBrowser + Playwright for stealth browsing.
    """

    def __init__(
        self,
        scraper_url: str = "http://discovery-scraper:8010",
        timeout: float = 30.0,
    ):
        self.scraper_url = scraper_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def __init_subclass__(cls, **kwargs):
        pass

    async def scan_trends(
        self,
        niche: str,
        published_after: Optional[datetime.datetime] = None,
        region: Optional[str] = "US",
        **kwargs,
    ) -> list[ContentCandidate]:
        """
        Scrape YouTube trends using the CloakBrowser service.
        Falls back gracefully if the scraper is unavailable.
        """
        try:
            params = {
                "niche": niche,
                "region": region or "US",
                "max_results": 10,
            }
            response = await self.client.get(
                f"{self.scraper_url}/scrape/youtube",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                logger.error(
                    f"CloakBrowser scraper failed: {data.get('error', 'unknown')}"
                )
                return []

            candidates = []
            for item in data.get("candidates", []):
                video_id = item.get("id", "")
                if not video_id:
                    continue

                candidates.append(
                    ContentCandidate(
                        id=f"cloak_yt_{video_id}",
                        platform="YouTube",
                        source_uri=item.get("url", ""),
                        creator_name=item.get("channel", "Unknown"),
                        title=item.get("title", "No Title"),
                        thumbnail_uri=item.get("thumbnail", ""),
                        view_count=self._parse_views(item.get("views", "0")),
                        like_count=0,
                        comment_count=0,
                        share_count=0,
                        engagement_score=0.0,
                        viral_score=0,
                        region=region or "US",
                        category="video",
                        tags=[niche, "cloak-scraped"],
                        metadata={"scraper": "cloakbrowser", "source": "youtube_web"},
                    )
                )

            logger.info(
                f"CloakBrowser scan returned {len(candidates)} candidates for '{niche}'"
            )
            return candidates

        except httpx.ConnectError:
            logger.warning(
                f"Cannot connect to CloakBrowser scraper at {self.scraper_url}"
            )
            return []
        except httpx.TimeoutException:
            logger.warning(f"CloakBrowser scraper timed out for niche '{niche}'")
            return []
        except Exception as e:
            logger.exception(f"CloakBrowser scan failed for niche '{niche}': {e}")
            return []

    def _parse_views(self, views_str: str) -> int:
        """Parse view count strings like '1.2M views', '500K views', '1,234 views'."""
        if not views_str:
            return 0
        # Remove the word 'views' and trim
        views_str = views_str.replace("views", "").replace("view", "").strip()
        # Remove commas
        views_str = views_str.replace(",", "")
        match = re.match(r"([\d.]+)\s*([MK]?)", views_str, re.IGNORECASE)
        if not match:
            return 0
        num = float(match.group(1))
        suffix = match.group(2).upper()
        if suffix == "M":
            return int(num * 1_000_000)
        elif suffix == "K":
            return int(num * 1_000)
        return int(num)

    async def close(self):
        """Clean up the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
