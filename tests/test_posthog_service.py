import pytest
from unittest.mock import patch, MagicMock
from src.services.analytics.posthog_service import PostHogAnalyticsService


def test_posthog_service_capture():
    service = PostHogAnalyticsService()
    service.enabled = True

    with patch("src.services.analytics.posthog_service.posthog") as mock_ph:
        service.capture("user_123", "test_event", {"foo": "bar"})
        mock_ph.capture.assert_called_once_with(
            distinct_id="user_123",
            event="test_event",
            properties={"foo": "bar"},
        )


def test_posthog_service_track_llm():
    service = PostHogAnalyticsService()
    service.enabled = True

    with patch("src.services.analytics.posthog_service.posthog") as mock_ph:
        service.track_llm_generation(
            distinct_id="system",
            provider="groq",
            model="llama-3.3-70b-versatile",
            prompt_tokens=250,
            completion_tokens=120,
            latency_ms=450.0,
            cost_usd=0.00025,
            task_name="viral_script",
        )
        mock_ph.capture.assert_called_once()
        args, kwargs = mock_ph.capture.call_args
        assert kwargs["event"] == "$ai_generation"
        assert kwargs["properties"]["$ai_model"] == "llama-3.3-70b-versatile"
        assert kwargs["properties"]["$ai_total_tokens"] == 370
