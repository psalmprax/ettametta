from .publisher_base import SocialPublisher
from .models import PostMetadata
from typing import Optional
from .auth import token_manager
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

class YouTubePublisher(SocialPublisher):
    async def upload_video(self, video_path: str, metadata: PostMetadata, account_id: Optional[int] = None) -> Optional[str]:
        """
        Uploads a video to YouTube as a Short using the Data API v3.
        """
        access_token = token_manager.get_token("youtube", account_id=account_id)
        if not access_token:
            print("[YouTubePublisher] ERROR: No access token found. Please authenticate via Dashboard.")
            return None

        # Build credentials
        creds = Credentials(token=access_token)
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": metadata.title[:100], # YouTube limit
                "description": f"{metadata.description}\n\n#shorts {' '.join(metadata.hashtags)}",
                "categoryId": "22" # People & Blogs
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
        )

        try:
            print(f"[YouTubePublisher] Uploading {video_path} to YouTube...")
            response = insert_request.execute()
            video_id = response.get("id")
            return f"https://youtube.com/shorts/{video_id}"
        except Exception as e:
            print(f"[YouTubePublisher] FAILED: {str(e)}")
            return None

    def health_check(self) -> bool:
        return token_manager.get_token("youtube") is not None

base_youtube_publisher = YouTubePublisher()
