import aiohttp
import logging
import json
from typing import List, Optional
from .models import ContentCandidate
from datetime import datetime
from api.config import settings

logger = logging.getLogger(__name__)


class GoogleSearchScanner:
    """
    Google Search scanner for discovering popular products and monetization opportunities.
    Uses Google Custom Search API (free tier: 100 searches/day) or scraping (for development).
    """
    
    def __init__(self):
        self.platform = "Google Search"
        self.api_key = getattr(settings, 'GOOGLE_API_KEY', '')
        self.cx = getattr(settings, 'GOOGLE_SEARCH_CX', '')  # Custom Search Engine ID
        
    async def scan_trends(self, niche: str, published_after: Optional[datetime] = None) -> List[ContentCandidate]:
        """
        Searches Google for trending products, affiliate opportunities, and monetization ideas.
        Uses Google Custom Search API.
        """
        logger.info(f"[GoogleSearch] Searching for monetization opportunities in: {niche}")
        
        if not self.api_key or not self.cx:
            logger.warning("[GoogleSearch] Google API key or CX not configured. Using fallback method.")
            return await self._scan_with_scrape(niche)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": self.api_key,
                    "cx": self.cx,
                    "q": f"best {niche} products 2024 trending",
                    "num": 10
                }
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.warning(f"[GoogleSearch] API returned status {response.status}")
                        return await self._scan_with_scrape(niche)
                    
                    data = await response.json()
                    items = data.get("items", [])
                    
                    candidates = []
                    for item in items:
                        candidates.append(ContentCandidate(
                            id=f"gs_{hash(item.get('link', '')) % 100000}",
                            platform=self.platform,
                            url=item.get("link", ""),
                            author=item.get("displayLink", ""),
                            title=item.get("title", ""),
                            description=item.get("snippet", ""),
                            view_count=10000,  # Estimate
                            engagement_rate=0.05,
                            discovery_date=datetime.now(),
                            tags=[niche, "search", "monetization"],
                            metadata={
                                "source": "google_search",
                                "search_type": "product"
                            }
                        ))
                    
                    if candidates:
                        logger.info(f"[GoogleSearch] Found {len(candidates)} search results")
                        return candidates
                        
        except Exception as e:
            logger.error(f"[GoogleSearch] Error: {e}")
        
        return await self._scan_with_scrape(niche)
    
    async def _scan_with_scrape(self, niche: str) -> List[ContentCandidate]:
        """
        Fallback: Try to scrape Google Shopping/Trends results directly.
        Note: This is fragile and may break. For production, use the API.
        """
        logger.info(f"[GoogleSearch] Attempting direct scrape for: {niche}")
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                # Search for trending products in niche
                search_queries = [
                    f"trending {niche} products",
                    f"best {niche} 2024",
                    f"{niche} affiliate programs"
                ]
                
                all_results = []
                for query in search_queries[:2]:  # Limit searches
                    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=shop"
                    
                    try:
                        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                # For now, just return a placeholder
                                # Real scraping requires handling JavaScript
                                pass
                    except:
                        pass
                
                # If scraping failed, return empty list instead of fake data
                logger.warning(f"[GoogleSearch] Scraping failed for {niche}. Configure GOOGLE_API_KEY and GOOGLE_SEARCH_CX for production.")
                return []
                
        except Exception as e:
            logger.error(f"[GoogleSearch] Scrape error: {e}")
        
        return []


base_google_search_scanner = GoogleSearchScanner()
