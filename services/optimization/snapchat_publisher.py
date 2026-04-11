"""
Snapchat Publisher for Viral Forge
Handles video uploads to Snapchat Spotlight via Snapchat Marketing API
Features: Retry logic, rate limiting, file validation, proper logging
"""

import asyncio
import os
from typing import Optional
import httpx
import logging

from .publisher_base import SocialPublisher, RetryConfig, RateLimitConfig
from .models import PostMetadata
from .auth import token_manager

logger = logging.getLogger(__name__)


class SnapchatPublisher(SocialPublisher):
    """Snapchat Spotlight video publisher with production-grade features"""

    def __init__(self):
        super().__init__(
            platform_name="snapchat",
            max_file_size_mb=1000,  # Snapchat limit
            supported_formats=["mp4", "mov"],
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
        """Snapchat-specific upload implementation"""
        access_token = await token_manager.get_token(
            "snapchat", user_id=user_id, account_id=account_id
        )

        if not access_token:
            logger.error(f"[SnapchatPublisher] No authentication for user {user_id}")
            return None

        video_url = await self._resolve_video_url(video_path)
        if not video_url:
            return None

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Step 1: Create Creative (Upload video)
            creative_url = (
                "https://adsapi.snapchat.com/v1/adaccounts/{ad_account_id}/creatives"
            )

            # Need to get ad account ID - this would come from OAuth setup
            ad_account_id = headers.get("snapchat_ad_account_id")
            if not ad_account_id:
                logger.error("[SnapchatPublisher] No ad account ID provided")
                return None

            creative_data = {
                "name": metadata.title[:80],  # Snapchat name limit
                "type": "VIDEO",
                "headline": metadata.title[:35],  # Spotlight headline limit
                "call_to_action": "VIEW_MORE",
                "video_url": video_url,
                "brand_name": "Viral Forge",
            }

            creative_response = await client.post(
                creative_url.format(ad_account_id=ad_account_id),
                json=creative_data,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if creative_response.status_code not in (200, 201):
                error_msg = creative_response.text
                logger.error(
                    f"[SnapchatPublisher] Creative creation failed: {error_msg}"
                )
                return None

            creative_result = creative_response.json()
            creative_id = creative_result.get("creative", {}).get("id")

            if not creative_id:
                logger.error("[SnapchatPublisher] No creative ID in response")
                return None

            logger.info(f"[SnapchatPublisher] Creative created: {creative_id}")

            # Step 2: Create Spotlight Post
            spotlight_url = "https://adsapi.snapchat.com/v1/spotlight"

            spotlight_data = {
                "creative_id": creative_id,
                "caption": self._build_caption(metadata),
                "call_to_action": "VIEW_MORE",
                "brand_safety": True,
            }

            spotlight_response = await client.post(
                spotlight_url,
                json=spotlight_data,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if spotlight_response.status_code in (200, 201):
                spotlight_result = spotlight_response.json()
                post_id = spotlight_result.get("spotlight", {}).get("id")

                if post_id:
                    logger.info(
                        f"[SnapchatPublisher] Spotlight post created: {post_id}"
                    )
                    return f"https://www.snapchat.com/spotlight/{post_id}"

            error_msg = spotlight_response.text
            logger.error(f"[SnapchatPublisher] Spotlight creation failed: {error_msg}")
            return None

    async def _resolve_video_url(self, video_path: str) -> Optional[str]:
        """Resolve video path to URL - upload to Snapchat's media endpoint"""
        if video_path.startswith(("http://", "https://")):
            return video_path

        if os.path.isfile(video_path):
            # Need to upload to Snapchat's media library first
            # This would require additional implementation
            logger.error(
                "[SnapchatPublisher] Local file upload not implemented - requires media library upload"
            )
            return None

        logger.error(f"[SnapchatPublisher] Invalid video path: {video_path}")
        return None

    def _build_caption(self, metadata: PostMetadata) -> str:
        """Build optimized caption from metadata"""
        parts = []
        if metadata.description:
            parts.append(metadata.description[:150])  # Snapchat caption limit
        if metadata.hashtags:
            tags = " ".join(
                h if h.startswith("#") else f"#{h}" for h in metadata.hashtags[:5]
            )
            parts.append(tags)
        return " ".join(parts)[:150]

    async def _get_metrics_impl(
        self,
        platform_id: str,
        user_id: int,
        account_id: Optional[int],
        headers: dict,
    ) -> dict:
        """Fetch Snapchat Spotlight metrics"""
        access_token = await token_manager.get_token(
            "snapchat", user_id=user_id, account_id=account_id
        )

        async with httpx.AsyncClient() as client:
            url = f"https://adsapi.snapchat.com/v1/spotlight/{platform_id}/stats"
            params = {
                "metrics": "impressions,views,saves,screenshots,shares",
                "granularity": "TOTAL",
            }

            response = await client.get(
                url, params=params, headers={"Authorization": f"Bearer {access_token}"}
            )

            data = response.json()

            if "stats" in data:
                stats = data["stats"]
                return {
                    "views": stats.get("views", 0),
                    "impressions": stats.get("impressions", 0),
                    "saves": stats.get("saves", 0),
                    "shares": stats.get("shares", 0),
                    "screenshots": stats.get("screenshots", 0),
                }

            return {"error": data.get("error", {}).get("message", "Unknown error")}

    async def health_check(self, user_id: int) -> bool:
        """Verify Snapchat credentials"""
        return await token_manager.get_token("snapchat", user_id=user_id) is not None


base_snapchat_publisher = SnapchatPublisher()
