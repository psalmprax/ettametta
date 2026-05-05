import httpx
import logging
import json
import re
import random
from datetime import datetime
from .models import ContentCandidate

logger = logging.getLogger(__name__)


class BilibiliScanner:
    """
    Scans Bilibili for trending videos in a niche.
    Bilibili is a major Chinese video platform with English interface available.
    Uses web scraping to discover popular content.
    """
    
    def __init__(self):
        self.platform = "Bilibili"
        self.base_url = "https://www.bilibili.com"
        self.api_url = "https://api.bilibili.com"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        ]
    
    async def scan_trends(self, niche: str, published_after: datetime | None = None, **kwargs) -> list[ContentCandidate]:
        """
        Scans Bilibili for trending videos in a niche.
        Uses the popular/ranking page and search functionality.
        """
        logger.info(f"[BilibiliScanner] Scanning Bilibili for: {niche}")
        
        candidates = []
        
        # Try trending/ranking
        try:
            results = await self._get_popular(niche)
            candidates.extend(results)
        except Exception as e:
            logger.warning(f"[BilibiliScanner] Popular fetch failed: {e}")
        
        # Try search
        if not candidates:
            try:
                results = await self._search_videos(niche)
                candidates.extend(results)
            except Exception as e:
                logger.warning(f"[BilibiliScanner] Search failed: {e}")
        
        # Remove duplicates
        seen = set()
        unique = []
        for c in candidates:
            if c.source_uri not in seen:
                seen.add(c.source_uri)
                unique.append(c)
        
        logger.info(f"[BilibiliScanner] Found {len(unique)} videos")
        return unique[:15]
    
    async def _get_popular(self, niche: str) -> list[ContentCandidate]:
        """Get Bilibili popular/ranking videos."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bilibili.com"
        }
        
        # Bilibili ranking/popular API
        url = f"{self.api_url}/x/web-interface/ranking/v2?rid=0&type=all"
        
        candidates = []
        
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                list_data = data.get("data", {}).get("list", [])
                
                for item in list_data:
                    video = self._parse_video_item(item)
                    if video:
                        candidates.append(video)
                        
        except Exception as e:
            logger.warning(f"[BilibiliScanner] Popular error: {e}")
        
        return candidates
    
    async def _search_videos(self, query: str) -> list[ContentCandidate]:
        """Search Bilibili for videos."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bilibili.com"
        }
        
        # Bilibili search API
        url = f"{self.api_url}/x/web-interface/search/type?search_type=video&keyword={query.replace(' ', '%20')}&page=1&page_size=20"
        
        candidates = []
        
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                result_list = data.get("data", {}).get("result", [])
                
                for item in result_list:
                    video = self._parse_search_item(item)
                    if video:
                        candidates.append(video)
                        
        except Exception as e:
            logger.warning(f"[BilibiliScanner] Search error: {e}")
        
        return candidates
    
    def _parse_video_item(self, item: dict) -> ContentCandidate | None:
        """Parse a Bilibili video item from ranking/popular."""
        try:
            bvid = item.get("bvid", "")
            aid = item.get("aid", 0)
            
            if not bvid and not aid:
                return None
            
            # Get title (Bilibili uses escape characters)
            title = item.get("title", "")
            if title:
                # Remove HTML tags
                title = re.sub(r'<[^>]+>', '', title)
            
            # Get author
            author = item.get("author", "Unknown")
            
            # Get stats
            view = item.get("view", 0)
            like = item.get("like", 0)
            coin = item.get("coin", 0)
            favorite = item.get("favorite", 0)
            share = item.get("share", 0)
            reply = item.get("reply", 0)
            
            # Views might be in different format
            if isinstance(view, str):
                view = self._parse_count(view)
            
            # Calculate engagement
            engagement = like + coin + favorite + share + reply
            views = view if isinstance(view, int) else 0
            engagement_score = engagement / max(views, 1) if views else 0.05
            
            # Get thumbnail (Bilibili uses specific format)
            pic = item.get("pic", "")
            if pic:
                thumbnail = f"https:{pic}" if not pic.startswith("http") else pic
            else:
                thumbnail = ""
            
            # Get URL
            url = f"{self.base_url}/video/{bvid}"
            
            # Get duration
            duration_str = item.get("duration", "00:00")
            duration_seconds = self._parse_duration(duration_str)
            
            # Get description
            description = item.get("desc", "")
            
            # Get tags
            tags = item.get("tag", [])
            
            return ContentCandidate(
                id=f"bilibili_{bvid or aid}",
                platform="Bilibili",
                source_uri=url,
                creator_name=author,
                title=title or "Bilibili Video",
                view_count=views,
                like_count=like,
                comment_count=reply,
                share_count=share,
                engagement_score=engagement_score,
                thumbnail_uri=thumbnail,
                duration_seconds=duration_seconds,
                metadata={
                    "likes": like,
                    "coins": coin,
                    "favorites": favorite,
                    "shares": share,
                    "replies": reply,
                    "tags": tags,
                    "description": description
                }
            )
            
        except Exception as e:
            logger.debug(f"[BilibiliScanner] Video parse error: {e}")
        
        return None
    
    def _parse_search_item(self, item: dict) -> ContentCandidate | None:
        """Parse a Bilibili video item from search results."""
        try:
            bvid = item.get("bvid", "")
            aid = item.get("aid", 0)
            
            if not bvid and not aid:
                return None
            
            # Get title
            title = item.get("title", "")
            if title:
                # Remove HTML tags
                title = re.sub(r'<[^>]+>', '', title)
            
            # Get author
            author = item.get("author", "Unknown")
            
            # Get description
            description = item.get("description", "")
            
            # Get stats (search results have different format)
            view = item.get("view", 0)
            if isinstance(view, str):
                view = self._parse_count(view)
            
            like = item.get("like", 0)
            if isinstance(like, str):
                like = self._parse_count(like)
            
            # Calculate engagement
            engagement = like
            views = view if isinstance(view, int) else 0
            engagement_score = engagement / max(views, 1) if views else 0.05
            
            # Get thumbnail
            pic = item.get("pic", "")
            if pic:
                thumbnail = f"https:{pic}" if not pic.startswith("http") else pic
            else:
                thumbnail = ""
            
            # Get URL
            url = f"{self.base_url}/video/{bvid}"
            
            # Get duration
            duration_str = item.get("duration", "00:00")
            duration_seconds = self._parse_duration(duration_str)
            
            return ContentCandidate(
                id=f"bilibili_{bvid or aid}",
                platform="Bilibili",
                source_uri=url,
                creator_name=author,
                title=title or "Bilibili Video",
                view_count=views,
                like_count=like,
                comment_count=0,
                share_count=0,
                engagement_score=engagement_score,
                thumbnail_uri=thumbnail,
                duration_seconds=duration_seconds,
                metadata={"description": description}
            )
            
        except Exception as e:
            logger.debug(f"[BilibiliScanner] Search parse error: {e}")
        
        return None
    
    def _parse_count(self, count_str: str) -> int:
        """Parse Chinese number format (e.g., 10.5万 = 1050000)."""
        if not count_str:
            return 0
        
        count_str = str(count_str).strip()
        
        try:
            if "万" in count_str:
                return int(float(count_str.replace("万", "")) * 10000)
            elif "万" in count_str:
                return int(float(count_str.replace("万", "")) * 10000)
            else:
                return int(count_str)
        except:
            return 0
    
    def _parse_duration(self, duration_str: str) -> float:
        """Parse duration string to seconds."""
        if not duration_str:
            return 0.0
        
        parts = duration_str.split(":")
        try:
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except:
            pass
        
        return 0.0


base_bilibili_service = BilibiliScanner()
