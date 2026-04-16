import httpx
import logging
import json
import re
import random
from typing import List, Optional
from datetime import datetime
from .models import ContentCandidate

logger = logging.getLogger(__name__)


class LinkedInScanner:
    """
    Scans LinkedIn for trending professional content in a niche.
    Uses web scraping to discover popular posts and videos.
    Note: LinkedIn has strong anti-scraping measures, results may be limited.
    """
    
    def __init__(self):
        self.platform = "LinkedIn"
        self.base_url = "https://www.linkedin.com"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]
    
    async def scan_trends(self, niche: str, published_after: Optional[datetime] = None) -> List[ContentCandidate]:
        """
        Scans LinkedIn for trending professional content in a niche.
        Uses search and pulse (news) pages.
        """
        logger.info(f"[LinkedInScanner] Scanning LinkedIn for: {niche}")
        
        candidates = []
        
        # Try feed/trending
        try:
            results = await self._get_feed(niche)
            candidates.extend(results)
        except Exception as e:
            logger.warning(f"[LinkedInScanner] Feed fetch failed: {e}")
        
        # Try search
        if not candidates:
            try:
                results = await self._search_posts(niche)
                candidates.extend(results)
            except Exception as e:
                logger.warning(f"[LinkedInScanner] Search failed: {e}")
        
        # Remove duplicates
        seen = set()
        unique = []
        for c in candidates:
            if c.url not in seen:
                seen.add(c.url)
                unique.append(c)
        
        logger.info(f"[LinkedInScanner] Found {len(unique)} posts")
        return unique[:15]
    
    async def _get_feed(self, niche: str) -> List[ContentCandidate]:
        """Get LinkedIn feed/trending posts."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        # Try LinkedIn feed URL
        url = f"{self.base_url}/feed/"
        
        candidates = []
        
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return []
                
                # LinkedIn heavily uses JS, try to find any JSON data
                script_matches = re.findall(
                    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    response.text,
                    re.DOTALL
                )
                
                for json_str in script_matches:
                    try:
                        data = json.loads(json_str)
                        posts = self._extract_posts_from_json(data)
                        candidates.extend(posts)
                    except:
                        pass
                        
        except Exception as e:
            logger.warning(f"[LinkedInScanner] Feed error: {e}")
        
        return candidates
    
    async def _search_posts(self, niche: str) -> List[ContentCandidate]:
        """Search LinkedIn for posts."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        # LinkedIn search URL
        url = f"{self.base_url}/search/results/content/?keywords={niche.replace(' ', '%20')}"
        
        candidates = []
        
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return []
                
                # Try to extract JSON data
                script_matches = re.findall(
                    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    response.text,
                    re.DOTALL
                )
                
                for json_str in script_matches:
                    try:
                        data = json.loads(json_str)
                        posts = self._extract_posts_from_json(data)
                        candidates.extend(posts)
                    except:
                        pass
                        
        except Exception as e:
            logger.warning(f"[LinkedInScanner] Search error: {e}")
        
        return candidates
    
    def _extract_posts_from_json(self, data: dict) -> List[ContentCandidate]:
        """Extract post data from LinkedIn JSON."""
        candidates = []
        
        try:
            # Navigate LinkedIn's JSON
            props = data.get("props", {})
            page_props = props.get("pageProps", {})
            
            # Try to find feed data
            feed_data = page_props.get("feedData", {})
            if not feed_data:
                feed_data = page_props.get("data", {})
            
            # Look for elements
            elements = feed_data.get("elements", [])
            
            for element in elements:
                post = self._parse_post(element)
                if post:
                    candidates.append(post)
            
            # Try alternate path
            if not candidates:
                # Recursively search for posts
                candidates = self._find_posts_recursive(data)
                    
        except Exception as e:
            logger.debug(f"[LinkedInScanner] JSON extraction error: {e}")
        
        return candidates
    
    def _find_posts_recursive(self, obj, depth=0) -> List[ContentCandidate]:
        """Recursively search for post objects."""
        candidates = []
        
        if depth > 4:
            return candidates
            
        if isinstance(obj, dict):
            # Check if this looks like a post
            if "urn" in obj and ("update" in str(obj).lower() or "post" in str(obj).lower()):
                post = self._parse_post(obj)
                if post:
                    candidates.append(post)
            
            # Recurse
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    candidates.extend(self._find_posts_recursive(value, depth + 1))
                    
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    candidates.extend(self._find_posts_recursive(item, depth + 1))
        
        return candidates
    
    def _parse_post(self, item: dict) -> Optional[ContentCandidate]:
        """Parse a single LinkedIn post."""
        try:
            # Get the post URN/ID
            urn = item.get("urn", "")
            if not urn:
                return None
            
            # Extract post ID from URN
            post_id = urn.split(":")[-1] if urn else str(hash(str(item)))[-8:]
            
            # Get update info
            update = item.get("updateMetadata", {}) or item.get("update", {})
            
            # Get author
            actor = update.get("actor", {}) or item.get("actor", {})
            author = actor.get("name", {}).get("text", "Unknown")
            if not author:
                author = actor.get("subDescription", {}).get("text", "Unknown")
            
            # Get title/content
            headline = update.get("header", {}) or {}
            title = headline.get("text", "LinkedIn Post")
            
            # Try to get description/caption
            desc = update.get("description", {})
            if not title:
                title = desc.get("text", "LinkedIn Post")
            
            summary = update.get("summary", {})
            if not title:
                title = summary.get("text", "LinkedIn Post")[:100]
            
            # Get URL
            target = update.get("target", {})
            url = target.get("navigation", {}).get("actionLink", "")
            if not url:
                url = f"{self.base_url}/feed/update/{post_id}"
            
            # Get metrics
            social_metadata = item.get("socialMetadata", {})
            likes = social_metadata.get("totalLikes", 0) or social_metadata.get("likes", 0)
            comments = social_metadata.get("totalComments", 0) or social_metadata.get("comments", 0)
            shares = social_metadata.get("shares", 0)
            
            # Estimate views
            engagement = likes + comments + shares
            views = engagement * 30  # LinkedIn typically has higher engagement
            engagement_rate = engagement / max(views, 1) if views else 0.03
            
            # Get thumbnail if present
            image = target.get("image", [])
            thumbnail = image[0] if image else ""
            if isinstance(thumbnail, dict):
                thumbnail = thumbnail.get("url", "")
            
            return ContentCandidate(
                id=f"li_{post_id}",
                platform="LinkedIn",
                url=url,
                author=author,
                title=title[:100] if title else "LinkedIn Post",
                view_count=views,
                engagement_rate=engagement_rate,
                thumbnail_url=thumbnail,
                metadata={"likes": likes, "comments": comments, "shares": shares}
            )
            
        except Exception as e:
            logger.debug(f"[LinkedInScanner] Post parse error: {e}")
        
        return None


base_linkedin_scanner = LinkedInScanner()
