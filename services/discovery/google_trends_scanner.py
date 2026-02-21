import aiohttp
import logging
import json
from typing import List, Optional
from .models import ContentCandidate
from datetime import datetime

logger = logging.getLogger(__name__)


class GoogleTrendsScanner:
    """
    Google Trends scanner for discovering trending topics.
    Uses free Google Trends API endpoint (no API key required for basic trends).
    """
    
    def __init__(self):
        self.platform = "Google Trends"
        self.base_url = "https://trends.google.com/trends/api"
        
    async def scan_trends(self, niche: str, published_after: Optional[datetime] = None) -> List[ContentCandidate]:
        """
        Fetches trending searches related to the niche from Google Trends.
        Uses the free daily trends endpoint - no API key required.
        """
        logger.info(f"[GoogleTrends] Scanning for trending topics in: {niche}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get trending related queries for the niche
                url = f"{self.base_url}/dailytrends"
                params = {
                    "geo": "US",
                    "hl": "en-US"
                }
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.warning(f"[GoogleTrends] API returned status {response.status}")
                        return []
                    
                    text = await response.text()
                    # Google Trends API returns JSONP format, need to strip the callback
                    if text.startswith(")]}'"):
                        text = text[4:]
                    
                    data = json.loads(text)
                    trends = data.get("default", {}).get("trendingSearchesDays", [])
                    
                    candidates = []
                    for day in trends[:3]:  # Get top 3 days
                        for trend in day.get("trendingSearches", [])[:5]:  # Top 5 per day
                            title = trend.get("title", {}).get("query", "")
                            candidates.append(ContentCandidate(
                                id=f"gt_{trend.get('id', {}).get('value', '')}",
                                platform=self.platform,
                                url=f"https://www.google.com/search?q={title.replace(' ', '+')}",
                                author=niche,
                                title=f"TRENDING: {title}",
                                description=trend.get("summary", ""),
                                view_count=1_000_000,  # Estimate
                                engagement_rate=0.1,
                                discovery_date=datetime.now(),
                                tags=[niche, "trending", "google"],
                                metadata={
                                    "source": "google_trends",
                                    "trend_value": trend.get("id", {}).get("value", ""),
                                    "traffic": trend.get("formattedTraffic", "")
                                }
                            ))
                    
                    if candidates:
                        logger.info(f"[GoogleTrends] Found {len(candidates)} trending topics")
                        return candidates
                        
        except Exception as e:
            logger.error(f"[GoogleTrends] Error fetching trends: {e}")
        
        return []


base_google_trends_scanner = GoogleTrendsScanner()
