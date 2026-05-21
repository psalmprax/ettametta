"""
Facebook Publisher for ettametta
Handles video uploads to Facebook via Meta Graph API
Features: Retry logic, rate limiting, file validation, proper logging
"""

import asyncio
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
        user_id: str,
        account_id: int | None,
        headers: dict,
    ) -> str | None:
        """Facebook-specific upload implementation"""
        access_token = await token_manager.get_token(
            "facebook", user_id=user_id, account_id=account_id
        )

        if not access_token and "Cookie" not in headers:
            logger.error(f"[FacebookPublisher] No authentication for user {user_id}")
            return None

        video_uri = await self._resolve_video_uri(video_path)
        if not video_uri:
            return None

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Step 1: Create video container (similar to Instagram approach)
            container_url = "https://graph.facebook.com/v20.0/me/videos"
            container_data = {
                "upload_phase": "start",
                "access_token": access_token or headers.get("Cookie"),
            }

            container_response = await client.post(container_url, data=container_data)
            container_result = container_response.json()

            if "upload_session_id" not in container_result:
                error_msg = container_result.get("error", {}).get(
                    "message", str(container_result)
                )
                logger.error(
                    f"[FacebookPublisher] Container creation failed: {error_msg}"
                )
                return None

            upload_session_id = container_result["upload_session_id"]
            logger.info(
                f"[FacebookPublisher] Upload session created: {upload_session_id}"
            )

            # Step 2: Upload video content
            upload_url = f"https://graph.facebook.com/v20.0/{upload_session_id}"
            upload_data = {
                "upload_phase": "transfer",
                "access_token": access_token or headers.get("Cookie"),
                "file_url": video_uri,
            }

            upload_response = await client.post(upload_url, data=upload_data)
            upload_result = upload_response.json()

            if "success" not in upload_result or not upload_result.get("success"):
                error_msg = upload_result.get("error", {}).get(
                    "message", str(upload_result)
                )
                logger.error(f"[FacebookPublisher] Upload failed: {error_msg}")
                return None

            logger.info(f"[FacebookPublisher] Video uploaded successfully")

            # Step 3: Finalize upload
            finalize_url = f"https://graph.facebook.com/v20.0/{upload_session_id}"
            finalize_data = {
                "upload_phase": "finish",
                "access_token": access_token or headers.get("Cookie"),
                "title": metadata.title[:60],
                "description": metadata.description[:500],
            }

            finalize_response = await client.post(finalize_url, data=finalize_data)
            finalize_result = finalize_response.json()

            if "success" not in finalize_result or not finalize_result.get("success"):
                error_msg = finalize_result.get("error", {}).get(
                    "message", str(finalize_result)
                )
                logger.error(f"[FacebookPublisher] Finalize failed: {error_msg}")
                return None

            # Step 4: Poll for processing completion (like Instagram)
            video_id = finalize_result.get("video_id")
            if not video_id:
                logger.error("[FacebookPublisher] No video_id in finalize response")
                return None

            max_polls = 60
            poll_interval = 5
            for _ in range(max_polls):
                await asyncio.sleep(poll_interval)
                status_url = f"https://graph.facebook.com/v20.0/{video_id}"
                status_params = {
                    "fields": "status",
                    "access_token": access_token or headers.get("Cookie"),
                }
                status_resp = await client.get(status_url, params=status_params)
                status_data = status_resp.json()

                if status_data.get("status", {}).get("video_status") == "ready":
                    break
                if "error" in status_data:
                    logger.error(
                        f"[FacebookPublisher] Status check error: {status_data}"
                    )
                    return None
            else:
                logger.error("[FacebookPublisher] Video processing timeout")
                return None

            logger.info(f"[FacebookPublisher] Published successfully: {video_id}")
            return f"https://www.facebook.com/watch/?v={video_id}"

    async def _resolve_video_uri(self, video_path: str) -> str | None:
        """Resolve video path to URL"""
        import os

        if video_path and video_path.startswith(("http://", "https://")):
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
        user_id: str,
        account_id: int | None,
        headers: dict,
    ) -> dict:
        """Fetch Facebook video insights"""
        access_token = await token_manager.get_token(
            "facebook", user_id=user_id, account_id=account_id
        )

        async with httpx.AsyncClient() as client:
            url = f"https://graph.facebook.com/v20.0/{platform_id}/insights"
            params = {
                "metric": "total_video_views,total_video_reactions,total_video_comments,total_video_shares",
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

    async def health_check(self, user_id: str) -> bool:
        """Verify Facebook credentials"""
        return await token_manager.get_token("facebook", user_id=user_id) is not None


base_facebook_publisher_service = FacebookPublisher()
