"""
Facebook Publisher for Viral Forge
Handles video uploads to Facebook via Meta Graph API
Features: Retry logic, rate limiting, file validation, proper logging
"""

from typing import Optional
import httpx
import logging

from .publisher_base import SocialPublisher, RetryConfig, RateLimitConfig
from .models import PostMetadata
from .auth import token_manager

logger = logging.getLogger(__name__)


class FacebookPublisher(SocialPublisher):
    """Facebook video publisher with production-grade features"""

    def __init__(self):
        super().__init__(
            platform_name="facebook",
            max_file_size_mb=1024,  # Facebook limit
            supported_formats=["mp4", "mov", "avi"],
            retry_config=RetryConfig(max_retries=3, base_delay=2.0),
            rate_limit_config=RateLimitConfig(max_retries=5),
        )

    async def _upload_impl(
        self,
        video_path: str,
        metadata: PostMetadata,
        user_id: int,
        account_id: Optional[int],
        headers: dict,
    ) -> Optional[str]:
        """Facebook-specific upload implementation"""
        access_token = token_manager.get_token(
            "facebook", user_id=user_id, account_id=account_id
        )

        if not access_token and "Cookie" not in headers:
            logger.error(f"[FacebookPublisher] No authentication for user {user_id}")
            return None

        video_url = await self._resolve_video_url(video_path)
        if not video_url:
            return None

        async with httpx.AsyncClient(timeout=300.0) as client:
            upload_url = "https://graph.facebook.com/v18.0/me/videos"
            video_data = {
                "file_url": video_url,
                "title": metadata.title[:60],
                "description": metadata.description[:500],
                "access_token": access_token or headers.get("Cookie"),
            }

            response = await client.post(upload_url, data=video_data)
            result = response.json()

            if "id" in result:
                video_id = result["id"]
                logger.info(f"[FacebookPublisher] Published successfully: {video_id}")
                return f"https://www.facebook.com/watch/?v={video_id}"

            error_msg = result.get("error", {}).get("message", str(result))
            logger.error(f"[FacebookPublisher] Upload failed: {error_msg}")
            return None

    async def _resolve_video_url(self, video_path: str) -> Optional[str]:
        """Resolve video path to URL"""
        import os

        if video_path.startswith(("http://", "https://")):
            return video_path

        if os.path.isfile(video_path):
            logger.warning(
                "[FacebookPublisher] Local files require S3/cloud storage for Facebook API. "
                "Configure a storage provider for local file uploads."
            )
            return video_path

        logger.error(f"[FacebookPublisher] Invalid video path: {video_path}")
        return None

    async def _get_metrics_impl(
        self,
        platform_id: str,
        user_id: int,
        account_id: Optional[int],
        headers: dict,
    ) -> dict:
        """Fetch Facebook video insights"""
        access_token = token_manager.get_token(
            "facebook", user_id=user_id, account_id=account_id
        )

        async with httpx.AsyncClient() as client:
            url = f"https://graph.facebook.com/v18.0/{platform_id}/insights"
            params = {
                "metric": "total_views,total_reactions,total_comments,total_shares",
                "access_token": access_token or headers.get("Cookie"),
            }

            response = await client.get(url, params=params)
            data = response.json()

            if "data" in data:
                metrics = {}
                for item in data["data"]:
                    metrics[item["name"]] = item.get("values", [{}])[0].get("value", 0)
                return {
                    "views": metrics.get("total_views", 0),
                    "likes": metrics.get("total_reactions", 0),
                    "comments": metrics.get("total_comments", 0),
                    "shares": metrics.get("total_shares", 0),
                }

            return {"error": data.get("error", {}).get("message", "Unknown error")}

    def health_check(self, user_id: int) -> bool:
        """Verify Facebook credentials"""
        return token_manager.get_token("facebook", user_id=user_id) is not None


base_facebook_publisher = FacebookPublisher()
