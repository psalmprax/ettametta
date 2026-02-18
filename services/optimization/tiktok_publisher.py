from .publisher_base import SocialPublisher
from .models import PostMetadata
from typing import Optional
from .auth import token_manager

class TikTokPublisher(SocialPublisher):
    async def upload_video(self, video_path: str, metadata: PostMetadata, account_id: Optional[int] = None) -> Optional[str]:
        """
        Skeleton for TikTok Video Kit API integration.
        """
        token_data = token_manager.get_token_data("tiktok", account_id=account_id)
        if not token_data or "access_token" not in token_data:
            import logging
            logging.error("[TikTokPublisher] ERROR: No access token found (or invalid format).")
            return None
            
        access_token = token_data["access_token"]
        open_id = token_data.get("open_id", "user_id_placeholder") # Should store open_id in auth flow

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
                
                print(f"[TikTokPublisher] Init chunked upload ({total_chunk_count} chunks): {metadata.title}")
                init_response = await client.post(INIT_URL, json=init_payload, headers=headers)
                
                if init_response.status_code != 200:
                    logging.error(f"[TikTokPublisher] Init failed: {init_response.text}")
                    return None
                
                init_data = init_response.json()
                upload_url = init_data["data"]["upload_url"]
                publish_id = init_data["data"]["publish_id"]

                # 2. Upload Video in Chunks
                print(f"[TikTokPublisher] Uploading {file_size} bytes to {upload_url[:30]}...")
                
                with open(video_path, "rb") as f:
                    for i in range(total_chunk_count):
                        start_byte = i * CHUNK_SIZE
                        chunk_data = f.read(CHUNK_SIZE)
                        end_byte = start_byte + len(chunk_data) - 1
                        
                        upload_headers = {
                            "Content-Type": "video/mp4",
                            "Content-Range": f"bytes {start_byte}-{end_byte}/{file_size}"
                        }
                        
                        print(f"[TikTokPublisher] Uploading chunk {i+1}/{total_chunk_count} ({len(chunk_data)} bytes)...")
                        upload_response = await client.put(upload_url, content=chunk_data, headers=upload_headers)
                        
                        if upload_response.status_code not in [200, 201]:
                            logging.error(f"[TikTokPublisher] Chunk {i+1} upload failed: {upload_response.text}")
                            return None

                print(f"[TikTokPublisher] Upload successful! Publish ID: {publish_id}")
                return f"https://www.tiktok.com/@{open_id}/video/{publish_id}"

        except Exception as e:
            logging.error(f"[TikTokPublisher] Exception during chunked upload: {e}")
            return None

    def health_check(self) -> bool:
        return token_manager.get_token("tiktok") is not None

base_tiktok_publisher = TikTokPublisher()
