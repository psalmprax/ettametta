from .scanner_base import TrendScanner
from .models import ContentCandidate
from typing import List, Optional
import random
from api.config import settings
from googleapiclient.discovery import build
import datetime
import re

class YouTubeLongScanner(TrendScanner):
    async def scan_trends(self, niche: str, published_after: Optional[datetime.datetime] = None) -> List[ContentCandidate]:
        """
        Scans YouTube for high-performance long-form videos (4-20 mins) in a niche.
        """
        if not settings.YOUTUBE_API_KEY:
            return []

        try:
            youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
            
            # Search for 'medium' duration (4 to 20 mins)
            search_params = {
                "q": f"{niche} guide",
                "part": "id,snippet",
                "maxResults": 5,
                "type": "video",
                "videoDuration": "medium",
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
                
                video_response = youtube.videos().list(
                    id=video_id,
                    part="statistics,contentDetails"
                ).execute()
                
                if not video_response.get("items"): continue
                
                v_data = video_response["items"][0]
                stats = v_data["statistics"]
                # Duration is in ISO 8601 (e.g. PT10M30S)
                duration_raw = v_data["contentDetails"]["duration"]
                duration_seconds = self._parse_duration(duration_raw)
                
                views = int(stats.get("viewCount", 0))
                engagement_score = self._calculate_engagement(stats)
                
                # Calculate viral score (Pillar specific)
                pub_date_str = snippet.get("publishedAt")
                viral_score = self._calculate_viral_score(views, pub_date_str, engagement_score)

                candidates.append(ContentCandidate(
                    id=f"yt_long_{video_id}",
                    platform="YouTube (Pillar)",
                    url=f"https://youtube.com/watch?v={video_id}",
                    author=snippet.get("channelTitle", "Unknown"),
                    title=snippet.get("title", "No Title"),
                    view_count=views, # Legacy
                    engagement_rate=engagement_score, # Legacy
                    views=views,
                    engagement_score=engagement_score,
                    viral_score=viral_score,
                    duration_seconds=float(duration_seconds),
                    tags=[niche, "Pillar", "Long-Form"],
                    metadata={
                        "published_at": pub_date_str,
                        "duration": duration_raw,
                        "type": "pillar"
                    }
                ))
            
            return candidates

        except Exception as e:
            print(f"[YouTubeLongScanner] ERROR: {str(e)}")
            return []

    def _calculate_engagement(self, stats: dict) -> float:
        views = int(stats.get("viewCount", 1))
        likes = int(stats.get("likeCount", 0))
        return likes / views if views > 0 else 0.0

    def _calculate_viral_score(self, views: int, published_at: str, engagement_score: float) -> int:
        if not published_at:
            return int(views / 10000)
        try:
            pub_date = datetime.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            hours_since = (datetime.datetime.now(datetime.timezone.utc) - pub_date).total_seconds() / 3600
            # Long form has slower velocity expectations
            velocity = views / max(hours_since, 1)
            score = int((velocity / 500) * (1 + engagement_score * 20))
            return min(max(score, 1), 99)
        except:
            return 0

    def _parse_duration(self, duration_str: str) -> int:
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(duration_str)
        if not match: return 0
        h = int(match.group(1) or 0)
        m = int(match.group(2) or 0)
        s = int(match.group(3) or 0)
        return h * 3600 + m * 60 + s

    def identify_viral_velocity(self, candidate: ContentCandidate) -> float:
        return candidate.views / 100 # Rough estimate for long-form
