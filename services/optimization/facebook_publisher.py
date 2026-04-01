"""
Facebook Publisher for Viral Forge
Handles video uploads to Facebook via Meta Graph API
"""

from .publisher_base import SocialPublisher
from .models import PostMetadata
from typing import Optional
from .auth import token_manager
import httpx


class FacebookPublisher(SocialPublisher):
    async def upload_video(
        self,
        video_path: str,
        metadata: PostMetadata,
        user_id: int,
        account_id: Optional[int] = None,
    ) -> Optional[str]:
        """
        Uploads a video to Facebook via Meta Graph API.
        """
        # 1. Get Auth Headers (OAuth or Cookies)
        headers = token_manager.get_auth_headers("facebook", user_id, account_id)
        
        access_token = token_manager.get_token("facebook", user_id=user_id, account_id=account_id)
        if not access_token and "Cookie" not in headers:
            print(f"[FacebookPublisher] ERROR: No authentication (token or cookies) for user {user_id}.")
            return None

        try:
            # Create video on Facebook
            video_url = video_path  # Would need to be a public URL

            upload_url = "https://graph.facebook.com/v18.0/me/videos"
            video_data = {
                "file_url": video_url,
                "title": metadata.title[:60],
                "description": metadata.description[:500],
                "access_token": access_token or headers.get("Cookie"), # Fallback for Graph API
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(upload_url, data=video_data)
                result = response.json()

                if "id" in result:
                    video_id = result["id"]
                    return f"https://www.facebook.com/watch/?v={video_id}"
                else:
                    print(f"[FacebookPublisher] Failed: {result}")
                    return None

        except Exception as e:
            print(f"[FacebookPublisher] FAILED: {str(e)}")
            return None

    async def ensure_valid_token(self, user_id: int, account_id: Optional[int] = None):
        """Token validation and refresh via TokenManager"""
        return await token_manager.ensure_valid_token(
            "facebook", user_id=user_id, account_id=account_id
        )

    def health_check(self, user_id: int) -> bool:
        return token_manager.get_token("facebook", user_id=user_id) is not None


base_facebook_publisher = FacebookPublisher()
