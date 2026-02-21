from .scanner_base import TrendScanner
from .models import ContentCandidate
from typing import List, Optional
import random
from api.config import settings
from googleapiclient.discovery import build
import datetime
import re

from api.utils.vault import get_secret

class YouTubeShortsScanner(TrendScanner):
    async def scan_trends(self, niche: str, published_after: Optional[datetime.datetime] = None) -> List[ContentCandidate]:
        """
        Scans YouTube for trending Shorts in a specific niche using the Data API v3.
        """
        api_key = get_secret("youtube_api_key")
        if not api_key:
            print("[YouTubeScanner] ERROR: No YOUTUBE_API_KEY found. Cannot scan trends.")
            raise ValueError("YouTube API key not configured. Please set YOUTUBE_API_KEY in environment.")

        try:
            youtube = build("youtube", "v3", developerKey=api_key)
            
            # 1. Search for trending videos in the niche
            # We filter for 'short' duration and 'video' type
            search_params = {
                "q": f"{niche} #shorts",
                "part": "id,snippet",
                "maxResults": 10,
                "type": "video",
                "videoDuration": "short",
                "relevanceLanguage": "en",
                "order": "viewCount"
            }
            
            if published_after:
                search_params["publishedAfter"] = published_after.isoformat().replace("+00:00", "") + "Z"

            search_response = youtube.search().list(**search_params).execute()

            candidates = []
            for item in search_response.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                
                # 2. Get detailed video stats
                video_response = youtube.videos().list(
                    id=video_id,
                    part="statistics,contentDetails"
                ).execute()
                
                video_data = video_response["items"][0] if video_response.get("items") else {}
                stats = video_data.get("statistics", {})
                content_details = video_data.get("contentDetails", {})
                
                # Parse duration
                duration_str = content_details.get("duration", "PT0S")
                duration_seconds = self._parse_duration(duration_str)
                
                views = int(stats.get("viewCount", 0))
                engagement_score = self._calculate_engagement(stats)
                
                # Calculate viral score (Real metrics)
                pub_date_str = snippet.get("publishedAt")
                viral_score = self._calculate_viral_score(views, pub_date_str, engagement_score)

                candidates.append(ContentCandidate(
                    id=f"yt_{video_id}",
                    platform="YouTube Shorts",
                    url=f"https://youtube.com/shorts/{video_id}",
                    author=snippet.get("channelTitle", "Unknown"),
                    title=snippet.get("title", "No Title"),
                    view_count=views, # Legacy
                    engagement_rate=engagement_score, # Legacy
                    views=views,
                    engagement_score=engagement_score,
                    viral_score=viral_score,
                    duration_seconds=float(duration_seconds),
                    tags=[niche, "Shorts", "Trending"],
                    thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url") or snippet.get("thumbnails", {}).get("default", {}).get("url"),
                    metadata={
                        "published_at": pub_date_str,
                        "thumbnails": snippet.get("thumbnails"),
                        "video_id": video_id,
                        "duration": duration_str
                    }
                ))
            
            return candidates

        except Exception as e:
            print(f"[YouTubeScanner] ERROR: {str(e)}")
            raise ValueError(f"YouTube API error: {str(e)}")

    def _calculate_engagement(self, stats: dict) -> float:
        views = int(stats.get("viewCount", 1))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        return (likes + comments) / views if views > 0 else 0.0

    def _calculate_viral_score(self, views: int, published_at: str, engagement_score: float) -> int:
        if not published_at:
            return int(views / 1000)
        try:
            pub_date = datetime.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            hours_since = (datetime.datetime.now(datetime.timezone.utc) - pub_date).total_seconds() / 3600
            velocity = views / max(hours_since, 1)
            # Viral score = base velocity weight + engagement bonus
            score = int((velocity / 100) * (1 + engagement_score * 10))
            return min(max(score, 1), 99) # Keep it in 1-99 range for UI aesthetics
        except:
            return 0

    def _parse_duration(self, duration_str: str) -> int:
        """Parses ISO 8601 duration string like PT1M30S into seconds."""
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(duration_str)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds

    def identify_viral_velocity(self, candidate: ContentCandidate) -> float:
        # Better velocity: views per hour since publication
        pub_date_str = candidate.metadata.get("published_at") if candidate.metadata else None
        if not pub_date_str:
            return candidate.view_count / 24 # Fallback
            
        pub_date = datetime.datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
        hours_since = (datetime.datetime.now(datetime.timezone.utc) - pub_date).total_seconds() / 3600
        return candidate.view_count / max(hours_since, 1)

    def _get_mock_data(self, niche: str) -> List[ContentCandidate]:
        return [
            ContentCandidate(
                id=f"yt_mock_{i}",
                platform="YouTube Shorts",
                url=f"http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                author=f"Creator_{i}",
                title=f"The Future of AI in {niche}",
                view_count=random.randint(50000, 1000000),
                engagement_rate=random.uniform(0.05, 0.15),
                views=random.randint(50000, 1000000),
                engagement_score=random.uniform(0.05, 0.15),
                viral_score=random.randint(40, 95),
                duration_seconds=float(random.randint(15, 60)),
                tags=["AI", niche, "Tech", "Viral"],
                thumbnail_url=f"http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/ForBiggerBlazes.jpg"
            )
            for i in range(3)
        ]
