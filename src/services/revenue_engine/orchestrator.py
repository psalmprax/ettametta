"""
Revenue Engine Orchestrator — Ties Everything Together

Runs the full pipeline: Research → Create → List → Traffic → Optimize
Self-improving loop that gets smarter over time.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from .market_researcher import MarketResearcher
from .product_creator import ProductCreator
from .listing_optimizer import ListingOptimizer
from .traffic_driver import TrafficDriver
from .performance_monitor import PerformanceMonitor, ProductMetrics
from .self_optimizer import SelfOptimizer, LearningEntry
from .etsy_api_client import EtsyAPIClient
from .google_etsy_scraper import GoogleEtsyScraper
from ..discovery.cloak_pinterest_scanner import CloakPinterestScanner

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/revenue_engine")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class PipelineRun:
    run_id: str
    niches: list[str] = field(default_factory=list)
    products_created: int = 0
    listings_optimized: int = 0
    posts_generated: int = 0
    status: str = "running"
    started_at: str = ""
    completed_at: str = ""
    results: dict = field(default_factory=dict)


class RevenueEngine:
    """
    Self-improving revenue automation system.

    Pipeline:
    1. Research profitable niches
    2. Create digital products
    3. Optimize listings
    4. Generate traffic content
    5. Monitor performance
    6. Learn and improve
    """

    def __init__(self, scraper_url: str = "http://cloakbrowser:8010", etsy_api_key: str = ""):
        self.scraper_url = scraper_url
        self.researcher = MarketResearcher(scraper_url)
        self.creator = ProductCreator()
        self.optimizer = ListingOptimizer()
        self.traffic = TrafficDriver()
        self.monitor = PerformanceMonitor()
        self.self_optimizer = SelfOptimizer()
        self.etsy_api = EtsyAPIClient(api_key=etsy_api_key)
        self.google_etsy = GoogleEtsyScraper()
        self.pinterest = CloakPinterestScanner(scraper_url=scraper_url)
        self.current_run: Optional[PipelineRun] = None

    async def run_pipeline(
        self,
        niches: list[str],
        product_types: list[str] = None,
        auto_traffic: bool = True,
    ) -> PipelineRun:
        """Run the full revenue pipeline for given niches."""
        if product_types is None:
            product_types = ["template", "guide", "checklist"]

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_run = PipelineRun(
            run_id=run_id,
            niches=niches,
            started_at=datetime.now().isoformat(),
        )

        logger.info(f"[RevenueEngine] Starting pipeline run {run_id} for {niches}")

        try:
            # Step 1: Research
            logger.info("[Step 1] Researching niches...")
            opportunities = await self.researcher.research_multiple(niches)
            self.current_run.results["opportunities"] = [
                asdict(o) for o in opportunities
            ]
            await self.researcher.save_results(opportunities, f"run_{run_id}")

            # Step 2: Create products
            logger.info("[Step 2] Creating products...")
            products = []
            for opp in opportunities:
                for ptype in product_types:
                    product = self.creator.generate_product(opp.niche, ptype)
                    products.append(product)
                    self.creator.generate_product(opp.niche, ptype)
            self.current_run.products_created = len(products)
            self.current_run.results["products"] = [asdict(p) for p in products]

            # Step 3: Optimize listings
            logger.info("[Step 3] Optimizing listings...")
            listings = []
            for product in products:
                listing = self.optimizer.optimize(
                    product.name,
                    product.niche,
                    product.price,
                    product.target_audience,
                    product.problem_solved,
                    product.product_type,
                )
                listings.append(listing)
            self.current_run.listings_optimized = len(listings)
            self.current_run.results["listings"] = [asdict(l) for l in listings]

            # Step 4: Generate traffic content
            if auto_traffic:
                logger.info("[Step 4] Generating traffic content...")
                all_posts = []
                email_sequences = []
                seo_articles = []
                for product in products:
                    posts = self.traffic.generate_social_posts(
                        product.name, product.niche
                    )
                    all_posts.extend(posts)
                    email_seq = self.traffic.generate_email_sequence(
                        product.name, product.niche
                    )
                    email_sequences.append(email_seq)
                    seo = self.traffic.generate_seo_article(product.niche, product.name)
                    seo_articles.append(seo)
                self.current_run.posts_generated = len(all_posts)
                self.current_run.results["social_posts"] = len(all_posts)
                self.current_run.results["email_sequences"] = [asdict(e) for e in email_sequences]
                self.current_run.results["seo_articles"] = [asdict(s) for s in seo_articles]

            self.current_run.status = "completed"
            self.current_run.completed_at = datetime.now().isoformat()

            # Save run results
            self._save_run(self.current_run)

            logger.info(
                f"[RevenueEngine] Pipeline completed: "
                f"{self.current_run.products_created} products, "
                f"{self.current_run.listings_optimized} listings, "
                f"{self.current_run.posts_generated} posts"
            )

        except Exception as e:
            self.current_run.status = "failed"
            self.current_run.results["error"] = str(e)
            logger.error(f"[RevenueEngine] Pipeline failed: {e}")

        return self.current_run

    async def quick_test(self, niche: str) -> dict:
        """Quick test: research + one product concept."""
        opp = await self.researcher.research_niche(niche)
        product = self.creator.generate_product(niche, "template")
        listing = self.optimizer.optimize(
            product.name, niche, product.price,
            product.target_audience, product.problem_solved
        )

        return {
            "opportunity": asdict(opp),
            "product": asdict(product),
            "listing": asdict(listing),
        }

    async def research_etsy(self, niche: str) -> dict:
        """Research Etsy using both API and Google proxy."""
        results = {
            "niche": niche,
            "api_results": [],
            "google_results": [],
            "combined_analysis": {},
        }

        # Try Etsy API first (if key available)
        if self.etsy_api.api_key:
            api_products = await self.etsy_api.search_listings(niche, limit=25)
            results["api_results"] = [
                {
                    "title": p.title,
                    "price": p.price,
                    "rating": p.rating,
                    "reviews": p.review_count,
                    "shop": p.shop_name,
                    "url": p.url,
                    "tags": p.tags,
                }
                for p in api_products
            ]
            results["combined_analysis"] = self.etsy_api.analyze_niche(api_products)

        # Google proxy (always works)
        google_results = await self.google_etsy.search_digital_products(niche, max_results=15)
        results["google_results"] = [
            {
                "title": r.title,
                "price": r.price,
                "shop": r.shop_name,
                "url": r.url,
            }
            for r in google_results
        ]

        # Merge analysis
        if not results["combined_analysis"]:
            google_analysis = await self.google_etsy.analyze_niche(niche)
            results["combined_analysis"] = google_analysis

        return results

    async def research_pinterest(self, niche: str) -> dict:
        """Research Pinterest for visual product intelligence."""
        pins = await self.pinterest.scan_visual_products(niche)

        return {
            "niche": niche,
            "total_pins": len(pins),
            "pins": [
                {
                    "title": p.title,
                    "url": p.source_uri,
                    "thumbnail": p.thumbnail_uri,
                    "platform": p.platform,
                }
                for p in pins[:15]
            ],
            "visual_themes": self._extract_visual_themes(pins),
        }

    def _extract_visual_themes(self, pins) -> list[str]:
        """Extract common visual themes from Pinterest pins."""
        themes = []
        for pin in pins:
            title_lower = pin.title.lower()
            if "template" in title_lower:
                themes.append("templates")
            if "flyer" in title_lower:
                themes.append("flyers")
            if "brochure" in title_lower:
                themes.append("brochures")
            if "social" in title_lower:
                themes.append("social media")
            if "logo" in title_lower:
                themes.append("logos")
            if "website" in title_lower:
                themes.append("websites")
        return list(set(themes))[:10]

    def record_performance(self, metrics: ProductMetrics):
        """Record performance metrics and trigger optimization."""
        self.monitor.record_metrics(metrics)

        insights = self.monitor.get_insights(metrics.product_name)
        for insight in insights:
            learning = LearningEntry(
                category=insight.category,
                observation=insight.insight,
                action_taken=insight.recommendation,
                outcome="pending",
                lesson=f"Insight: {insight.insight}",
            )
            self.self_optimizer.record_learning(learning)

    def get_optimization_recommendations(self) -> list[str]:
        """Get recommendations from the self-optimizer."""
        return self.self_optimizer.get_recommendations()

    def _save_run(self, run: PipelineRun):
        """Save pipeline run results."""
        path = DATA_DIR / f"run_{run.run_id}.json"
        path.write_text(json.dumps(asdict(run), indent=2))

    async def close(self):
        """Clean up resources."""
        await self.researcher.close()
        await self.etsy_api.close()
        await self.google_etsy.close()
        await self.pinterest.close()
