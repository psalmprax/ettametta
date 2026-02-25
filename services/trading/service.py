"""
Trading Service - Optional trading API integration
===================================================
Disabled by default. Enable with: ENABLE_TRADING=true

This service provides market analysis and trading automation:
- Alpha Vantage (stocks, forex)
- CoinGecko (cryptocurrency)
- Market sentiment analysis

Used for market-related content creation and trend analysis.
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
        
        if not self.enabled:
            logger.info("Trading service is disabled (ENABLE_TRADING=false)")
            return
        
        has_api = any([self.alpha_vantage_key, self.coingecko_key])
        
        if not has_api:
            logger.warning("No trading API keys configured. Service enabled but may not work.")
        
        logger.info("Trading service initialized")
    
    def is_enabled(self) -> bool:
        """Check if service is enabled."""
        return self.enabled
    
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
                "apikey": self.alpha_vantage_key
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
                            "timestamp": datetime.utcnow().isoformat()
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
                "include_market_cap": "true"
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
                            "timestamp": datetime.utcnow().isoformat()
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
            "timestamp": datetime.utcnow().isoformat()
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
            "energy": ["XOM", "CVX", "TSLA"]
        }
        
        symbols = niche_map.get(niche.lower(), [])
        
        results = {
            "niche": niche,
            "analyzed": [],
            "overall_sentiment": "neutral"
        }
        
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
                
                results["analyzed"].append({
                    "symbol": symbol,
                    "sentiment": sentiment,
                    "price": quote.get("price") or quote.get("price", 0)
                })
        
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
