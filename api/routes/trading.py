from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from typing import Optional, List
import httpx
import re
from sqlalchemy.ext.asyncio import AsyncSession
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from api.utils.database import get_db

router = APIRouter(prefix="/trading", tags=["Trading"])


def validate_symbol(symbol: str) -> str:
    """
    Sanitize symbol parameter to prevent injection attacks.
    Only allows alphanumeric, dots, hyphens, and slashes (e.g., BTC/USD, AAPL).
    """
    if not symbol or len(symbol) > 20:
        raise HTTPException(status_code=400, detail="Invalid symbol length")

    # Only allow valid characters for stock/crypto symbols
    if not re.match(r"^[A-Za-z0-9./-]+$", symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol characters")

    return symbol.upper()


class MarketDataRequest(BaseModel):
    symbol: str
    interval: str = "1d"

    @validator("symbol")
    def validate_symbol_field(cls, v):
        return validate_symbol(v)


class CryptoRequest(BaseModel):
    coin_id: str


@router.get("/")
async def get_trading_summary(
    current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get trading dashboard summary.
    """
    # Return stub data for now
    return {
        "positions": 0,
        "unrealized_pnl": 0.0,
        "status": "no_positions",
    }


@router.get("/market/{symbol}")
async def get_market_data(
    symbol: str, interval: str = "1d", current_user: UserDB = Depends(get_current_user)
):
    """
    Get market data for a symbol using Alpha Vantage.
    """
    # Validate and sanitize symbol
    symbol = validate_symbol(symbol)
    from api.config import settings
    import httpx

    if not settings.ALPHA_VANTAGE_API_KEY:
        raise HTTPException(status_code=503, detail="Alpha Vantage API not configured")

    # Map intervals to Alpha Vantage functions
    function_map = {
        "1min": "TIME_SERIES_INTRADAY",
        "5min": "TIME_SERIES_INTRADAY",
        "15min": "TIME_SERIES_INTRADAY",
        "30min": "TIME_SERIES_INTRADAY",
        "60min": "TIME_SERIES_INTRADAY",
        "1d": "TIME_SERIES_DAILY",
        "1wk": "TIME_SERIES_WEEKLY",
        "1mo": "TIME_SERIES_MONTHLY",
    }

    av_function = function_map.get(interval, "TIME_SERIES_DAILY")

    try:
        async with httpx.AsyncClient() as client:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": av_function,
                "symbol": symbol,
                "apikey": settings.ALPHA_VANTAGE_API_KEY,
            }

            if av_function == "TIME_SERIES_INTRADAY":
                params["interval"] = interval

            response = await client.get(url, params=params)
            data = response.json()

            if "Error Message" in data:
                raise HTTPException(
                    status_code=400, detail=f"Invalid symbol or interval for {symbol}"
                )

            if "Note" in data and "rate limit" in data["Note"].lower():
                raise HTTPException(
                    status_code=429,
                    detail="Market data rate limit reached. Please wait a minute.",
                )

            return data
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crypto/{coin_id}")
async def get_crypto_data(
    coin_id: str = "bitcoin", current_user: UserDB = Depends(get_current_user)
):
    """
    Get cryptocurrency data using CoinGecko.
    """
    from api.config import settings
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            # Use CoinGecko free API
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            }
            response = await client.get(url, params=params)
            data = response.json()

            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crypto/trending")
async def get_trending_crypto(current_user: UserDB = Depends(get_current_user)):
    """
    Get trending cryptocurrencies.
    """
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.coingecko.com/api/v3/search/trending"
            response = await client.get(url)
            data = response.json()

            # Return top 10 trending coins
            coins = data.get("coins", [])[:10]
            return {
                "trending": [
                    {
                        "name": c["item"]["name"],
                        "symbol": c["item"]["symbol"],
                        "price": c["item"]["price_usd"],
                        "change_24h": c["item"]["price_change_percentage_24h"],
                    }
                    for c in coins
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screener")
async def market_screener(
    sector: Optional[str] = None,
    min_market_cap: Optional[int] = None,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Screen stocks using Alpha Vantage TOP_GAINERS_LOSERS and SECTOR PERFORMANCE APIs.
    Falls back to CoinGecko trending crypto if Alpha Vantage is unavailable.
    """
    from api.config import settings
    import httpx

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            results = []

            if settings.ALPHA_VANTAGE_API_KEY:
                # Use Alpha Vantage market movers API
                url = "https://www.alphavantage.co/query"
                params = {
                    "function": "TOP_GAINERS_LOSERS",
                    "apikey": settings.ALPHA_VANTAGE_API_KEY,
                }
                response = await client.get(url, params=params)
                data = response.json()

                if "top_gainers" in data or "top_losers" in data:
                    for category in (
                        "top_gainers",
                        "top_losers",
                        "most_actively_traded",
                    ):
                        for item in data.get(category, [])[:10]:
                            results.append(
                                {
                                    "symbol": item.get("ticker", ""),
                                    "name": item.get("ticker", ""),
                                    "price": float(item.get("price", 0)),
                                    "change_percentage": item.get(
                                        "change_percentage", "0%"
                                    ),
                                    "change_amount": float(
                                        item.get("change_amount", 0)
                                    ),
                                    "volume": int(item.get("volume", 0)),
                                    "category": category.replace("top_", "").replace(
                                        "most_actively_", ""
                                    ),
                                }
                            )

            if not results:
                # Fallback: use CoinGecko trending crypto as screener data
                cg_url = "https://api.coingecko.com/api/v3/coins/markets"
                cg_params = {
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 25,
                    "page": 1,
                    "sparkline": "false",
                }
                cg_response = await client.get(cg_url, params=cg_params)
                cg_data = cg_response.json()

                if isinstance(cg_data, list):
                    for coin in cg_data:
                        results.append(
                            {
                                "symbol": coin.get("symbol", "").upper(),
                                "name": coin.get("name", ""),
                                "price": coin.get("current_price", 0),
                                "change_percentage": f"{coin.get('price_change_percentage_24h', 0):.2f}%",
                                "volume": coin.get("total_volume", 0),
                                "market_cap": coin.get("market_cap", 0),
                                "category": "crypto",
                            }
                        )

            # Apply filters if provided
            if sector:
                results = [
                    r
                    for r in results
                    if r.get("category", "").lower() == sector.lower()
                ]
            if min_market_cap:
                results = [
                    r for r in results if r.get("market_cap", 0) >= min_market_cap
                ]

            return {
                "results": results[:25],
                "count": len(results[:25]),
                "filters": {"sector": sector, "min_market_cap": min_market_cap},
                "source": "alphavantage"
                if settings.ALPHA_VANTAGE_API_KEY
                else "coingecko",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screener unavailable: {str(e)}")


@router.get("/analysis/{symbol}")
async def get_symbol_analysis(
    symbol: str, current_user: UserDB = Depends(get_current_user)
):
    """
    Get AI-powered analysis for a symbol.
    """
    # Validate and sanitize symbol
    symbol = validate_symbol(symbol)

    from api.config import settings
    from groq import AsyncGroq
    import httpx

    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ API not configured")

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    try:
        # Fetch market data directly instead of calling the endpoint
        # (which would cause duplicate API calls and unnecessary auth overhead)
        market_data = await _fetch_market_data(symbol, "1d", settings)
        if not market_data:
            raise HTTPException(status_code=500, detail="Failed to fetch market data")

        # Generate analysis using LLM
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial analyst. Provide a brief analysis of the stock based on the market data provided.",
                },
                {
                    "role": "user",
                    "content": f"Analyze this stock data for {symbol}: {market_data}",
                },
            ],
            temperature=0.5,
            max_tokens=500,
        )

        analysis = response.choices[0].message.content

        return {"symbol": symbol, "market_data": market_data, "analysis": analysis}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _fetch_market_data(symbol: str, interval: str, settings) -> Optional[dict]:
    """Fetch market data without external API dependencies."""
    import httpx

    if not settings.ALPHA_VANTAGE_API_KEY:
        return None

    function_map = {
        "1min": "TIME_SERIES_INTRADAY",
        "5min": "TIME_SERIES_INTRADAY",
        "15min": "TIME_SERIES_INTRADAY",
        "30min": "TIME_SERIES_INTRADAY",
        "60min": "TIME_SERIES_INTRADAY",
        "1d": "TIME_SERIES_DAILY",
        "1wk": "TIME_SERIES_WEEKLY",
        "1mo": "TIME_SERIES_MONTHLY",
    }

    av_function = function_map.get(interval, "TIME_SERIES_DAILY")

    try:
        async with httpx.AsyncClient() as client:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": av_function,
                "symbol": symbol,
                "apikey": settings.ALPHA_VANTAGE_API_KEY,
            }
            if av_function == "TIME_SERIES_INTRADAY":
                params["interval"] = interval

            response = await client.get(url, params=params)
            data = response.json()

            if "Error Message" in data:
                return None
            if "Note" in data and "rate limit" in data.get("Note", "").lower():
                return None

            return data
    except Exception:
        return None


