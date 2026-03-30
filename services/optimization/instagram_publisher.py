"""
Instagram Publisher for Viral Forge
Handles video uploads to Instagram via Meta Graph API
"""

from .publisher_base import SocialPublisher
from .models import PostMetadata
from typing import Optional
from .auth import token_manager
import httpx


class InstagramPublisher(SocialPublisher):
    async def upload_video(
        self,
        video_path: str,
        metadata: PostMetadata,
        user_id: int,
        account_id: Optional[int] = None,
    ) -> Optional[str]:
        """
        Uploads a video to Instagram via Meta Graph API.
        """
        # 1. Get access token
        access_token = token_manager.get_token(
            "instagram", user_id=user_id, account_id=account_id
        )
        if not access_token:
            print(
                f"[InstagramPublisher] ERROR: No access token found for user {user_id}. Please authenticate via Dashboard."
            )
            return None

        try:
            # 2. Create media container
            container_url = "https://graph.facebook.com/v18.0/me/media"

            # Extract video URL or use local file (for cloud storage)
            video_url = video_path  # Would need to be a public URL for Instagram API

            container_data = {
                "media_type": "VIDEO",
                "video_url": video_url,
                "caption": f"{metadata.title}\n\n{metadata.description}\n\n{' '.join(metadata.hashtags)}",
                "access_token": access_token,
            }

            async with httpx.AsyncClient() as client:
                # Create media container
                container_response = await client.post(
                    container_url, data=container_data
                )
                container_result = container_response.json()

                if "id" not in container_result:
                    print(
                        f"[InstagramPublisher] Failed to create container: {container_result}"
                    )
                    return None

                container_id = container_result["id"]

                # 3. Publish media
                publish_url = "https://graph.facebook.com/v18.0/me/media_publish"
                publish_data = {
                    "creation_id": container_id,
                    "access_token": access_token,
                }

                publish_response = await client.post(publish_url, data=publish_data)
                publish_result = publish_response.json()

                if "id" in publish_result:
                    media_id = publish_result["id"]
                    return f"https://instagram.com/p/{media_id}"
                else:
                    print(f"[InstagramPublisher] Failed to publish: {publish_result}")
                    return None

        except Exception as e:
            print(f"[InstagramPublisher] FAILED: {str(e)}")
            return None

    async def ensure_valid_token(self, user_id: int, account_id: Optional[int] = None):
        """Token validation and refresh via TokenManager"""
        return await token_manager.ensure_valid_token(
            "instagram", user_id=user_id, account_id=account_id
        )

    def health_check(self, user_id: int) -> bool:
        return token_manager.get_token("instagram", user_id=user_id) is not None


base_instagram_publisher = InstagramPublisher()
