"""
Trading Service - Optional trading API integration
==================================================
Disabled by default. Enable with: ENABLE_TRADING=true

This service provides market analysis and trading automation:
- Alpha Vantage (stocks, forex)
- CoinGecko (cryptocurrency)
- Portfolio tracking and history
- Market sentiment analysis
- Real-time price alerts
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)


class TradingService:
    """
    Optional trading API integration.

    Disabled by default - set ENABLE_TRADING=true to enable.
    Supports Alpha Vantage and CoinGecko APIs.
    """

    def __init__(self):
        self.enabled = os.getenv("ENABLE_TRADING", "false").lower() == "true"

        from api.config import settings

        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.coingecko_key = settings.COINGECKO_API_KEY

        # In-memory portfolio (in production, use database)
        self._portfolio_cache: Dict[int, Dict[str, Any]] = {}
        self._price_alerts: Dict[int, List[Dict]] = {}

        if not self.enabled:
            logger.info("Trading service is disabled (ENABLE_TRADING=false)")
            return

        has_api = any([self.alpha_vantage_key, self.coingecko_key])

        if not has_api:
            logger.warning(
                "No trading API keys configured. Service enabled but may not work."
            )

        logger.info("Trading service initialized")

    def is_enabled(self) -> bool:
        """Check if service is enabled."""
        return self.enabled

    def get_portfolio(self, user_id: int) -> Dict[str, Any]:
        """Get user's portfolio holdings."""
        if user_id not in self._portfolio_cache:
            self._portfolio_cache[user_id] = {
                "holdings": [],
                "cash": 10000.0,  # Default starting balance
                "total_value": 10000.0,
                "last_updated": datetime.utcnow().isoformat(),
            }
        return self._portfolio_cache[user_id]

    def add_position(
        self,
        user_id: int,
        symbol: str,
        quantity: float,
        price: float,
        position_type: str = "buy",
    ) -> Dict[str, Any]:
        """Add a position to user's portfolio."""
        portfolio = self.get_portfolio(user_id)

        # Update cash
        cost = quantity * price
        if position_type == "buy":
            if cost > portfolio["cash"]:
                return {"error": "Insufficient funds"}
            portfolio["cash"] -= cost

            # Add or update holding
            found = False
            for holding in portfolio["holdings"]:
                if holding["symbol"] == symbol:
                    new_qty = holding["quantity"] + quantity
                    holding["quantity"] = new_qty
                    holding["avg_price"] = (
                        holding["avg_price"] * holding["quantity"] + price * quantity
                    ) / new_qty
                    found = True
                    break

            if not found:
                portfolio["holdings"].append(
                    {
                        "symbol": symbol,
                        "quantity": quantity,
                        "avg_price": price,
                        "purchase_date": datetime.utcnow().isoformat(),
                    }
                )
        else:  # sell
            for holding in portfolio["holdings"]:
                if holding["symbol"] == symbol:
                    if holding["quantity"] < quantity:
                        return {"error": "Insufficient holdings"}
                    holding["quantity"] -= quantity
                    portfolio["cash"] += cost

                    # Remove if fully sold
                    if holding["quantity"] <= 0:
                        portfolio["holdings"].remove(holding)
                    break

        portfolio["last_updated"] = datetime.utcnow().isoformat()
        self._portfolio_cache[user_id] = portfolio

        return {"status": "success", "portfolio": portfolio}

    def get_portfolio_value(self, user_id: int) -> Dict[str, Any]:
        """Calculate total portfolio value with current market prices."""
        import asyncio

        portfolio = self.get_portfolio(user_id)

        total_holdings_value = 0.0
        holdings_value = []

        for holding in portfolio["holdings"]:
            symbol = holding["symbol"]

            # Get current price asynchronously
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Determine if stock or crypto
            if (
                symbol.islower()
                or symbol.startswith("bitcoin")
                or symbol.startswith("ethereum")
            ):
                price_data = loop.run_until_complete(self.get_crypto_quote(symbol))
            else:
                price_data = loop.run_until_complete(self.get_stock_quote(symbol))

            current_price = (
                price_data.get("price", holding["avg_price"])
                if price_data
                else holding["avg_price"]
            )
            value = current_price * holding["quantity"]
            total_holdings_value += value

            holdings_value.append(
                {
                    "symbol": holding["symbol"],
                    "quantity": holding["quantity"],
                    "avg_price": holding["avg_price"],
                    "current_price": current_price,
                    "value": value,
                    "gain_loss": value - (holding["avg_price"] * holding["quantity"]),
                    "gain_loss_pct": (
                        (current_price - holding["avg_price"])
                        / holding["avg_price"]
                        * 100
                    )
                    if holding["avg_price"] > 0
                    else 0,
                }
            )

        return {
            "cash": portfolio["cash"],
            "holdings_value": total_holdings_value,
            "total_value": portfolio["cash"] + total_holdings_value,
            "holdings": holdings_value,
            "updated_at": datetime.utcnow().isoformat(),
        }

    def add_price_alert(
        self, user_id: int, symbol: str, target_price: float, condition: str = "above"
    ) -> Dict[str, Any]:
        """Add a price alert for a symbol."""
        if user_id not in self._price_alerts:
            self._price_alerts[user_id] = []

        alert = {
            "id": len(self._price_alerts[user_id]) + 1,
            "symbol": symbol.upper(),
            "target_price": target_price,
            "condition": condition,  # above, below
            "created_at": datetime.utcnow().isoformat(),
            "triggered": False,
        }

        self._price_alerts[user_id].append(alert)

        return {"status": "success", "alert": alert}

    def check_price_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """Check and return triggered price alerts."""
        triggered = []

        if user_id not in self._price_alerts:
            return triggered

        for alert in self._price_alerts[user_id]:
            if alert["triggered"]:
                continue

            symbol = alert["symbol"]

            # Get current price
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if symbol.islower():
                price_data = loop.run_until_complete(self.get_crypto_quote(symbol))
            else:
                price_data = loop.run_until_complete(self.get_stock_quote(symbol))

            current_price = price_data.get("price") if price_data else None

            if current_price:
                if (
                    alert["condition"] == "above"
                    and current_price >= alert["target_price"]
                ):
                    alert["triggered"] = True
                    alert["triggered_at"] = datetime.utcnow().isoformat()
                    alert["current_price"] = current_price
                    triggered.append(alert)
                elif (
                    alert["condition"] == "below"
                    and current_price <= alert["target_price"]
                ):
                    alert["triggered"] = True
                    alert["triggered_at"] = datetime.utcnow().isoformat()
                    alert["current_price"] = current_price
                    triggered.append(alert)

        return triggered

    def get_price_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all price alerts for user."""
        return self._price_alerts.get(user_id, [])

    async def get_historical_data(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Get historical price data for a symbol."""
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")

        # Try Alpha Vantage first
        if self.alpha_vantage_key and symbol.isupper():
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    "function": "TIME_SERIES_DAILY",
                    "symbol": symbol,
                    "apikey": self.alpha_vantage_key,
                    "outputsize": "compact",
                }

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as resp:
                        data = await resp.json()

                        if "Time Series (Daily)" in data:
                            time_series = data["Time Series (Daily)"]
                            dates = sorted(time_series.keys(), reverse=True)[:days]

                            return {
                                "symbol": symbol,
                                "data": [
                                    {
                                        "date": date,
                                        "open": float(time_series[date]["1. open"]),
                                        "high": float(time_series[date]["2. high"]),
                                        "low": float(time_series[date]["3. low"]),
                                        "close": float(time_series[date]["4. close"]),
                                        "volume": int(time_series[date]["5. volume"]),
                                    }
                                    for date in dates
                                ],
                                "source": "alphavantage",
                            }
            except Exception as e:
                logger.warning(f"Alpha Vantage historical data error: {e}")

        # Fallback: use recent CoinGecko data
        if symbol.islower():
            try:
                url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
                params = {"vs_currency": "usd", "days": days}

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as resp:
                        data = await resp.json()

                        if "prices" in data:
                            return {
                                "symbol": symbol,
                                "data": [
                                    {
                                        "date": datetime.fromtimestamp(
                                            p[0] / 1000
                                        ).isoformat(),
                                        "close": p[1],
                                        "volume": data.get(
                                            "total_volumes", [[p[0], 0]]
                                        )[i][1]
                                        if i < len(data.get("total_volumes", []))
                                        else 0,
                                    }
                                    for i, p in enumerate(data["prices"])
                                ],
                                "source": "coingecko",
                            }
            except Exception as e:
                logger.warning(f"CoinGecko historical data error: {e}")

        return {"symbol": symbol, "data": [], "error": "No historical data available"}

    async def get_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """Calculate basic technical indicators for a symbol."""
        history = await self.get_historical_data(symbol, days=50)

        if not history.get("data"):
            return {"error": "Insufficient data for technical analysis"}

        prices = [d["close"] for d in history["data"]]

        # Simple Moving Averages
        sma_20 = sum(prices[:20]) / 20 if len(prices) >= 20 else None
        sma_50 = sum(prices[:50]) / 50 if len(prices) >= 50 else None

        # RSI (14-period)
        gains = []
        losses = []
        for i in range(1, min(15, len(prices))):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 0
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))

        # Current price
        current_price = prices[0] if prices else 0

        return {
            "symbol": symbol,
            "current_price": current_price,
            "sma_20": round(sma_20, 2) if sma_20 else None,
            "sma_50": round(sma_50, 2) if sma_50 else None,
            "rsi": round(rsi, 2),
            "trend": "bullish"
            if sma_20 and sma_50 and sma_20 > sma_50
            else "bearish"
            if sma_50
            else "neutral",
            "analysis": self._generate_technical_analysis(
                sma_20, sma_50, rsi, current_price
            ),
        }

    def _generate_technical_analysis(
        self, sma_20: float, sma_50: float, rsi: float, current_price: float
    ) -> str:
        """Generate a text analysis based on technical indicators."""
        signals = []

        if sma_20 and sma_50:
            if sma_20 > sma_50:
                signals.append("Uptrend (SMA bullish crossover)")
            else:
                signals.append("Downtrend (SMA bearish crossover)")

        if rsi > 70:
            signals.append("Overbought (RSI)")
        elif rsi < 30:
            signals.append("Oversold (RSI)")
        else:
            signals.append("Neutral momentum")

        return f"{' | '.join(signals)}" if signals else "Insufficient data"

    async def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time stock quote.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, GOOGL)

        Returns:
            Dict with price, change, volume, etc.
        """
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")

        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return {}

        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()

                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        return {
                            "symbol": quote.get("01. symbol"),
                            "price": float(quote.get("05. price", 0)),
                            "change": float(quote.get("09. change", 0)),
                            "change_percent": quote.get("10. change percent", "0%"),
                            "volume": int(quote.get("06. volume", 0)),
                            "timestamp": datetime.utcnow().isoformat(),
                        }

                    return {}

        except Exception as e:
            logger.error(f"Alpha Vantage API error: {e}")
            return {}

    async def get_crypto_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get cryptocurrency quote.

        Args:
            symbol: Crypto symbol (e.g., bitcoin, ethereum)

        Returns:
            Dict with price, market cap, etc.
        """
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")

        if not self.coingecko_key:
            logger.warning("CoinGecko API key not configured")
            return {}

        try:
            # CoinGecko free API (no key needed for basic)
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": symbol,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_market_cap": "true",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()

                    if symbol in data:
                        quote = data[symbol]
                        return {
                            "symbol": symbol,
                            "price": quote.get("usd", 0),
                            "change_24h": quote.get("usd_24h_change", 0),
                            "market_cap": quote.get("usd_market_cap", 0),
                            "timestamp": datetime.utcnow().isoformat(),
                        }

                    return {}

        except Exception as e:
            logger.error(f"CoinGecko API error: {e}")
            return {}

    async def get_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Get market sentiment for symbol.

        Args:
            symbol: Stock or crypto symbol

        Returns:
            Dict with sentiment analysis
        """
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")

        # Try both stock and crypto
        stock_quote = await self.get_stock_quote(symbol.upper())
        crypto_quote = await self.get_crypto_quote(symbol.lower())

        sentiment = "neutral"
        confidence = 0.5

        if stock_quote.get("change_percent"):
            change = float(stock_quote["change_percent"].replace("%", ""))
            if change > 2:
                sentiment = "bullish"
                confidence = min(0.9, 0.5 + abs(change) / 20)
            elif change < -2:
                sentiment = "bearish"
                confidence = min(0.9, 0.5 + abs(change) / 20)

        if crypto_quote:
            change = crypto_quote.get("change_24h", 0)
            if change > 5:
                sentiment = "bullish"
                confidence = min(0.9, 0.5 + abs(change) / 25)
            elif change < -5:
                sentiment = "bearish"
                confidence = min(0.9, 0.5 + abs(change) / 25)

        return {
            "symbol": symbol,
            "sentiment": sentiment,
            "confidence": confidence,
            "stock_quote": stock_quote,
            "crypto_quote": crypto_quote,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def analyze_trends(self, niche: str) -> Dict[str, Any]:
        """
        Analyze market trends related to a niche.

        Args:
            niche: Topic/niche to analyze

        Returns:
            Dict with trend analysis
        """
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")

        # Map common niches to stock symbols
        niche_map = {
            "tech": ["AAPL", "GOOGL", "MSFT", "NVDA"],
            "crypto": ["bitcoin", "ethereum", "solana"],
            "gaming": ["NTDOY", "EA", "ATVI"],
            "ai": ["NVDA", "MSFT", "GOOGL"],
            "finance": ["JPM", "GS", "V"],
            "energy": ["XOM", "CVX", "TSLA"],
        }

        symbols = niche_map.get(niche.lower(), [])

        results = {"niche": niche, "analyzed": [], "overall_sentiment": "neutral"}

        bullish_count = 0
        bearish_count = 0

        for symbol in symbols:
            # Try as stock first, then crypto
            if symbol.isupper():
                quote = await self.get_stock_quote(symbol)
            else:
                quote = await self.get_crypto_quote(symbol)

            if quote:
                sentiment_data = await self.get_market_sentiment(symbol)
                sentiment = sentiment_data.get("sentiment", "neutral")

                if sentiment == "bullish":
                    bullish_count += 1
                elif sentiment == "bearish":
                    bearish_count += 1

                results["analyzed"].append(
                    {
                        "symbol": symbol,
                        "sentiment": sentiment,
                        "price": quote.get("price") or quote.get("price", 0),
                    }
                )

        # Calculate overall
        total = bullish_count + bearish_count
        if total > 0:
            if bullish_count > bearish_count:
                results["overall_sentiment"] = "bullish"
            elif bearish_count > bullish_count:
                results["overall_sentiment"] = "bearish"

        results["timestamp"] = datetime.utcnow().isoformat()

        return results

    async def get_trending_tickers(self) -> List[Dict[str, Any]]:
        """
        Get trending market tickers.

        Returns:
            List of trending symbols with sentiment
        """
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")

        # Common trending tickers
        trending = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "META", "AMZN"]

        results = []

        for symbol in trending[:5]:  # Limit to 5
            quote = await self.get_stock_quote(symbol)
            if quote:
                results.append(quote)

        return results


# Singleton instance
trading_service = TradingService()
