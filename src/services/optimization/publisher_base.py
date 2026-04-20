"""
Base Publisher for ettametta
Provides common functionality for all social platform publishers including:
- Retry mechanisms with exponential backoff
- File validation
- Rate limit handling
- Health checks
"""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel
from .models import PostMetadata
from .auth import token_manager
import asyncio
import logging
import os

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base


class RateLimitConfig:
    """Configuration for rate limit handling"""

    def __init__(
        self,
        max_retries: int = 5,
        backoff_factor: float = 2.0,
        retry_after_header: str = "Retry-After",
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_after_header = retry_after_header


class SocialPublisher(ABC):
    """Base class for all social media publishers with production-grade features"""

    def __init__(
        self,
        platform_name: str,
        max_file_size_mb: int = 512,
        supported_formats: list = None,
        retry_config: RetryConfig = None,
        rate_limit_config: RateLimitConfig = None,
    ):
        self.platform_name = platform_name
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.supported_formats = supported_formats or ["mp4", "mov", "avi"]
        self.retry_config = retry_config or RetryConfig()
        self.rate_limit_config = rate_limit_config or RateLimitConfig()

    @abstractmethod
    async def _upload_impl(
        self,
        video_path: str,
        metadata: PostMetadata,
        user_id: int,
        account_id: int | None,
        headers: dict[str, str],
    ) -> str | None:
        """Platform-specific upload implementation. Returns post URL or None."""
        pass

    @abstractmethod
    async def _get_metrics_impl(
        self,
        platform_id: str,
        user_id: int,
        account_id: int | None,
        headers: dict[str, str],
    ) -> dict:
        """Platform-specific metrics fetching implementation."""
        pass

    def _validate_video(self, video_path: str) -> tuple[bool, str]:
        """Validate video file before upload"""
        if not video_path:
            return False, "Video path is empty"

        # Check if it's a URL (external) or local file
        if video_path.startswith(("http://", "https://")):
            return True, "External URL - will validate after download"

        # Local file validation
        if not os.path.isfile(video_path):
            return False, f"File does not exist: {video_path}"

        # Check file size
        file_size = os.path.getsize(video_path)
        if file_size > self.max_file_size_bytes:
            return (
                False,
                f"File too large: {file_size / (1024 * 1024):.1f}MB (max: {self.max_file_size_bytes / (1024 * 1024)}MB)",
            )

        if file_size == 0:
            return False, "File is empty"

        # Check extension
        ext = os.path.splitext(video_path)[1].lstrip(".").lower()
        if ext not in self.supported_formats:
            return (
                False,
                f"Unsupported format: {ext} (supported: {', '.join(self.supported_formats)})",
            )

        return True, "Valid"

    async def _download_video(
        self, url: str, timeout: float = 120.0
    ) -> tuple[bytes | None, str]:
        """Download video from URL with validation"""
        import httpx

        try:
            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True
            ) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return None, f"Download failed with status {response.status_code}"

                content = response.content
                if len(content) == 0:
                    return None, "Downloaded content is empty"

                if len(content) > self.max_file_size_bytes:
                    return (
                        None,
                        f"Downloaded file too large: {len(content) / (1024 * 1024):.1f}MB",
                    )

                return content, "Downloaded successfully"
        except Exception as e:
            return None, f"Download error: {str(e)}"

    def _calculate_delay(self, attempt: int, retry_after: int = None) -> float:
        """Calculate exponential backoff delay"""
        if retry_after:
            return min(retry_after, self.retry_config.max_delay)

        delay = min(
            self.retry_config.base_delay
            * (self.retry_config.exponential_base**attempt),
            self.retry_config.max_delay,
        )
        return delay

    async def _execute_with_retry(
        self, operation, *args, **kwargs
    ) -> tuple[Any, str | None]:
        """Execute operation with retry logic and rate limit handling"""
        last_error = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                result = await operation(*args, **kwargs)
                return result, None
            except Exception as e:
                error_str = str(e).lower()
                last_error = str(e)

                # Check for rate limiting (429)
                if "429" in error_str or "rate limit" in error_str:
                    # Try to get retry-after header
                    retry_after = None
                    if hasattr(e, "response") and e.response:
                        retry_after = e.response.headers.get("Retry-After")

                    if retry_after:
                        try:
                            retry_after = int(retry_after)
                        except ValueError:
                            retry_after = None

                    if attempt < self.retry_config.max_retries:
                        delay = self._calculate_delay(attempt, retry_after)
                        logger.warning(
                            f"[{self.platform_name}] Rate limited, retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{self.retry_config.max_retries + 1})"
                        )
                        await asyncio.sleep(delay)
                        continue

                # Check for server errors (5xx) - retry with backoff
                if any(x in error_str for x in ["500", "502", "503", "504", "timeout"]):
                    if attempt < self.retry_config.max_retries:
                        delay = self._calculate_delay(attempt)
                        logger.warning(
                            f"[{self.platform_name}] Server error, retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{self.retry_config.max_retries + 1})"
                        )
                        await asyncio.sleep(delay)
                        continue

                # For other errors, log and return immediately
                logger.error(
                    f"[{self.platform_name}] Non-retryable error: {last_error}"
                )
                return None, last_error

        return None, f"Max retries exceeded. Last error: {last_error}"

    async def upload_video(
        self,
        video_path: str,
        metadata: PostMetadata,
        user_id: int,
        account_id: int | None = None,
    ) -> str | None:
        """
        Uploads video to platform with validation and retry logic.
        Returns post URL on success, None on failure.
        """
        # Validate video
        is_valid, validation_msg = self._validate_video(video_path)
        if not is_valid:
            logger.error(f"[{self.platform_name}] Validation failed: {validation_msg}")
            return None

        # Get authentication
        headers = await token_manager.get_auth_headers(
            self.platform_name, user_id, account_id
        )
        if not headers:
            logger.error(f"[{self.platform_name}] No authentication for user {user_id}")
            return None

        # Execute upload with retry
        result, error = await self._execute_with_retry(
            self._upload_impl, video_path, metadata, user_id, account_id, headers
        )

        if error:
            logger.error(f"[{self.platform_name}] Upload failed: {error}")

        return result

    async def get_metrics(
        self,
        platform_id: str,
        user_id: int,
        account_id: int | None = None,
    ) -> dict:
        """Fetches live engagement metrics for a post"""
        headers = await token_manager.get_auth_headers(
            self.platform_name, user_id, account_id
        )
        if not headers:
            logger.error(f"[{self.platform_name}] No authentication for user {user_id}")
            return {"error": "No authentication"}

        try:
            return await self._get_metrics_impl(
                platform_id, user_id, account_id, headers
            )
        except Exception as e:
            logger.error(f"[{self.platform_name}] Metrics fetch failed: {e}")
            return {"error": str(e)}

    @abstractmethod
    async def health_check(self, user_id: int) -> bool:
        """Verifies API credentials and connectivity"""
        pass

    async def ensure_valid_token(self, user_id: int, account_id: int | None = None):
        """Token validation and refresh"""
        return await token_manager.ensure_valid_token(
            self.platform_name, user_id=user_id, account_id=account_id
        )


class MetricsResponse(BaseModel):
    """Standard metrics response format"""

    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    engagement_score: float = 0.0
    timestamp: str = None
