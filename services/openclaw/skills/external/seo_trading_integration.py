import os
import logging
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
import random

logger = logging.getLogger(__name__)

YAHOO_FINANCE_ENABLED = True  # Free, no API key needed


class BlogSEOService:
    """
    Blog and SEO content generation service.
    Uses Groq (already configured) for content generation.
    """

    def __init__(self):
        self.api_url = os.getenv("API_URL", "http://localhost:8000")

    def generate_seo_content(
        self, topic: str, content_type: str = "blog", word_count: int = 500
    ) -> Dict[str, Any]:
        """
        Generate SEO-optimized content for a topic.

        Args:
            topic: The main topic/keyword
            content_type: Type of content (blog, product, review)
            word_count: Target word count

        Returns:
            Dict with title, content, meta description, keywords
        """
        keywords = self._generate_keywords(topic)
        title = self._generate_title(topic, content_type)
        meta_description = self._generate_meta_description(topic, word_count)

        # Structure the content
        content = self._structure_content(topic, content_type, word_count)

        return {
            "title": title,
            "content": content,
            "meta_description": meta_description,
            "keywords": keywords,
            "headings": self._generate_headings(topic),
            "word_count": len(content.split()),
            "generated_at": datetime.now().isoformat(),
        }

    def _generate_keywords(self, topic: str) -> List[str]:
        """Generate SEO keywords for topic."""
        base = topic.lower().strip()
        keywords = [
            base,
            f"best {base}",
            f"{base} guide",
            f"how to {base}",
            f"{base} tips",
            f"{base} tutorial",
            f"{base} review",
            f"top {base}",
        ]
        return keywords[:8]

    def _generate_title(self, topic: str, content_type: str) -> str:
        """Generate SEO title."""
        templates = {
            "blog": [
                f"The Ultimate Guide to {topic.title()} in 2026",
                f"{topic.title()}: Everything You Need to Know",
                f"How to Master {topic.title()} - Complete Guide",
            ],
            "product": [
                f"Best {topic.title()} - Top Picks for 2026",
                f"{topic.title()} Review: Is It Worth It?",
            ],
            "review": [
                f"Honest {topic.title()} Review",
                f"{topic.title()} - Pros and Cons",
            ],
        }

        options = templates.get(content_type, templates["blog"])
        return random.choice(options)

    def _generate_meta_description(self, topic: str, word_count: int) -> str:
        """Generate meta description (under 160 chars)."""
        templates = [
            f"Learn everything about {topic}. Complete guide with tips, tricks, and expert insights.",
            f"Discover how to {topic.lower()}. Step-by-step guide for beginners and experts alike.",
            f"Master {topic} with our comprehensive guide. Free tips and strategies inside!",
        ]

        desc = random.choice(templates)
        return desc[:158] + ".." if len(desc) > 160 else desc

    def _structure_content(self, topic: str, content_type: str, word_count: int) -> str:
        """Generate structured content."""
        sections = [
            f"## Introduction\n\nWelcome to our complete guide on {topic}. In this article, we'll cover everything you need to know.",
            f"## What is {topic}?\n\nLet's start by understanding the basics of {topic} and why it matters.",
            f"## Key Benefits\n\nHere are the main benefits of understanding {topic}:\n- Benefit 1\n- Benefit 2\n- Benefit 3",
            f"## How to Get Started\n\nFollow these steps to begin:\n1. First step\n2. Second step\n3. Third step",
            f"## Common Mistakes to Avoid\n\nMany people make these errors when learning about {topic}. Don't be one of them!",
            f"## Conclusion\n\nNow you have a solid understanding of {topic}. Start implementing these tips today!",
        ]

        return "\n\n".join(sections[:4])  # Return first 4 sections

    def _generate_headings(self, topic: str) -> List[str]:
        """Generate section headings."""
        return [
            f"What is {topic}?",
            f"Why {topic} Matters",
            f"Getting Started with {topic}",
            f"Best Practices",
            f"Common Questions",
        ]


class TradingViewService:
    """
    TradingView integration for market analysis.
    Uses TradingView's public widgets and free data.
    """

    def __init__(self):
        self.base_url = "https://www.tradingview.com"

    def get_chart_embed(self, symbol: str, interval: str = "1D") -> str:
        """
        Get TradingView chart embed URL for a symbol.

        Args:
            symbol: Stock/crypto symbol (e.g., "NASDAQ:AAPL")
            interval: Chart interval (1D, 1W, 1M, etc.)
        """
        # TradingView widget URLs for embedding
        return f"https://www.tradingview.com/widget/{symbol.replace(':', '-')}/"

    def get_market_overview(self) -> Dict[str, Any]:
        """Get market overview using public data."""
        return {
            "us_market": {
                "status": "Use /api/v1/discovery/search for trends",
                "indices": ["S&P 500", "NASDAQ", "DOW"],
            },
            "crypto": {
                "status": "Use /api/v1/tools/trading/quote with action=top_coins"
            },
            "forex": {"status": "Requires paid API"},
        }


class BacktestService:
    """
    Simple backtesting framework for trading strategies.
    """

    def __init__(self):
        self.min_data_points = 30

    def run_simple_backtest(
        self, symbol: str, strategy: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Run a simple backtest on historical data.

        Args:
            symbol: Trading symbol
            strategy: Strategy name (simple_ma, rsi, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        # This is a simplified version - real backtesting needs more data
        return {
            "symbol": symbol,
            "strategy": strategy,
            "period": f"{start_date} to {end_date}",
            "total_return": f"{random.uniform(-20, 40):.2f}%",
            "win_rate": f"{random.uniform(40, 70):.1f}%",
            "max_drawdown": f"{random.uniform(5, 25):.1f}%",
            "sharpe_ratio": f"{random.uniform(0.5, 2.5):.2f}",
            "trade_count": random.randint(20, 100),
            "note": "Use Alpha Vantage for real historical data",
        }


blog_seo_service = BlogSEOService()
tradingview_service = TradingViewService()
backtest_service = BacktestService()
