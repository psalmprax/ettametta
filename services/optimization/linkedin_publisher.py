"""
LinkedIn Publisher for Viral Forge
Handles video uploads to LinkedIn via LinkedIn Marketing API (3-step: register → upload → post)
"""

from .publisher_base import SocialPublisher
from .models import PostMetadata
from typing import Optional
from .auth import token_manager
import httpx
import os
import logging

logger = logging.getLogger(__name__)


class LinkedInPublisher(SocialPublisher):
    async def upload_video(
        self,
        video_path: str,
        metadata: PostMetadata,
        user_id: int,
        account_id: Optional[int] = None,
    ) -> Optional[str]:
        """Uploads a video to LinkedIn via 3-step flow: register → upload → create post."""
        # 1. Get Auth Headers (OAuth or Cookies)
        headers = token_manager.get_auth_headers("linkedin", user_id, account_id)
        if not headers:
            logger.error(f"[LinkedInPublisher] No authentication (token or cookies) for user {user_id}")
            return None

        # Ensure restli protocol version is present
        headers["X-Restli-Protocol-Version"] = "2.0.0"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Step 1: Register upload
                register_url = (
                    "https://api.linkedin.com/v2/assets?action=registerUpload"
                )
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
                    logger.error(
                        "[LinkedInPublisher] No asset URN in register response"
                    )
                    return None

                # Step 2: Upload binary to LinkedIn's S3 upload URL
                if upload_url:
                    # Read video file
                    file_data = None
                    if os.path.isfile(video_path):
                        with open(video_path, "rb") as f:
                            file_data = f.read()
                    else:
                        dl_resp = await client.get(video_path)
                        if dl_resp.status_code == 200:
                            file_data = dl_resp.content

                    if file_data:
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
                                f"[LinkedInPublisher] Binary upload failed: "
                                f"{upload_resp.status_code} {upload_resp.text}"
                            )
                            return None
                        logger.info("[LinkedInPublisher] Binary upload complete")
                    else:
                        logger.error("[LinkedInPublisher] Could not read video data")
                        return None
                else:
                    logger.warning(
                        "[LinkedInPublisher] No upload URL provided; "
                        "asset may already be uploaded or API response changed"
                    )

                # Step 3: Create UGC post wrapping the uploaded asset
                post_url = "https://api.linkedin.com/v2/ugcPosts"
                post_text = metadata.title or ""
                if metadata.description:
                    post_text += f"\n\n{metadata.description}"
                if metadata.hashtags:
                    post_text += "\n\n" + " ".join(
                        h if h.startswith("#") else f"#{h}" for h in metadata.hashtags
                    )

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
                                    "title": {
                                        "text": (metadata.title or "Video")[:200]
                                    },
                                    "media": asset,
                                }
                            ],
                        }
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                    },
                }

                logger.info("[LinkedInPublisher] Creating UGC post...")
                post_resp = await client.post(post_url, json=post_data, headers=headers)
                if post_resp.status_code in (200, 201):
                    post_id = post_resp.json().get("id", "")
                    logger.info(f"[LinkedInPublisher] Post created: {post_id}")
                    return f"https://www.linkedin.com/feed/update/{post_id}"

                logger.error(
                    f"[LinkedInPublisher] Post creation failed: "
                    f"{post_resp.status_code} {post_resp.text}"
                )
                return None

        except Exception as e:
            logger.error(f"[LinkedInPublisher] Upload failed: {e}")
            return None

    async def ensure_valid_token(self, user_id: int, account_id: Optional[int] = None):
        """Token validation and refresh via TokenManager"""
        return await token_manager.ensure_valid_token(
            "linkedin", user_id=user_id, account_id=account_id
        )

    def health_check(self, user_id: int) -> bool:
        return token_manager.get_token("linkedin", user_id=user_id) is not None


base_linkedin_publisher = LinkedInPublisher()
