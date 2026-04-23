"""
opencli-rs Service — Per-User Chrome Session Bridge
===================================================

Wraps the opencli-rs CLI tool to provide per-user platform access
via Chrome browser session cookies. Each user has their own isolated
session data directory.

Architecture:
- Each user gets a session dir: OPENCLI_SESSIONS_DIR/user_{id}/
- Cookie files are stored per platform: {platform}_cookies.txt
- opencli-rs commands are executed with --cookies pointing to user's file
- Results are parsed into ettametta's ContentCandidate/PostMetadata format

Supported platforms (via opencli-rs):
youtube, x, reddit, instagram, tiktok, facebook, hackernews,
stackoverflow, wikipedia, notion, discord, telegram, twitch,
pinterest, linkedin, threads, bluesky, snapchat, github, etc.
"""

import os
import json
import asyncio
import logging
import subprocess
import time
from typing import Any
from pathlib import Path
from datetime import datetime
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.api.config import settings

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures"""
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 120):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "CLOSED"

    def is_open(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

# Platform capabilities matrix — what each platform supports via opencli-rs
PLATFORM_CAPABILITIES = {
    "youtube": ["search", "feed", "trending", "comments", "like", "subscribe"],
    "x": ["search", "feed", "trending", "post", "like", "follow", "retweet"],
    "reddit": ["search", "feed", "hot", "top", "upvote", "comment"],
    "instagram": ["search", "feed", "explore", "like", "follow", "comment"],
    "tiktok": ["search", "feed", "trending", "like", "follow", "comment"],
    "facebook": ["search", "feed", "like", "comment", "share"],
    "hackernews": ["search", "feed", "top", "new", "upvote"],
    "twitch": ["search", "feed", "trending", "follow"],
    "pinterest": ["search", "feed", "explore", "pin", "follow"],
    "linkedin": ["search", "feed", "post", "like", "connect"],
    "threads": ["search", "feed", "post", "like", "follow"],
    "bluesky": ["search", "feed", "post", "like", "follow"],
    "github": ["search", "feed", "trending", "star", "follow"],
    "discord": ["search", "feed", "message"],
    "telegram": ["search", "feed", "message"],
    "snapchat": ["search", "feed", "explore"],
    "wikipedia": ["search"],
    "notion": ["search", "read"],
    "stackoverflow": ["search", "feed", "top"],
}

# Map ettametta platform names to opencli-rs CLI names
PLATFORM_MAP = {
    "youtube": "youtube",
    "tiktok": "tiktok",
    "instagram": "instagram",
    "x": "x",
    "twitter": "x",
    "reddit": "reddit",
    "facebook": "facebook",
    "twitch": "twitch",
    "pinterest": "pinterest",
    "linkedin": "linkedin",
    "threads": "threads",
    "bluesky": "bluesky",
    "github": "github",
    "snapchat": "snapchat",
    "hackernews": "hackernews",
    "stackoverflow": "stackoverflow",
    "wikipedia": "wikipedia",
    "notion": "notion",
    "discord": "discord",
    "telegram": "telegram",
}


class OpenCLIService:
    """Per-user opencli-rs session manager."""

    def __init__(self):
        self.enabled = settings.ENABLE_OPENCLI
        self.binary = settings.OPENCLI_BIN
        self.sessions_dir = Path(settings.OPENCLI_SESSIONS_DIR)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._binary_available = None
        self.circuit_breaker = CircuitBreaker()

    def _check_binary(self) -> bool:
        """Check if opencli-rs binary is installed."""
        if self._binary_available is not None:
            return self._binary_available
        try:
            result = subprocess.run(
                [self.binary, "--version"], capture_output=True, timeout=5
            )
            self._binary_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._binary_available = False
        if not self._binary_available:
            logger.warning(
                f"[OpenCLI] Binary '{self.binary}' not found. "
                "Install with: cargo install opencli-rs"
            )
        return self._binary_available

    def _user_session_dir(self, user_id: str) -> Path:
        """Get the session directory for a specific user."""
        user_dir = self.sessions_dir / f"user_{user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def _cookie_path(self, user_id: str, platform: str) -> Path:
        """Get the cookie file path for a user+platform, with global fallback."""
        # 1. User-specific path
        user_path = self._user_session_dir(user_id) / f"{platform}_cookies.txt"
        if user_path.exists():
            return user_path
            
        # 2. Global fallback (from our new ./cookies folder)
        from .scanner import logger
        global_mapping = {
            "twitter": "twitter_cookies.txt",
            "x": "twitter_cookies.txt"
        }
        filename = global_mapping.get(platform, f"{platform}_cookies.txt")
        global_path = Path("cookies") / filename
        
        if global_path.exists():
            logger.info(f"[OpenCLI] Using global cookie fallback for {platform}")
            return global_path
            
        return user_path

    def _config_path(self, user_id: str) -> Path:
        """Get the opencli config path for a user."""
        return self._user_session_dir(user_id) / "config.json"

    async def is_available(self) -> bool:
        """Check if opencli is enabled and binary exists."""
        if not self.enabled:
            return False
        return await asyncio.to_thread(self._check_binary)

    async def get_supported_platforms(self) -> list[dict[str, Any]]:
        """Return list of supported platforms with their capabilities."""
        return [
            {
                "platform": platform,
                "capabilities": caps,
                "display_name": platform.replace("_", " ").title(),
            }
            for platform, caps in PLATFORM_CAPABILITIES.items()
        ]

    async def save_user_cookies(
        self, user_id: str, platform: str, cookies: str
    ) -> bool:
        """Save Chrome session cookies for a user+platform.

        Args:
            user_id: User ID
            platform: Platform name (youtube, tiktok, etc.)
            cookies: Cookie string from Chrome extension (Netscape format or JSON)

        Returns:
            True if saved successfully
        """
        platform = platform.lower()
        if platform not in PLATFORM_CAPABILITIES:
            logger.error(f"[OpenCLI] Unsupported platform: {platform}")
            return False

        try:
            cookie_path = self._cookie_path(user_id, platform)
            cookie_path.write_text(cookies)
            logger.info(
                f"[OpenCLI] Saved cookies for user={user_id} platform={platform}"
            )
            return True
        except Exception as e:
            logger.error(f"[OpenCLI] Failed to save cookies: {e}")
            return False

    async def verify_user_session(self, user_id: str, platform: str) -> dict[str, Any]:
        """Verify if a user's session for a platform is valid.

        Returns:
            dict with status, platform, capabilities, last_verified
        """
        platform = platform.lower()
        cookie_path = self._cookie_path(user_id, platform)

        if not cookie_path.exists():
            return {
                "platform": platform,
                "status": "disconnected",
                "capabilities": [],
                "message": "No session cookies found",
            }

        if not await self.is_available():
            return {
                "platform": platform,
                "status": "error",
                "capabilities": [],
                "message": "opencli-rs binary not available",
            }

        # Verify by running a lightweight command
        try:
            result = await self._run_opencli(user_id, platform, "feed", {"limit": "1"})
            if result is not None:
                return {
                    "platform": platform,
                    "status": "connected",
                    "capabilities": PLATFORM_CAPABILITIES.get(platform, []),
                    "last_verified": datetime.utcnow().isoformat(),
                    "message": "Session valid",
                }
            else:
                return {
                    "platform": platform,
                    "status": "expired",
                    "capabilities": PLATFORM_CAPABILITIES.get(platform, []),
                    "message": "Session cookies may be expired",
                }
        except Exception as e:
            return {
                "platform": platform,
                "status": "error",
                "capabilities": [],
                "message": str(e),
            }

    async def get_user_sessions(self, user_id: str) -> list[dict[str, Any]]:
        """Get all platform session statuses for a user."""
        sessions = []
        user_dir = self._user_session_dir(user_id)

        for platform in PLATFORM_CAPABILITIES:
            cookie_path = self._cookie_path(user_id, platform)
            if cookie_path.exists():
                status = await self.verify_user_session(user_id, platform)
                sessions.append(status)
            else:
                sessions.append(
                    {
                        "platform": platform,
                        "status": "disconnected",
                        "capabilities": PLATFORM_CAPABILITIES[platform],
                        "message": "Not connected",
                    }
                )

        return sessions

    async def disconnect_platform(self, user_id: str, platform: str) -> bool:
        """Remove session cookies for a user+platform."""
        platform = platform.lower()
        cookie_path = self._cookie_path(user_id, platform)
        try:
            if cookie_path.exists():
                cookie_path.unlink()
                logger.info(
                    f"[OpenCLI] Disconnected user={user_id} platform={platform}"
                )
            return True
        except Exception as e:
            logger.error(f"[OpenCLI] Failed to disconnect: {e}")
            return False

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((asyncio.TimeoutError, subprocess.SubprocessError)),
        reraise=False
    )
    async def _run_opencli(
        self,
        user_id: str,
        platform: str,
        command: str,
        params: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any] | None:
        """Execute an opencli-rs command with circuit breaking and retries."""
        if self.circuit_breaker.is_open():
            logger.warning("[OpenCLI] Circuit breaker is OPEN - skipping execution")
            return None

        platform = platform.lower()
        cookie_path = self._cookie_path(user_id, platform)

        if not cookie_path.exists():
            logger.error(f"[OpenCLI] No cookies for user={user_id} platform={platform}")
            return None

        if not await self.is_available():
            return None

        # Build command
        cmd = [
            self.binary,
            "--cookies",
            str(cookie_path),
            "--output",
            "json",
            platform,
            command,
        ]

        if params:
            for key, value in params.items():
                cmd.extend([f"--{key}", str(value)])

        try:
            logger.info(f"[OpenCLI] Running: {' '.join(cmd)}")
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            if proc.returncode != 0:
                self.circuit_breaker.record_failure()
                logger.error(
                    f"[OpenCLI] Command failed (rc={proc.returncode}): "
                    f"{stderr.decode()[:500]}"
                )
                return None

            output = stdout.decode().strip()
            if not output:
                return None

            result = json.loads(output)
            self.circuit_breaker.record_success()
            return result

        except asyncio.TimeoutError:
            self.circuit_breaker.record_failure()
            logger.error(f"[OpenCLI] Command timed out after {timeout}s")
            return None
        except json.JSONDecodeError:
            logger.warning(f"[OpenCLI] Non-JSON output: {output[:200]}")
            return {"raw": output}
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"[OpenCLI] Execution error: {e}")
            return None

    # ─── Discovery Integration ─────────────────────────────────────────

    async def search_platform(
        self,
        user_id: str,
        platform: str,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search a platform using the user's Chrome session.

        Returns results in ContentCandidate-compatible format.
        """
        result = await self._run_opencli(
            user_id, platform, "search", {"query": query, "limit": str(limit)}
        )

        if not result:
            return []

        # Parse opencli-rs output into ettametta's candidate format
        candidates = []
        items = result.get("results", result.get("items", []))
        if isinstance(result, list):
            items = result

        for item in items:
            candidate = {
                "platform": platform,
                "url": item.get("url") or item.get("link") or item.get("permalink", ""),
                "title": item.get("title") or item.get("text", "")[:200],
                "author": item.get("author")
                or item.get("username")
                or item.get("channel", ""),
                "views": self._parse_count(
                    item.get("views") or item.get("view_count", 0)
                ),
                "engagement_score": float(
                    item.get("engagement") or item.get("score", 0)
                ),
                "viral_score": min(
                    100, int(float(item.get("score") or item.get("upvotes", 0)) / 10)
                ),
                "duration_seconds": float(item.get("duration") or 0),
                "thumbnail_url": item.get("thumbnail") or item.get("image", ""),
                "tags": item.get("tags") or [],
                "discovery_method": "opencli-rs",
                "metadata_json": {
                    "opencli_platform": platform,
                    "raw_data": item,
                },
            }
            candidates.append(candidate)

        return candidates

    async def get_platform_feed(
        self,
        user_id: str,
        platform: str,
        feed_type: str = "feed",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get feed/trending content from a platform.

        Args:
            user_id: User ID
            platform: Platform name
            feed_type: feed, trending, hot, top, explore
            limit: Number of results
        """
        result = await self._run_opencli(
            user_id, platform, feed_type, {"limit": str(limit)}
        )

        if not result:
            return []

        items = result.get("results", result.get("items", result.get("posts", [])))
        if isinstance(result, list):
            items = result

        candidates = []
        for item in items:
            candidate = {
                "platform": platform,
                "url": item.get("url") or item.get("link") or item.get("permalink", ""),
                "title": item.get("title") or item.get("text", "")[:200],
                "author": item.get("author")
                or item.get("username")
                or item.get("channel", ""),
                "views": self._parse_count(
                    item.get("views") or item.get("view_count", 0)
                ),
                "engagement_score": float(
                    item.get("engagement") or item.get("score", 0)
                ),
                "viral_score": min(
                    100, int(float(item.get("score") or item.get("upvotes", 0)) / 10)
                ),
                "thumbnail_url": item.get("thumbnail") or item.get("image", ""),
                "tags": item.get("tags") or [],
                "discovery_method": "opencli-rs",
                "metadata_json": {
                    "opencli_platform": platform,
                    "feed_type": feed_type,
                    "raw_data": item,
                },
            }
            candidates.append(candidate)

        return candidates

    # ─── Publishing Integration ─────────────────────────────────────────

    async def post_to_platform(
        self,
        user_id: str,
        platform: str,
        content: str,
        media_url: str | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Post content to a platform using the user's session.

        Args:
            user_id: User ID
            platform: Target platform
            content: Text content to post
            media_url: Any media URL to attach
            extra_params: Additional platform-specific parameters

        Returns:
            dict with success status and post URL
        """
        params = {"content": content}
        if media_url:
            params["media"] = media_url
        if extra_params:
            params.update(extra_params)

        result = await self._run_opencli(user_id, platform, "post", params, timeout=60)

        if result:
            return {
                "success": True,
                "url": result.get("url") or result.get("permalink", ""),
                "post_id": result.get("id") or result.get("post_id", ""),
                "platform": platform,
            }
        return {
            "success": False,
            "error": "opencli command failed or returned no data",
            "platform": platform,
        }

    async def interact_with_content(
        self,
        user_id: str,
        platform: str,
        action: str,
        content_url: str,
    ) -> dict[str, Any]:
        """Perform an interaction on platform content (like, comment, follow, etc.).

        Args:
            user_id: User ID
            platform: Target platform
            action: Interaction type (like, follow, comment, retweet, upvote, etc.)
            content_url: URL of the content to interact with
        """
        result = await self._run_opencli(
            user_id, platform, action, {"url": content_url}, timeout=15
        )

        return {
            "success": result is not None,
            "action": action,
            "platform": platform,
            "url": content_url,
            "result": result,
        }

    # ─── Utilities ──────────────────────────────────────────────────────

    @staticmethod
    def _parse_count(value) -> int:
        """Parse view/engagement counts that might be strings like '1.2M'."""
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if not isinstance(value, str):
            return 0
        value = value.strip().upper().replace(",", "")
        multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
        for suffix, mult in multipliers.items():
            if value.endswith(suffix):
                try:
                    return int(float(value[:-1]) * mult)
                except ValueError:
                    return 0
        try:
            return int(float(value))
        except ValueError:
            return 0

    async def get_user_platforms_status(self, user_id: str) -> dict[str, Any]:
        """Get a summary of all platform connections for a user."""
        sessions = await self.get_user_sessions(user_id)
        connected = [s for s in sessions if s["status"] == "connected"]
        expired = [s for s in sessions if s["status"] == "expired"]

        return {
            "total_platforms": len(PLATFORM_CAPABILITIES),
            "connected": len(connected),
            "expired": len(expired),
            "disconnected": len(sessions) - len(connected) - len(expired),
            "sessions": sessions,
            "available": await self.is_available(),
        }


# Global instance
opencli_service = OpenCLIService()