class PortfolioPosition(BaseModel):
    symbol: str
    quantity: float
    price: float
    position_type: str = "buy"


class PriceAlertRequest(BaseModel):
    symbol: str
    target_price: float
    condition: str = "above"


@router.get("/portfolio")
async def get_portfolio(current_user: UserDB = Depends(get_current_user)):
    """
    Get user's trading portfolio with current values.
    """
    from services.trading.service import trading_service

    if not trading_service.is_enabled():
        raise HTTPException(status_code=503, detail="Trading service not enabled")

    return await trading_service.get_portfolio_value(current_user.id)


@router.post("/portfolio/position")
async def add_portfolio_position(
    position: PortfolioPosition, current_user: UserDB = Depends(get_current_user)
):
    """
    Add a buy or sell position to portfolio.
    """
    from services.trading.service import trading_service

    if not trading_service.is_enabled():
        raise HTTPException(status_code=503, detail="Trading service not enabled")

    return await trading_service.add_position(
        current_user.id,
        position.symbol.upper(),
        position.quantity,
        position.price,
        position.position_type,
    )


@router.get("/alerts")
async def get_price_alerts(current_user: UserDB = Depends(get_current_user)):
    """
    Get all price alerts for user.
    """
    from services.trading.service import trading_service

    if not trading_service.is_enabled():
        raise HTTPException(status_code=503, detail="Trading service not enabled")

    return {"alerts": await trading_service.get_price_alerts(current_user.id)}


