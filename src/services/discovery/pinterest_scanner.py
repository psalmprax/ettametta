import httpx
import logging
import json
import re
import random
from datetime import datetime
from .models import ContentCandidate

logger = logging.getLogger(__name__)


class PinterestScanner:
    """
    Scans Pinterest for trending pins and videos in a niche.
    Uses web scraping to discover popular content without API.
    """
    
    def __init__(self):
        self.platform = "Pinterest"
        self.base_url = "https://www.pinterest.com"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        ]
    
    async def scan_trends(self, niche: str, published_after: datetime | None = None) -> list[ContentCandidate]:
        """
        Scans Pinterest for trending pins in a niche.
        Uses the search functionality to find popular content.
        """
        logger.info(f"[PinterestScanner] Scanning Pinterest for: {niche}")
        
        candidates = []
        
        # Try search
        try:
            results = await self._search_pins(niche)
            candidates.extend(results)
        except Exception as e:
            logger.warning(f"[PinterestScanner] Search failed: {e}")
        
        # Try trending as fallback
        if not candidates:
            try:
                results = await self._get_trending()
                candidates.extend(results)
            except Exception as e:
                logger.warning(f"[PinterestScanner] Trending failed: {e}")
        
        # Remove duplicates
        seen = set()
        unique = []
        for c in candidates:
            if c.source_url not in seen:
                seen.add(c.source_url)
                unique.append(c)
        
        logger.info(f"[PinterestScanner] Found {len(unique)} pins")
        return unique[:15]
    
    async def _search_pins(self, query: str) -> list[ContentCandidate]:
        """Search Pinterest for pins."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        # Pinterest search URL
        url = f"{self.base_url}/search/pins/?q={query.replace(' ', '%20')}"
        
        candidates = []
        
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return []
                
                # Look for JSON data
                script_matches = re.findall(
                    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    response.text,
                    re.DOTALL
                )
                
                for json_str in script_matches:
                    try:
                        data = json.loads(json_str)
                        pins = self._extract_pins_from_json(data)
                        candidates.extend(pins)
                    except:
                        pass
                
                # Try alternate data format
                if not candidates:
                    resource_matches = re.findall(
                        r'<script[^>]*data-test-id="pin-grid-item"[^>]*>(.*?)</script>',
                        response.text,
                        re.DOTALL
                    )
                    # Parse individual pin items
                    
        except Exception as e:
            logger.warning(f"[PinterestScanner] Search error: {e}")
        
        return candidates
    
    async def _get_trending(self) -> list[ContentCandidate]:
        """Get trending pins from Pinterest."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        # Try trending URL
        url = f"{self.base_url}/_ngjs/core/insights/popular/"
        
        candidates = []
        
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return []
                    
        except Exception as e:
            logger.warning(f"[PinterestScanner] Trending error: {e}")
        
        return candidates
    
    def _extract_pins_from_json(self, data: dict) -> list[ContentCandidate]:
        """Extract pin data from Pinterest JSON."""
        candidates = []
        
        try:
            # Navigate Pinterest's JSON structure
            props = data.get("props", {})
            page_props = props.get("pageProps", {})
            
            # Try to find pin data
            initial_data = page_props.get("initialData", {})
            
            # Look for board or pin data
            boards_or_pins = []
            
            # Try various paths
            if "boards" in str(initial_data):
                boards = initial_data.get("boards", {})
                if boards:
                    boards_or_pins = boards
            
            # Try resource response
            resource = page_props.get("resourceData", {})
            if resource:
                results = resource.get("results", [])
                for item in results:
                    pin = self._parse_pin_item(item)
                    if pin:
                        candidates.append(pin)
            
            # Generic search through data
            if not candidates:
                # Recursively search for pins
                candidates = self._find_pins_recursive(initial_data)
                    
        except Exception as e:
            logger.debug(f"[PinterestScanner] JSON extraction error: {e}")
        
        return candidates
    
    def _find_pins_recursive(self, obj, depth=0) -> list[ContentCandidate]:
        """Recursively search for pin objects."""
        candidates = []
        
        if depth > 5:
            return candidates
            
        if isinstance(obj, dict):
            # Check if this looks like a pin
            if "id" in obj and ("image" in str(obj).lower() or "pin" in str(obj).lower()):
                pin = self._parse_pin_item(obj)
                if pin:
                    candidates.append(pin)
            
            # Recurse
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    candidates.extend(self._find_pins_recursive(value, depth + 1))
                    
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    candidates.extend(self._find_pins_recursive(item, depth + 1))
        
        return candidates
    
    def _parse_pin_item(self, item: dict) -> ContentCandidate | None:
        """Parse a single pin item."""
        try:
            pin_id = item.get("id", "")
            if not pin_id:
                return None
            
            # Get title/description
            title = item.get("title", "") or item.get("description", "Pinterest Pin")
            if not title:
                title = "Pinterest Pin"
            
            # Get creator
            author = "Unknown"
            owner = item.get("owner", {})
            if owner:
                author = owner.get("username", "Unknown") or owner.get("full_name", "Unknown")
            
            # Get image/thumbnail
            images = item.get("images", {})
            if images:
                url_dict = images.get("1000x1500") or images.get("600x") or images.get("orig")
                if isinstance(url_dict, dict):
                    thumbnail = url_dict.get("url", "")
                else:
                    thumbnail = url_dict
            else:
                thumbnail = ""
            
            # Get link (could be external or pinterest)
            link = item.get("link", "")
            if not link:
                # Use pinterest URL
                pin_id_str = str(pin_id)
                link = f"{self.base_url}/pin/{pin_id_str}"
            
            # Get stats if available
            repins = item.get("repin_count", 0) or item.get("repins", 0)
            comments = item.get("comment_count", 0) or item.get("comments", 0)
            likes = item.get("like_count", 0) or item.get("likes", 0)
            
            # Estimate views
            views = repins * 25  # Rough estimate
            engagement = repins + comments + likes
            engagement_score = engagement / max(views, 1) if views else 0.05
            
            return ContentCandidate(
                id=f"pin_{pin_id}",
                platform="Pinterest",
                source_url=link,
                creator_name=author,
                title=title[:100],
                view_count=views,
                like_count=likes,
                comment_count=comments,
                share_count=repins,
                engagement_score=engagement_score,
                thumbnail_url=thumbnail,
                metadata={}
            )
            
        except Exception as e:
            logger.debug(f"[PinterestScanner] Pin parse error: {e}")
        
        return None


base_pinterest_scanner = PinterestScanner()
