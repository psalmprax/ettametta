"""
PostHog Analytics & LLM Observability Service
Provides unified telemetry for video rendering, content discovery, and LLM inference costs.
"""

import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger("PostHogService")

try:
    import posthog
except ImportError:
    posthog = None


class PostHogAnalyticsService:
    """
    Unified telemetry service managing PostHog product events and LLM observability.
    """

    def __init__(self):
        self.api_key = os.getenv("POSTHOG_API_KEY", "")
        self.host = os.getenv("POSTHOG_SERVER_URL", "https://app.posthog.com")
        self.enabled = bool(self.api_key and posthog is not None)

        if self.enabled:
            try:
                posthog.api_key = self.api_key
                posthog.host = self.host
                posthog.disabled = False
            except Exception as e:
                logger.warning(f"Failed to initialize posthog SDK: {e}")
                self.enabled = False

    def capture(self, distinct_id: str, event_name: str, properties: Optional[dict[str, Any]] = None):
        """Send generic product event to PostHog"""
        if not self.enabled:
            return
        try:
            posthog.capture(
                distinct_id=distinct_id,
                event=event_name,
                properties=properties or {},
            )
        except Exception as e:
            logger.warning(f"Error capturing PostHog event '{event_name}': {e}")

    def track_llm_generation(
        self,
        distinct_id: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        cost_usd: float = 0.0,
        task_name: str = "script_generation",
        success: bool = True,
    ):
        """
        Track LLM token consumption, latency, and cost for observability.
        """
        total_tokens = prompt_tokens + completion_tokens
        properties = {
            "$ai_provider": provider,
            "$ai_model": model,
            "$ai_input_tokens": prompt_tokens,
            "$ai_output_tokens": completion_tokens,
            "$ai_total_tokens": total_tokens,
            "$ai_latency_ms": latency_ms,
            "$ai_cost_usd": cost_usd,
            "task_name": task_name,
            "success": success,
        }
        self.capture(
            distinct_id=distinct_id,
            event_name="$ai_generation",
            properties=properties,
        )

    def track_video_pipeline_step(
        self,
        distinct_id: str,
        step: str,
        job_id: str,
        status: str,
        duration_ms: float = 0.0,
        extra: Optional[dict[str, Any]] = None,
    ):
        """
        Track discrete video pipeline transitions (download -> transcribe -> compose -> render -> publish).
        """
        props = {
            "pipeline_step": step,
            "job_id": job_id,
            "status": status,
            "duration_ms": duration_ms,
            **(extra or {}),
        }
        self.capture(
            distinct_id=distinct_id,
            event_name="video_pipeline_step",
            properties=props,
        )


base_posthog_service = PostHogAnalyticsService()
