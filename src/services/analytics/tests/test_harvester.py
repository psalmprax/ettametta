"""
Unit Tests for AnalyticsHarvester (The Raven)
===============================================
Tests the autonomous analytics harvester lifecycle, polling logic,
metrics harvesting, error handling, and seen_video_ids tracking.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone


@pytest.fixture
def harvester():
    """Create a fresh harvester instance for each test."""
    from src.services.analytics.harvester import AnalyticsHarvester

    h = AnalyticsHarvester()
    h.poll_interval = 0.01  # Fast for testing
    return h


class TestHarvesterLifecycle:
    """Test harvester start/stop lifecycle."""

    def test_init_defaults(self, harvester):
        """Test default initialization values."""
        assert harvester.seen_video_ids == set()
        assert harvester.is_running is False
        assert harvester.poll_interval == 0.01  # Overridden by fixture
        assert harvester._max_seen == 1000

    @pytest.mark.asyncio
    async def test_start_harvest_loop_sets_running(self, harvester):
        """Test start_harvest_loop sets is_running True."""
        with patch.object(harvester, "_poll_published_content", new_callable=AsyncMock) as mock_poll:
            # Start the loop in a task
            loop_task = asyncio.create_task(harvester.start_harvest_loop())
            await asyncio.sleep(0.05)  # Let it run briefly

            assert harvester.is_running is True
            assert mock_poll.called

            # Stop it
            await harvester.stop()
            loop_task.cancel()

    @pytest.mark.asyncio
    async def test_stop_sets_running_false(self, harvester):
        """Test stop sets is_running False."""
        with patch.object(harvester, "_poll_published_content", new_callable=AsyncMock):
            harvester.is_running = True
            await harvester.stop()
            assert harvester.is_running is False

    @pytest.mark.asyncio
    async def test_start_harvest_loop_idempotent(self, harvester):
        """Test start_harvest_loop does nothing if already running."""
        harvester.is_running = True
        with patch.object(harvester, "_poll_published_content", new_callable=AsyncMock) as mock_poll:
            await harvester.start_harvest_loop()
            assert not mock_poll.called


class TestPollPublishedContent:
    """Test polling published content from the database."""

    @pytest.mark.asyncio
    async def test_poll_empty_db(self, harvester):
        """Test polling when DB returns no content."""
        with patch("src.api.utils.database.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)

            await harvester._poll_published_content()
            # Should exit cleanly — no assertion needed beyond no exception
            assert len(harvester.seen_video_ids) == 0

    @pytest.mark.asyncio
    async def test_poll_with_content(self, harvester):
        """Test polling when DB returns published content."""
        with (
            patch("src.api.utils.database.async_session_factory") as mock_factory,
            patch.object(harvester, "_harvest_content_metrics", new_callable=AsyncMock) as mock_harvest,
        ):
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            # Mock a published content item
            mock_content = MagicMock()
            mock_content.id = "video_123"
            mock_content.user_id = "user_456"
            mock_content.platform = "youtube"
            mock_content.published_at = datetime.now(timezone.utc) - timedelta(days=1)
            mock_content.niche = "Tech"

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_content]
            mock_session.execute = AsyncMock(return_value=mock_result)

            await harvester._poll_published_content()

            # Verify harvest was called with the content
            mock_harvest.assert_called_once_with(mock_content)
            assert "video_123" in harvester.seen_video_ids

    @pytest.mark.asyncio
    async def test_poll_skips_already_seen(self, harvester):
        """Test polling skips content that was already processed."""
        harvester.seen_video_ids.add("video_123")

        with (
            patch("src.api.utils.database.async_session_factory") as mock_factory,
            patch.object(harvester, "_harvest_content_metrics", new_callable=AsyncMock) as mock_harvest,
        ):
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            mock_content = MagicMock()
            mock_content.id = "video_123"
            mock_content.user_id = "user_456"
            mock_content.platform = "youtube"
            mock_content.published_at = datetime.now(timezone.utc) - timedelta(days=1)

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_content]
            mock_session.execute = AsyncMock(return_value=mock_result)

            await harvester._poll_published_content()
            mock_harvest.assert_not_called()

    @pytest.mark.asyncio
    async def test_poll_handles_db_error(self, harvester):
        """Test polling handles database errors gracefully."""
        with patch("src.api.utils.database.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_session.execute = AsyncMock(side_effect=Exception("DB connection lost"))

            # Should not raise
            await harvester._poll_published_content()
            assert len(harvester.seen_video_ids) == 0


class TestHarvestContentMetrics:
    """Test the core metrics harvesting logic."""

    @pytest.mark.asyncio
    async def test_harvest_content_metrics_success(self, harvester):
        """Test full harvest flow with real performance data."""
        with (
            patch("src.services.analytics.harvester.base_analytics_service") as mock_analytics,
            patch("src.services.analytics.harvester.base_bridge_service") as mock_bridge,
            patch("src.services.analytics.harvester.base_analyst_service") as mock_analyst,
        ):
            # Mock performance report
            mock_performance = MagicMock()
            mock_performance.view_count = 50000
            mock_performance.like_count = 2500
            mock_performance.share_count = 1000
            mock_performance.comment_count = 500
            mock_performance.retention_rate = 0.65
            mock_performance.watch_time = 120.0
            mock_analytics.get_performance_report = AsyncMock(return_value=mock_performance)

            # Mock analyst regret analysis
            mock_analyst.analyze_regret = AsyncMock(return_value={
                "causal_reason": "Strong hook retention",
                "gap_score": 0.15,
            })

            # Mock bridge ingestion
            mock_bridge.ingest_performance = AsyncMock(return_value={"status": "success"})

            # Mock snapshot recording
            mock_analytics.record_snapshot = AsyncMock(return_value=None)

            # Mock oracle predictor (imported locally inside harvester method)
            with patch("src.services.optimization.oracle_predictor.base_oracle_service") as mock_oracle:
                import numpy as np
                mock_oracle.predict_curve = MagicMock(return_value=np.array([0.7, 0.6, 0.5, 0.4, 0.3]))

                # Create mock content
                mock_content = MagicMock()
                mock_content.id = "video_789"
                mock_content.user_id = "user_abc"
                mock_content.platform = "youtube"
                mock_content.niche = "Tech"
                mock_content.published_at = datetime.now(timezone.utc) - timedelta(days=3)

                await harvester._harvest_content_metrics(mock_content)

                # Verify performance report was fetched
                mock_analytics.get_performance_report.assert_called_once_with(
                    post_id="video_789",
                    user_id="user_abc",
                    platform="youtube",
                )

                # Verify bridge ingestion was called
                mock_bridge.ingest_performance.assert_called_once()
                call_args = mock_bridge.ingest_performance.call_args[0]
                assert call_args[0] == "video_789"  # video_id
                assert call_args[1]["views"] == 50000  # metrics dict
                assert "predicted_retention_curve" in call_args[2]  # production_data

                # Verify snapshot was recorded
                mock_analytics.record_snapshot.assert_called_once_with(
                    post_id="video_789",
                    views=50000,
                    likes=2500,
                    shares=1000,
                    comments=500,
                    retention_rate=0.65,
                    avg_duration=120.0,
                )

    @pytest.mark.asyncio
    async def test_harvest_platform_fallback(self, harvester):
        """Test harvest falls back to default platform when platform is None."""
        with (
            patch("src.services.analytics.harvester.base_analytics_service") as mock_analytics,
            patch("src.services.analytics.harvester.base_bridge_service") as mock_bridge,
            patch("src.services.analytics.harvester.base_analyst_service") as mock_analyst,
        ):
            mock_performance = MagicMock()
            mock_performance.view_count = 0
            mock_performance.like_count = 0
            mock_performance.share_count = 0
            mock_performance.comment_count = 0
            mock_performance.retention_rate = 0.0
            mock_performance.watch_time = 0.0
            mock_analytics.get_performance_report = AsyncMock(return_value=mock_performance)
            mock_analyst.analyze_regret = AsyncMock(return_value={"causal_reason": "No data"})
            mock_bridge.ingest_performance = AsyncMock()
            mock_analytics.record_snapshot = AsyncMock()

            mock_content = MagicMock()
            mock_content.id = "video_no_platform"
            mock_content.user_id = "user_abc"
            mock_content.platform = None  # No platform set
            mock_content.niche = "General"
            mock_content.published_at = datetime.now(timezone.utc) - timedelta(days=1)

            await harvester._harvest_content_metrics(mock_content)

            # Should fall back to "youtube" platform
            mock_analytics.get_performance_report.assert_called_once_with(
                post_id="video_no_platform",
                user_id="user_abc",
                platform="youtube",
            )

    @pytest.mark.asyncio
    async def test_harvest_api_failure(self, harvester):
        """Test harvest handles analytics API failure gracefully."""
        with (
            patch("src.services.analytics.harvester.base_analytics_service") as mock_analytics,
            patch("src.services.analytics.harvester.base_bridge_service") as mock_bridge,
            patch("src.services.analytics.harvester.base_analyst_service") as mock_analyst,
        ):
            # Simulate API failure
            mock_analytics.get_performance_report = AsyncMock(
                side_effect=Exception("YouTube API quota exceeded")
            )
            mock_analytics.record_snapshot = AsyncMock()
            mock_bridge.ingest_performance = AsyncMock()
            mock_analyst.analyze_regret = AsyncMock()

            mock_content = MagicMock()
            mock_content.id = "video_fail"
            mock_content.user_id = "user_abc"
            mock_content.platform = "youtube"
            mock_content.published_at = datetime.now(timezone.utc) - timedelta(days=1)

            # Should not raise exception — caught internally
            await harvester._harvest_content_metrics(mock_content)

            # Bridge should NOT have been called since performance fetch failed
            mock_bridge.ingest_performance.assert_not_called()

    @pytest.mark.asyncio
    async def test_harvest_oracle_failure_uses_fallback_curve(self, harvester):
        """Test harvest falls back to linear decay curve when Oracle is unavailable."""
        with (
            patch("src.services.analytics.harvester.base_analytics_service") as mock_analytics,
            patch("src.services.analytics.harvester.base_bridge_service") as mock_bridge,
            patch("src.services.analytics.harvester.base_analyst_service") as mock_analyst,
        ):
            mock_performance = MagicMock()
            mock_performance.view_count = 10000
            mock_performance.like_count = 500
            mock_performance.share_count = 100
            mock_performance.comment_count = 50
            mock_performance.retention_rate = 0.7
            mock_performance.watch_time = 60.0
            mock_analytics.get_performance_report = AsyncMock(return_value=mock_performance)
            mock_analyst.analyze_regret = AsyncMock(return_value={"causal_reason": "Good"})
            mock_bridge.ingest_performance = AsyncMock()
            mock_analytics.record_snapshot = AsyncMock()

            mock_content = MagicMock()
            mock_content.id = "video_oracle_fail"
            mock_content.user_id = "user_abc"
            mock_content.platform = "youtube"
            mock_content.niche = "Tech"
            mock_content.published_at = datetime.now(timezone.utc) - timedelta(days=2)

            await harvester._harvest_content_metrics(mock_content)

            # Should still ingest data even without oracle
            mock_bridge.ingest_performance.assert_called_once()
            call_args = mock_bridge.ingest_performance.call_args[0]
            # production_data should still have predicted_retention_curve
            assert "predicted_retention_curve" in call_args[2]

    @pytest.mark.asyncio
    async def test_seen_video_ids_cap(self, harvester):
        """Test seen_video_ids clears when exceeding max."""
        harvester._max_seen = 3
        harvester.seen_video_ids = {"old_1", "old_2", "old_3"}

        with (
            patch("src.services.analytics.harvester.base_analytics_service") as mock_analytics,
            patch("src.services.analytics.harvester.base_bridge_service") as mock_bridge,
            patch("src.services.analytics.harvester.base_analyst_service") as mock_analyst,
        ):
            mock_performance = MagicMock()
            mock_performance.view_count = 0
            mock_performance.like_count = 0
            mock_performance.share_count = 0
            mock_performance.comment_count = 0
            mock_performance.retention_rate = 0.0
            mock_performance.watch_time = 0.0
            mock_analytics.get_performance_report = AsyncMock(return_value=mock_performance)
            mock_analyst.analyze_regret = AsyncMock(return_value={})
            mock_bridge.ingest_performance = AsyncMock()
            mock_analytics.record_snapshot = AsyncMock()

            mock_content = MagicMock()
            mock_content.id = "new_video"
            mock_content.user_id = "user"
            mock_content.platform = "youtube"
            mock_content.published_at = datetime.now(timezone.utc)

            # The check is len > max, and we have 3 existing + 1 new = 4 > 3, so it should clear
            await harvester._harvest_content_metrics(mock_content)

            # After clear, seen set should only contain the new video
            assert len(harvester.seen_video_ids) <= harvester._max_seen

    @pytest.mark.asyncio
    async def test_harvest_content_metrics_with_oracle_prediction(self, harvester):
        """Test that Oracle-predicted curves are used when available."""
        with (
            patch("src.services.analytics.harvester.base_analytics_service") as mock_analytics,
            patch("src.services.analytics.harvester.base_bridge_service") as mock_bridge,
            patch("src.services.analytics.harvester.base_analyst_service") as mock_analyst,
            patch("src.services.optimization.oracle_predictor.base_oracle_service") as mock_oracle,
        ):
            import numpy as np

            mock_performance = MagicMock()
            mock_performance.view_count = 100000
            mock_performance.like_count = 5000
            mock_performance.share_count = 2000
            mock_performance.comment_count = 1000
            mock_performance.retention_rate = 0.8
            mock_performance.watch_time = 90.0
            mock_analytics.get_performance_report = AsyncMock(return_value=mock_performance)
            mock_analyst.analyze_regret = AsyncMock(return_value={"causal_reason": "Oracle curve used"})
            mock_bridge.ingest_performance = AsyncMock()
            mock_analytics.record_snapshot = AsyncMock()

            # Oracle produces a realistic curve
            mock_oracle.predict_curve = MagicMock(return_value=np.array([0.85, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25]))

            mock_content = MagicMock()
            mock_content.id = "video_oracle_ok"
            mock_content.user_id = "user_abc"
            mock_content.platform = "youtube"
            mock_content.niche = "Gaming"
            mock_content.published_at = datetime.now(timezone.utc) - timedelta(days=5)

            await harvester._harvest_content_metrics(mock_content)

            # Oracle should have been called with features + zero vector
            mock_oracle.predict_curve.assert_called_once()
            call_args = mock_oracle.predict_curve.call_args[0]
            assert len(call_args[0]) == 5  # 5 features
            assert call_args[0][0] == pytest.approx(0.1)  # view_count / 1M = 0.1
            assert len(call_args[1]) == 512  # zero vector

            # Ingestion should have been called with oracle curve
            mock_bridge.ingest_performance.assert_called_once()
            production_data = mock_bridge.ingest_performance.call_args[0][2]
            assert len(production_data["predicted_retention_curve"]) <= 7


class TestBridgeIntegration:
    """Test integration with the bridge service."""

    @pytest.mark.asyncio
    async def test_bridge_gets_correct_metrics_dict(self, harvester):
        """Test that metrics dict passed to bridge has expected structure."""
        with (
            patch("src.services.analytics.harvester.base_analytics_service") as mock_analytics,
            patch("src.services.analytics.harvester.base_bridge_service") as mock_bridge,
            patch("src.services.analytics.harvester.base_analyst_service") as mock_analyst,
        ):
            mock_performance = MagicMock()
            mock_performance.view_count = 75000
            mock_performance.like_count = 3000
            mock_performance.share_count = 1500
            mock_performance.comment_count = 750
            mock_performance.retention_rate = 0.72
            mock_performance.watch_time = 0.0
            mock_analytics.get_performance_report = AsyncMock(return_value=mock_performance)
            mock_analyst.analyze_regret = AsyncMock(return_value={
                "causal_reason": "Strong middle-section retention",
                "gap_score": 0.12,
            })
            mock_bridge.ingest_performance = AsyncMock()
            mock_analytics.record_snapshot = AsyncMock()

            mock_content = MagicMock()
            mock_content.id = "video_bridge_test"
            mock_content.user_id = "user_bridge"
            mock_content.platform = "youtube"
            mock_content.niche = "Education"
            mock_content.published_at = datetime.now(timezone.utc) - timedelta(days=7)

            await harvester._harvest_content_metrics(mock_content)

            # Verify the metrics dict structure
            call_args = mock_bridge.ingest_performance.call_args
            metrics = call_args[0][1]
            production_data = call_args[0][2]

            # Metrics dict should have all expected keys
            assert metrics["video_id"] == "video_bridge_test"
            assert metrics["views"] == 75000
            assert metrics["likes"] == 3000
            assert metrics["shares"] == 1500
            assert metrics["comments"] == 750
            assert metrics["retention_p50"] == 0.72
            assert "causal_insight" in metrics

            # Production data should have blueprint
            assert "blueprint" in production_data
            assert production_data["blueprint"]["strategy"] == "Education"
            assert production_data["variant_id"] == "video_bridge_test"
