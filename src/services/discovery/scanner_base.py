from abc import ABC, abstractmethod
import datetime
import math
from .models import ContentCandidate


class DiscoveryScannerBase(ABC):
    @abstractmethod
    async def scan_trends(
        self, niche: str, published_after: datetime.datetime | None = None, region: str | None = None
    ) -> list[ContentCandidate]:
        pass

    def identify_viral_velocity(self, candidate: ContentCandidate) -> float:
        """
        Calculates how fast the content is gaining views/engagement.
        Default implementation: views per hour based on published_at or scanned_at.
        Can be overridden by scanners with more accurate data (like YouTube API).
        """

        # Try to get publication date from various sources
        pub_date = None

        # 1. Check metadata_json for published_at
        candidate_metadata = candidate.metadata_json or {}
        if candidate_metadata:
            pub_date_str = candidate_metadata.get(
                "published_at"
            ) or candidate_metadata.get("publishedTime")
            if pub_date_str:
                try:
                    pub_date = datetime.datetime.fromisoformat(
                        pub_date_str.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass

        # 2. Fall back to published_at field
        if not pub_date and candidate.published_at:
            pub_date = candidate.published_at

        # 3. Fall back to scanned_at
        if not pub_date and candidate.scanned_at:
            pub_date = candidate.scanned_at

        # Calculate hours since publication
        if pub_date:
            try:
                now = datetime.datetime.now(datetime.timezone.utc)
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=datetime.timezone.utc)
                hours_since = (now - pub_date).total_seconds() / 3600
                hours_since = max(hours_since, 0.5)  # At least 30 min to avoid division by zero
                return candidate.view_count / hours_since
            except (AttributeError, TypeError, ValueError):
                pass

        # 4. Ultimate fallback: estimate based on engagement
        # newer content with high engagement = higher velocity
        hours_estimated = 24  # Assume 24 hours old if unknown
        return candidate.view_count / hours_estimated

    def calculate_viral_score(self, candidate: ContentCandidate) -> int:
        """
        Calculate a composite viral score (0-100) based on multiple factors.
        Uses adaptive logarithmic view scaling and engagement-weighted bonuses.
        Override this for platform-specific scoring.
        """
        velocity = self.identify_viral_velocity(candidate)

        # Adaptive logarithmic view score (log10 scaling, 1k views = 0, 10M = 5)
        if candidate.view_count > 0:
            log_views = math.log10(candidate.view_count)
            # Scale: log10(1000) = 3 -> score 0; log10(10_000_000) = 7 -> score 5
            view_score = min(5.0, max(0.0, (log_views - 3.0) * 1.25))
        else:
            view_score = 0.0

        # Engagement bonus with standardized ratio weighting
        # Normalize engagement_score to ratio (e.g. 0.065 = 6.5%)
        raw_engagement = (
            candidate.engagement_score / 100.0
            if candidate.engagement_score and candidate.engagement_score > 1.0
            else candidate.engagement_score or 0.0
        )
        # High engagement bonus (up to 5.0 points): 6.5% engagement = ~2.5 points, 20%+ = 5 points
        engagement_bonus = min(5.0, raw_engagement * 25.0) if raw_engagement else 0.0

        # Duration bonus (shorts/preferred durations get boosted)
        duration_bonus = 0
        if candidate.duration_seconds:
            # Optimal: 15-60 seconds for shorts gets 15 boost, 60-180s gets 10
            if 15 <= candidate.duration_seconds <= 60:
                duration_bonus = 15
            elif 60 < candidate.duration_seconds <= 180:
                duration_bonus = 10

        return min(int(view_score + engagement_bonus + duration_bonus), 100)

    # Rate limiting utilities for scanner operations
    _rate_limit_timestamp = 0.0
    _rate_limit_delay = 1.0  # Minimum seconds between requests per scanner

    async def _rate_limit(self):
        """Ensure minimum delay between requests to avoid rate limiting."""
        import asyncio
        now = asyncio.get_running_loop().time()
        elapsed = now - self._rate_limit_timestamp
        if elapsed < self._rate_limit_delay:
            wait_time = self._rate_limit_delay - elapsed
            await asyncio.sleep(wait_time)
        self._rate_limit_timestamp = asyncio.get_running_loop().time()
