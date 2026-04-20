"""
YouTube Publisher for ettametta
Handles video uploads to YouTube via Data API v3
Features: Circuit breaker, token refresh, resumable uploads, proper logging
"""

import os
import logging

from .publisher_base import SocialPublisher, RetryConfig, RateLimitConfig
from .models import PostMetadata
from .auth import token_manager

logger = logging.getLogger(__name__)


class YouTubePublisher(SocialPublisher):
    """YouTube video publisher with production-grade features"""

    def __init__(self):
        super().__init__(
            platform_name="youtube",
            max_file_size_mb=256,  # YouTube Shorts limit
            supported_formats=["mp4", "mov"],
            retry_config=RetryConfig(max_retries=3, base_delay=2.0),
            rate_limit_config=RateLimitConfig(max_retries=5),
        )

    async def _upload_impl(
        self,
        video_path: str,
        metadata: PostMetadata,
        user_id: int,
        account_id: int | None,
        headers: dict,
    ) -> str | None:
        """YouTube-specific upload implementation"""
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials

        access_token = await token_manager.get_token(
            "youtube", user_id=user_id, account_id=account_id
        )
        if not access_token:
            logger.error(f"[YouTubePublisher] No authentication for user {user_id}")
            return None

        try:
            creds = Credentials(token=access_token)
            youtube = build("youtube", "v3", credentials=creds)

            body = {
                "snippet": {
                    "title": metadata.title[:100],
                    "description": f"{metadata.description}\n\n#shorts {' '.join(metadata.hashtags[:15])}",
                    "categoryId": "22",
                },
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
            }

            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            request = youtube.videos().insert(
                part="snippet,status", body=body, media_body=media
            )

            logger.info(f"[YouTubePublisher] Uploading {video_path} to YouTube...")
            response = request.execute()

            video_id = response.get("id")
            if video_id:
                logger.info(f"[YouTubePublisher] Uploaded successfully: {video_id}")
                return f"https://youtube.com/shorts/{video_id}"

            logger.error("[YouTubePublisher] No video ID in response")
            return None

        except Exception as e:
            logger.error(f"[YouTubePublisher] Upload failed: {e}")
            return None

    async def _get_metrics_impl(
        self,
        platform_id: str,
        user_id: int,
        account_id: int | None,
        headers: dict,
    ) -> dict:
        """Fetch YouTube video statistics"""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        access_token = await token_manager.get_token(
            "youtube", user_id=user_id, account_id=account_id
        )
        if not access_token:
            return {"error": "No authentication"}

        try:
            creds = Credentials(token=access_token)
            youtube = build("youtube", "v3", credentials=creds)

            request = youtube.videos().list(part="statistics", id=platform_id)
            response = request.execute()

            if not response.get("items"):
                return {"views": 0, "likes": 0, "comments": 0, "shares": 0}

            stats = response["items"][0]["statistics"]
            return {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "shares": 0,
            }
        except Exception as e:
            logger.error(f"[YouTubePublisher] Metrics fetch failed: {e}")
            return {"error": str(e)}

    async def health_check(self, user_id: int) -> bool:
        """Verify YouTube credentials"""
        return await token_manager.get_token("youtube", user_id=user_id) is not None


base_youtube_publisher = YouTubePublisher()
