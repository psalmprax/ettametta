import logging
from datetime import datetime
from services.trading.service import trading_service
from .models import ContentCandidate

logger = logging.getLogger(__name__)


class TradingScanner:
    """
    Scanner that converts financial market events into content candidates.
    Flags high-volatility events (e.g., >10% moves) as "Viral triggers".
    """

    def __init__(self):
        self.platform = "market_news"

    async def scan_trends(
        self, niche: str, published_after: datetime | None = None
    ) -> list[ContentCandidate]:
        if not trading_service.is_enabled():
            return []

        # Only scan for financial-related niches or if it's a deep scan
        financial_niches = [
            "crypto",
            "finance",
            "stocks",
            "trading",
            "economy",
            "money",
            "bitcoin",
        ]
        if niche.lower() not in financial_niches:
            return []

        candidates = []
        try:
            # Check major tickers based on niche
            tickers = []
            if niche.lower() in ["crypto", "bitcoin"]:
                tickers = ["bitcoin", "ethereum", "solana", "dogecoin"]
            elif niche.lower() in ["finance", "stocks"]:
                tickers = ["NVDA", "TSLA", "AAPL", "MSFT", "GOOGL"]

            for symbol in tickers:
                sentiment_data = await trading_service.get_market_sentiment(symbol)

                # Check for significant moves (>5% for sentiment, >10% for "Viral")
                change = 0
                if "stock_quote" in sentiment_data and sentiment_data[
                    "stock_quote"
                ].get("change_percent"):
                    change = abs(
                        float(
                            sentiment_data["stock_quote"]["change_percent"].replace(
                                "%", ""
                            )
                        )
                    )
                elif "crypto_quote" in sentiment_data:
                    change = abs(sentiment_data["crypto_quote"].get("change_24h", 0))

                if change >= 5:
                    # Create a "Market Alert" candidate
                    viral_score = min(100, 60 + (change * 2))

                    candidates.append(
                        ContentCandidate(
                            id=f"trading-{symbol}-{datetime.now().strftime('%Y%m%d')}",
                            platform=self.platform,
                            source_url=f"https://www.coingecko.com/en/coins/{symbol}"
                            if symbol.islower()
                            else f"https://finance.yahoo.com/quote/{symbol}",
                            creator_name="Market Pulse",
                            title=f"🚨 BREAKING: {symbol.upper()} is up {change}%! Market Shockwave detected.",
                            description=f"{symbol.upper()} is showing massive {sentiment_data.get('sentiment')} momentum with {sentiment_data.get('confidence')} confidence.",
                            thumbnail_url=f"https://avatar.vercel.sh/{symbol}.png",
                            view_count=int(change * 10000),  # Simulated interest
                            like_count=int(change * 500),
                            comment_count=int(change * 100),
                            share_count=int(change * 50),
                            engagement_score=round(change / 10, 2),
                            viral_score=int(viral_score),
                            duration_seconds=0,
                            category="news",
                            niche=niche,
                            metadata={
                                "symbol": symbol,
                                "change_pct": change,
                                "sentiment": sentiment_data.get("sentiment"),
                                "source": "TradingService",
                            },
                        )
                    )

            if candidates:
                logger.info(
                    f"[TradingScanner] Identified {len(candidates)} market signals for niche: {niche}"
                )

        except Exception as e:
            logger.error(f"[TradingScanner] Scan failed: {e}")

        return candidates
