import os
import logging
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
COINGECKO_KEY = os.getenv("COINGECKO_API_KEY", "")


class TradingService:
    """
    Trading and market data integration.
    Uses Alpha Vantage for stocks/forex and CoinGecko for crypto.
    Optional - requires API keys for full functionality.
    """

    def __init__(self):
        self.alpha_key = ALPHA_VANTAGE_KEY
        self.coingecko_key = COINGECKO_KEY

    def get_stock_quote(self, symbol: str) -> str:
        """Get stock quote from Alpha Vantage."""
        if not self.alpha_key:
            return "Alpha Vantage API key not configured. Set ALPHA_VANTAGE_API_KEY"

        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_key,
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            quote = data.get("Global Quote", {})
            if quote:
                price = quote.get("05. price", "N/A")
                change = quote.get("09. change", "N/A")
                return f"📈 {symbol}: ${price} ({change})"
            return f"No data for {symbol}"
        except Exception as e:
            logger.error(f"Error fetching stock quote: {e}")
            return f"Error: {str(e)}"

    def get_crypto_price(self, coin_id: str) -> str:
        """Get crypto price from CoinGecko (free, no key needed)."""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            }
            if self.coingecko_key:
                params["x_cg_demo_api_key"] = self.coingecko_key

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if coin_id in data:
                price = data[coin_id].get("usd", 0)
                change = data[coin_id].get("usd_24h_change", 0)
                return f"₿ {coin_id}: ${price:,.2f} (24h: {change:+.2f}%)"
            return f"No data for {coin_id}"
        except Exception as e:
            logger.error(f"Error fetching crypto price: {e}")
            return f"Error: {str(e)}"

    def get_market_sentiment(self, symbol: str) -> str:
        """Get market sentiment for a symbol."""
        if not self.alpha_key:
            return "Alpha Vantage API key not configured"

        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": symbol,
                "apikey": self.alpha_key,
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            feed = data.get("feed", [])
            if feed:
                sentiment = feed[0].get("overall_sentiment_score", "N/A")
                return f"📊 Sentiment for {symbol}: {sentiment}"
            return f"No news for {symbol}"
        except Exception as e:
            logger.error(f"Error fetching sentiment: {e}")
            return f"Error: {str(e)}"

    def get_top_coins(self, limit: int = 10) -> str:
        """Get top cryptocurrencies by market cap."""
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "sparkline": "false",
            }
            if self.coingecko_key:
                params["x_cg_demo_api_key"] = self.coingecko_key

            response = requests.get(url, params=params, timeout=10)
            coins = response.json()

            result = "🔥 **Top Cryptocurrencies:**\n"
            for coin in coins:
                name = coin.get("name", "N/A")
                symbol = coin.get("symbol", "N/A").upper()
                price = coin.get("current_price", 0)
                change = coin.get("price_change_percentage_24h", 0)
                result += f"{name} ({symbol}): ${price:,.2f} ({change:+.2f}%)\n"

            return result
        except Exception as e:
            logger.error(f"Error fetching top coins: {e}")
            return f"Error: {str(e)}"

    def get_trending_searches(self) -> str:
        """Get trending stock searches from Alpha Vantage."""
        if not self.alpha_key:
            return "Alpha Vantage API key not configured"

        try:
            url = "https://www.alphavantage.co/query"
            params = {"function": "REALTIME_INTRADAY_SYMBOLS", "apikey": self.alpha_key}
            response = requests.get(url, params=params, timeout=10)
            return "Trending data unavailable"
        except Exception as e:
            logger.error(f"Error fetching trending: {e}")
            return f"Error: {str(e)}"


class MarketAnalysisService:
    """
    Market analysis for trend-based content creation.
    """

    @staticmethod
    def analyze_niche_market(niche: str) -> Dict[str, Any]:
        """Analyze market conditions for a niche."""
        return {
            "niche": niche,
            "timestamp": datetime.now().isoformat(),
            "trends": "Use /api/v1/discovery/search for trends",
            "monetization_potential": "Use /api/v1/monetization/recommend-links",
            "competition": "Use /api/v1/discovery/trends to analyze",
        }

    @staticmethod
    def get_content_opportunities() -> List[Dict]:
        """Get content opportunities based on market data."""
        return [
            {
                "type": "crypto",
                "opportunity": "Crypto price updates",
                "api": "/api/v1/tools/metrics (CoinGecko)",
            },
            {
                "type": "stocks",
                "opportunity": "Stock market updates",
                "api": "Alpha Vantage (requires key)",
            },
            {
                "type": "trending",
                "opportunity": "Viral trends",
                "api": "/api/v1/discovery/search",
            },
        ]


trading_service = TradingService()
market_analysis = MarketAnalysisService()
