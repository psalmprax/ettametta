import aiohttp
import logging
from .models import ContentCandidate
from .google_trends_scanner import base_google_trends_service
from .google_search_scanner import base_google_search_service
from datetime import datetime

logger = logging.getLogger(__name__)


class MetasearchScanner:
    """
    Metasearch scanner that combines Google Trends and Google Search for 
    comprehensive trend and monetization discovery.
    This replaces the previous mock implementation with real free APIs.
    """
    
    def __init__(self):
        self.platform = "Metasearch (Google)"
        
    async def scan_trends(self, niche: str, published_after: datetime | None = None) -> list[ContentCandidate]:
        """
        Combines Google Trends and Google Search results for comprehensive discovery.
        """
        logger.info(f"[Metasearch] Running comprehensive search for: {niche}")
        
        all_candidates = []
        
        # Get Google Trends
        try:
            trends = await base_google_trends_service.scan_trends(niche, published_after)
            all_candidates.extend(trends)
        except Exception as e:
            logger.warning(f"[Metasearch] Google Trends failed: {e}")
        
        # Get Google Search for monetization opportunities
        try:
            search_results = await base_google_search_service.scan_trends(niche, published_after)
            all_candidates.extend(search_results)
        except Exception as e:
            logger.warning(f"[Metasearch] Google Search failed: {e}")
        
        if all_candidates:
            logger.info(f"[Metasearch] Found {len(all_candidates)} total results")
            return all_candidates
        
        # Return empty list instead of mock data
        logger.warning(f"[Metasearch] No results found for {niche}. Configure API keys for better results.")
        return []


base_metasearch_service = MetasearchScanner()
