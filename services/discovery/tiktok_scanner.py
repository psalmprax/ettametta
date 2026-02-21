import httpx
import re
import json
from typing import List, Optional
from .models import ContentCandidate
import random
from datetime import datetime
import logging

class TikTokScanner:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        ]

    async def scan_trends(self, niche: str, published_after: Optional[datetime] = None) -> List[ContentCandidate]:
        """
        Scans TikTok for trending videos in a niche by scraping the public search page.
        This is a cost-free alternative to paid APIs.
        """
        print(f"[TikTokScanner] Real scan for niche: {niche}...")
        
        url = f"https://www.tiktok.com/search/video?q={niche.replace(' ', '%20')}"
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    print(f"[TikTokScanner] Scrape Failed: Status {response.status_code}")
                    return []

                # Extracts JSON data from the __UNIVERSAL_DATA_FOR_REHYDRATION__ script tag
                # which contains the search results in a structured format.
                match = re.search(r'id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)<\/script>', response.text)
                if not match:
                    print("[TikTokScanner] No rehydration data found in TikTok response")
                    return []

                raw_data = json.loads(match.group(1))
                # The path to search results can change, we'll try to find the standard 2026 structure
                # This is a common pattern for TikTok's SSR data
                video_list = []
                try:
                    # Traverses the complex rehydration object
                    default_scope = raw_data.get("__DEFAULT_SCOPE__", {})
                    search_results = default_scope.get("webapp.search-video", {}).get("data", {}).get("item_list", [])
                    video_list = search_results
                except Exception as e:
                    logging.error(f"Parsing TikTok JSON failed: {e}")

                candidates = []
                for i, item in enumerate(video_list):
                    video_id = item.get("id")
                    if not video_id: continue
                    
                    # Estimate publication date if not present (TikTok scrape is limited)
                    # For filtering, we'll check if it matches the horizon if we can find a timestamp
                    # Otherwise, we'll include it to avoid empty results on scrape.
                    create_time = item.get("createTime")
                    if create_time and published_after:
                        pub_dt = datetime.fromtimestamp(int(create_time))
                        if pub_dt < published_after:
                            continue

                    author_data = item.get("author", {})
                    stats = item.get("stats", {})
                    
                    views = stats.get("playCount", 0)
                    engagement_score = self._calc_engagement(stats)
                    duration_seconds = float(item.get("video", {}).get("duration", 0))
                    
                    # Calculate viral score (Scrape-based fallback logic)
                    viral_score = int((views / 10000) * (1 + engagement_score * 5))
                    viral_score = min(max(viral_score, 1), 95)

                    candidates.append(ContentCandidate(
                        id=f"tt_{video_id}",
                        platform="TikTok",
                        url=f"https://www.tiktok.com/@{author_data.get('uniqueId', 'user')}/video/{video_id}",
                        author=author_data.get("nickname", "Unknown Creator"),
                        title=item.get("desc", f"Viral {niche} Insight"),
                        description=item.get("desc", ""),
                        view_count=views, # Legacy
                        engagement_rate=engagement_score, # Legacy
                        views=views,
                        engagement_score=engagement_score,
                        viral_score=viral_score,
                        duration_seconds=duration_seconds,
                        discovery_date=datetime.now(),
                        tags=item.get("challenges", []),
                        thumbnail_url=item.get("video", {}).get("cover"),
                        metadata={
                            "cover": item.get("video", {}).get("cover"),
                            "duration": duration_seconds,
                            "published_at": datetime.fromtimestamp(int(create_time)).isoformat() if create_time else None
                        }
                    ))
                    
                    if len(candidates) >= 5: break
                
                if not candidates:
                    return []
                return candidates

        except Exception as e:
            logging.error(f"TikTok Scanner Error: {e}")
            return []

    def _calc_engagement(self, stats: dict) -> float:
        plays = stats.get("playCount", 1)
        likes = stats.get("diggCount", 0)
        comments = stats.get("commentCount", 0)
        shares = stats.get("shareCount", 0)
        if plays == 0: return 0.0
        return (likes + comments + shares) / plays