@router.post("/alerts")
async def add_price_alert(
    alert: PriceAlertRequest, current_user: UserDB = Depends(get_current_user)
):
    """
    Add a price alert.
    """
    from services.trading.service import trading_service

    if not trading_service.is_enabled():
        raise HTTPException(status_code=503, detail="Trading service not enabled")

    return await trading_service.add_price_alert(
        current_user.id, alert.symbol.upper(), alert.target_price, alert.condition
    )


@router.get("/alerts/check")
async def check_price_alerts(current_user: UserDB = Depends(get_current_user)):
    """
    Check for triggered price alerts.
    """
    from services.trading.service import trading_service

    if not trading_service.is_enabled():
        raise HTTPException(status_code=503, detail="Trading service not enabled")

    triggered = await trading_service.check_price_alerts(current_user.id)
    return {"triggered": triggered, "count": len(triggered)}


@router.get("/history/{symbol}")
async def get_symbol_history(
    symbol: str, days: int = 30, current_user: UserDB = Depends(get_current_user)
):
    """
    Get historical price data for a symbol.
    """
    from services.trading.service import trading_service

    if not trading_service.is_enabled():
        raise HTTPException(status_code=503, detail="Trading service not enabled")

    return await trading_service.get_historical_data(symbol.upper(), days)


@router.get("/technical/{symbol}")
async def get_technical_analysis(
    symbol: str, current_user: UserDB = Depends(get_current_user)
):
    """
    Get technical indicators for a symbol (SMA, RSI, trend).
    """
    from services.trading.service import trading_service

    if not trading_service.is_enabled():
        raise HTTPException(status_code=503, detail="Trading service not enabled")

    return await trading_service.get_technical_indicators(symbol.upper())
