"""Tests for Phase 10-01 Foundation: AnalysisReport contract + persistence columns.

These tests do NOT need a database connection — they cover the pure-Python
contract (AnalysisReport Pydantic model, the feature flag, and the schema
column presence on the SQLAlchemy declarative class). Migration-level tests
live separately in `tests/alembic/` once we add that directory.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.services.discovery.schemas import (
    AnalysisReport,
    AnalysisStatus,
    HookInsights,
    PacingInsights,
    SentimentInsights,
    StructureInsights,
    StyleInsights,
)


def _sample_report(**overrides) -> AnalysisReport:
    """Build a well-formed AnalysisReport for tests."""
    payload = {
        "candidate_id": "cand_abc123",
        "source_uri": "https://example.com/watch?v=xyz",
        "hook": HookInsights(
            first_3_seconds="Asks a provocative question",
            emotional_angle="curiosity",
            scroll_stopper=True,
        ),
        "pacing": PacingInsights(
            bpm=128, cuts_per_minute=12.0, recommended_duration_s=45
        ),
        "structure": StructureInsights(
            arc=["hook", "build", "payoff"],
            act_breaks=[3, 20],
            retention_curve=[1.0, 0.85, 0.7, 0.6, 0.55],
        ),
        "style": StyleInsights(
            recommended_style="educational",
            color_palette=["#0a0a0a", "#fafafa"],
            music_genre="lofi",
            motion_graphics=["zoom-pulse", "lower-third"],
        ),
        "sentiment": SentimentInsights(
            overall="positive",
            target_audience="creators aged 18-34",
            emotional_triggers=["curiosity", "validation"],
        ),
        "summary": "A punchy hook about AI productivity that uses rapid cuts.",
        "viral_score": 78.5,
        "confidence": 0.87,
    }
    payload.update(overrides)
    return AnalysisReport(**payload)


class TestAnalysisReportRoundtrip:
    def test_to_db_payload_is_json_serializable(self):
        report = _sample_report()
        db_payload = report.to_db_payload()

        # Top-level keys present
        assert db_payload["id"] == report.id
        assert db_payload["candidate_id"] == "cand_abc123"
        assert db_payload["source_uri"] == "https://example.com/watch?v=xyz"
        assert db_payload["status"] == "COMPLETED"
        assert db_payload["viral_score"] == 78.5
        assert db_payload["confidence"] == 0.87

        # Nested objects serialized
        assert db_payload["hook"]["first_3_seconds"] == "Asks a provocative question"
        assert db_payload["hook"]["scroll_stopper"] is True
        assert db_payload["pacing"]["bpm"] == 128
        assert db_payload["structure"]["arc"] == ["hook", "build", "payoff"]
        assert db_payload["style"]["recommended_style"] == "educational"

        # analyzed_at is ISO string (JSON-friendly)
        assert isinstance(db_payload["analyzed_at"], str)
        assert "T" in db_payload["analyzed_at"]  # ISO 8601 marker

    def test_from_db_payload_roundtrip_preserves_all_fields(self):
        original = _sample_report()
        rehydrated = AnalysisReport.from_db_payload(original.to_db_payload())

        assert rehydrated.id == original.id
        assert rehydrated.candidate_id == original.candidate_id
        assert rehydrated.source_uri == original.source_uri
        assert rehydrated.hook == original.hook
        assert rehydrated.pacing == original.pacing
        assert rehydrated.structure == original.structure
        assert rehydrated.style == original.style
        assert rehydrated.sentiment == original.sentiment
        assert rehydrated.summary == original.summary
        assert rehydrated.viral_score == original.viral_score
        assert rehydrated.confidence == original.confidence
        # Roundtrip via ISO string is exact to the millisecond
        assert rehydrated.analyzed_at == original.analyzed_at

    def test_recommended_style_hot_path(self):
        report = _sample_report()
        assert report.recommended_style() == "educational"

    def test_viral_score_velocity_uses_duration_factor(self):
        report = _sample_report()
        # viral_score 78.5 * confidence 0.87 * (60/45) = ~91
        velocity = report.viral_score_velocity()
        assert 85 < velocity < 100

    def test_retention_curve_is_clamped_to_unit_interval(self):
        # Out-of-range values are silently normalized (clamped) rather than
        # rejected — this is the intentional defensive behavior so a bad LLM
        # output doesn't crash the persisted report.
        s = StructureInsights(
            arc=["x"],
            act_breaks=[],
            retention_curve=[1.5, 0.5, -0.1, 0.0, 1.0],
        )
        assert s.retention_curve == [1.0, 0.5, 0.0, 0.0, 1.0]


class TestAnalysisReportValidation:
    def test_viral_score_above_100_rejected(self):
        with pytest.raises(ValidationError):
            _sample_report(viral_score=150.0)

    def test_viral_score_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _sample_report(viral_score=-0.1)

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _sample_report(confidence=1.5)

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _sample_report(confidence=-0.1)

    def test_empty_summary_rejected(self):
        with pytest.raises(ValidationError):
            _sample_report(summary="")

    def test_missing_required_hook_rejected(self):
        with pytest.raises(ValidationError):
            AnalysisReport(
                candidate_id="c1",
                source_uri="https://x",
                # no `hook` kwarg
                pacing=PacingInsights(bpm=100, cuts_per_minute=8, recommended_duration_s=30),
                structure=StructureInsights(),
                style=StyleInsights(recommended_style="x"),
                sentiment=SentimentInsights(overall="positive", target_audience="x"),
                summary="x",
                viral_score=50,
                confidence=0.5,
            )


class TestAnalysisStatusEnum:
    def test_all_four_states_present(self):
        assert {s.value for s in AnalysisStatus} == {
            "PENDING",
            "RUNNING",
            "COMPLETED",
            "FAILED",
        }

    def test_enum_is_string_serializable(self):
        # Used as the value stored in ContentCandidateDB.analysis_status
        assert AnalysisStatus.COMPLETED.value == "COMPLETED"
        assert AnalysisStatus.RUNNING.value == "RUNNING"


class TestPersistedAnalysisFlag:
    def test_default_is_false_for_safe_rollout(self):
        from src.api.config.settings import settings

        # Default must be False during 10-01 (Foundation); 10-02 will flip
        # this to True after the Celery-task rewrite is verified.
        assert settings.ENABLE_PERSISTED_ANALYSIS is False

    def test_flag_is_a_bool_not_a_string(self):
        from src.api.config.settings import Settings

        annotations = Settings.model_fields
        assert "ENABLE_PERSISTED_ANALYSIS" in annotations
        # pydantic-settings coerces env strings, so verify the type hint
        assert annotations["ENABLE_PERSISTED_ANALYSIS"].annotation is bool


class TestContentCandidateDBSchema:
    def test_new_persistence_columns_exist(self):
        from src.api.utils.models import ContentCandidateDB

        col_names = {c.name for c in ContentCandidateDB.__table__.columns}
        expected = {
            "analysis_task_id",
            "analysis_status",
            "analysis_payload",
            "analysis_persisted_at",
            "viral_score_velocity",
            "recommended_style",
        }
        missing = expected - col_names
        assert not missing, f"Missing columns: {missing}"

    def test_new_columns_are_nullable(self):
        from src.api.utils.models import ContentCandidateDB

        for col_name in (
            "analysis_task_id",
            "analysis_status",
            "analysis_payload",
            "analysis_persisted_at",
            "viral_score_velocity",
            "recommended_style",
        ):
            col = ContentCandidateDB.__table__.columns[col_name]
            assert col.nullable is True, f"{col_name} should be nullable"

    def test_legacy_analysis_columns_still_exist(self):
        """We added new columns WITHOUT removing the old ones; verify that."""
        from src.api.utils.models import ContentCandidateDB

        col_names = {c.name for c in ContentCandidateDB.__table__.columns}
        # Legacy columns from the original Phase 2 work — must still be there
        assert "analysis_results" in col_names
        assert "analyzed_at" in col_names
