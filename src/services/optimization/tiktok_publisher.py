"""
TikTok Publisher for ettametta
Handles video uploads to TikTok via Video Kit API
Features: Chunked uploads, token refresh, proper logging
"""

import os
import httpx
import logging
from typing import Any

from .publisher_base import SocialPublisher, RetryConfig, RateLimitConfig
from .models import PostMetadata
from .auth import token_manager

logger = logging.getLogger(__name__)


class TikTokPublisher(SocialPublisher):
    """TikTok video publisher with production-grade features"""

    def __init__(self):
        super().__init__(
            platform_name="tiktok",
            max_file_size_mb=287,  # TikTok limit
            supported_formats=["mp4", "mov"],
            retry_config=RetryConfig(max_retries=3, base_delay=2.0, max_delay=60.0),
            rate_limit_config=RateLimitConfig(max_retries=5),
        )

    async def _upload_impl(
        self,
        video_path: str,
        metadata: PostMetadata,
        user_id: str,
        account_id: int | None,
        headers: dict,
    ) -> str | None:
        """TikTok-specific upload implementation with chunked uploads"""
        if not headers:
            logger.error(f"[TikTokPublisher] No authentication for user {user_id}")
            return None

        headers["Content-Type"] = "application/json; charset=UTF-8"

        token_data = await token_manager.get_token_data(
            "tiktok", user_id=user_id, account_id=account_id
        )
        open_id = token_data.get("username") if token_data else "me"

        CHUNK_SIZE = 10 * 1024 * 1024  # 10MB Chunks

        try:
            file_size = os.path.getsize(video_path)
            total_chunk_count = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE

            INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"

            async with httpx.AsyncClient(timeout=300.0) as client:
                # Step 1: Initialize Upload
                init_payload = {
                    "post_info": {
                        "title": metadata.title[:150],
                        "privacy_level": "SELF_ONLY",
                        "disable_duet": False,
                        "disable_comment": False,
                        "disable_stitch": False,
                        "video_cover_timestamp_ms": 1000,
                    },
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": file_size,
                        "chunk_size": CHUNK_SIZE,
                        "total_chunk_count": total_chunk_count,
                    },
                }

                logger.info(
                    f"[TikTokPublisher] Initializing chunked upload for user {user_id}"
                )
                init_response = await client.post(
                    INIT_URL, json=init_payload, headers=headers
                )

                if init_response.status_code != 200:
                    logger.error(f"[TikTokPublisher] Init failed: {init_response.text}")
                    return None

                init_data = init_response.json()
                upload_url = init_data["data"]["upload_url"]
                publish_id = init_data["data"]["publish_id"]

                logger.info(
                    f"[TikTokPublisher] Uploading {file_size} bytes in {total_chunk_count} chunks..."
                )

                # Step 2: Upload Video in Chunks
                with open(video_path, "rb") as f:
                    for i in range(total_chunk_count):
                        start_byte = i * CHUNK_SIZE
                        chunk_data = f.read(CHUNK_SIZE)
                        end_byte = start_byte + len(chunk_data) - 1

                        upload_headers = {
                            "Content-Type": "video/mp4",
                            "Content-Range": f"bytes {start_byte}-{end_byte}/{file_size}",
                        }

                        upload_response = await client.put(
                            upload_url, content=chunk_data, headers=upload_headers
                        )

                        if upload_response.status_code not in [200, 201]:
                            logger.error(
                                f"[TikTokPublisher] Chunk {i + 1} upload failed: {upload_response.text}"
                            )
                            return None

                logger.info(
                    f"[TikTokPublisher] Upload successful! Publish ID: {publish_id}"
                )
                return f"https://www.tiktok.com/@{open_id}/video/{publish_id}"

        except Exception as e:
            logger.exception(f"[TikTokPublisher] Upload failed: {e}")
            return None

    async def _get_metrics_impl(
        self,
        platform_id: str,
        user_id: str,
        account_id: int | None,
        headers: dict,
    ) -> dict:
        """Fetch TikTok video metrics"""
        headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Use the correct TikTok API endpoint to get video metrics by video ID
                # Note: TikTok API may require specific video ID format and proper authorization
                video_response = await client.get(
                    f"https://open.tiktokapis.com/v2/video/query/?video_id={platform_id}&fields=id,like_count,comment_count,share_count,view_count",
                    headers=headers,
                )

                if video_response.status_code != 200:
                    logger.error(
                        f"[TikTokPublisher] Failed to fetch metrics: {video_response.status_code} - {video_response.text}"
                    )
                    return {"views": 0, "likes": 0, "comments": 0, "shares": 0}

                data = video_response.json()
                video = data.get("data", {})

                if video and str(video.get("id")) == str(platform_id):
                    return {
                        "views": video.get("view_count", 0),
                        "likes": video.get("like_count", 0),
                        "comments": video.get("comment_count", 0),
                        "shares": video.get("share_count", 0),
                    }

                logger.warning(
                    f"[TikTokPublisher] Video {platform_id} not found or API returned no data"
                )
                return {"views": 0, "likes": 0, "comments": 0, "shares": 0}

            except Exception as e:
                logger.exception(f"[TikTokPublisher] Metrics fetch error: {e}")
                return {"error": str(e)}

    async def _get_comments_impl(
        self,
        platform_id: str,
        user_id: str,
        account_id: int | None,
        headers: dict,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch TikTok video comments"""
        headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # TikTok API for fetching video comments
                comments_response = await client.get(
                    f"https://open.tiktokapis.com/v2/video/comment/list/?video_id={platform_id}&cursor=0&max_count={limit}",
                    headers=headers,
                )

                if comments_response.status_code != 200:
                    logger.error(
                        f"[TikTokPublisher] Failed to fetch comments: {comments_response.status_code} - {comments_response.text}"
                    )
                    return []

                data = comments_response.json()
                comments = data.get("data", {}).get("comments", [])

                # Format comments for consistent API response
                formatted_comments = []
                for comment in comments:
                    formatted_comments.append(
                        {
                            "id": comment.get("id"),
                            "text": comment.get("text"),
                            "author": comment.get("user", {}).get(
                                "nickname", "Unknown"
                            ),
                            "likes": comment.get("like_count", 0),
                            "replies": comment.get("reply_count", 0),
                            "created_at": comment.get("create_time"),
                        }
                    )

                return formatted_comments

            except Exception as e:
                logger.exception(f"[TikTokPublisher] Comments fetch error: {e}")
                return []

    async def health_check(self, user_id: str) -> bool:
        """Verify TikTok credentials"""
        return await token_manager.get_token("tiktok", user_id=user_id) is not None


base_tiktok_service = TikTokPublisher()
