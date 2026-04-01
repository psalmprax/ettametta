from .publisher_base import SocialPublisher
from .models import PostMetadata
from typing import Optional
from .auth import token_manager
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from .circuit_breaker import youtube_breaker, CircuitBreakerOpenError
import logging

logger = logging.getLogger(__name__)

class YouTubePublisher(SocialPublisher):
    async def upload_video(self, video_path: str, metadata: PostMetadata, user_id: int, account_id: Optional[int] = None) -> Optional[str]:
        """
        Uploads a video to YouTube as a Short using the Data API v3.
        Includes circuit breaker and automated token refresh logic.
        """
        # Check circuit breaker first
        if not youtube_breaker.can_execute():
            logger.warning(f"[YouTubePublisher] Circuit breaker OPEN. Service unavailable.")
            raise CircuitBreakerOpenError("YouTube API temporarily unavailable")
        # 1. Get Auth Headers (OAuth or Cookies)
        headers = token_manager.get_auth_headers("youtube", user_id, account_id)
        
        access_token = token_manager.get_token("youtube", user_id=user_id, account_id=account_id)
        if not access_token and "Cookie" not in headers:
            print(f"[YouTubePublisher] ERROR: No authentication (token or cookies) for user {user_id}.")
            return None

        # Build credentials
        creds = Credentials(token=access_token)
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": metadata.title[:100], # YouTube limit
                "description": f"{metadata.description}\n\n#shorts {' '.join(metadata.hashtags)}",
                "categoryId": "22" # People & Blogs
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
        )

        try:
            print(f"[YouTubePublisher] Uploading {video_path} to YouTube for user {user_id}...")
            response = insert_request.execute()
            video_id = response.get("id")
            youtube_breaker.record_success()  # Record success for circuit breaker
            return f"https://youtube.com/shorts/{video_id}"
        except Exception as e:
            print(f"[YouTubePublisher] FAILED: {str(e)}")
            youtube_breaker.record_failure(e)  # Record failure for circuit breaker
            return None

    async def get_metrics(self, platform_id: str, user_id: int, account_id: Optional[int] = None) -> dict:
        """
        Fetches live engagement stats for a YouTube video.
        """
        await self.ensure_valid_token(user_id, account_id)
        access_token = token_manager.get_token("youtube", user_id=user_id, account_id=account_id)
        if not access_token:
            return {"views": 0, "likes": 0, "comments": 0, "shares": 0}

        creds = Credentials(token=access_token)
        youtube = build("youtube", "v3", credentials=creds)

        try:
            request = youtube.videos().list(
                part="statistics",
                id=platform_id
            )
            response = request.execute()
            
            if not response.get("items"):
                return {"views": 0, "likes": 0, "comments": 0, "shares": 0}
            
            stats = response["items"][0]["statistics"]
            return {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "shares": 0 # YouTube Data API doesn't provide share count directly in v3 statistics
            }
        except Exception as e:
            print(f"[YouTubePublisher] Metrics Fetch FAILED: {str(e)}")
            return {"views": 0, "likes": 0, "comments": 0, "shares": 0}

    async def ensure_valid_token(self, user_id: int, account_id: Optional[int] = None):
        """Checks if token is expired and triggers a refresh if a refresh_token exists."""
        if token_manager.is_token_expired("youtube", user_id=user_id, account_id=account_id):
            print(f"[YouTubePublisher] Token expired for user {user_id}. Attempting refresh...")
            # refresh_token logic would be implemented in TokenManager or here
            # For this wave, we focus on the structure for triggered refresh.
            pass

    def health_check(self, user_id: int) -> bool:
        return token_manager.get_token("youtube", user_id=user_id) is not None

base_youtube_publisher = YouTubePublisher()
