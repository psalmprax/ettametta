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

Mapping from LLM output: `AnalysisReport.from_llm_output()` and the free
function `llm_output_to_analysis_report()` convert the narrow
`ViralPattern` returned by the deconstructor (or a richer LLM dict) into
a fully-populated `AnalysisReport`. See Phase 10-02.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from .models import ContentCandidate, ViralPattern


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

    # ── Hot-path accessors (used by the video job dispatcher in 10-04) ────

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

    # ── LLM-output mapping (Phase 10-02) ──────────────────────────────────

    @classmethod
    def from_llm_output(
        cls,
        pattern: "ViralPattern",
        candidate: "ContentCandidate",
        *,
        raw: dict[str, Any] | None = None,
    ) -> "AnalysisReport":
        """Map a (narrow) ViralPattern + ContentCandidate into an AnalysisReport.

        The deconstructor (`src/services/discovery/deconstructor.py`) returns a
        `ViralPattern` with only 5 fields: hook_score, retention_estimate,
        pacing_bpm, style_keywords, emotional_triggers. This mapper fills in
        the rest with sensible defaults so the persisted `AnalysisReport` is
        always self-contained.

        If `raw` is provided, any canonical keys it contains
        (``hook``, ``pacing``, ``structure``, ``style``, ``sentiment``,
        ``summary``, ``viral_score``, ``confidence``) **override** the
        derived values. This is the extension point for a richer LLM prompt
        that returns the full `AnalysisReport` shape directly.

        Field-level derivation rules (see ``_derive_from_pattern``):

        * ``hook.first_3_seconds``  ← first 3 style_keywords joined
        * ``hook.emotional_angle``  ← first emotional_trigger
        * ``hook.scroll_stopper``   ← hook_score >= 0.7
        * ``pacing.bpm``            ← pattern.pacing_bpm (default 120)
        * ``pacing.cuts_per_minute``← bpm / 12
        * ``pacing.recommended_duration_s`` ← clamped candidate.duration
        * ``structure.arc``         ← 3-act if retention >= 0.5, else 2-act
        * ``structure.act_breaks``  ← at 1/3 and 2/3 of duration
        * ``structure.retention_curve`` ← [1.0, 0.8, ret, 0.5]
        * ``style.recommended_style`` ← first style_keyword
        * ``style.motion_graphics``  ← style_keywords[1:5]
        * ``sentiment.overall``      ← "positive" if hook_score >= 0.5
        * ``sentiment.target_audience`` ← candidate.niche
        * ``sentiment.emotional_triggers`` ← pattern.emotional_triggers
        * ``summary``                ← candidate.title (truncated to 200)
        * ``viral_score``            ← round(hook_score * 100)
        * ``confidence``             ← 0.5 if pattern.id is a fallback
                                        ("os_pattern"), else 0.85
        """
        derived = cls._derive_from_pattern(pattern, candidate)

        # Apply raw overrides at the top-level scalar + nested-dict level.
        # A richer LLM prompt can return any of: summary, viral_score,
        # confidence, hook, pacing, structure, style, sentiment.
        if raw:
            for top_key in (
                "summary",
                "viral_score",
                "confidence",
                "hook",
                "pacing",
                "structure",
                "style",
                "sentiment",
            ):
                if top_key in raw and raw[top_key] is not None:
                    if top_key in ("summary",):
                        derived[top_key] = str(raw[top_key])[:1000]
                    elif top_key in ("viral_score", "confidence"):
                        # Let Pydantic validate the type & bounds.
                        derived[top_key] = raw[top_key]
                    else:
                        # Nested Pydantic model — merge so a partial override
                        # doesn't blow away the rest of the derived fields.
                        existing = dict(derived.get(top_key) or {})
                        incoming = dict(raw[top_key] or {})
                        existing.update(incoming)
                        derived[top_key] = existing

        report = cls.model_validate(derived)

        # Preserve the raw dict for debugging / future re-parsing.
        if raw is not None:
            report.raw_model_output = raw
        else:
            # Stash the pattern's own fields as the raw output.
            try:
                report.raw_model_output = (
                    pattern.model_dump() if hasattr(pattern, "model_dump") else pattern.dict()
                )
            except Exception:
                report.raw_model_output = None
        return report

    @staticmethod
    def _derive_from_pattern(
        pattern: "ViralPattern",
        candidate: "ContentCandidate",
    ) -> dict[str, Any]:
        """Pure-function helper that returns the dict ``from_llm_output``
        will feed to ``cls.model_validate``. No I/O, no Pydantic side effects.
        Exposed at module level as :func:`llm_output_to_analysis_report` too.
        """
        style_keywords = list(pattern.style_keywords or [])
        emotional_triggers = list(pattern.emotional_triggers or [])

        # Pacing
        bpm = int(pattern.pacing_bpm) if pattern.pacing_bpm is not None else 120
        bpm = max(0, min(bpm, 400))
        cuts_per_minute = round(bpm / 12.0, 2)
        # Clamp duration to 5..180 seconds (PacingInsights bounds).
        dur = int(candidate.duration_seconds) if candidate.duration_seconds else 30
        recommended_duration_s = max(5, min(dur, 180))

        # Structure — two shapes depending on retention
        if pattern.retention_estimate >= 0.5:
            arc = ["setup", "build", "payoff"]
        else:
            arc = ["hook", "payoff"]
        act_breaks = [
            recommended_duration_s // 3,
            recommended_duration_s * 2 // 3,
        ]
        retention_curve = [
            1.0,
            0.8,
            round(float(pattern.retention_estimate), 4),
            0.5,
        ]

        # Hook
        first_3 = " ".join(style_keywords[:3]).strip() or "Visual hook"
        emotional_angle = emotional_triggers[0] if emotional_triggers else "curiosity"
        scroll_stopper = bool(pattern.hook_score >= 0.7)

        # Style
        recommended_style = style_keywords[0] if style_keywords else "educational"
        motion_graphics = style_keywords[1:5]

        # Sentiment
        overall = "positive" if pattern.hook_score >= 0.5 else "neutral"
        target_audience = candidate.niche or "creators"
        # Pydantic will truncate to 20 entries; pre-clamp to avoid a warning.
        emotional_triggers_bounded = emotional_triggers[:20]

        # Score
        viral_score = float(round(pattern.hook_score * 100))
        viral_score = max(0.0, min(viral_score, 100.0))
        # Lower confidence for the open-source / fallback path so the UI
        # can show "low-confidence analysis" badges.
        is_fallback = isinstance(pattern.id, str) and (
            pattern.id.startswith("os_pattern")
            or pattern.id.startswith("fallback")
        )
        confidence = 0.5 if is_fallback else 0.85

        # Summary — prefer the candidate's title (Pydantic truncates to 1000).
        title = (candidate.title or "").strip()
        summary = title[:200] if title else "Viral pattern analysis"

        return {
            "candidate_id": candidate.id or "",
            "source_uri": candidate.source_uri or "",
            "hook": {
                "first_3_seconds": first_3[:500],
                "emotional_angle": emotional_angle[:100],
                "scroll_stopper": scroll_stopper,
            },
            "pacing": {
                "bpm": bpm,
                "cuts_per_minute": cuts_per_minute,
                "recommended_duration_s": recommended_duration_s,
            },
            "structure": {
                "arc": arc,
                "act_breaks": act_breaks,
                "retention_curve": retention_curve,
            },
            "style": {
                "recommended_style": recommended_style[:64] or "educational",
                "color_palette": [],
                "music_genre": None,
                "motion_graphics": motion_graphics,
            },
            "sentiment": {
                "overall": overall[:32],
                "target_audience": target_audience[:200] or "creators",
                "emotional_triggers": emotional_triggers_bounded,
            },
            "summary": summary[:1000],
            "viral_score": viral_score,
            "confidence": confidence,
        }

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"AnalysisReport(candidate={self.candidate_id!r}, "
            f"viral={self.viral_score:.0f}, confidence={self.confidence:.2f}, "
            f"hook={self.hook.first_3_seconds[:30]!r})"
        )


# Module-level convenience wrapper (symmetric with the rest of the codebase)
def llm_output_to_analysis_report(
    pattern: "ViralPattern",
    candidate: "ContentCandidate",
    *,
    raw: dict[str, Any] | None = None,
) -> AnalysisReport:
    """Free-function alias for :meth:`AnalysisReport.from_llm_output`.

    This exists so the Celery task in ``tasks.py`` can do::

        from .schemas import llm_output_to_analysis_report
        report = llm_output_to_analysis_report(pattern, candidate)

    without having to reach for the classmethod explicitly.
    """
    return AnalysisReport.from_llm_output(pattern, candidate, raw=raw)
