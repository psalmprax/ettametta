import httpx
import logging
import json
import re
import random
from datetime import datetime
from .models import ContentCandidate

logger = logging.getLogger(__name__)


class SnapchatScanner:
    """
    Scans Snapchat for trending content in a niche.
    Uses web scraping to discover popular stories and Spotlight content.
    Note: Snapchat has very limited public access, results will be limited.
    """
    
    def __init__(self):
        self.platform = "Snapchat"
        self.base_url = "https://www.snapchat.com"
        self.user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
    
    async def scan_trends(self, niche: str, published_after: datetime | None = None) -> list[ContentCandidate]:
        """
        Scans Snapchat for trending Spotlight content in a niche.
        Note: Snapchat has limited public discovery via web.
        """
        logger.info(f"[SnapchatScanner] Scanning Snapchat for: {niche}")
        
        candidates = []
        
        # Try Spotlight page
        try:
            results = await self._get_spotlight(niche)
            candidates.extend(results)
        except Exception as e:
            logger.warning(f"[SnapchatScanner] Spotlight fetch failed: {e}")
        
        # Try explore/discover
        if not candidates:
            try:
                results = await self._get_discover()
                candidates.extend(results)
            except Exception as e:
                logger.warning(f"[SnapchatScanner] Discover failed: {e}")
        
        # Remove duplicates
        seen = set()
        unique = []
        for c in candidates:
            if c.source_uri not in seen:
                seen.add(c.source_uri)
                unique.append(c)
        
        logger.info(f"[SnapchatScanner] Found {len(unique)} snaps")
        return unique[:15]
    
    async def _get_spotlight(self, niche: str) -> list[ContentCandidate]:
        """Get Snapchat Spotlight trending content."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        # Snapchat Spotlight URL
        url = f"{self.base_url}/spotlight"
        
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
                        snaps = self._extract_snaps_from_json(data, niche)
                        candidates.extend(snaps)
                    except:
                        pass
                        
        except Exception as e:
            logger.warning(f"[SnapchatScanner] Spotlight error: {e}")
        
        return candidates
    
    async def _get_discover(self) -> list[ContentCandidate]:
        """Get Snapchat Discover/Explore content."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        # Discover page
        url = f"{self.base_url}/discover"
        
        candidates = []
        
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return []
                
                # Try to extract JSON
                script_matches = re.findall(
                    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    response.text,
                    re.DOTALL
                )
                
                for json_str in script_matches:
                    try:
                        data = json.loads(json_str)
                        snaps = self._extract_snaps_from_json(data, "")
                        candidates.extend(snaps)
                    except:
                        pass
                        
        except Exception as e:
            logger.warning(f"[SnapchatScanner] Discover error: {e}")
        
        return candidates
    
    def _extract_snaps_from_json(self, data: dict, niche: str) -> list[ContentCandidate]:
        """Extract snap/video data from Snapchat JSON."""
        candidates = []
        
        try:
            # Navigate Snapchat's JSON
            props = data.get("props", {})
            page_props = props.get("pageProps", {})
            
            # Try to find content data
            content_data = page_props.get("contentData", {})
            if not content_data:
                content_data = page_props.get("data", {})
            
            # Look for items/videos
            items = content_data.get("items", [])
            if not items:
                items = content_data.get("videos", [])
            if not items:
                items = content_data.get("snapList", [])
            
            for item in items:
                snap = self._parse_snap_item(item, niche)
                if snap:
                    candidates.append(snap)
            
            # Try alternate search
            if not candidates:
                candidates = self._find_snaps_recursive(data)
                    
        except Exception as e:
            logger.debug(f"[SnapchatScanner] JSON extraction error: {e}")
        
        return candidates
    
    def _find_snaps_recursive(self, obj, depth=0) -> list[ContentCandidate]:
        """Recursively search for snap objects."""
        candidates = []
        
        if depth > 4:
            return candidates
            
        if isinstance(obj, dict):
            # Check if this looks like a snap/video
            if "id" in obj and ("video" in str(obj).lower() or "snap" in str(obj).lower() or "spotlight" in str(obj).lower()):
                snap = self._parse_snap_item(obj, "")
                if snap:
                    candidates.append(snap)
            
            # Recurse
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    candidates.extend(self._find_snaps_recursive(value, depth + 1))
                    
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    candidates.extend(self._find_snaps_recursive(item, depth + 1))
        
        return candidates
    
    def _parse_snap_item(self, item: dict, niche: str) -> ContentCandidate | None:
        """Parse a single Snapchat item."""
        try:
            snap_id = item.get("id", "") or item.get("snapId", "")
            if not snap_id:
                # Generate ID from hash
                snap_id = str(abs(hash(str(item))))[:8]
            
            # Get title
            title = item.get("title", "") or item.get("caption", "") or "Snapchat Video"
            
            # Get creator
            creator = item.get("creator", {}) or item.get("author", {})
            author = "Unknown"
            if isinstance(creator, dict):
                author = creator.get("username", "") or creator.get("displayName", "Unknown")
            elif isinstance(creator, str):
                author = creator
            
            # Get thumbnail
            thumbnail = item.get("thumbnail", "") or item.get("thumbnailUrl", "")
            if isinstance(thumbnail, dict):
                thumbnail = thumbnail.get("url", "")
            
            # Get video URL
            video_uri = item.get("videoUrl", "") or item.get("url", "")
            
            # Get metrics
            views = item.get("viewCount", 0) or item.get("views", 0)
            if not views:
                # Estimate from other metrics
                likes = item.get("likes", 0) or item.get("likeCount", 0)
                shares = item.get("shares", 0) or item.get("shareCount", 0)
                views = (likes + shares) * 20
            
            # Calculate engagement
            likes = item.get("likes", 0) or item.get("likeCount", 0)
            comments = item.get("comments", 0) or item.get("commentCount", 0)
            shares = item.get("shares", 0) or item.get("shareCount", 0)
            engagement = likes + comments + shares
            engagement_score = engagement / max(views, 1) if views else 0.06
            
            # Get URL
            url = video_uri
            if not url:
                snap_id_str = str(snap_id)
                url = f"{self.base_url}/spotlight/{snap_id_str}"
            
            # Determine platform type
            platform_type = "Snapchat Spotlight"
            if "discover" in str(item).lower():
                platform_type = "Snapchat Discover"
            
            return ContentCandidate(
                id=f"snap_{snap_id}",
                platform=platform_type,
                source_uri=url,
                creator_name=author,
                title=title[:100] if title else "Snapchat Video",
                view_count=views,
                like_count=likes,
                comment_count=comments,
                share_count=shares,
                engagement_score=engagement_score,
                thumbnail_uri=thumbnail,
                metadata={"niche": niche}
            )
            
        except Exception as e:
            logger.debug(f"[SnapchatScanner] Snap parse error: {e}")
        
        return None


base_snapchat_scanner = SnapchatScanner()
