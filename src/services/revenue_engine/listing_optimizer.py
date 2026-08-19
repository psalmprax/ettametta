"""
Listing Optimizer — Automated Marketplace Listing Creation

Generates optimized titles, descriptions, and tags for Etsy listings.
Uses competitor analysis to maximize visibility.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/revenue_engine")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ListingOptimization:
    title: str
    description: str
    tags: list[str] = field(default_factory=list)
    price: float = 0.0
    sections: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    optimized_at: str = ""

    def __post_init__(self):
        if not self.optimized_at:
            self.optimized_at = datetime.now().isoformat()


class ListingOptimizer:
    """Creates optimized Etsy listings based on product data and market research."""

    def optimize_title(self, product_name: str, niche: str, keywords: list[str] = None) -> str:
        """Create an SEO-optimized title (max 140 chars for Etsy)."""
        base = product_name
        if keywords:
            primary_keyword = keywords[0] if keywords else niche
            base = f"{primary_keyword.title()} {product_name}"
        title = base[:140]
        return title

    def optimize_description(
        self,
        product_name: str,
        niche: str,
        target_audience: str = "",
        problem_solved: str = "",
    ) -> str:
        """Create a conversion-optimized description."""
        audience = target_audience or "professionals"
        problem = problem_solved or f"creating {niche} materials"

        description = (
            f"🔥 {product_name}\n\n"
            f"Stop wasting hours {problem}.\n\n"
            f"This premium template pack gives you:\n"
            f"✅ Professional, ready-to-use designs\n"
            f"✅ Fully editable and customizable\n"
            f"✅ Instant digital download\n"
            f"✅ Works with free tools (Canva, Google Docs)\n\n"
            f"Perfect for: {audience}\n\n"
            f"📦 What's included:\n"
            f"- High-quality template files\n"
            f" step-by-step instructions\n"
            f"- Bonus tips and tricks guide\n\n"
            f"⚡ Download instantly and start using today.\n\n"
            f"Questions? Message us anytime — we respond within 24 hours."
        )
        return description

    def generate_tags(self, niche: str, product_type: str = "template") -> list[str]:
        """Generate optimized tags (Etsy allows 13)."""
        base_tags = niche.lower().split()
        tags = []
        for word in base_tags:
            if word not in tags and len(word) > 2:
                tags.append(word)
        tags.extend([
            product_type,
            "digital download",
            "instant download",
            "editable",
            "printable",
            "template",
        ])
        return tags[:13]

    def optimize(
        self,
        product_name: str,
        niche: str,
        price: float = 9.99,
        target_audience: str = "",
        problem_solved: str = "",
        product_type: str = "template",
    ) -> ListingOptimization:
        """Full listing optimization."""
        tags = self.generate_tags(niche, product_type)
        title = self.optimize_title(product_name, niche, tags)
        description = self.optimize_description(
            product_name, niche, target_audience, problem_solved
        )

        return ListingOptimization(
            title=title,
            description=description,
            tags=tags,
            price=price,
            keywords=tags[:5],
        )

    def analyze_competitor(self, competitor_title: str, competitor_tags: list[str]) -> dict:
        """Analyze a competitor listing for insights."""
        return {
            "title_length": len(competitor_title),
            "tag_count": len(competitor_tags),
            "keywords_found": competitor_tags[:5],
            "title_words": competitor_title.split()[:10],
        }

    def save_optimization(self, optimization: ListingOptimization, product_name: str) -> Path:
        """Save optimization results."""
        filename = product_name.lower().replace(" ", "_") + "_listing.json"
        path = DATA_DIR / filename
        path.write_text(json.dumps(asdict(optimization), indent=2))
        logger.info(f"Saved listing optimization to {path}")
        return path
