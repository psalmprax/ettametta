"""
Social Media Publishing Service
===============================
Handles OAuth authentication and video uploading to major platforms.
Currently supports YouTube Data API v3.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# Scopes for YouTube Data API
YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']


class YouTubePublisher:
    """Handles YouTube video uploads via Data API v3."""

    def __init__(self):
        self.client_secrets_file = os.getenv('YOUTUBE_CLIENT_SECRETS', 'client_secrets.json')
        self.token_file = Path("data/storage/tokens/youtube_token.json")
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

    def get_authenticated_service(self, user_id: str) -> Any:
        """Get authenticated YouTube service instance for a user."""
        credentials = None
        
        # Load existing token if available
        if self.token_file.exists():
            try:
                credentials = Credentials.from_authorized_user_file(
                    str(self.token_file), YOUTUBE_SCOPES
                )
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")

        # If no valid credentials, let the user log in (in a real app, this would be a web flow)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                # For server-to-server or initial setup, we might use service accounts or manual token input
                # Here we assume credentials are provided via env or pre-configured for simplicity
                raise Exception("YouTube authentication required. Please connect your account.")

        return build('youtube', 'v3', credentials=credentials)

    async def upload_video(
        self, 
        video_path: str, 
        title: str, 
        description: str, 
        tags: list[str], 
        privacy_status: str = "private"
    ) -> dict[str, Any]:
        """
        Upload a video to YouTube.
        
        Args:
            video_path: Path to the video file
            title: Video title
            description: Video description
            tags: List of tags
            privacy_status: 'public', 'private', or 'unlisted'
            
        Returns:
            Dict with video_id and link
        """
        try:
            youtube = self.get_authenticated_service("current_user")
            
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }

            insert_request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
            )

            response = insert_request.execute()
            
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"Successfully uploaded video {video_id}")
            
            return {
                "platform": "youtube",
                "video_id": video_id,
                "url": video_url,
                "status": "published",
                "privacy": privacy_status
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
        platform: str, 
        video_path: str, 
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Publish video to specified platform.
        
        Args:
            platform: 'youtube', 'tiktok', etc.
            video_path: Path to video file
            metadata: Title, description, tags, etc.
        """
        if platform == "youtube":
            return await self.youtube.upload_video(
                video_path=video_path,
                title=metadata.get("title", "Untitled"),
                description=metadata.get("description", ""),
                tags=metadata.get("tags", []),
                privacy_status=metadata.get("privacy", "private")
            )
        elif platform == "tiktok":
            raise NotImplementedError("TikTok publishing coming soon")
        else:
            raise ValueError(f"Unsupported platform: {platform}")


# Singleton instance
base_publishing_service = PublishingService()
