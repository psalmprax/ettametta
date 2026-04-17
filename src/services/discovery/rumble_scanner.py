import httpx
import logging
import json
import re
import random
from datetime import datetime
from .models import ContentCandidate

logger = logging.getLogger(__name__)


class RumbleScanner:
    """
    Scans Rumble for trending videos in a niche.
    Rumble is an alternative video platform growing in popularity.
    Uses web scraping to discover popular content.
    """
    
    def __init__(self):
        self.platform = "Rumble"
        self.base_url = "https://rumble.com"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        ]
    
    async def scan_trends(self, niche: str, published_after: datetime | None = None) -> list[ContentCandidate]:
        """
        Scans Rumble for trending videos in a niche.
        Uses the trending page and search functionality.
        """
        logger.info(f"[RumbleScanner] Scanning Rumble for: {niche}")
        
        candidates = []
        
        # Try trending
        try:
            results = await self._get_trending()
            candidates.extend(results)
        except Exception as e:
            logger.warning(f"[RumbleScanner] Trending fetch failed: {e}")
        
        # Try search
        if not candidates:
            try:
                results = await self._search_videos(niche)
                candidates.extend(results)
            except Exception as e:
                logger.warning(f"[RumbleScanner] Search failed: {e}")
        
        # Remove duplicates
        seen = set()
        unique = []
        for c in candidates:
            if c.url not in seen:
                seen.add(c.url)
                unique.append(c)
        
        logger.info(f"[RumbleScanner] Found {len(unique)} videos")
        return unique[:15]
    
    async def _get_trending(self) -> list[ContentCandidate]:
        """Get Rumble trending videos."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        # Rumble trending URL
        url = f"{self.base_url}/videos?sort=trending"
        
        candidates = []
        
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return []
                
                # Look for JSON data in script tags
                script_matches = re.findall(
                    r'<script[^>]*data-type="video"[^>]*>(.*?)</script>',
                    response.text,
                    re.DOTALL
                )
                
                for json_str in script_matches:
                    try:
                        data = json.loads(json_str)
                        videos = self._extract_videos_from_json(data)
                        candidates.extend(videos)
                    except:
                        pass
                
                # Try alternate pattern - video items in HTML
                if not candidates:
                    video_items = re.findall(
                        r'<a[^>]*href="(/[^"]+)"[^>]*class="[^"]*video[^"]*"[^>]*>(.*?)</a>',
                        response.text,
                        re.DOTALL
                    )
                    
        except Exception as e:
            logger.warning(f"[RumbleScanner] Trending error: {e}")
        
        return candidates
    
    async def _search_videos(self, query: str) -> list[ContentCandidate]:
        """Search Rumble for videos."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        # Rumble search URL
        url = f"{self.base_url}/search?q={query.replace(' ', '%20')}"
        
        candidates = []
        
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return []
                
                # Look for video data in JSON format
                script_matches = re.findall(
                    r'<script[^>]*data-type="video"[^>]*>(.*?)</script>',
                    response.text,
                    re.DOTALL
                )
                
                for json_str in script_matches:
                    try:
                        data = json.loads(json_str)
                        videos = self._extract_videos_from_json(data)
                        candidates.extend(videos)
                    except:
                        pass
                        
        except Exception as e:
            logger.warning(f"[RumbleScanner] Search error: {e}")
        
        return candidates
    
    def _extract_videos_from_json(self, data: dict) -> list[ContentCandidate]:
        """Extract video data from Rumble JSON."""
        candidates = []
        
        try:
            # Handle single video object
            if "video" in data:
                video = self._parse_video_item(data.get("video", {}))
                if video:
                    candidates.append(video)
            
            # Handle array of videos
            if isinstance(data, list):
                for item in data:
                    video = self._parse_video_item(item)
                    if video:
                        candidates.append(video)
            
            # Handle nested data
            if "videos" in data:
                videos = data.get("videos", [])
                for video in videos:
                    parsed = self._parse_video_item(video)
                    if parsed:
                        candidates.append(parsed)
            
            if "items" in data:
                items = data.get("items", [])
                for item in items:
                    video = self._parse_video_item(item)
                    if video:
                        candidates.append(video)
                        
        except Exception as e:
            logger.debug(f"[RumbleScanner] JSON extraction error: {e}")
        
        return candidates
    
    def _parse_video_item(self, item: dict) -> ContentCandidate | None:
        """Parse a Rumble video item."""
        try:
            # Get video ID
            video_id = item.get("id", "") or item.get("video_id", "")
            if not video_id:
                return None
            
            # Get title
            title = item.get("title", "Rumble Video")
            if not title:
                title = item.get("name", "Rumble Video")
            
            # Get author/uploader
            author = "Unknown"
            if "author" in item:
                author_data = item.get("author", {})
                if isinstance(author_data, dict):
                    author = author_data.get("name", "Unknown") or author_data.get("username", "Unknown")
                elif isinstance(author_data, str):
                    author = author_data
            
            # Get thumbnail
            thumbnail = item.get("thumbnail", "") or item.get("image", "")
            if isinstance(thumbnail, dict):
                thumbnail = thumbnail.get("src", "") or thumbnail.get("url", "")
            
            # Get video URL
            url = item.get("url", "")
            if not url:
                slug = item.get("slug", "")
                url = f"{self.base_url}/{slug}" if slug else f"{self.base_url}/v/{video_id}"
            
            # Get duration
            duration = item.get("duration", 0)
            if isinstance(duration, str):
                duration = self._parse_duration(duration)
            
            # Get views
            views = item.get("views", 0)
            if not views:
                views = item.get("view_count", 0)
            if isinstance(views, str):
                views = self._parse_count(views)
            
            # Get engagement metrics
            likes = item.get("likes", 0)
            if isinstance(likes, str):
                likes = self._parse_count(likes)
            
            dislikes = item.get("dislikes", 0)
            if isinstance(dislikes, str):
                dislikes = self._parse_count(dislikes)
            
            # Calculate engagement rate
            engagement = likes + dislikes
            engagement_rate = engagement / max(views, 1) if views else 0.03
            
            # Get published date
            published = item.get("published", "")
            
            # Get description
            description = item.get("description", "") or item.get("summary", "")
            
            return ContentCandidate(
                id=f"rumble_{video_id}",
                platform="Rumble",
                url=url,
                author=author,
                title=title[:100] if title else "Rumble Video",
                view_count=views,
                engagement_rate=engagement_rate,
                thumbnail_url=thumbnail,
                duration_seconds=float(duration) if duration else 0.0,
                published_at=published,
                metadata={
                    "likes": likes,
                    "dislikes": dislikes,
                    "description": description
                }
            )
            
        except Exception as e:
            logger.debug(f"[RumbleScanner] Video parse error: {e}")
        
        return None
    
    def _parse_count(self, count_str: str) -> int:
        """Parse count string to integer."""
        if not count_str:
            return 0
        
        count_str = str(count_str).strip().lower()
        
        try:
            # Handle K, M suffixes
            if "k" in count_str:
                return int(float(count_str.replace("k", "")) * 1000)
            elif "m" in count_str:
                return int(float(count_str.replace("m", "")) * 1000000)
            else:
                return int(count_str.replace(",", ""))
        except:
            return 0
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to seconds."""
        if not duration_str:
            return 0
        
        try:
            # Try HH:MM:SS or MM:SS format
            parts = duration_str.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            
            # Try just seconds
            return int(duration_str)
        except:
            return 0


base_rumble_scanner = RumbleScanner()
