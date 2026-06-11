"""
Stable Pydantic contract for AI-generated analysis of a content candidate.

This is the persisted shape that flows through the Discovery → Analysis → Video
pipeline. Defined once, here, so that:
- The Celery task (10-02) writes a normalized payload to the DB.
- The status endpoint (10-03) returns the same shape.
- The video job dispatcher (10-04) can read the same fields without re-parsing
  whatever raw dict the LLM happened to produce.

The model deliberately does NOT inherit from ViralPattern — that is the internal
LLM deconstruction output, which is richer and unstable. AnalysisReport is the
public, persisted, UI-friendly contract.

Persistence: `AnalysisReport.to_db_payload()` returns a dict ready to store in
the `ContentCandidateDB.analysis_payload` JSONB column. Use
`AnalysisReport.from_db_payload()` to rehydrate. Both helpers exist so the
column shape is a one-line decision; everything else uses the Pydantic model.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class AnalysisStatus(str, Enum):
    """Lifecycle of a single analysis run for a content candidate."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class HookInsights(BaseModel):
    """First-3-seconds analysis: what stops the scroll."""

    first_3_seconds: str = Field(..., min_length=1, max_length=500)
    emotional_angle: str = Field(..., min_length=1, max_length=100)
    scroll_stopper: bool = False


class PacingInsights(BaseModel):
    """How fast the content moves."""

    bpm: int = Field(..., ge=0, le=400)
    cuts_per_minute: float = Field(..., ge=0.0, le=120.0)
    recommended_duration_s: int = Field(..., ge=1, le=600)


class StructureInsights(BaseModel):
    """Narrative arc and retention shape."""

    arc: list[str] = Field(default_factory=list, max_length=20)
    act_breaks: list[int] = Field(default_factory=list, max_length=20)
    retention_curve: list[float] = Field(default_factory=list, max_length=50)

    @field_validator("retention_curve")
    @classmethod
    def _clamp_curve(cls, v: list[float]) -> list[float]:
        # Retention is a 0..1 series; clamp any out-of-range values defensively.
        return [max(0.0, min(1.0, float(x))) for x in v]


class StyleInsights(BaseModel):
    """Visual / audio style recommendations for the recreated video."""

    recommended_style: str = Field(..., min_length=1, max_length=64)
    color_palette: list[str] = Field(default_factory=list, max_length=16)
    music_genre: str | None = Field(default=None, max_length=64)
    motion_graphics: list[str] = Field(default_factory=list, max_length=16)


class SentimentInsights(BaseModel):
    """Audience and emotional framing."""

    overall: str = Field(..., min_length=1, max_length=32)
    target_audience: str = Field(..., min_length=1, max_length=200)
    emotional_triggers: list[str] = Field(default_factory=list, max_length=20)


class AnalysisReport(BaseModel):
    """Public, persisted shape of an AI deconstruction of a content candidate.

    This is what the frontend renders, what the video job dispatcher reads, and
    what the status endpoint returns. It is intentionally narrower than the raw
    `ViralPattern` returned by the LLM — the raw pattern is kept in
    `raw_model_output` for debugging but the rest of the system only touches the
    well-typed fields below.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    candidate_id: str
    source_uri: str
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: AnalysisStatus = AnalysisStatus.COMPLETED

    hook: HookInsights
    pacing: PacingInsights
    structure: StructureInsights
    style: StyleInsights
    sentiment: SentimentInsights

    summary: str = Field(..., min_length=1, max_length=1000)
    viral_score: float = Field(..., ge=0.0, le=100.0)
    confidence: float = Field(..., ge=0.0, le=1.0)

    raw_model_output: dict[str, Any] | None = None

    # ── Persistence helpers ────────────────────────────────────────────────

    def to_db_payload(self) -> dict[str, Any]:
        """Serialize for `ContentCandidateDB.analysis_payload` (JSONB).

        Uses `model_dump(mode="json")` so datetimes/enums become strings, then
        adds the `id` and `analyzed_at` at the top level for fast lookups.
        """
        dumped = self.model_dump(mode="json")
        dumped["id"] = self.id
        dumped["analyzed_at"] = self.analyzed_at.isoformat()
        return dumped

    @classmethod
    def from_db_payload(cls, payload: dict[str, Any]) -> "AnalysisReport":
        """Rehydrate from the `ContentCandidateDB.analysis_payload` JSONB dict.

        Tolerant: missing optional fields fall back to Pydantic defaults.
        """
        if "analyzed_at" in payload and isinstance(payload["analyzed_at"], str):
            # Pydantic will accept the ISO string and re-parse; nothing to do.
            pass
        return cls.model_validate(payload)

    # ── Convenience ────────────────────────────────────────────────────────

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"AnalysisReport(candidate={self.candidate_id!r}, "
            f"viral={self.viral_score:.0f}, confidence={self.confidence:.2f}, "
            f"hook={self.hook.first_3_seconds[:30]!r})"
        )

    def recommended_style(self) -> str:
        """Hot-path accessor used by the video job dispatcher (10-04)."""
        return self.style.recommended_style

    def viral_score_velocity(self) -> float:
        """Estimate the 'viral velocity' used by the dashboard for sort ordering.

        Heuristic: viral_score × confidence × (60 / recommended_duration_s).
        Higher = more viral, more confident, shorter = trends faster.
        """
        duration_factor = 60.0 / max(self.pacing.recommended_duration_s, 1)
        return round(self.viral_score * self.confidence * duration_factor, 4)
