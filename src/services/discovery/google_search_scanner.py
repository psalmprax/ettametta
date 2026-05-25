import aiohttp
import logging
import random
from .models import ContentCandidate
from datetime import datetime
from src.api.config import settings

logger = logging.getLogger(__name__)


class GoogleSearchScanner:
    """
    Google Search scanner for discovering popular products and monetization opportunities.
    Uses Google Custom Search API (free tier: 100 searches/day) or scraping (for development).
    """

    def __init__(self):
        self.platform = "Google Search"
        self.api_key = getattr(settings, "GOOGLE_API_KEY", "")
        self.cx = getattr(settings, "GOOGLE_SEARCH_CX", "")  # Custom Search Engine ID
        self.current_year = datetime.now().year
        self.current_month = datetime.now().strftime("%B")

    def _build_queries(self, niche: str) -> list[str]:
        """Build dynamic search queries based on niche and current time."""
        templates = [
            f"best {niche} products {self.current_year} trending",
            f"top {niche} {self.current_year}",
            f"{niche} affiliate programs",
            f"trending {niche} {self.current_month} {self.current_year}",
            f"popular {niche} items",
        ]
        return random.sample(templates, min(3, len(templates)))

    async def scan_trends(self, niche: str, published_after: datetime | None = None, **kwargs) -> list[ContentCandidate]:
        """
        Searches Google for trending products, affiliate opportunities, and monetization ideas.
        Uses Google Custom Search API.
        """
        logger.info(
            f"[GoogleSearch] Searching for monetization opportunities in: {niche}"
        )

        # Build dynamic queries for fresh results
        queries = self._build_queries(niche)
        primary_query = (
            queries[0]
            if queries
            else f"best {niche} products {self.current_year} trending"
        )

        if not self.api_key or not self.cx:
            logger.warning(
                "[GoogleSearch] Google API key or CX not configured. Using fallback method."
            )
            return await self._scan_with_scrape(niche)

        try:
            async with aiohttp.ClientSession() as session:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": self.api_key,
                    "cx": self.cx,
                    "q": primary_query,
                    "num": 10,
                }

                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.warning(
                            f"[GoogleSearch] API returned status {response.status}"
                        )
                        return await self._scan_with_scrape(niche)

                    data = await response.json()
                    items = data.get("items", [])

                    candidates = []
                    for item in items:
                        candidates.append(
                            ContentCandidate(
                                id=f"gs_{hash(item.get('link', '')) % 100000}",
                                platform=self.platform,
                                source_uri=item.get("link", ""),
                                creator_name=item.get("displayLink", ""),
                                title=item.get("title", ""),
                                view_count=10000,  # Estimate
                                like_count=0,
                                comment_count=0,
                                share_count=0,
                                engagement_score=0.05,
                                thumbnail_uri=None,
                                tags=[niche, "search", "monetization"],
                                metadata={
                                    "source": "google_search",
                                    "search_type": "product",
                                },
                            )
                        )

                    if candidates:
                        logger.info(
                            f"[GoogleSearch] Found {len(candidates)} search results"
                        )
                        return candidates

        except Exception as e:
            logger.exception(f"[GoogleSearch] Error: {e}")

        return await self._scan_with_scrape(niche)

    async def _scan_with_scrape(self, niche: str) -> list[ContentCandidate]:
        """
        Fallback: Try to scrape Google Shopping/Trends results directly.
        Note: This is fragile and may break. For production, use the API.
        """
        logger.info(f"[GoogleSearch] Attempting direct scrape for: {niche}")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }

                # Search for trending products in niche
                search_queries = self._build_queries(niche)

                all_results = []
                for query in search_queries[:2]:  # Limit searches
                    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=shop"

                    try:
                        async with session.get(
                            url,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10),
                        ) as response:
                            if response.status == 200:
                                html = await response.text()
                                from bs4 import BeautifulSoup

                                soup = BeautifulSoup(html, "html.parser")

                                # Extract product cards from Google Shopping results
                                for result in soup.select(
                                    ".sh-dgr__gr-auto, .sh-dgr__content"
                                ):
                                    title_el = result.select_one(
                                        "h3, .tAxDx, [data-name]"
                                    )
                                    price_el = result.select_one(
                                        ".a8Pemb, .HRLxBb, [data-price]"
                                    )
                                    link_el = result.select_one("a[href]")

                                    if title_el:
                                        title = title_el.get_text(strip=True)
                                        price = (
                                            price_el.get_text(strip=True)
                                            if price_el
                                            else "N/A"
                                        )
                                        href = (
                                            link_el.get("href", "") if link_el else ""
                                        )

                                        if title and len(title) > 5:
                                            all_results.append(
                                                {
                                                    "title": title,
                                                    "price": price,
                                                    "url": href,
                                                }
                                            )
                            elif response.status == 429:
                                logger.warning(
                                    f"[GoogleSearch] Rate limited on query: {query}"
                                )
                                break
                    except Exception as scrape_err:
                        logger.debug(
                            f"[GoogleSearch] Scrape error for '{query}': {scrape_err}"
                        )

                candidates = []
                for res in all_results:
                    candidates.append(
                        ContentCandidate(
                            id=f"gs_scrape_{hash(res['url']) % 100000}",
                            platform=self.platform,
                            source_uri=res["url"],
                            creator_name="Google Shopping",
                            title=res["title"],
                            view_count=5000,
                            like_count=0,
                            comment_count=0,
                            share_count=0,
                            engagement_score=0.03,
                            metadata={"price": res["price"]},
                        )
                    )
                return candidates[:10]

        except Exception as e:
            logger.exception(f"[GoogleSearch] Scrape error: {e}")

        return []


base_google_search_service = GoogleSearchScanner()
