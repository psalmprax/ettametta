"""
Real Social Media Publishing Service
====================================
Handles OAuth authentication and video uploading to major platforms.
"""

import logging
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Google API imports (for YouTube)
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

logger = logging.getLogger(__name__)


class YouTubePublisher:
    """Handles real YouTube video uploads via Data API v3."""

    def __init__(self):
        self.client_id = os.getenv('YOUTUBE_CLIENT_ID')
        self.client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
        self.token_dir = Path("data/storage/tokens")
        self.token_dir.mkdir(parents=True, exist_ok=True)

    def _get_credentials(self, user_id: str) -> Optional[Any]:
        """Load user credentials from disk."""
        token_file = self.token_dir / f"youtube_{user_id}.json"
        if not token_file.exists():
            logger.warning(f"No YouTube token found for user {user_id}")
            return None
        
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            creds = Credentials(
                token=token_data['token'],
                refresh_token=token_data.get('refresh_token'),
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=['https://www.googleapis.com/auth/youtube.upload']
            )
            return creds
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return None

    async def upload_video(
        self, 
        user_id: str,
        video_path: str, 
        title: str, 
        description: str, 
        tags: list[str], 
        privacy_status: str = "private"
    ) -> dict[str, Any]:
        """
        Upload a video to YouTube using real API.
        """
        if not GOOGLE_API_AVAILABLE:
            raise Exception("Google API libraries not installed. Run: pip install google-api-python-client google-auth-oauthlib")
        
        creds = self._get_credentials(user_id)
        if not creds:
            raise Exception("YouTube account not connected. Please authenticate first.")

        try:
            youtube = build('youtube', 'v3', credentials=creds)
            
            body = {
                'snippet': {
                    'title': title[:100],  # YouTube limit
                    'description': description[:5000],  # YouTube limit
                    'tags': tags[:50],  # YouTube limit
                    'categoryId': '28'  # Science & Technology (default)
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }

            # Check if file exists
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

            insert_request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=MediaFileUpload(
                    video_path, 
                    chunksize=-1, 
                    resumable=True
                )
            )

            logger.info(f"Starting upload for {title}...")
            response = insert_request.execute()
            
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"Successfully uploaded: {video_url}")
            
            return {
                "platform": "youtube",
                "video_id": video_id,
                "url": video_url,
                "status": "published",
                "privacy": privacy_status,
                "published_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"YouTube upload failed: {str(e)}")
            raise Exception(f"YouTube upload failed: {str(e)}")


class PublishingService:
    """Unified service for multi-platform publishing."""

    def __init__(self):
        self.youtube = YouTubePublisher()

    async def publish_to_platform(
        self, 
        user_id: str,
        platform: str, 
        video_path: str, 
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Publish video to specified platform.
        """
        if platform == "youtube":
            return await self.youtube.upload_video(
                user_id=user_id,
                video_path=video_path,
                title=metadata.get("title", "Untitled"),
                description=metadata.get("description", ""),
                tags=metadata.get("tags", []),
                privacy_status=metadata.get("privacy", "private")
            )
        elif platform == "tiktok":
            # TikTok Direct API is restricted to Enterprise Partners.
            # Implementation: Use a third-party automation tool like Selenium/Appium 
            # or a service like Zapier/Make.com webhook.
            # For now, we provide a "Manual Publish" kit.
            logger.warning("TikTok direct publishing requires Enterprise API. Providing manual download link.")
            return {
                "platform": "tiktok",
                "status": "manual_action_required",
                "message": "Please download the video and upload manually to TikTok.",
                "download_link": f"/api/v1/video/download/{user_id}" # Hypothetical endpoint
            }
        else:
            raise ValueError(f"Unsupported platform: {platform}")


# Singleton instance
base_publishing_service = PublishingService()
