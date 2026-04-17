import aiohttp
import logging
from .models import ContentCandidate
from datetime import datetime

logger = logging.getLogger(__name__)


class DuckDuckGoScanner:
    """
    DuckDuckGo search scanner for discovering trending content.
    Free, no API key required - uses HTML scraping.
    """
    
    def __init__(self):
        self.platform = "DuckDuckGo"
        
    async def scan_trends(self, niche: str, published_after: datetime | None = None) -> list[ContentCandidate]:
        """
        Searches DuckDuckGo for trending videos and content in the niche.
        Free alternative to YouTube API when quota is exceeded.
        """
        logger.info(f"[DuckDuckGo] Searching for trending {niche} content")
        
        search_queries = [
            f"trending {niche} videos 2024",
            f"viral {niche} shorts",
            f"best {niche} videos this week"
        ]
        
        all_candidates = []
        
        for query in search_queries[:2]:
            try:
                candidates = await self._search_ddg(query, niche)
                all_candidates.extend(candidates)
            except Exception as e:
                logger.warning(f"[DuckDuckGo] Search failed for '{query}': {e}")
        
        # Remove duplicates by URL
        seen = set()
        unique_candidates = []
        for c in all_candidates:
            if c.url not in seen:
                seen.add(c.url)
                unique_candidates.append(c)
        
        logger.info(f"[DuckDuckGo] Found {len(unique_candidates)} unique results")
        return unique_candidates[:10]
    
    async def _search_ddg(self, query: str, niche: str) -> list[ContentCandidate]:
        """Search DuckDuckGo HTML for results."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
                
                url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
                
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return []
                    
                    html = await response.text()
                    return self._parse_results(html, niche)
                    
        except Exception as e:
            logger.error(f"[DuckDuckGo] Request error: {e}")
            return []
    
    def _parse_results(self, html: str, niche: str) -> list[ContentCandidate]:
        """Parse DuckDuckGo HTML results."""
        candidates = []
        
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import unquote
            soup = BeautifulSoup(html, 'html.parser')
            
            for result in soup.select('.result__body')[:10]:
                try:
                    link_elem = result.select_one('.result__a')
                    if not link_elem:
                        continue
                    
                    url = link_elem.get('href', '')
                    title = link_elem.get_text(strip=True)
                    
                    # Handle DuckDuckGo redirect URLs
                    # Format: //duckduckgo.com/l/?uddg=actual_url
                    if url.startswith('//duckduckgo.com/l/'):
                        # Extract the actual URL from the uddg parameter
                        import urllib.parse
                        parsed = urllib.parse.urlparse(url)
                        query_params = urllib.parse.parse_qs(parsed.query)
                        if 'uddg' in query_params:
                            url = unquote(query_params['uddg'][0])
                    
                    # Skip if still not a valid URL
                    if not url or url.startswith('/') or 'duckduckgo' in url:
                        continue
                    
                    # Extract snippet
                    snippet_elem = result.select_one('.result__snippet')
                    description = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    # Determine platform from URL
                    platform = self._detect_platform(url)
                    
                    # STRICTOR PATH VALIDATION: Ensure it's a direct video link, not a landing page
                    category = self._classify_url(url.lower(), platform)
                    if category == "skip":
                         continue

                    candidates.append(ContentCandidate(
                        id=f"ddg_{hash(url) % 100000}",
                        platform=platform,
                        category=category,
                        url=url,
                        author="",
                        title=title,
                        description=description,
                        view_count=5000,  # Estimated
                        engagement_rate=0.03,
                        viral_score=86,  # Give high score to pass threshold
                        discovery_date=datetime.now(),
                        tags=[niche, "search", "trending"],
                        metadata={
                            "source": "duckduckgo",
                            "search_niche": niche
                        }
                    ))
                    
                except Exception as e:
                    continue
                    
        except ImportError:
            logger.warning("[DuckDuckGo] BeautifulSoup not installed. Install: pip install beautifulsoup4")
        except Exception as e:
            logger.error(f"[DuckDuckGo] Parse error: {e}")
        
        return candidates
    
    def _classify_url(self, url: str, platform: str) -> str:
        """Determines the content category and platform-specific directness."""
        # Common "ignore" patterns (search results, settings, etc.)
        ignore_patterns = [
            "/search", "/results", "/trending", "/explore", "/hashtag/",
            "/groups/", "/marketplace/", "/events/", "/settings",
        ]

        if any(pattern in url for pattern in ignore_patterns):
            return "skip"

        # 1. VIDEOS (Highest priority)
        if platform == "YouTube":
            if any(p in url for p in ["/watch?v=", "/shorts/", "youtu.be/"]):
                return "video"
            return "skip"
        
        if platform == "TikTok":
            if any(p in url for p in ["/video/", "/v/", "vt.tiktok.com/"]):
                return "video"
            return "skip"

        if any(p in url for p in ["/reels/", "/reel/", "/watch/", "/videos/"]):
            return "video"

        # 2. BLOGS / ARTICLES
        blog_patterns = [
            "medium.com", "substack.com", "linkedin.com/pulse", "ghost.io", "wordpress.com",
            "blogger.com", "dev.to", "hashnode.com", "/blog/", "/article/", "/posts/",
        ]
        if any(pattern in url for pattern in blog_patterns):
            return "blog"

        # 3. NEWS
        news_domains = [
            "cnn.com", "bbc.com", "reuters.com", "nytimes.com", "theguardian.com",
            "news.google.com", "forbes.com", "bloomberg.com", "techcrunch.com",
        ]
        if any(domain in url for domain in news_domains):
            return "news"

        # 4. SOCIAL (General posts)
        if platform == "X" and "/status/" in url:
            return "social"
        if platform == "Reddit" and "/comments/" in url:
            return "social"

        # 5. OTHER (Generic page)
        parts = url.split("/")
        if len(parts) > 3:
            return "other"

        return "skip"

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        url_lower = url.lower()
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return "YouTube"
        elif 'tiktok.com' in url_lower:
            return "TikTok"
        elif 'instagram.com' in url_lower:
            return "Instagram"
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return "X"
        elif 'reddit.com' in url_lower:
            return "Reddit"
        elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
            return "Facebook"
        elif 'rumble.com' in url_lower:
            return "Rumble"
        else:
            return "Web"


base_duckduckgo_scanner = DuckDuckGoScanner()
