"""
Google Search Proxy — Scrape Etsy listings via Google

Searches `site:etsy.com` on Google to get listing data without hitting Etsy directly.
Google is less aggressive with CAPTCHAs for headless browsers.
"""

import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import unquote

import httpx

logger = logging.getLogger(__name__)


@dataclass
class GoogleEtsyResult:
    title: str
    url: str
    snippet: str = ""
    price: float = 0.0
    shop_name: str = ""
    rating: float = 0.0
    review_count: int = 0
    thumbnail: str = ""

    @property
    def listing_id(self) -> str:
        match = re.search(r'/listing/(\d+)', self.url)
        return match.group(1) if match else hashlib.md5(self.url.encode()).hexdigest()[:12]


class GoogleEtsyScraper:
    """
    Scrapes Etsy listings via Google search.

    Searches for: site:etsy.com "keywords"
    Extracts: titles, URLs, prices, snippets
    """

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
        return self._client

    async def search(
        self,
        keywords: str,
        max_results: int = 20,
        region: str = "us",
    ) -> list[GoogleEtsyResult]:
        """Search Google for Etsy listings."""
        query = f'site:etsy.com "{keywords}"'
        results = []

        # Google pagination
        pages_needed = (max_results // 10) + 1
        for page in range(min(pages_needed, 3)):
            start = page * 10
            url = f"https://www.google.com/search?q={self._encode(query)}&start={start}&gl={region}"

            try:
                response = await self.client.get(url)
                response.raise_for_status()
                html = response.text

                page_results = self._parse_google_results(html)
                results.extend(page_results)

                if len(results) >= max_results:
                    break

                # Be polite
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Google search page {page} failed: {e}")
                break

        return results[:max_results]

    async def search_digital_products(
        self,
        niche: str,
        max_results: int = 20,
    ) -> list[GoogleEtsyResult]:
        """Search specifically for digital products in a niche."""
        queries = [
            f'site:etsy.com "{niche}" digital download',
            f'site:etsy.com "{niche}" template',
            f'site:etsy.com "{niche}" canva',
        ]

        all_results = []
        for query in queries:
            try:
                results = await self._search_query(query, max_results=10)
                all_results.extend(results)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Query failed: {e}")

        # Deduplicate by listing_id
        seen = set()
        unique = []
        for r in all_results:
            if r.listing_id not in seen:
                seen.add(r.listing_id)
                unique.append(r)

        return unique[:max_results]

    async def _search_query(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[GoogleEtsyResult]:
        """Execute a single Google search."""
        url = f"https://www.google.com/search?q={self._encode(query)}&num={max_results}"

        response = await self.client.get(url)
        response.raise_for_status()
        return self._parse_google_results(response.text)

    def _parse_google_results(self, html: str) -> list[GoogleEtsyResult]:
        """Parse Google search results HTML for Etsy listings."""
        results = []

        # Pattern for Google search result blocks
        # Look for links to etsy.com/listing/
        listing_pattern = re.compile(
            r'href="(https?://(?:www\.)?etsy\.com/listing/\d+/[^"]*)"',
            re.IGNORECASE
        )

        urls_found = listing_pattern.findall(html)
        urls_seen = set()

        for url in urls_found:
            if url in urls_seen:
                continue
            urls_seen.add(url)

            # Try to extract title and snippet around this URL
            title = self._extract_title_near_url(html, url)
            snippet = self._extract_snippet_near_url(html, url)
            price = self._extract_price_from_snippet(snippet)
            shop = self._extract_shop_from_url(url)

            results.append(GoogleEtsyResult(
                title=title,
                url=url,
                snippet=snippet,
                price=price,
                shop_name=shop,
            ))

        return results

    def _extract_title_near_url(self, html: str, url: str) -> str:
        """Extract the title near a URL in Google results."""
        # Find the position of the URL
        pos = html.find(url)
        if pos == -1:
            return "Unknown"

        # Look backward for the title tag
        preceding = html[max(0, pos - 2000):pos]

        # Google wraps titles in <h3> tags
        h3_match = re.findall(r'<h3[^>]*>(.*?)</h3>', preceding, re.DOTALL)
        if h3_match:
            title = h3_match[-1]
            title = re.sub(r'<[^>]+>', '', title)
            return unquote(title).strip()

        # Fallback: extract text between tags
        text_before = re.sub(r'<[^>]+>', ' ', preceding)
        text_before = ' '.join(text_before.split())
        if text_before:
            words = text_before.split()[-10:]
            return ' '.join(words)

        return "Unknown"

    def _extract_snippet_near_url(self, html: str, url: str) -> str:
        """Extract the snippet text near a URL."""
        pos = html.find(url)
        if pos == -1:
            return ""

        # Look forward for snippet text
        following = html[pos:pos + 3000]

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', following)
        text = re.sub(r'\s+', ' ', text).strip()

        # Get first meaningful chunk
        words = text.split()[:50]
        return ' '.join(words)

    def _extract_price_from_snippet(self, snippet: str) -> float:
        """Extract price from snippet text."""
        price_match = re.search(r'\$(\d+\.?\d*)', snippet)
        if price_match:
            try:
                return float(price_match.group(1))
            except ValueError:
                pass
        return 0.0

    def _extract_shop_from_url(self, url: str) -> str:
        """Extract shop name from Etsy URL."""
        # Etsy shop URLs look like: etsy.com/listing/123/... or etsy.com/shop/shopname
        shop_match = re.search(r'etsy\.com/listing/\d+/([^/]+)', url)
        if shop_match:
            return unquote(shop_match.group(1)).replace('-', ' ').title()
        return "Unknown"

    def _encode(self, text: str) -> str:
        """URL-encode search query."""
        from urllib.parse import quote_plus
        return quote_plus(text)

    async def analyze_niche(self, niche: str) -> dict:
        """Analyze a niche using Google as proxy."""
        results = await self.search_digital_products(niche, max_results=20)

        prices = [r.price for r in results if r.price > 0]

        return {
            "niche": niche,
            "total_results": len(results),
            "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
            "min_price": min(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
            "listings": [
                {
                    "title": r.title,
                    "url": r.url,
                    "price": r.price,
                    "shop": r.shop_name,
                }
                for r in results[:10]
            ],
        }

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
