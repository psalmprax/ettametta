from datetime import datetime, timedelta
import random
from src.shared.enums import ContentPublishStatus


class SmartScheduler:
    def __init__(self):
        # Default peak engagement windows (Fallback)
        self.default_windows = [
            {"start": 9, "end": 11},  # Morning rush
            {"start": 12, "end": 14},  # Lunch break
            {"start": 18, "end": 21},  # Evening peak
        ]

    async def _get_peak_windows_from_db(self, user_id: str = None) -> list[dict]:
        """
        Dynamically calculate peak engagement windows based on historic real performance.
        Falls back to default windows if insufficient data.
        """
        try:
            from src.api.utils.database import async_session_factory
            from src.api.utils.models import PublishedContentDB
            from sqlalchemy import extract, func, select

            async with async_session_factory() as db:
                # Query views grouped by the hour the post was created/published
                stmt = select(
                    extract("hour", PublishedContentDB.published_at).label("hour"),
                    func.avg(PublishedContentDB.view_count).label("avg_views"),
                ).where(
                    PublishedContentDB.status == ContentPublishStatus.PUBLISHED,
                    PublishedContentDB.view_count > 0,
                )

                if user_id:
                    stmt = stmt.where(PublishedContentDB.user_id == user_id)

                stmt = (
                    stmt.group_by(extract("hour", PublishedContentDB.published_at))
                    .order_by(func.avg(PublishedContentDB.view_count).desc())
                    .limit(3)
                )

                result = await db.execute(stmt)
                results = result.all()

                if len(results) >= 2:
                    # Construct smart windows based on top performing hours
                    windows = []
                    for row in results:
                        hour = int(row.hour)
                        windows.append({"start": hour, "end": hour + 2})
                    return sorted(windows, key=lambda x: x["start"])
        except Exception as e:
            # If DB error or missing models, we fall back to defaults
            import logging

            logging.getLogger("SmartScheduler").warning(
                f"Failed to calculate dynamic peak windows: {e}. Using fallback."
            )

        return self.default_windows

    def calculate_next_posting_time(
        self, last_post_time: datetime | None = None, user_id: str = None
    ) -> datetime:
        """
        Calculates the optimal next posting window based on current trends and peak times.
        """
        now = datetime.utcnow()
        base_time = last_post_time if last_post_time and last_post_time > now else now

        # Add random buffer to avoid bot detection patterns (30-90 mins)
        next_time = base_time + timedelta(minutes=random.randint(30, 90))

        # Adjust to nearest peak window
        import asyncio

        peak_windows = asyncio.run(self._get_peak_windows_from_db(user_id))
        current_hour = next_time.hour
        for window in peak_windows:
            if current_hour >= window["start"] and current_hour <= window["end"]:
                return next_time

        # If not in window, find the next one
        for window in peak_windows:
            if window["start"] > current_hour:
                return next_time.replace(
                    hour=window["start"], minute=random.randint(0, 30)
                )

        # Next day first window
        return (next_time + timedelta(days=1)).replace(
            hour=peak_windows[0]["start"], minute=random.randint(0, 30)
        )

    def calculate_n_optimal_windows(
        self, count: int = 3, user_id: str = None
    ) -> list[dict]:
        """
        Returns the top N optimal posting windows with engagement predictions.

        Args:
            count: Number of windows to return (default 3)
            user_id: Optional user ID for personalized windows

        Returns:
            List of dicts with: {window_start, window_end, hour, engagement_prediction}
        """
        import asyncio

        peak_windows = asyncio.run(self._get_peak_windows_from_db(user_id))

        # Generate predictions based on position (top window = highest prediction)
        results = []
        base_prediction = 85  # Base engagement prediction

        for i, window in enumerate(peak_windows[:count]):
            # Decrease prediction for each subsequent window
            prediction = max(base_prediction - (i * 10), 40)  # Min 40%
            results.append(
                {
                    "window_start": window["start"],
                    "window_end": window["end"],
                    "hour": window["start"],
                    "engagement_prediction": prediction,
                    "reason": f"{prediction}% predicted engagement"
                    if i == 0
                    else f"{prediction}% predicted engagement",
                }
            )

        return results

    def is_parallel_allowed(
        self, scheduled_time: datetime, last_post_time: datetime | None = None
    ) -> bool:
        """
        Determines if parallel posting is allowed based on spacing.

        Args:
            scheduled_time: The time being considered for the new post
            last_post_time: The time of the last post (if any)

        Returns:
            True if parallel is allowed (4+ hours apart), False otherwise
        """
        if last_post_time is None:
            return True  # No previous posts, parallel is fine

        hours_apart = (scheduled_time - last_post_time).total_seconds() / 3600
        return hours_apart >= 4

    def predict_engagement(self, user_id: str, scheduled_time: datetime) -> float:
        """
        Predicts engagement percentage for a given scheduled time.

        Args:
            user_id: User ID for personalized predictions
            scheduled_time: The time to predict engagement for

        Returns:
            Predicted engagement percentage (0-100)
        """
        import asyncio

        hour = scheduled_time.hour

        # Get windows and find position
        try:
            windows = asyncio.run(self._get_peak_windows_from_db(user_id))
        except Exception:
            windows = self.default_windows

        # Find which window this hour falls into
        for i, window in enumerate(windows):
            if window["start"] <= hour < window["end"]:
                # Within a peak window - higher prediction
                base = 85 - (i * 10) if i > 0 else 85
                return float(max(base - 5, 50))  # Slight penalty for exact match

        # Outside peak window - lower prediction
        return 45.0


smart_scheduler = SmartScheduler()
