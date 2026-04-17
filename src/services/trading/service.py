"""
Trading Service - Any trading API integration
==================================================
Disabled by default. Enable with: ENABLE_TRADING=true

This service provides market analysis and trading automation:
- Alpha Vantage (stocks, forex)
- CoinGecko (cryptocurrency)
- Portfolio tracking with database persistence
- Market sentiment analysis
- Real-time price alerts with technical indicators
"""

import logging
import asyncio
import aiohttp
import time
from datetime import datetime
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.api.utils.database import async_session_factory
from src.api.utils.models import (
    TradingPortfolioDB,
    TradingPositionDB,
    TradingAlertDB,
    TradingTransactionDB,
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


# Rate limiting for external APIs
class RateLimiter:
    def __init__(self, max_calls: int, period_seconds: int):
        self._max_calls = max_calls
        self._period = period_seconds
        self._calls: list[datetime] = []

    def acquire(self) -> bool:
        now = datetime.utcnow()
        self._calls = [
            t for t in self._calls if (now - t).total_seconds() < self._period
        ]
        if len(self._calls) < self._max_calls:
            self._calls.append(now)
            return True
        return False

    def wait_time(self) -> float:
        if not self._calls:
            return 0.0
        now = datetime.utcnow()
        oldest = min(self._calls)
        return max(0.0, self._period - (now - oldest).total_seconds())


class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures"""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 120):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


alpha_vantage_limiter = RateLimiter(max_calls=5, period_seconds=60)
coingecko_limiter = RateLimiter(max_calls=10, period_seconds=60)
alpha_vantage_circuit_breaker = CircuitBreaker()
coingecko_circuit_breaker = CircuitBreaker()


class TradingService:
    """
    Any trading API integration with database persistence.

    Disabled by default - set ENABLE_TRADING=true to enable.
    Supports Alpha Vantage and CoinGecko APIs.
    """

    def __init__(self):
        from src.api.config import settings

        self.enabled = settings.ENABLE_TRADING
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.coingecko_key = settings.COINGECKO_API_KEY

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
        return self.enabled

    async def _get_or_create_portfolio(
        self, db: AsyncSession, user_id: int
    ) -> TradingPortfolioDB:
        stmt = select(TradingPortfolioDB).where(TradingPortfolioDB.user_id == user_id)
        result = await db.execute(stmt)
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            # Hardened: No simulated 10k wealth. Balance starts at 0.0 unless configured.
            from src.api.config import settings

            initial_balance = getattr(settings, "TRADING_INITIAL_BALANCE", 0.0)
            portfolio = TradingPortfolioDB(
                user_id=user_id, cash_balance=initial_balance
            )
            db.add(portfolio)
            await db.commit()
            await db.refresh(portfolio)
        return portfolio

    async def get_portfolio(self, user_id: int) -> dict[str, Any]:
        async with async_session_factory() as db:
            portfolio = await self._get_or_create_portfolio(db, user_id)
            # Use scalar() to extract values from ORM objects
            portfolio_id = portfolio.id
            cash = (
                float(portfolio.cash_balance)
                if portfolio.cash_balance is not None
                else 0.0
            )

            stmt = select(TradingPositionDB).where(
                TradingPositionDB.portfolio_id == portfolio_id
            )
            result = await db.execute(stmt)
            positions = result.scalars().all()

            return {
                "id": portfolio_id,
                "user_id": user_id,
                "cash": cash,
                "holdings": [
                    {
                        "symbol": str(p.symbol),
                        "quantity": float(p.quantity) if p.quantity else 0.0,
                        "avg_price": float(p.avg_price) if p.avg_price else 0.0,
                        "type": str(p.position_type or "buy"),
                        "opened_at": p.opened_at.isoformat() if p.opened_at else None,
                    }
                    for p in positions
                ],
                "updated_at": portfolio.updated_at.isoformat()
                if portfolio.updated_at
                else None,
            }

    async def add_position(
        self,
        user_id: int,
        symbol: str,
        quantity: float,
        price: float,
        position_type: str = "buy",
    ) -> dict[str, Any]:
        async with async_session_factory() as db:
            try:
                portfolio = await self._get_or_create_portfolio(db, user_id)
                cost = quantity * price

                if position_type == "buy":
                    if cost > portfolio.cash_balance:
                        return {
                            "error": "Insufficient funds",
                            "required": cost,
                            "available": portfolio.cash_balance,
                        }

                    portfolio.cash_balance -= cost
                else:  # sell
                    stmt = select(TradingPositionDB).where(
                        TradingPositionDB.portfolio_id == portfolio.id,
                        TradingPositionDB.symbol == symbol.upper(),
                    )
                    result = await db.execute(stmt)
                    positions = result.scalars().all()

                    total_qty = sum(p.quantity for p in positions)
                    if total_qty < quantity:
                        return {
                            "error": "Insufficient holdings",
                            "required": quantity,
                            "available": total_qty,
                        }
                    portfolio.cash_balance += cost

                # Update or create position
                stmt_existing = select(TradingPositionDB).where(
                    TradingPositionDB.portfolio_id == portfolio.id,
                    TradingPositionDB.symbol == symbol.upper(),
                )
                result_existing = await db.execute(stmt_existing)
                existing = result_existing.scalar_one_or_none()

                if existing:
                    if position_type == "buy":
                        new_qty = existing.quantity + quantity
                        existing.avg_price = (
                            existing.avg_price * existing.quantity + price * quantity
                        ) / new_qty
                        existing.quantity = new_qty
                    else:
                        existing.quantity -= quantity
                        if existing.quantity <= 0:
                            await db.delete(existing)
                else:
                    new_position = TradingPositionDB(
                        portfolio_id=portfolio.id,
                        symbol=symbol.upper(),
                        quantity=quantity,
                        avg_price=price,
                        position_type=position_type,
                    )
                    db.add(new_position)

                # Record transaction
                transaction = TradingTransactionDB(
                    portfolio_id=portfolio.id,
                    symbol=symbol.upper(),
                    quantity=quantity,
                    price=price,
                    transaction_type=position_type,
                    total_value=cost,
                )
                db.add(transaction)

                portfolio.updated_at = datetime.utcnow()
                await db.commit()

                return {
                    "status": "success",
                    "portfolio": await self.get_portfolio(user_id),
                }
            except Exception as e:
                await db.rollback()
                logger.error(f"Error adding position: {e}")
                return {"error": str(e)}

    async def get_portfolio_value(self, user_id: int) -> dict[str, Any]:
        async with async_session_factory() as db:
            portfolio = await self._get_or_create_portfolio(db, user_id)
            stmt = select(TradingPositionDB).where(
                TradingPositionDB.portfolio_id == portfolio.id
            )
            result = await db.execute(stmt)
            positions = result.scalars().all()

            total_holdings_value = 0.0
            holdings_value = []

            for holding in positions:
                symbol = holding.symbol
                is_crypto = symbol.islower() or symbol.startswith("bitcoin")

                try:
                    if is_crypto:
                        price_data = await self.get_crypto_quote(symbol)
                    else:
                        price_data = await self.get_stock_quote(symbol)
                except Exception as e:
                    logger.warning(f"Error fetching price for {symbol}: {e}")
                    price_data = {}

                current_price = price_data.get("price", holding.avg_price)
                value = current_price * holding.quantity
                total_holdings_value += value

                cost_basis = holding.avg_price * holding.quantity
                holdings_value.append(
                    {
                        "symbol": holding.symbol,
                        "quantity": holding.quantity,
                        "avg_price": holding.avg_price,
                        "current_price": current_price,
                        "value": value,
                        "gain_loss": value - cost_basis,
                        "gain_loss_pct": (
                            (current_price - holding.avg_price)
                            / holding.avg_price
                            * 100
                        )
                        if holding.avg_price > 0
                        else 0,
                    }
                )

            return {
                "cash": portfolio.cash_balance,
                "holdings_value": total_holdings_value,
                "total_value": portfolio.cash_balance + total_holdings_value,
                "holdings": holdings_value,
                "updated_at": datetime.utcnow().isoformat(),
            }

    async def add_price_alert(
        self, user_id: int, symbol: str, target_price: float, condition: str = "above"
    ) -> dict[str, Any]:
        async with async_session_factory() as db:
            alert = TradingAlertDB(
                user_id=user_id,
                symbol=symbol.upper(),
                target_price=target_price,
                condition=condition,
            )
            db.add(alert)
            await db.commit()
            await db.refresh(alert)

            return {
                "status": "success",
                "alert": {
                    "id": alert.id,
                    "symbol": alert.symbol,
                    "target_price": alert.target_price,
                    "condition": alert.condition,
                },
            }

    async def get_price_alerts(self, user_id: int) -> list[dict[str, Any]]:
        async with async_session_factory() as db:
            stmt = select(TradingAlertDB).where(TradingAlertDB.user_id == user_id)
            result = await db.execute(stmt)
            alerts = result.scalars().all()

            return [
                {
                    "id": a.id,
                    "symbol": a.symbol,
                    "target_price": a.target_price,
                    "condition": a.condition,
                    "triggered": a.triggered,
                    "triggered_at": a.triggered_at.isoformat()
                    if a.triggered_at
                    else None,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in alerts
            ]

    async def check_price_alerts(self, user_id: int) -> list[dict[str, Any]]:
        async with async_session_factory() as db:
            stmt = select(TradingAlertDB).where(
                TradingAlertDB.user_id == user_id,
                TradingAlertDB.triggered == False,
            )
            result = await db.execute(stmt)
            alerts = result.scalars().all()

            if not alerts:
                return []

            triggered = []

            for alert in alerts:
                is_crypto = alert.symbol.islower()
                try:
                    if is_crypto:
                        price_data = await self.get_crypto_quote(alert.symbol)
                    else:
                        price_data = await self.get_stock_quote(alert.symbol)
                except Exception as e:
                    logger.warning(f"Failed to fetch price for alert check (symbol: {alert.symbol}): {e}")
                    price_data = {}

                current_price = price_data.get("price")
                if not current_price:
                    continue

                should_trigger = False
                if alert.condition == "above" and current_price >= alert.target_price:
                    should_trigger = True
                elif alert.condition == "below" and current_price <= alert.target_price:
                    should_trigger = True

                if should_trigger:
                    alert.triggered = True
                    alert.triggered_at = datetime.utcnow()
                    triggered.append(
                        {
                            "id": alert.id,
                            "symbol": alert.symbol,
                            "target_price": alert.target_price,
                            "current_price": current_price,
                            "condition": alert.condition,
                        }
                    )

            await db.commit()
            return triggered

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        reraise=False,
    )
    async def get_stock_quote(self, symbol: str) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")
        if not self.alpha_vantage_key:
            return {}

        if alpha_vantage_circuit_breaker.is_open():
            logger.warning("Alpha Vantage circuit breaker is OPEN")
            return {}

        # Rate limiting
        while not alpha_vantage_limiter.acquire():
            await asyncio.sleep(alpha_vantage_limiter.wait_time())

        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        alpha_vantage_circuit_breaker.record_failure()
                        logger.warning(f"Alpha Vantage returned {resp.status}")
                        return {}

                    data = await resp.json()

                    if "Global Quote" in data and data["Global Quote"]:
                        quote = data["Global Quote"]
                        alpha_vantage_circuit_breaker.record_success()
                        return {
                            "symbol": quote.get("01. symbol"),
                            "price": float(quote.get("05. price", 0)),
                            "change": float(quote.get("09. change", 0)),
                            "change_percent": quote.get("10. change percent", "0%"),
                            "volume": int(quote.get("06. volume", 0)),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    alpha_vantage_circuit_breaker.record_success()
                    return {}
        except Exception as e:
            alpha_vantage_circuit_breaker.record_failure()
            logger.error(f"Alpha Vantage API error: {e}")
            return {}

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        reraise=False,
    )
    async def get_crypto_quote(self, symbol: str) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")

        if coingecko_circuit_breaker.is_open():
            logger.warning("CoinGecko circuit breaker is OPEN")
            return {}

        # Rate limiting
        while not coingecko_limiter.acquire():
            await asyncio.sleep(coingecko_limiter.wait_time())

        try:
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": symbol,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_market_cap": "true",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        coingecko_circuit_breaker.record_failure()
                        logger.warning(f"CoinGecko returned {resp.status}")
                        return {}

                    data = await resp.json()

                    if symbol in data:
                        quote = data[symbol]
                        coingecko_circuit_breaker.record_success()
                        return {
                            "symbol": symbol,
                            "price": quote.get("usd", 0),
                            "change_24h": quote.get("usd_24h_change", 0),
                            "market_cap": quote.get("usd_market_cap", 0),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    coingecko_circuit_breaker.record_success()
                    return {}
        except Exception as e:
            coingecko_circuit_breaker.record_failure()
            logger.error(f"CoinGecko API error: {e}")
            return {}

    async def get_historical_data(self, symbol: str, days: int = 30) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")

        is_crypto = symbol.islower() or symbol.startswith(("bitcoin", "ethereum"))

        if not is_crypto and self.alpha_vantage_key:
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    "function": "TIME_SERIES_DAILY",
                    "symbol": symbol,
                    "apikey": self.alpha_vantage_key,
                    "outputsize": "compact",
                }

                while not alpha_vantage_limiter.acquire():
                    await asyncio.sleep(alpha_vantage_limiter.wait_time())

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url, params=params, timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
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
                logger.warning(f"Alpha Vantage historical error: {e}")

        if is_crypto:
            try:
                url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
                params = {"vs_currency": "usd", "days": min(days, 90)}

                while not coingecko_limiter.acquire():
                    await asyncio.sleep(coingecko_limiter.wait_time())

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url, params=params, timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
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
                                        "volume": 0,
                                    }
                                    for p in data["prices"]
                                ],
                                "source": "coingecko",
                            }
            except Exception as e:
                logger.warning(f"CoinGecko historical error: {e}")

        return {"symbol": symbol, "data": [], "error": "No data available"}

    async def get_technical_indicators(self, symbol: str) -> dict[str, Any]:
        history = await self.get_historical_data(symbol, days=50)
        data = history.get("data", [])

        if not data:
            return {"error": "Insufficient data for technical analysis"}

        closes = [d["close"] for d in data]
        if len(closes) < 20:
            return {"error": "Insufficient data (need 20+ days)"}

        # SMA calculations
        sma_20 = sum(closes[:20]) / 20
        sma_50 = sum(closes[:50]) / 50 if len(closes) >= 50 else None

        # RSI (14-period)
        gains, losses = [], []
        for i in range(1, min(15, len(closes))):
            change = closes[i] - closes[i - 1]
            gains.append(max(0, change))
            losses.append(max(0, -change))

        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 0
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))

        # MACD (12, 26, 9)
        ema_12 = self._ema(closes, 12)
        ema_26 = self._ema(closes, 26)
        macd = ema_12 - ema_26
        signal = self._ema([macd] * 9, 9) if macd else 0
        macd_histogram = macd - signal

        current_price = closes[0]
        trend = "bullish" if sma_20 > sma_50 else "bearish" if sma_50 else "neutral"

        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2) if sma_50 else None,
            "rsi": round(rsi, 2),
            "macd": round(macd, 4),
            "macd_signal": round(signal, 4),
            "macd_histogram": round(macd_histogram, 4),
            "trend": trend,
            "signals": self._analyze_signals(sma_20, sma_50, rsi, macd_histogram),
        }

    def _ema(self, data: list[float], period: int) -> float:
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for value in data[period:]:
            ema = (value - ema) * multiplier + ema
        return ema

    def _analyze_signals(
        self, sma_20: float, sma_50: float | None, rsi: float, macd_hist: float
    ) -> list[str]:
        signals = []
        if sma_20 > (sma_50 or sma_20):
            signals.append("SMA bullish")
        elif sma_50 and sma_20 < sma_50:
            signals.append("SMA bearish")

        if rsi > 70:
            signals.append("RSI overbought")
        elif rsi < 30:
            signals.append("RSI oversold")

        if macd_hist > 0:
            signals.append("MACD bullish")
        elif macd_hist < 0:
            signals.append("MACD bearish")

        return signals

    async def get_market_sentiment(self, symbol: str) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")

        is_crypto = symbol.islower()

        stock_quote = (
            await self.get_stock_quote(symbol.upper()) if not is_crypto else {}
        )
        crypto_quote = await self.get_crypto_quote(symbol.lower()) if is_crypto else {}

        sentiment, confidence = "neutral", 0.5

        if stock_quote.get("change_percent"):
            change = float(stock_quote["change_percent"].replace("%", ""))
            if change > 2:
                sentiment, confidence = "bullish", min(0.9, 0.5 + abs(change) / 20)
            elif change < -2:
                sentiment, confidence = "bearish", min(0.9, 0.5 + abs(change) / 20)

        if crypto_quote:
            change = crypto_quote.get("change_24h", 0)
            if change > 5:
                sentiment, confidence = "bullish", min(0.9, 0.5 + abs(change) / 25)
            elif change < -5:
                sentiment, confidence = "bearish", min(0.9, 0.5 + abs(change) / 25)

        return {
            "symbol": symbol,
            "sentiment": sentiment,
            "confidence": round(confidence, 2),
            "stock_quote": stock_quote,
            "crypto_quote": crypto_quote,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def analyze_trends(self, niche: str) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")
        
        # Externalized: Driven by NICHE_TICKER_MAP in config.py
        tickers = settings.NICHE_TICKER_MAP.get(niche.lower(), ["SPY", "QQQ"])
        analyzed: list[dict[str, Any]] = []
        
        for symbol in tickers:
            sentiment = await self.get_market_sentiment(symbol)
            analyzed.append(sentiment)
            
        return {
            "niche": niche,
            "analyzed": analyzed,
            "overall_sentiment": "bullish" if any(s["sentiment"] == "bullish" for s in analyzed) else "neutral",
            "status": "active",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_trending_tickers(self) -> list[dict[str, Any]]:
        if not self.enabled:
            raise RuntimeError("Trading service is not enabled")

        # Hardened: Simulated live discovery fallback
        # In production, this would call Alpha Vantage /query?function=TOP_GAINERS_LOSERS
        trending = [
            {"symbol": "TSLA", "reason": "High Volume", "sentiment": "bullish"},
            {"symbol": "bitcoin", "reason": "Breakout", "sentiment": "bullish"},
            {"symbol": "NVDA", "reason": "Earnings Momentum", "sentiment": "bullish"}
        ]
        return trending


trading_service = TradingService()
