"""
LinkedIn Publisher for Viral Forge
Handles video uploads to LinkedIn via LinkedIn Marketing API (3-step: register → upload → post)
Features: Retry logic, rate limiting, file validation, proper logging
"""

import os
import httpx
import logging

from .publisher_base import SocialPublisher, RetryConfig, RateLimitConfig
from .models import PostMetadata
from .auth import token_manager

logger = logging.getLogger(__name__)


class LinkedInPublisher(SocialPublisher):
    """LinkedIn video publisher with production-grade features"""

    def __init__(self):
        super().__init__(
            platform_name="linkedin",
            max_file_size_mb=512,  # LinkedIn limit
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
        """LinkedIn-specific upload implementation"""
        if not headers:
            logger.error(f"[LinkedInPublisher] No authentication for user {user_id}")
            return None

        headers["X-Restli-Protocol-Version"] = "2.0.0"

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Step 1: Register upload
            register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
            register_data = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                    "owner": f"urn:li:person:{user_id}",
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent",
                        }
                    ],
                }
            }

            logger.info("[LinkedInPublisher] Registering upload...")
            register_resp = await client.post(
                register_url, json=register_data, headers=headers
            )

            if register_resp.status_code not in (200, 201):
                logger.error(
                    f"[LinkedInPublisher] Register failed: {register_resp.status_code} {register_resp.text}"
                )
                return None

            reg_value = register_resp.json().get("value", {})
            asset = reg_value.get("asset")
            upload_mechanism = reg_value.get("uploadMechanism", {})
            upload_url = upload_mechanism.get(
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}
            ).get("uploadUrl")

            if not asset:
                logger.error("[LinkedInPublisher] No asset URN in register response")
                return None

            # Step 2: Upload binary to LinkedIn's S3 upload URL
            if not upload_url:
                logger.warning("[LinkedInPublisher] No upload URL in response")
                return None

            file_data = await self._load_video_data(video_path, client)
            if not file_data:
                logger.error("[LinkedInPublisher] Could not load video data")
                return None

            logger.info(
                f"[LinkedInPublisher] Uploading {len(file_data)} bytes to LinkedIn storage..."
            )
            upload_headers = headers.copy()
            upload_headers["Content-Type"] = "application/octet-stream"
            upload_resp = await client.put(
                upload_url, content=file_data, headers=upload_headers
            )

            if upload_resp.status_code not in (200, 201):
                logger.error(
                    f"[LinkedInPublisher] Binary upload failed: {upload_resp.status_code} {upload_resp.text}"
                )
                return None

            logger.info("[LinkedInPublisher] Binary upload complete")

            # Step 3: Create UGC post
            post_url = "https://api.linkedin.com/v2/ugcPosts"
            post_text = self._build_post_text(metadata)

            post_data = {
                "author": f"urn:li:person:{user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": post_text[:3000]},
                        "shareMediaCategory": "VIDEO",
                        "media": [
                            {
                                "status": "READY",
                                "title": {"text": (metadata.title or "Video")[:200]},
                                "media": asset,
                            }
                        ],
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            }

            logger.info("[LinkedInPublisher] Creating UGC post...")
            post_resp = await client.post(post_url, json=post_data, headers=headers)

            if post_resp.status_code in (200, 201):
                post_id = post_resp.json().get("id", "")
                logger.info(f"[LinkedInPublisher] Post created: {post_id}")
                return f"https://www.linkedin.com/feed/update/{post_id}"

            logger.error(
                f"[LinkedInPublisher] Post creation failed: {post_resp.status_code} {post_resp.text}"
            )
            return None

    async def _load_video_data(
        self, video_path: str, client: httpx.AsyncClient
    ) -> bytes | None:
        """Load video data from path or URL"""
        if os.path.isfile(video_path):
            with open(video_path, "rb") as f:
                return f.read()

        if video_path.startswith(("http://", "https://")):
            dl_resp = await client.get(video_path)
            if dl_resp.status_code == 200:
                return dl_resp.content

        return None

    def _build_post_text(self, metadata: PostMetadata) -> str:
        """Build post text from metadata"""
        parts = [metadata.title]
        if metadata.description:
            parts.append(f"\n\n{metadata.description}")
        if metadata.hashtags:
            tags = " ".join(
                h if h.startswith("#") else f"#{h}" for h in metadata.hashtags[:10]
            )
            parts.append(f"\n\n{tags}")
        if metadata.cta:
            parts.append(f"\n\n{metadata.cta}")
        return "".join(parts)

    async def _get_metrics_impl(
        self,
        platform_id: str,
        user_id: int,
        account_id: int | None,
        headers: dict,
    ) -> dict:
        """Fetch LinkedIn post metrics"""
        async with httpx.AsyncClient() as client:
            url = f"https://api.linkedin.com/v2/ugcPosts/{platform_id}"

            response = await client.get(url, headers=headers)
            data = response.json()

            if "id" in data:
                return {
                    "views": data.get("viewCount", 0),
                    "likes": data.get("likeCount", 0),
                    "comments": data.get("commentCount", 0),
                    "shares": data.get("shareCount", 0),
                }

            return {"error": data.get("message", "Unknown error")}

    async def health_check(self, user_id: int) -> bool:
        """Verify LinkedIn credentials"""
        return await token_manager.get_token("linkedin", user_id=user_id) is not None


base_linkedin_publisher = LinkedInPublisher()
