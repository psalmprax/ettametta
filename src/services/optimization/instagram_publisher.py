"""
Instagram Publisher for ettametta
Handles video uploads to Instagram via Meta Graph API
Features: Retry logic, rate limiting, file validation, proper logging
"""

import asyncio
import httpx
import logging

from .publisher_base import SocialPublisher, RetryConfig, RateLimitConfig
from .models import PostMetadata
from .auth import token_manager

logger = logging.getLogger(__name__)


class InstagramPublisher(SocialPublisher):
    """Instagram video publisher with production-grade features"""

    def __init__(self):
        super().__init__(
            platform_name="instagram",
            max_file_size_mb=650,  # Instagram limit
            supported_formats=["mp4", "mov"],
            retry_config=RetryConfig(max_retries=3, base_delay=2.0),
            rate_limit_config=RateLimitConfig(max_retries=5),
        )

    async def _upload_impl(
        self,
        video_path: str,
        metadata: PostMetadata,
        user_id: str,
        account_id: int | None,
        headers: dict,
    ) -> str | None:
        """Instagram-specific upload implementation"""
        access_token = await token_manager.get_token(
            "instagram", user_id=user_id, account_id=account_id
        )

        if not access_token and "Cookie" not in headers:
            logger.error(f"[InstagramPublisher] No authentication for user {user_id}")
            return None

        video_uri = await self._resolve_video_uri(video_path)
        if not video_uri:
            return None

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Step 1: Create media container
            container_url = "https://graph.facebook.com/v18.0/me/media"
            container_data = {
                "media_type": "VIDEO",
                "video_uri": video_uri,
                "caption": self._build_caption(metadata),
                "access_token": access_token or headers.get("Cookie"),
            }

            container_response = await client.post(container_url, data=container_data)
            container_result = container_response.json()

            if "id" not in container_result:
                error_msg = container_result.get("error", {}).get(
                    "message", "Unknown error"
                )
                logger.error(
                    f"[InstagramPublisher] Container creation failed: {error_msg}"
                )
                return None

            container_id = container_result["id"]
            logger.info(f"[InstagramPublisher] Container created: {container_id}")

            # Step 2: Poll for media readiness (video processing takes time)
            max_polls = 60
            poll_interval = 5
            for _ in range(max_polls):
                await asyncio.sleep(poll_interval)
                status_url = f"https://graph.facebook.com/v18.0/{container_id}"
                status_resp = await client.get(
                    status_url, params={"access_token": access_token}
                )
                status_data = status_resp.json()

                if status_data.get("uri"):
                    break
                if "error" in status_data:
                    logger.error(
                        f"[InstagramPublisher] Media status error: {status_data}"
                    )
                    return None
            else:
                logger.error("[InstagramPublisher] Media processing timeout")
                return None

            # Step 3: Publish media
            publish_url = "https://graph.facebook.com/v18.0/me/media_publish"
            publish_data = {
                "creation_id": container_id,
                "access_token": access_token or headers.get("Cookie"),
            }

            publish_response = await client.post(publish_url, data=publish_data)
            publish_result = publish_response.json()

            if "id" in publish_result:
                media_id = publish_result["id"]
                logger.info(f"[InstagramPublisher] Published successfully: {media_id}")
                return f"https://instagram.com/p/{media_id}"

            error_msg = publish_result.get("error", {}).get(
                "message", str(publish_result)
            )
            logger.error(f"[InstagramPublisher] Publish failed: {error_msg}")
            return None

    async def _resolve_video_uri(self, video_path: str) -> str | None:
        """Resolve video path to URL - return if already URL, otherwise handle local file"""
        import os

        if video_path.startswith(("http://", "https://")):
            return video_path

        if os.path.isfile(video_path):
            logger.error(
                "[InstagramPublisher] Local files require S3/cloud storage for Instagram API. "
                "Cannot upload local files directly to Instagram."
            )
            return None

        logger.error(f"[InstagramPublisher] Invalid video path: {video_path}")
        return None

    def _build_caption(self, metadata: PostMetadata) -> str:
        """Build optimized caption from metadata"""
        parts = [metadata.title]
        if metadata.description:
            parts.append(f"\n\n{metadata.description}")
        if metadata.hashtags:
            tags = " ".join(
                h if h.startswith("#") else f"#{h}" for h in metadata.hashtags[:30]
            )
            parts.append(f"\n\n{tags}")
        if metadata.cta:
            parts.append(f"\n\n{metadata.cta}")
        return "".join(parts)[:2200]  # Instagram caption limit

    async def _get_metrics_impl(
        self,
        platform_id: str,
        user_id: str,
        account_id: int | None,
        headers: dict,
    ) -> dict:
        """Fetch Instagram media insights"""
        access_token = await token_manager.get_token(
            "instagram", user_id=user_id, account_id=account_id
        )

        async with httpx.AsyncClient() as client:
            url = f"https://graph.facebook.com/v18.0/{platform_id}/insights"
            params = {
                "metric": "views,likes,comments,saves,shares",
                "access_token": access_token or headers.get("Cookie"),
            }

            response = await client.get(url, params=params)
            data = response.json()

            if "data" in data:
                metrics = {}
                for item in data["data"]:
                    metrics[item["name"]] = item.get("values", [{}])[0].get("value", 0)
                return {
                    "views": metrics.get("views", 0),
                    "likes": metrics.get("likes", 0),
                    "comments": metrics.get("comments", 0),
                    "saves": metrics.get("saves", 0),
                    "shares": metrics.get("shares", 0),
                }

            return {"error": data.get("error", {}).get("message", "Unknown error")}

    async def health_check(self, user_id: str) -> bool:
        """Verify Instagram credentials"""
        return await token_manager.get_token("instagram", user_id=user_id) is not None


base_instagram_service = InstagramPublisher()
