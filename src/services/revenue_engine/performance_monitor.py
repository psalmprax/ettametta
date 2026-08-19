"""
Performance Monitor — Tracks and Analyzes Revenue Metrics

Monitors product performance, traffic, conversions, and revenue.
Provides insights for self-optimization.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/revenue_engine/metrics")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ProductMetrics:
    product_name: str
    views: int = 0
    sales: int = 0
    revenue: float = 0.0
    conversion_rate: float = 0.0
    avg_rating: float = 0.0
    review_count: int = 0
    traffic_sources: dict = field(default_factory=dict)
    period: str = "daily"
    tracked_at: str = ""

    def __post_init__(self):
        if not self.tracked_at:
            self.tracked_at = datetime.now().isoformat()
        if self.views > 0:
            self.conversion_rate = round((self.sales / self.views) * 100, 2)


@dataclass
class PerformanceInsight:
    category: str
    insight: str
    confidence: float = 0.0
    recommendation: str = ""
    impact: str = "medium"


class PerformanceMonitor:
    """Tracks product performance and generates insights."""

    def __init__(self):
        self.metrics_history: list[ProductMetrics] = []
        self.insights: list[PerformanceInsight] = []

    def record_metrics(self, metrics: ProductMetrics):
        """Record metrics for a product."""
        self.metrics_history.append(metrics)
        self._analyze_metrics(metrics)
        self._save_metrics(metrics)

    def get_trends(self, product_name: str, days: int = 30) -> dict:
        """Get performance trends for a product."""
        relevant = [m for m in self.metrics_history if m.product_name == product_name]
        if not relevant:
            return {"product": product_name, "data_points": 0}

        total_views = sum(m.views for m in relevant)
        total_sales = sum(m.sales for m in relevant)
        total_revenue = sum(m.revenue for m in relevant)

        return {
            "product": product_name,
            "data_points": len(relevant),
            "total_views": total_views,
            "total_sales": total_sales,
            "total_revenue": round(total_revenue, 2),
            "avg_conversion": round((total_sales / max(total_views, 1)) * 100, 2),
            "period_days": days,
        }

    def get_insights(self, product_name: Optional[str] = None) -> list[PerformanceInsight]:
        """Get optimization insights."""
        if product_name:
            return [i for i in self.insights if product_name.lower() in i.insight.lower()]
        return self.insights

    def _analyze_metrics(self, metrics: ProductMetrics):
        """Analyze metrics and generate insights."""
        if metrics.conversion_rate < 1.0 and metrics.views > 50:
            self.insights.append(PerformanceInsight(
                category="conversion",
                insight=f"Low conversion rate ({metrics.conversion_rate}%) for {metrics.product_name}",
                confidence=0.8,
                recommendation="Consider adjusting price, improving listing photos, or rewriting description",
                impact="high",
            ))

        if metrics.views > 100 and metrics.sales == 0:
            self.insights.append(PerformanceInsight(
                category="conversion",
                insight=f"High traffic ({metrics.views} views) but no sales for {metrics.product_name}",
                confidence=0.9,
                recommendation="Check pricing, listing quality, or product-market fit",
                impact="high",
            ))

        if metrics.avg_rating < 4.0 and metrics.review_count > 5:
            self.insights.append(PerformanceInsight(
                category="quality",
                insight=f"Below average rating ({metrics.avg_rating}) for {metrics.product_name}",
                confidence=0.7,
                recommendation="Review customer feedback and improve product quality",
                impact="high",
            ))

        if metrics.sales > 50:
            self.insights.append(PerformanceInsight(
                category="success",
                insight=f"Strong performer: {metrics.sales} sales for {metrics.product_name}",
                confidence=0.95,
                recommendation="Create variations or bundles to maximize revenue",
                impact="medium",
            ))

    def _save_metrics(self, metrics: ProductMetrics):
        """Save metrics to file."""
        filename = f"{metrics.product_name.lower().replace(' ', '_')}_{metrics.tracked_at[:10]}.json"
        path = DATA_DIR / filename
        path.write_text(json.dumps(asdict(metrics), indent=2))

    def generate_report(self) -> dict:
        """Generate a summary report of all tracked products."""
        products = {}
        for m in self.metrics_history:
            if m.product_name not in products:
                products[m.product_name] = {
                    "views": 0, "sales": 0, "revenue": 0, "data_points": 0
                }
            products[m.product_name]["views"] += m.views
            products[m.product_name]["sales"] += m.sales
            products[m.product_name]["revenue"] += m.revenue
            products[m.product_name]["data_points"] += 1

        for _name, data in products.items():
            data["conversion_rate"] = round(
                (data["sales"] / max(data["views"], 1)) * 100, 2
            )
            data["revenue"] = round(data["revenue"], 2)

        return {
            "total_products": len(products),
            "total_revenue": round(sum(d["revenue"] for d in products.values()), 2),
            "total_sales": sum(d["sales"] for d in products.values()),
            "products": products,
            "insights_count": len(self.insights),
            "generated_at": datetime.now().isoformat(),
        }
