from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB

router = APIRouter(prefix="/trading", tags=["Trading"])


class MarketDataRequest(BaseModel):
    symbol: str
    interval: str = "1d"


class CryptoRequest(BaseModel):
    coin_id: str


@router.get("/market/{symbol}")
async def get_market_data(
    symbol: str, interval: str = "1d", current_user: UserDB = Depends(get_current_user)
):
    """
    Get market data for a symbol using Alpha Vantage.
    """
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
                raise HTTPException(status_code=400, detail=f"Invalid symbol or interval for {symbol}")
            
            if "Note" in data and "rate limit" in data["Note"].lower():
                 raise HTTPException(status_code=429, detail="Market data rate limit reached. Please wait a minute.")

            return data
    except Exception as e:
        if isinstance(e, HTTPException): raise e
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
    from api.config import settings
    from groq import AsyncGroq

    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ API not configured")

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    try:
        # Get market data first
        market_data = await get_market_data(symbol, current_user=current_user)

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
