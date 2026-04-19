"""
opencli-rs Discovery Scanner
============================

Wraps per-user opencli-rs sessions into the DiscoveryService scanner interface.
Unlike other scanners that use global API keys, this scanner uses the
individual user's Chrome session cookies.

Each user can have their own connected platforms (YouTube, TikTok, Reddit, etc.)
and this scanner will use their session to search/fetch content.
"""

import logging
from typing import Any
from services.discovery.models import ContentCandidate

logger = logging.getLogger(__name__)


class OpenCLIScanner:
    """Scanner that uses a specific user's opencli-rs sessions."""

    def __init__(self, user_id: int):
        self.user_id = user_id

    async def scan_trends(
        self,
        niche: str,
        published_after=None,
        platforms: list[str] | None = None,
    ) -> list[ContentCandidate]:
        """Search all connected platforms for the user.

        Args:
            niche: Search query / niche keyword
            platforms: Specific platforms to search (None = all connected)
        """
        from services.opencli.service import opencli_service
        from api.config import settings

        if not settings.ENABLE_OPENCLI:
            return []

        if not await opencli_service.is_available():
            return []

        # Get user's connected platforms
        sessions = await opencli_service.get_user_sessions(self.user_id)
        connected = [
            s
            for s in sessions
            if s["status"] == "connected"
            and (platforms is None or s["platform"] in platforms)
        ]

        if not connected:
            logger.debug(
                f"[OpenCLIScanner] No connected platforms for user={self.user_id}"
            )
            return []

        # Search each connected platform in parallel
        import asyncio

        tasks = []
        for session in connected:
            tasks.append(
                opencli_service.search_platform(
                    self.user_id, session["platform"], niche, limit=20
                )
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert to ContentCandidate format
        candidates = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"[OpenCLIScanner] Search failed: {result}")
                continue
            for item in result:
                try:
                    candidate = ContentCandidate(
                        id=f"oc_{hash(item.get('url', '')) % 100000}",
                        platform=item.get("platform", "unknown"),
                        source_url=item.get("url", ""),
                        creator_name=item.get("author", ""),
                        title=item.get("title", ""),
                        view_count=item.get("views", 0),
                        like_count=0,
                        comment_count=0,
                        share_count=0,
                        engagement_score=item.get("engagement_score", 0.0),
                        viral_score=item.get("viral_score", 0),
                        duration_seconds=item.get("duration_seconds", 0.0),
                        thumbnail_url=item.get("thumbnail_url", ""),
                        tags=item.get("tags", []),
                    )
                    candidates.append(candidate)
                except Exception as e:
                    logger.warning(f"[OpenCLIScanner] Failed to parse result: {e}")

        logger.info(
            f"[OpenCLIScanner] Found {len(candidates)} candidates across "
            f"{len(connected)} platforms for user={self.user_id}"
        )
        return candidates

    async def get_platform_feed(
        self,
        platform: str,
        feed_type: str = "trending",
        limit: int = 20,
    ) -> list[ContentCandidate]:
        """Get feed/trending from a specific platform for the user."""
        from services.opencli.service import opencli_service

        results = await opencli_service.get_platform_feed(
            self.user_id, platform, feed_type, limit
        )

        candidates = []
        for item in results:
            try:
                candidate = ContentCandidate(
                    id=f"oc_feed_{hash(item.get('url', '')) % 100000}",
                    platform=item.get("platform", platform),
                    source_url=item.get("url", ""),
                    creator_name=item.get("author", ""),
                    title=item.get("title", ""),
                    view_count=item.get("views", 0),
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=item.get("engagement_score", 0.0),
                    viral_score=item.get("viral_score", 0),
                    duration_seconds=item.get("duration_seconds", 0.0),
                    thumbnail_url=item.get("thumbnail_url", ""),
                    tags=item.get("tags", []),
                )
                candidates.append(candidate)
            except Exception as e:
                logger.warning(f"[OpenCLIScanner] Failed to parse feed item: {e}")

        return candidates
