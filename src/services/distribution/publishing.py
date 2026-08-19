"""
Real Social Media Publishing Service
====================================
Handles OAuth authentication and video uploading to major platforms.
Hardened with Circuit Breakers and Retry logic for production reliability.
"""

import logging
import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Any
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.api.utils.resilience import CircuitBreaker

# Google API imports (for YouTube)
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

# Playwright imports for automation
try:
    from src.services.openclaw.skills.social_publisher import base_playwright_publisher
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)


class YouTubePublisher:
    """Handles real YouTube video uploads via Data API v3 with resilience."""

    def __init__(self):
        self.client_id = os.getenv('YOUTUBE_CLIENT_ID')
        self.client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
        self.token_dir = Path("data/storage/tokens")
        self.token_dir.mkdir(parents=True, exist_ok=True)
        self.breaker = CircuitBreaker(name="YouTube-API", failure_threshold=2, recovery_timeout=600)

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
            logger.exception(f"Failed to load credentials: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=10, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
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
        Upload a video to YouTube using real API with retry and breaker protection.
        """
        if not GOOGLE_API_AVAILABLE:
            raise RuntimeError("Google API libraries not installed.")

        if self.breaker.is_open():
            raise RuntimeError("YouTube API is currently blocked by CircuitBreaker")

        creds = self._get_credentials(user_id)
        if not creds:
            raise RuntimeError(f"YouTube account not connected for user {user_id}")

        try:
            # We use to_thread for blocking Google API calls to keep async loop free
            def _sync_upload():
                youtube = build('youtube', 'v3', credentials=creds)
                body = {
                    'snippet': {
                        'title': title[:100],
                        'description': description[:5000],
                        'tags': tags[:50],
                        'categoryId': '28'
                    },
                    'status': {
                        'privacyStatus': privacy_status
                    }
                }

                if not Path(video_path).exists():
                    raise FileNotFoundError(f"Video file not found: {video_path}")

                insert_request = youtube.videos().insert(
                    part=",".join(body.keys()),
                    body=body,
                    media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
                )
                return insert_request.execute()

            logger.info(f"[YouTube] Starting resilient upload for '{title}'...")
            response = await asyncio.to_thread(_sync_upload)

            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            self.breaker.record_success()
            logger.info(f"[YouTube] Successfully uploaded: {video_url}")

            return {
                "platform": "youtube",
                "video_id": video_id,
                "url": video_url,
                "status": "published",
                "privacy": privacy_status,
                "published_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            self.breaker.record_failure()
            logger.exception(f"[YouTube] Upload failed: {str(e)}")
            raise


class PublishingService:
    """Unified service for multi-platform publishing with resilience."""

    def __init__(self):
        self.youtube = YouTubePublisher()
        # Circuit breaker for browser-based automation
        self.automation_breaker = CircuitBreaker(name="Publish-Automation", failure_threshold=2)

    async def publish_to_platform(
        self,
        user_id: str,
        platform: str,
        video_path: str,
        metadata: dict[str, Any],
        use_automation: bool = False
    ) -> dict[str, Any]:
        """
        Publish video to specified platform with fallback logic.
        """
        if platform == "youtube":
            try:
                return await self.youtube.upload_video(
                    user_id=user_id,
                    video_path=video_path,
                    title=metadata.get("title", "Untitled"),
                    description=metadata.get("description", ""),
                    tags=metadata.get("tags", []),
                    privacy_status=metadata.get("privacy", "private")
                )
            except Exception as e:
                logger.exception(f"[Publishing] YouTube publication failed: {e}")
                return {
                    "platform": "youtube",
                    "status": "failed",
                    "error": str(e),
                    "instructions": "YouTube API failed. Please try again or download manually."
                }

        elif platform in ["tiktok", "instagram"]:
            if use_automation and PLAYWRIGHT_AVAILABLE and not self.automation_breaker.is_open():
                try:
                    logger.info(f"[Publishing] Attempting {platform} automation...")
                    if platform == "tiktok":
                        result = await base_playwright_publisher.post_to_tiktok(
                            user_id=user_id,
                            video_path=video_path,
                            description=metadata.get("description", ""),
                            tags=metadata.get("tags", [])
                        )
                    else:
                        result = await base_playwright_publisher.post_to_instagram(
                            user_id=user_id,
                            video_path=video_path,
                            description=metadata.get("description", ""),
                            tags=metadata.get("tags", [])
                        )
                    self.automation_breaker.record_success()
                    return result
                except Exception as e:
                    self.automation_breaker.record_failure()
                    logger.warning(f"[Publishing] {platform} automation failed, falling back to manual: {e}")

            # Fallback to Manual Publish Kit
            return {
                "platform": platform,
                "status": "manual_action_required",
                "message": f"{platform.capitalize()} requires manual action.",
                "download_link": f"/api/v1/video/download/{os.path.basename(video_path)}",
                "caption": metadata.get("description", ""),
                "hashtags": " ".join(metadata.get("tags", [])),
                "instructions": f"1. Download video. 2. Open {platform.capitalize()}. 3. Upload with provided caption."
            }
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    async def publish_to_multiple(
        self,
        user_id: str,
        platforms: list[str],
        video_path: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Publish to multiple platforms in parallel with isolated error handling.

        Each platform is published independently via publish_to_platform. If one
        platform fails, the others continue unaffected. Results include a summary
        of published/failed counts and per-platform details.

        Args:
            user_id: The user's identifier for credential lookup.
            platforms: List of platform names (e.g., ["youtube", "tiktok"]).
            video_path: Path to the video file to publish.
            metadata: Dict with title, description, tags, etc.

        Returns:
            Dict with keys: published, failed, total, results (per-platform list).
        """
        tasks = [
            self.publish_to_platform(
                user_id=user_id,
                platform=p,
                video_path=video_path,
                metadata=metadata,
            )
            for p in platforms
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        published = 0
        failed = 0
        processed: list[dict[str, Any]] = []

        for platform, result in zip(platforms, results, strict=False):
            if isinstance(result, Exception):
                failed += 1
                processed.append({
                    "platform": platform,
                    "status": "failed",
                    "error": str(result),
                })
            else:
                if result.get("status") in ("failed", "manual_action_required"):
                    failed += 1
                else:
                    published += 1
                processed.append(result)

        return {
            "published": published,
            "failed": failed,
            "total": len(platforms),
            "results": processed,
        }


# Singleton instance
base_publishing_service = PublishingService()
