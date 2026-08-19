"""
Postiz Headless Social Media Publishing Service
===============================================
Leverages open-source Postiz to publish videos and posts across 8+ social platforms
(TikTok, YouTube, Instagram, X/Twitter, LinkedIn, Pinterest, Threads, Facebook)
without maintaining bespoke OAuth refresh flows for each platform.
"""

import os
import json
import logging
import httpx
from typing import Any, Optional
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.api.utils.resilience import CircuitBreaker

logger = logging.getLogger("PostizPublisherService")


class PostizPostRequest(BaseModel):
    caption: str
    platforms: list[str] = Field(default_factory=lambda: ["youtube", "tiktok"])
    video_path: Optional[str] = None
    media_url: Optional[str] = None
    schedule_date: Optional[str] = None  # ISO timestamp
    tags: list[str] = Field(default_factory=list)


class PostizPostResponse(BaseModel):
    success: bool
    post_id: Optional[str] = None
    platforms: list[str] = Field(default_factory=list)
    scheduled_at: Optional[str] = None
    status: str
    error: Optional[str] = None


class PostizPublisherService:
    """
    Unified headless social publishing bridge using self-hosted or cloud Postiz.
    """

    def __init__(self):
        self.api_url = os.getenv("POSTIZ_API_URL", "http://postiz:3000/api/v1").rstrip("/")
        self.api_key = os.getenv("POSTIZ_API_KEY", "")
        self.breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=120)
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                timeout=30.0,
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            )
        return self._client

    async def get_connected_integrations(self) -> list[dict[str, Any]]:
        """Fetch active social channels connected in Postiz"""
        if not self.api_key:
            return [{"id": "mock_yt", "platform": "youtube", "name": "YouTube Shorts (Mock)"}]

        if self.breaker.is_open():
            logger.warning("[Postiz] Circuit breaker open; returning cached/empty integrations")
            return []

        try:
            response = await self.client.get("/integrations")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"[Postiz] Failed to fetch integrations: {e}")
            return []

    async def upload_media_file(self, file_path: str) -> Optional[str]:
        """Upload a local video file to Postiz media storage"""
        if not os.path.exists(file_path):
            logger.error(f"[Postiz] Media file not found: {file_path}")
            return None

        if not self.api_key:
            # Fallback for dev / simulation mode
            return f"https://mock-storage.ettametta.internal/{os.path.basename(file_path)}"

        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "video/mp4")}
                response = await self.client.post("/upload", files=files)
                if response.status_code in (200, 201):
                    data = response.json()
                    return data.get("url") or data.get("path")
                logger.error(f"[Postiz] Upload failed {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.exception(f"[Postiz] Upload exception: {e}")
            return None

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=False,
    )
    async def publish_video(
        self,
        video_path: Optional[str],
        caption: str,
        platforms: list[str],
        schedule_date: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> PostizPostResponse:
        """
        Schedule or immediately publish a video across target platforms via Postiz.
        """
        if self.breaker.is_open():
            return PostizPostResponse(
                success=False,
                status="circuit_breaker_open",
                error="Postiz circuit breaker is open",
                platforms=platforms,
            )

        # 1. Dev / Mock fallback if no API key configured
        if not self.api_key:
            logger.info(f"[Postiz] Simulation publish to {platforms}: '{caption[:40]}...'")
            return PostizPostResponse(
                success=True,
                post_id=f"postiz_sim_{os.urandom(4).hex()}",
                platforms=platforms,
                scheduled_at=schedule_date or "immediate",
                status="published_simulation",
            )

        # 2. Upload media if local file
        media_url = None
        if video_path and os.path.exists(video_path):
            media_url = await self.upload_media_file(video_path)

        # 3. Dispatch to Postiz API
        payload = {
            "content": caption,
            "platforms": platforms,
            "media": [media_url] if media_url else [],
            "scheduleDate": schedule_date,
            "tags": tags or [],
        }

        try:
            response = await self.client.post("/posts", json=payload)
            if response.status_code in (200, 201):
                data = response.json()
                return PostizPostResponse(
                    success=True,
                    post_id=str(data.get("id", "")),
                    platforms=platforms,
                    scheduled_at=schedule_date or "immediate",
                    status="scheduled" if schedule_date else "published",
                )
            else:
                self.breaker.record_failure()
                return PostizPostResponse(
                    success=False,
                    status="failed",
                    error=f"Postiz API returned {response.status_code}: {response.text}",
                    platforms=platforms,
                )
        except Exception as e:
            self.breaker.record_failure()
            logger.exception(f"[Postiz] Post request failed: {e}")
            return PostizPostResponse(
                success=False,
                status="error",
                error=str(e),
                platforms=platforms,
            )


base_postiz_service = PostizPublisherService()
