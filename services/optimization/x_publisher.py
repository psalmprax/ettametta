"""
X (Twitter) Publisher for Viral Forge
Handles video uploads to X via Twitter API v1.1 (chunked media upload) + v2 (tweet creation)
"""

from .publisher_base import SocialPublisher
from .models import PostMetadata
from typing import Optional
from .auth import token_manager
import httpx
import os
import logging

logger = logging.getLogger(__name__)


class XPublisher(SocialPublisher):
    async def upload_video(
        self,
        video_path: str,
        metadata: PostMetadata,
        user_id: int,
        account_id: Optional[int] = None,
    ) -> Optional[str]:
        """Uploads a video to X (Twitter) via chunked media upload v1.1 + tweet v2."""
        access_token = token_manager.get_token(
            "x", user_id=user_id, account_id=account_id
        )
        if not access_token:
            logger.error(f"[XPublisher] No access token for user {user_id}")
            return None

        # Validate token before upload
        await self.ensure_valid_token(user_id, account_id)
        access_token = token_manager.get_token(
            "x", user_id=user_id, account_id=account_id
        )

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            # Resolve local file path vs URL
            total_bytes = 0
            file_data = None
            if os.path.isfile(video_path):
                total_bytes = os.path.getsize(video_path)
                with open(video_path, "rb") as f:
                    file_data = f.read()
            else:
                # Try downloading from URL
                async with httpx.AsyncClient(timeout=60.0) as dl_client:
                    dl_resp = await dl_client.get(video_path)
                    if dl_resp.status_code == 200:
                        file_data = dl_resp.content
                        total_bytes = len(file_data)

            if not file_data or total_bytes == 0:
                logger.error(
                    f"[XPublisher] Could not read video data from {video_path}"
                )
                return None

            async with httpx.AsyncClient(timeout=120.0) as client:
                # Step 1: INIT
                init_url = "https://upload.twitter.com/1.1/media/upload.json"
                init_data = {
                    "command": "INIT",
                    "total_bytes": total_bytes,
                    "media_type": "video/mp4",
                    "media_category": "tweet_video",
                }
                init_resp = await client.post(init_url, data=init_data, headers=headers)
                if init_resp.status_code not in (200, 202):
                    logger.error(
                        f"[XPublisher] INIT failed: {init_resp.status_code} {init_resp.text}"
                    )
                    return None

                media_id = init_resp.json().get("media_id_string")
                if not media_id:
                    logger.error("[XPublisher] No media_id in INIT response")
                    return None

                logger.info(
                    f"[XPublisher] INIT ok, media_id={media_id}, bytes={total_bytes}"
                )

                # Step 2: APPEND (upload in 5MB chunks)
                chunk_size = 5 * 1024 * 1024  # 5MB
                segment_index = 0
                for offset in range(0, total_bytes, chunk_size):
                    chunk = file_data[offset : offset + chunk_size]
                    append_url = "https://upload.twitter.com/1.1/media/upload.json"
                    append_data = {
                        "command": "APPEND",
                        "media_id": media_id,
                        "segment_index": str(segment_index),
                    }
                    files = {"media": ("chunk", chunk, "application/octet-stream")}
                    append_resp = await client.post(
                        append_url, data=append_data, files=files, headers=headers
                    )
                    if append_resp.status_code not in (200, 202):
                        logger.error(
                            f"[XPublisher] APPEND segment {segment_index} failed: "
                            f"{append_resp.status_code} {append_resp.text}"
                        )
                        return None
                    segment_index += 1

                logger.info(
                    f"[XPublisher] APPEND complete, {segment_index} segments uploaded"
                )

                # Step 3: FINALIZE
                finalize_url = "https://upload.twitter.com/1.1/media/upload.json"
                finalize_data = {
                    "command": "FINALIZE",
                    "media_id": media_id,
                }
                finalize_resp = await client.post(
                    finalize_url, data=finalize_data, headers=headers
                )
                if finalize_resp.status_code not in (200, 201):
                    logger.error(
                        f"[XPublisher] FINALIZE failed: {finalize_resp.status_code} {finalize_resp.text}"
                    )
                    return None

                finalize_json = finalize_resp.json()
                processing_info = finalize_json.get("processing_info")

                # Step 3b: Poll for processing completion if needed
                if processing_info:
                    state = processing_info.get("state", "")
                    while state in ("pending", "in_progress"):
                        import asyncio

                        check_after = processing_info.get("check_after_secs", 5)
                        await asyncio.sleep(check_after)
                        status_resp = await client.get(
                            init_url,
                            params={"command": "STATUS", "media_id": media_id},
                            headers=headers,
                        )
                        if status_resp.status_code != 200:
                            break
                        status_json = status_resp.json()
                        processing_info = status_json.get("processing_info", {})
                        state = processing_info.get("state", "")
                        if state == "failed":
                            error = processing_info.get("error", {})
                            logger.error(f"[XPublisher] Processing failed: {error}")
                            return None

                logger.info(f"[XPublisher] FINALIZE ok, media ready")

                # Step 4: Create Tweet using v2 API
                tweet_url = "https://api.twitter.com/2/tweets"
                tweet_text = metadata.title or ""
                if metadata.hashtags:
                    tweet_text += "\n\n" + " ".join(
                        h if h.startswith("#") else f"#{h}" for h in metadata.hashtags
                    )
                tweet_data = {
                    "text": tweet_text[:280],
                    "media": {"media_ids": [media_id]},
                }
                tweet_resp = await client.post(
                    tweet_url, json=tweet_data, headers=headers
                )
                if tweet_resp.status_code in (200, 201):
                    tweet_id = tweet_resp.json().get("data", {}).get("id")
                    logger.info(f"[XPublisher] Tweet created: {tweet_id}")
                    return f"https://x.com/i/status/{tweet_id}"

                logger.error(
                    f"[XPublisher] Tweet creation failed: {tweet_resp.status_code} {tweet_resp.text}"
                )
                return None

        except Exception as e:
            logger.error(f"[XPublisher] Upload failed: {e}")
            return None

    async def ensure_valid_token(self, user_id: int, account_id: Optional[int] = None):
        """Token validation and refresh via TokenManager"""
        return await token_manager.ensure_valid_token(
            "x", user_id=user_id, account_id=account_id
        )

    def health_check(self, user_id: int) -> bool:
        return token_manager.get_token("x", user_id=user_id) is not None


base_x_publisher = XPublisher()
