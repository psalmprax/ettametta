"""
Etsy API Client — Official Etsy Open API v3 Integration

Free tier: 5,000 requests/day
Requires: API key from etsy.com/developers
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class EtsyProduct:
    listing_id: str
    title: str
    price: float
    currency_code: str = "USD"
    description: str = ""
    url: str = ""
    shop_name: str = ""
    rating: float = 0.0
    review_count: int = 0
    sales_count: int = 0
    thumbnail: str = ""
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)


class EtsyAPIClient:
    """
    Etsy Open API v3 client.

    Setup:
    1. Go to etsy.com/developers
    2. Create an app
    3. Get your API key
    4. Set environment variable: export ETSY_API_KEY="your_key"

    Free tier limits:
    - 5,000 requests/day
    - 10 requests/second
    """

    BASE_URL = "https://openapi.etsy.com/v3"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or self._get_api_key()
        self._client: Optional[httpx.AsyncClient] = None
        self._request_count = 0
        self._last_request_time = 0

    def _get_api_key(self) -> str:
        import os
        return os.environ.get("ETSY_API_KEY", "")

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def _rate_limit(self):
        """Respect rate limits (10 req/sec)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < 0.1:
            await asyncio.sleep(0.1 - elapsed)
        self._last_request_time = time.time()
        self._request_count += 1

    async def search_listings(
        self,
        keywords: str,
        limit: int = 25,
        offset: int = 0,
        sort_on: str = "score",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
    ) -> list[EtsyProduct]:
        """Search Etsy listings by keywords."""
        if not self.api_key:
            logger.warning("No Etsy API key set. Using fallback.")
            return []

        await self._rate_limit()

        params = {
            "keywords": keywords,
            "limit": min(limit, 100),
            "offset": offset,
            "sort_on": sort_on,
            "includes": "shop",
        }
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/application/listings/active",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            products = []
            for listing in data.get("results", []):
                shop = listing.get("shop", {})
                products.append(EtsyProduct(
                    listing_id=str(listing.get("listing_id", "")),
                    title=listing.get("title", ""),
                    price=listing.get("price", {}).get("amount", 0) / 100,
                    currency_code=listing.get("price", {}).get("currency_code", "USD"),
                    description=listing.get("description", "")[:200],
                    url=listing.get("url", ""),
                    shop_name=shop.get("shop_name", ""),
                    rating=listing.get("rating", 0),
                    review_count=listing.get("review_count", 0),
                    thumbnail=listing.get("url_170x135", ""),
                    tags=listing.get("tags", []),
                    categories=self._extract_categories(listing),
                ))

            logger.info(f"Etsy API: Found {len(products)} listings for '{keywords}'")
            return products

        except httpx.HTTPStatusError as e:
            logger.error(f"Etsy API error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Etsy API failed: {e}")
            return []

    async def get_listing(self, listing_id: str) -> Optional[EtsyProduct]:
        """Get a single listing by ID."""
        if not self.api_key:
            return None

        await self._rate_limit()

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/application/listings/{listing_id}",
                params={"includes": "shop"},
            )
            response.raise_for_status()
            listing = response.json()

            shop = listing.get("shop", {})
            return EtsyProduct(
                listing_id=str(listing.get("listing_id", "")),
                title=listing.get("title", ""),
                price=listing.get("price", {}).get("amount", 0) / 100,
                currency_code=listing.get("price", {}).get("currency_code", "USD"),
                description=listing.get("description", "")[:500],
                url=listing.get("url", ""),
                shop_name=shop.get("shop_name", ""),
                rating=listing.get("rating", 0),
                review_count=listing.get("review_count", 0),
                thumbnail=listing.get("url_170x135", ""),
                tags=listing.get("tags", []),
                categories=self._extract_categories(listing),
            )

        except Exception as e:
            logger.error(f"Failed to get listing {listing_id}: {e}")
            return None

    async def search_by_category(
        self,
        category_id: str,
        keywords: str = "",
        limit: int = 25,
    ) -> list[EtsyProduct]:
        """Search within a specific category."""
        if not self.api_key:
            return []

        await self._rate_limit()

        params = {
            "limit": min(limit, 100),
            "sort_on": "score",
            "includes": "shop",
        }
        if keywords:
            params["keywords"] = keywords

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/application/seller-taxonomy/nodes/{category_id}/listings",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            products = []
            for listing in data.get("results", []):
                shop = listing.get("shop", {})
                products.append(EtsyProduct(
                    listing_id=str(listing.get("listing_id", "")),
                    title=listing.get("title", ""),
                    price=listing.get("price", {}).get("amount", 0) / 100,
                    url=listing.get("url", ""),
                    shop_name=shop.get("shop_name", ""),
                    rating=listing.get("rating", 0),
                    review_count=listing.get("review_count", 0),
                    thumbnail=listing.get("url_170x135", ""),
                    tags=listing.get("tags", []),
                ))

            return products

        except Exception as e:
            logger.error(f"Category search failed: {e}")
            return []

    async def get_shop_listings(
        self,
        shop_id: str,
        limit: int = 25,
    ) -> list[EtsyProduct]:
        """Get all listings from a specific shop."""
        if not self.api_key:
            return []

        await self._rate_limit()

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/application/shops/{shop_id}/listings",
                params={"limit": min(limit, 100), "state": "active"},
            )
            response.raise_for_status()
            data = response.json()

            products = []
            for listing in data.get("results", []):
                products.append(EtsyProduct(
                    listing_id=str(listing.get("listing_id", "")),
                    title=listing.get("title", ""),
                    price=listing.get("price", {}).get("amount", 0) / 100,
                    url=listing.get("url", ""),
                    shop_name=shop_id,
                    rating=listing.get("rating", 0),
                    review_count=listing.get("review_count", 0),
                    thumbnail=listing.get("url_170x135", ""),
                ))

            return products

        except Exception as e:
            logger.error(f"Shop listings failed: {e}")
            return []

    def _extract_categories(self, listing: dict) -> list[str]:
        """Extract category names from listing."""
        categories = []
        taxonomy = listing.get("taxonomy", {})
        if taxonomy:
            path = taxonomy.get("path", [])
            categories = [c.get("name", "") for c in path if c.get("name")]
        return categories

    def analyze_niche(self, products: list[EtsyProduct]) -> dict:
        """Analyze a set of products for market insights."""
        if not products:
            return {}

        prices = [p.price for p in products if p.price > 0]
        ratings = [p.rating for p in products if p.rating > 0]
        reviews = [p.review_count for p in products]

        return {
            "total_products": len(products),
            "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
            "min_price": min(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
            "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
            "total_reviews": sum(reviews),
            "top_shops": list({p.shop_name for p in products if p.shop_name})[:10],
            "common_tags": self._get_common_tags(products),
        }

    def _get_common_tags(self, products: list[EtsyProduct]) -> list[str]:
        """Find most common tags across products."""
        tag_counts = {}
        for p in products:
            for tag in p.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return sorted(tag_counts.keys(), key=lambda x: tag_counts[x], reverse=True)[:15]

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
