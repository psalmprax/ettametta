import aiohttp
import logging
from typing import List, Optional
from .models import ContentCandidate

class RedditScanner:
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.subreddits = ["videos", "nextfuckinglevel", "shorts", "SpecialPeopleDoingThings"]
        self.headers = {
            "User-Agent": "ettametta/1.0 (Enterprise Content Engine)"
        }

    async def scan_trends(self, niche: str, published_after: Optional[any] = None) -> List[ContentCandidate]:
        """
        Scans top subreddits for trending video content.
        Note: Uses the .json endpoint to fetch data without requiring Oauth for public reads.
        """
        logging.info(f"[Reddit] Scanning subreddits for niche context: {niche}")
        candidates = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for sub in self.subreddits:
                try:
                    url = f"{self.base_url}/r/{sub}/top.json?t=day&limit=10"
                    async with session.get(url) as response:
                        if response.status != 200:
                            logging.warning(f"[Reddit] Failed to fetch /r/{sub}: {response.status}")
                            continue
                        
                        data = await response.json()
                        posts = data.get("data", {}).get("children", [])
                        
                        for post in posts:
                            post_data = post.get("data", {})
                            
                            # We only care about video posts
                            is_video = post_data.get("is_video", False)
                            hint_url = post_data.get("url", "")
                            
                            if not is_video and not any(ext in hint_url for ext in [".mp4", "youtube.com", "v.redd.it"]):
                                continue

                            candidate = ContentCandidate(
                                id=f"reddit_{post_data.get('id')}",
                                platform="Reddit",
                                thumbnail_url=post_data.get('thumbnail') if post_data.get('thumbnail', '').startswith('http') else None,
                                url=post_data.get("url"),
                                author=post_data.get("author"),
                                title=post_data.get("title"),
                                view_count=post_data.get("ups", 0), # Using upvotes as view/traction proxy
                                engagement_rate=post_data.get("upvote_ratio", 0.0),
                                metadata={
                                    "subreddit": sub,
                                    "num_comments": post_data.get("num_comments"),
                                    "award_count": post_data.get("total_awards_received", 0)
                                }
                            )
                            candidates.append(candidate)
                            
                except Exception as e:
                    logging.error(f"[Reddit] Error scanning /r/{sub}: {e}")
                    
        return candidates

base_reddit_scanner = RedditScanner()
