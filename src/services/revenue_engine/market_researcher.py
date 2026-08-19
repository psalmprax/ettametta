"""
Market Researcher — Automated Niche Discovery

Uses CloakBrowser + Etsy to find profitable product opportunities.
Analyzes competition, pricing, reviews, and demand signals.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/revenue_engine")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class NicheOpportunity:
    niche: str
    search_volume_estimate: int = 0
    avg_price: float = 0.0
    top_seller_sales: int = 0
    competitor_count: int = 0
    avg_rating: float = 0.0
    review_count: int = 0
    gap_score: float = 0.0
    opportunity_score: float = 0.0
    pain_points: list[str] = field(default_factory=list)
    trending: bool = False
    discovered_at: str = ""

    def __post_init__(self):
        if not self.discovered_at:
            self.discovered_at = datetime.now().isoformat()


class MarketResearcher:
    """Discovers profitable niches using automated research."""

    def __init__(self, scraper_url: str = "http://cloakbrowser:8010"):
        self.scraper_url = scraper_url
        self._cloak = None

    async def _get_cloak(self):
        if self._cloak is None:
            from ..discovery.cloak_scanner import CloakBrowserScanner
            self._cloak = CloakBrowserScanner(scraper_url=self.scraper_url, platform="etsy")
        return self._cloak

    async def research_niche(self, niche: str) -> NicheOpportunity:
        """Research a specific niche on Etsy."""
        cloak = await self._get_cloak()
        results = await cloak.scan_platform("etsy", niche, region="US")

        if not results:
            return NicheOpportunity(niche=niche)

        prices = []
        sales = []
        ratings = []
        shops = set()

        for r in results:
            meta = r.metadata_json or {}
            price = meta.get("price", 0)
            sale_count = meta.get("sales", 0)
            rating = meta.get("rating", 0)
            shop = meta.get("shop", "")

            if price > 0:
                prices.append(float(price))
            if sale_count > 0:
                sales.append(int(sale_count))
            if rating > 0:
                ratings.append(float(rating))
            if shop:
                shops.add(shop)

        avg_price = sum(prices) / len(prices) if prices else 0
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        top_sales = max(sales) if sales else 0
        total_reviews = sum(sales)

        gap_score = self._calculate_gap_score(
            avg_price, top_sales, len(results), avg_rating
        )

        return NicheOpportunity(
            niche=niche,
            search_volume_estimate=len(results) * 100,
            avg_price=round(avg_price, 2),
            top_seller_sales=top_sales,
            competitor_count=len(results),
            avg_rating=round(avg_rating, 2),
            review_count=total_reviews,
            gap_score=round(gap_score, 2),
            opportunity_score=round(gap_score * 1.5, 2),
        )

    async def research_multiple(self, niches: list[str]) -> list[NicheOpportunity]:
        """Research multiple niches concurrently."""
        tasks = [self.research_niche(n) for n in niches]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        opportunities = []
        for r in results:
            if isinstance(r, NicheOpportunity):
                opportunities.append(r)
            elif isinstance(r, Exception):
                logger.error(f"Research failed: {r}")
        opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
        return opportunities

    async def find_trending_niches(self, seed_niches: list[str]) -> list[str]:
        """Expand seed niches into trending sub-niches."""
        expanded = []
        prefixes = ["best selling", "trending", "new", "custom", "digital"]
        suffixes = ["template", "bundle", "pack", "guide", "checklist"]
        for seed in seed_niches:
            for prefix in prefixes[:2]:
                expanded.append(f"{prefix} {seed}")
            for suffix in suffixes[:2]:
                expanded.append(f"{seed} {suffix}")
        return list(set(expanded))

    def _calculate_gap_score(
        self, avg_price: float, top_sales: int, competitors: int, avg_rating: float
    ) -> float:
        """Calculate opportunity gap score (0-100)."""
        score = 0.0
        if avg_price > 5:
            score += 20
        if avg_price > 15:
            score += 10
        if top_sales > 100:
            score += 20
        if top_sales > 1000:
            score += 15
        if competitors < 50:
            score += 15
        if competitors < 20:
            score += 10
        if avg_rating < 4.5:
            score += 10
        return min(score, 100)

    async def save_results(self, opportunities: list[NicheOpportunity], filename: str = "research"):
        """Save research results to file."""
        data = [asdict(o) for o in opportunities]
        path = DATA_DIR / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(data, indent=2))
        logger.info(f"Saved {len(opportunities)} opportunities to {path}")
        return path

    async def close(self):
        if self._cloak:
            await self._cloak.close()
