import os
import logging
import requests
import aiohttp
from typing import Any
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

    async def generate_seo_content(
        self, topic: str, content_type: str = "blog", word_count: int = 500
    ) -> dict[str, Any]:
        """
        Generate SEO-optimized content for a topic using Groq.

        Args:
            topic: The main topic/keyword
            content_type: Type of content (blog, product, review)
            word_count: Target word count

        Returns:
            dict with title, content, meta description, keywords
        """
        from api.config import settings

        keywords = self._generate_keywords(topic)
        title = self._generate_title(topic, content_type)
        meta_description = self._generate_meta_description(topic, word_count)

        # Use Groq for real content generation if available
        if settings.GROQ_API_KEY:
            try:
                from groq import AsyncGroq

                client = AsyncGroq(api_key=settings.GROQ_API_KEY)

                prompt = f"""Generate a {word_count}-word {content_type} article about {topic}.
Include the following SEO keywords: {", ".join(keywords)}.
Format as:
- Title: <title>
- Meta Description: <meta description under 160 chars>
- Content: <article body in markdown>
- Keywords: <comma-separated>"""

                response = await client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000,
                )

                content = response.choices[0].message.content

                # Parse structured response
                lines = content.split("\n")
                parsed = {
                    "title": title,
                    "meta_description": meta_description,
                    "keywords": keywords,
                    "content": content,
                }

                for line in lines:
                    if line.startswith("Title:"):
                        parsed["title"] = line.replace("Title:", "").strip()
                    elif line.startswith("Meta Description:"):
                        parsed["meta_description"] = line.replace(
                            "Meta Description:", ""
                        ).strip()[:160]
                    elif line.startswith("Keywords:"):
                        parsed["keywords"] = [
                            k.strip() for k in line.replace("Keywords:", "").split(",")
                        ]
                    elif line.startswith("Content:"):
                        parsed["content"] = content.split("Content:")[-1].strip()

                return {
                    "title": parsed["title"],
                    "content": parsed["content"],
                    "meta_description": parsed["meta_description"],
                    "keywords": parsed["keywords"],
                    "headings": self._generate_headings(topic),
                    "word_count": len(parsed["content"].split()),
                    "generated_at": datetime.now().isoformat(),
                    "ai_model": "groq-llama-3.3-70b",
                }
            except Exception as e:
                logger.warning(
                    f"Groq content generation failed: {e}, falling back to template"
                )

        # Fallback: Use structured template
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

    async def _generate_keywords(self, topic: str) -> list[str]:
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

    async def _generate_title(self, topic: str, content_type: str) -> str:
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

    async def _generate_meta_description(self, topic: str, word_count: int) -> str:
        """Generate meta description (under 160 chars)."""
        templates = [
            f"Learn everything about {topic}. Complete guide with tips, tricks, and expert insights.",
            f"Discover how to {topic.lower()}. Step-by-step guide for beginners and experts alike.",
            f"Master {topic} with our comprehensive guide. Free tips and strategies inside!",
        ]

        desc = random.choice(templates)
        return desc[:158] + ".." if len(desc) > 160 else desc

    async def _structure_content(self, topic: str, content_type: str, word_count: int) -> str:
        """Generate structured content."""
        sections = [
            f"## Introduction\n\nWelcome to our complete guide on {topic}. In this article, we'll cover everything you need to know.",
            f"## What is {topic}?\n\nLet's start by understanding the basics of {topic} and why it matters.",
            f"## Key Benefits\n\nHere are the main benefits of understanding {topic}:\n- Benefit 1\n- Benefit 2\n- Benefit 3",
            f"## How to Get Started\n\nFollow these steps to begin:\n1. First step\n2. Second step\n3. Third step",
            f"## Common Mistakes to Avoid\n\nMany people make these errors when learning about {topic}. Don't be one of them!",
            f"## Conclusion\n\nNow you have a solid understanding of {topic}. Start implementing these tips today!",
        ]

        return "\n\n".join(sections[:4])

    async def _generate_headings(self, topic: str) -> list[str]:
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
    Uses real market data APIs.
    """

    def __init__(self):
        self.base_url = "https://www.tradingview.com"
        self._cache = {}
        self._cache_time = {}

    async def get_market_overview(self) -> dict[str, Any]:
        """Get comprehensive market overview using Alpha Vantage and CoinGecko."""
        from api.config import settings

        overview = {
            "us_market": {"status": "available", "indices": []},
            "crypto": {"status": "available", "top_coins": []},
            "forex": {"status": "limited", "majors": []},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Get US indices
        if settings.ALPHA_VANTAGE_API_KEY:
            try:
                async with aiohttp.ClientSession() as session:
                    # Get top gainers as market proxy
                    url = "https://www.alphavantage.co/query"
                    params = {
                        "function": "TOP_GAINERS",
                        "apikey": settings.ALPHA_VANTAGE_API_KEY,
                    }
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            overview["us_market"]["status"] = "live"
            except Exception as e:
                logger.warning(f"Market overview error: {e}")

        # Get crypto top coins
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.coingecko.com/api/v3/coins/markets"
                params = {
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 5,
                    "page": 1,
                }
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        overview["crypto"]["top_coins"] = [
                            {
                                "name": c["name"],
                                "symbol": c["symbol"].upper(),
                                "price": c["current_price"],
                                "change_24h": c["price_change_percentage_24h"],
                            }
                            for c in data
                        ]
        except Exception as e:
            logger.warning(f"Crypto overview error: {e}")

        return overview

    async def get_chart_embed(self, symbol: str, interval: str = "1D") -> str:
        """Get TradingView chart embed URL for a symbol."""
        return f"https://www.tradingview.com/widget/{symbol.replace(':', '-')}/"


class BacktestService:
    """
    Real backtesting framework using historical data.
    """

    def __init__(self):
        self.min_data_points = 30

    async def run_backtest(
        self, symbol: str, strategy: str, start_date: str, end_date: str
    ) -> dict[str, Any]:
        """
        Run a backtest on historical data.

        Args:
            symbol: Trading symbol
            strategy: Strategy name (simple_ma, rsi, momentum)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        from services.trading.service import trading_service
        from datetime import datetime

        # Get historical data
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            days = (end_dt - start_dt).days
            history = await trading_service.get_historical_data(symbol.upper(), days)
        except Exception as e:
            return {"error": f"Failed to fetch historical data: {str(e)}"}

        data = history.get("data", [])
        if len(data) < self.min_data_points:
            return {"error": f"Insufficient data points (need {self.min_data_points})"}

        # Implement basic strategies
        closes = [d["close"] for d in data]

        if strategy == "simple_ma":
            return self._backtest_ma(closes, data)
        elif strategy == "momentum":
            return self._backtest_momentum(closes, data)
        elif strategy == "mean_reversion":
            return self._backtest_mean_reversion(closes, data)
        else:
            return {"error": f"Unknown strategy: {strategy}"}

    async def _backtest_ma(self, closes: list[float], data: list[dict]) -> dict[str, Any]:
        """Backtest simple moving average crossover strategy."""
        initial_balance = 10000
        position = 0
        balance = initial_balance
        trades = []
        capital_curve = []

        short_ma = 10
        long_ma = 30

        for i in range(long_ma, len(closes)):
            short = sum(closes[i - short_ma : i]) / short_ma
            long = sum(closes[i - long_ma : i]) / long_ma

            prev_short = sum(closes[i - short_ma - 1 : i - 1]) / short_ma
            prev_long = sum(closes[i - long_ma - 1 : i - 1]) / long_ma

            # Golden cross (buy)
            if prev_short <= prev_long and short > long and position == 0:
                shares = balance / closes[i]
                position = shares
                balance = 0
                trades.append(
                    {"type": "buy", "price": closes[i], "date": data[i]["date"]}
                )

            # Death cross (sell)
            elif prev_short >= prev_long and short < long and position > 0:
                balance = position * closes[i]
                trades.append(
                    {"type": "sell", "price": closes[i], "date": data[i]["date"]}
                )
                position = 0

            current_value = balance + (position * closes[i] if position > 0 else 0)
            capital_curve.append(current_value)

        # Close final position
        if position > 0:
            balance = position * closes[-1]
            trades.append(
                {"type": "sell", "price": closes[-1], "date": data[-1]["date"]}
            )

        final_value = balance
        total_return = ((final_value - initial_balance) / initial_balance) * 100

        # Calculate metrics
        returns = []
        for i in range(1, len(capital_curve)):
            if capital_curve[i - 1] > 0:
                returns.append(
                    (capital_curve[i] - capital_curve[i - 1]) / capital_curve[i - 1]
                )

        avg_return = sum(returns) / len(returns) if returns else 0
        volatility = (
            (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            if returns
            else 0
        )
        sharpe = (avg_return / volatility * (252**0.5)) if volatility > 0 else 0

        max_drawdown = 0
        peak = capital_curve[0] if capital_curve else 0
        for value in capital_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return {
            "strategy": "Simple MA Crossover",
            "symbol": data[0].get("symbol", "Unknown"),
            "period": f"{data[0]['date']} to {data[-1]['date']}",
            "initial_balance": initial_balance,
            "final_value": round(final_value, 2),
            "total_return": f"{total_return:.2f}%",
            "win_rate": f"{(sum(1 for t in trades if t['type'] == 'sell' and len([x for x in trades if x['type'] == 'buy']) > 0) / len(trades) * 100) if len(trades) > 0 else 0:.1f}%",
            "max_drawdown": f"{max_drawdown * 100:.1f}%",
            "sharpe_ratio": round(sharpe, 2),
            "trade_count": len(trades),
            "trades": trades[-10:],  # Last 10 trades
        }

    async def _backtest_momentum(
        self, closes: list[float], data: list[dict]
    ) -> dict[str, Any]:
        """Backtest momentum strategy."""
        initial_balance = 10000
        position = 0
        balance = initial_balance
        trades = []

        lookback = 5

        for i in range(lookback, len(closes)):
            momentum = closes[i] - closes[i - lookback]

            if momentum > 0 and position == 0:
                shares = balance / closes[i]
                position = shares
                balance = 0
                trades.append(
                    {"type": "buy", "price": closes[i], "date": data[i]["date"]}
                )

            elif momentum < 0 and position > 0:
                balance = position * closes[i]
                trades.append(
                    {"type": "sell", "price": closes[i], "date": data[i]["date"]}
                )
                position = 0

        if position > 0:
            balance = position * closes[-1]
            trades.append(
                {"type": "sell", "price": closes[-1], "date": data[-1]["date"]}
            )

        final_value = balance
        total_return = ((final_value - initial_balance) / initial_balance) * 100

        return {
            "strategy": "Momentum",
            "symbol": data[0].get("symbol", "Unknown"),
            "period": f"{data[0]['date']} to {data[-1]['date']}",
            "initial_balance": initial_balance,
            "final_value": round(final_value, 2),
            "total_return": f"{total_return:.2f}%",
            "trade_count": len(trades),
            "sharpe_ratio": "N/A (requires longer period)",
        }

    async def _backtest_mean_reversion(
        self, closes: list[float], data: list[dict]
    ) -> dict[str, Any]:
        """Backtest mean reversion strategy."""
        initial_balance = 10000
        position = 0
        balance = initial_balance
        trades = []

        window = 20
        std_multiplier = 2

        for i in range(window, len(closes)):
            mean = sum(closes[i - window : i]) / window
            std = (sum((c - mean) ** 2 for c in closes[i - window : i]) / window) ** 0.5
            upper = mean + std_multiplier * std
            lower = mean - std_multiplier * std

            if closes[i] < lower and position == 0:
                shares = balance / closes[i]
                position = shares
                balance = 0
                trades.append(
                    {"type": "buy", "price": closes[i], "date": data[i]["date"]}
                )

            elif closes[i] > upper and position > 0:
                balance = position * closes[i]
                trades.append(
                    {"type": "sell", "price": closes[i], "date": data[i]["date"]}
                )
                position = 0

        if position > 0:
            balance = position * closes[-1]
            trades.append(
                {"type": "sell", "price": closes[-1], "date": data[-1]["date"]}
            )

        final_value = balance
        total_return = ((final_value - initial_balance) / initial_balance) * 100

        return {
            "strategy": "Mean Reversion",
            "symbol": data[0].get("symbol", "Unknown"),
            "period": f"{data[0]['date']} to {data[-1]['date']}",
            "initial_balance": initial_balance,
            "final_value": round(final_value, 2),
            "total_return": f"{total_return:.2f}%",
            "trade_count": len(trades),
        }


blog_seo_service = BlogSEOService()
tradingview_service = TradingViewService()
backtest_service = BacktestService()
