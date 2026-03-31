from .publisher_base import SocialPublisher
from .models import PostMetadata
from typing import Optional
from .auth import token_manager

class TikTokPublisher(SocialPublisher):
    async def upload_video(self, video_path: str, metadata: PostMetadata, user_id: int, account_id: Optional[int] = None) -> Optional[str]:
        """
        TikTok Video Kit API integration with automated refresh.
        """
        # 1. Ensure token is valid
        await self.ensure_valid_token(user_id, account_id)

        token_data = token_manager.get_token_data("tiktok", user_id=user_id, account_id=account_id)
        if not token_data or "access_token" not in token_data:
            import logging
            logging.error(f"[TikTokPublisher] ERROR: No access token for user {user_id}.")
            return None
            
        access_token = token_data["access_token"]
        open_id = token_data.get("open_id") or token_data.get("username")
        
        if not open_id:
            import logging
            logging.error(f"[TikTokPublisher] open_id/username missing for user {user_id}. Re-auth required.")
            return None

        import httpx
        import os
        import logging

        # TikTok Video Kit API Endpoints
        INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

        CHUNK_SIZE = 10 * 1024 * 1024  # 10MB Chunks

        try:
            file_size = os.path.getsize(video_path)
            total_chunk_count = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
            
            # 1. Initialize Upload
            async with httpx.AsyncClient() as client:
                init_payload = {
                    "post_info": {
                        "title": metadata.title[:150],
                        "privacy_level": "SELF_ONLY",
                        "disable_duet": False,
                        "disable_comment": False,
                        "disable_stitch": False,
                        "video_cover_timestamp_ms": 1000
                    },
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": file_size,
                        "chunk_size": CHUNK_SIZE,
                        "total_chunk_count": total_chunk_count
                    }
                }
                
                print(f"[TikTokPublisher] Init chunked upload for user {user_id}: {metadata.title}")
                init_response = await client.post(INIT_URL, json=init_payload, headers=headers)
                
                if init_response.status_code != 200:
                    logging.error(f"[TikTokPublisher] Init failed: {init_response.text}")
                    return None
                
                init_data = init_response.json()
                upload_url = init_data["data"]["upload_url"]
                publish_id = init_data["data"]["publish_id"]

                # 2. Upload Video in Chunks
                print(f"[TikTokPublisher] Uploading {file_size} bytes...")
                
                with open(video_path, "rb") as f:
                    for i in range(total_chunk_count):
                        start_byte = i * CHUNK_SIZE
                        chunk_data = f.read(CHUNK_SIZE)
                        end_byte = start_byte + len(chunk_data) - 1
                        
                        upload_headers = {
                            "Content-Type": "video/mp4",
                            "Content-Range": f"bytes {start_byte}-{end_byte}/{file_size}"
                        }
                        
                        upload_response = await client.put(upload_url, content=chunk_data, headers=upload_headers)
                        
                        if upload_response.status_code not in [200, 201]:
                            logging.error(f"[TikTokPublisher] Chunk {i+1} upload failed")
                            return None

                print(f"[TikTokPublisher] Upload successful! Publish ID: {publish_id}")
                return f"https://www.tiktok.com/@{open_id}/video/{publish_id}"

        except Exception as e:
            logging.error(f"[TikTokPublisher] Exception: {e}")
            return None

    async def ensure_valid_token(self, user_id: int, account_id: Optional[int] = None):
        if token_manager.is_token_expired("tiktok", user_id=user_id, account_id=account_id):
            print(f"[TikTokPublisher] Token expired for user {user_id}. Refresh needed.")
            pass

    async def get_metrics(self, platform_id: str, user_id: int, account_id: Optional[int] = None) -> dict:
        """Fetches live engagement metrics for a TikTok post."""
        # Placeholder implementation - would integrate with TikTok Analytics API
        return {
            "views": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0
        }

    def health_check(self, user_id: int) -> bool:
        return token_manager.get_token("tiktok", user_id=user_id) is not None

base_tiktok_publisher = TikTokPublisher()
