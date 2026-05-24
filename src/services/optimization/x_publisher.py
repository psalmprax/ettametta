"""
X (Twitter) Publisher for ettametta
Handles video uploads to X via Twitter API v1.1 (chunked media upload) + v2 (tweet creation)
Features: Retry logic, rate limiting, file validation, proper logging
"""

import asyncio
import os
import httpx
import logging

from .publisher_base import SocialPublisher, RetryConfig, RateLimitConfig
from .models import PostMetadata
from .auth import token_manager

logger = logging.getLogger(__name__)


class XPublisher(SocialPublisher):
    """X (Twitter) video publisher with production-grade features"""

    def __init__(self):
        super().__init__(
            platform_name="x",
            max_file_size_mb=512,  # X limit
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
        """X-specific upload implementation using chunked media upload"""
        if not headers:
            logger.error(f"[XPublisher] No authentication for user {user_id}")
            return None

        # Check file size before loading
        if os.path.isfile(video_path):
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            if file_size_mb > self.max_file_size_bytes / (1024 * 1024):
                logger.error(
                    f"[XPublisher] File size {file_size_mb:.2f}MB exceeds limit of {self.max_file_size_bytes / (1024 * 1024):.0f}MB"
                )
                return None

        file_data, total_bytes = await self._load_video_data(video_path)
        if not file_data or total_bytes == 0:
            logger.error(f"[XPublisher] Could not load video data from {video_path}")
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

            # Step 3b: Poll for processing completion
            if processing_info:
                state = processing_info.get("state", "")
                while state in ("pending", "in_progress"):
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

            logger.info("[XPublisher] FINALIZE ok, media ready")

            # Step 4: Create Tweet using v2 API
            tweet_url = "https://api.twitter.com/2/tweets"
            tweet_text = self._build_tweet_text(metadata)
            tweet_data = {
                "text": tweet_text[:280],
                "media": {"media_ids": [media_id]},
            }
            tweet_resp = await client.post(tweet_url, json=tweet_data, headers=headers)
            if tweet_resp.status_code in (200, 201):
                tweet_id = tweet_resp.json().get("data", {}).get("id")
                logger.info(f"[XPublisher] Tweet created: {tweet_id}")
                return f"https://x.com/i/status/{tweet_id}"

            logger.error(
                f"[XPublisher] Tweet creation failed: {tweet_resp.status_code} {tweet_resp.text}"
            )
            return None

    async def _load_video_data(self, video_path: str) -> tuple[bytes | None, int]:
        """Load video data from path or URL"""
        if os.path.isfile(video_path):
            total_bytes = os.path.getsize(video_path)
            with open(video_path, "rb") as f:
                file_data = f.read()
            return file_data, total_bytes

        # Try downloading from URL
        async with httpx.AsyncClient(timeout=60.0) as dl_client:
            dl_resp = await dl_client.get(video_path)
            if dl_resp.status_code == 200:
                return dl_resp.content, len(dl_resp.content)

        return None, 0

    def _build_tweet_text(self, metadata: PostMetadata) -> str:
        """Build tweet text from metadata"""
        parts = [metadata.title]
        if metadata.description:
            parts.append(f"\n\n{metadata.description}")
        if metadata.hashtags:
            tags = " ".join(
                h if h.startswith("#") else f"#{h}" for h in metadata.hashtags[:5]
            )
            parts.append(f"\n\n{tags}")
        if metadata.cta:
            parts.append(f"\n\n{metadata.cta}")
        return "".join(parts)

    async def _get_metrics_impl(
        self,
        platform_id: str,
        user_id: str,
        account_id: int | None,
        headers: dict,
    ) -> dict:
        """Fetch X tweet metrics"""
        async with httpx.AsyncClient() as client:
            url = f"https://api.twitter.com/2/tweets/{platform_id}"
            params = {"tweet.fields": "public_metrics"}

            response = await client.get(url, params=params, headers=headers)
            data = response.json()

            if "data" in data:
                metrics = data["data"].get("public_metrics", {})
                return {
                    "views": metrics.get("impression_count", 0),
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                    "bookmarks": metrics.get("bookmark_count", 0),
                }

            return {"error": data.get("error", {}).get("message", "Unknown error")}

    async def health_check(self, user_id: str) -> bool:
        """Verify X credentials"""
        return await token_manager.get_token("x", user_id=user_id) is not None


base_x_publisher_service = XPublisher()
