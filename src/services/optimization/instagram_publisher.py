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
from src.services.storage.service import base_storage_service

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

    async def _get_ig_user_id(
        self,
        access_token: str,
        client: httpx.AsyncClient,
    ) -> str | None:
        """Resolve the Instagram Business Account ID from the Facebook user's connected Pages.
        
        The Instagram Graph API requires the IG User ID (Instagram Business Account ID)
        in the URL path for media container creation, not 'me'. This resolves it by:
        1. Getting the user's Facebook Pages: GET /me/accounts
        2. Getting the Instagram Business Account for each Page: GET /{page-id}?fields=instagram_business_account
        """
        try:
            # Step 1: Get Facebook Pages the user manages
            pages_resp = await client.get(
                "https://graph.facebook.com/v20.0/me/accounts",
                params={"access_token": access_token, "limit": 10},
            )
            pages_data = pages_resp.json()

            pages = pages_data.get("data", [])
            if not pages:
                logger.warning(
                    "[InstagramPublisher] No Facebook Pages found for user. "
                    "Instagram Business Account must be connected to a Facebook Page."
                )
                return None

            # Step 2: For each Page, check if it has a connected Instagram Business Account
            for page in pages:
                page_id = page["id"]
                page_token = page.get("access_token", access_token)

                page_resp = await client.get(
                    f"https://graph.facebook.com/v20.0/{page_id}",
                    params={
                        "fields": "instagram_business_account",
                        "access_token": page_token,
                    },
                )
                page_info = page_resp.json()

                ig_account = page_info.get("instagram_business_account")
                if ig_account:
                    ig_id = ig_account.get("id")
                    logger.info(
                        f"[InstagramPublisher] Found IG Business Account: {ig_id} (Page: {page_id})"
                    )
                    return ig_id

            logger.warning(
                "[InstagramPublisher] No Facebook Page has an Instagram Business Account connected."
            )
            return None

        except Exception as e:
            logger.exception(
                f"[InstagramPublisher] Failed to resolve IG user ID: {e}"
            )
            return None

    async def _upload_impl(
        self,
        video_path: str,
        metadata: PostMetadata,
        user_id: str,
        account_id: int | None,
        headers: dict,
    ) -> str | None:
        """Instagram-specific upload implementation via Instagram Graph API"""
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
            # Step 0: Resolve the Instagram Business Account ID
            # Instagram Graph API requires /{ig-user-id}/media, NOT /me/media
            ig_user_id = await self._get_ig_user_id(
                access_token or headers.get("Cookie", ""), client
            )
            if not ig_user_id:
                logger.error(
                    "[InstagramPublisher] Could not resolve IG Business Account ID. "
                    "User must have an Instagram Business Account connected to a Facebook Page."
                )
                return None

            # Step 1: Create media container
            container_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media"
            container_data = {
                "media_type": "VIDEO",
                "video_url": video_uri,
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
                status_url = f"https://graph.facebook.com/v20.0/{container_id}"
                status_resp = await client.get(
                    status_url, params={"access_token": access_token}
                )
                status_data = status_resp.json()

                if status_data.get("id"):
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
            publish_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish"
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
        """
        Resolve video path to a publicly accessible URL.
        - If already a URL, return as-is.
        - If a local file, upload to cloud storage and return the presigned URL.
        """
        import os

        if video_path and video_path.startswith(("http://", "https://")):
            return video_path

        if os.path.isfile(video_path):
            logger.info(
                f"[InstagramPublisher] Uploading local file to cloud storage: {video_path}"
            )
            try:
                # Upload to configured cloud storage (S3/OCI/GCP) and get a presigned URL
                object_key = base_storage_service.upload_to_cloud(video_path)
                if object_key:
                    url = base_storage_service.get_file_url(object_key, expiration=86400)
                    if url:
                        logger.info(
                            f"[InstagramPublisher] File uploaded, using URL: {url}"
                        )
                        return url

                logger.warning(
                    "[InstagramPublisher] Cloud upload returned no URL. "
                    "Falling back to local static serving."
                )
                # Fallback: serve locally via the static outputs endpoint
                from src.api.config import settings
                filename = os.path.basename(video_path)
                local_url = f"{settings.PRODUCTION_DOMAIN}/static/outputs/{filename}"
                logger.info(f"[InstagramPublisher] Using local static URL: {local_url}")
                return local_url

            except Exception as e:
                logger.exception(
                    f"[InstagramPublisher] Failed to upload local file to cloud: {e}"
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
