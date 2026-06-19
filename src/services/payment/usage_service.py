"""Usage-based billing — track API usage per user and calculate bills."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    API_REQUESTS = "api_requests"
    COMPUTE_MINUTES = "compute_minutes"
    STORAGE_MB = "storage_mb"
    VIDEO_GENERATIONS = "video_generations"
    AI_REQUESTS = "ai_requests"


@dataclass
class UsageEntry:
    user_id: str
    metric_type: MetricType
    quantity: float
    timestamp: datetime
    metadata: dict = field(default_factory=dict)


@dataclass
class UsageSummary:
    user_id: str
    period_start: datetime
    period_end: datetime
    metrics: dict[MetricType, float] = field(default_factory=dict)
    total_cost: float = 0.0


# Pricing per unit (in credits or dollars)
METRIC_PRICING: dict[MetricType, float] = {
    MetricType.API_REQUESTS: 0.001,
    MetricType.COMPUTE_MINUTES: 0.05,
    MetricType.STORAGE_MB: 0.01,
    MetricType.VIDEO_GENERATIONS: 1.0,
    MetricType.AI_REQUESTS: 0.02,
}


class UsageService:
    def __init__(self) -> None:
        self._usage_store: list[UsageEntry] = []

    def track_usage(
        self,
        user_id: str,
        metric_type: MetricType,
        quantity: float,
        metadata: Optional[dict] = None,
    ) -> UsageEntry:
        entry = UsageEntry(
            user_id=user_id,
            metric_type=metric_type,
            quantity=quantity,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        self._usage_store.append(entry)
        logger.debug(
            "Usage tracked: user=%s metric=%s qty=%.2f",
            user_id, metric_type.value, quantity,
        )
        return entry

    def get_usage_summary(
        self,
        user_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> UsageSummary:
        now = datetime.now(timezone.utc)
        if period_end is None:
            period_end = now
        if period_start is None:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        entries = [
            e for e in self._usage_store
            if e.user_id == user_id
            and period_start <= e.timestamp <= period_end
        ]

        metrics: dict[MetricType, float] = {}
        for entry in entries:
            metrics[entry.metric_type] = (
                metrics.get(entry.metric_type, 0) + entry.quantity
            )

        return UsageSummary(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            metrics=metrics,
            total_cost=self.calculate_bill(metrics),
        )

    def calculate_bill(self, metrics: dict[MetricType, float]) -> float:
        total = 0.0
        for metric_type, quantity in metrics.items():
            rate = METRIC_PRICING.get(metric_type, 0.0)
            total += quantity * rate
        return round(total, 4)

    def get_usage_for_period(
        self,
        user_id: str,
        metric_type: MetricType,
        days: int = 30,
    ) -> float:
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)
        return sum(
            e.quantity
            for e in self._usage_store
            if e.user_id == user_id
            and e.metric_type == metric_type
            and e.timestamp >= start
        )


base_usage_service = UsageService()
