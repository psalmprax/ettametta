"""Tests for Phase 10-01 Foundation: AnalysisReport contract + persistence columns.

These tests do NOT need a database connection — they cover the pure-Python
contract (AnalysisReport Pydantic model, the feature flag, and the schema
column presence on the SQLAlchemy declarative class). Migration-level tests
live separately in `tests/alembic/` once we add that directory.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.services.discovery.models import ContentCandidate, ViralPattern
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


# ─────────────────────────────────────────────────────────────────────────────
# Phase 10-02 tests: LLM-output mapper + Celery task rewrite
# ─────────────────────────────────────────────────────────────────────────────


def _candidate(**overrides) -> "ContentCandidate":
    """Build a minimal ContentCandidate for mapper tests."""
    from src.services.discovery.models import ContentCandidate

    payload = {
        "id": "cand_test_001",
        "platform": "youtube",
        "source_uri": "https://youtube.com/watch?v=abc123",
        "title": "The 3-step framework that went viral in 48 hours",
        "creator_name": "Test Creator",
        "duration_seconds": 45.0,
        "niche": "ai-productivity",
    }
    payload.update(overrides)
    return ContentCandidate(**payload)


def _viral_pattern(**overrides) -> "ViralPattern":
    """Build a minimal ViralPattern as the deconstructor would return."""
    from src.services.discovery.models import ViralPattern

    payload = {
        "id": "groq_cand_test_001",
        "hook_score": 0.82,
        "retention_estimate": 0.68,
        "pacing_bpm": 132,
        "style_keywords": ["educational", "zoom-pulse", "lower-third", "b-roll"],
        "emotional_triggers": ["curiosity", "validation"],
    }
    payload.update(overrides)
    return ViralPattern(**payload)


class TestFromLLMOutput:
    """``AnalysisReport.from_llm_output`` mapper behavior (Phase 10-02)."""

    def test_minimal_viralpattern_produces_valid_report(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        report = llm_output_to_analysis_report(_viral_pattern(), _candidate())
        assert report.candidate_id == "cand_test_001"
        assert report.source_uri == "https://youtube.com/watch?v=abc123"
        # Derived fields are populated and pass Pydantic validation
        assert report.hook.first_3_seconds
        assert report.hook.emotional_angle == "curiosity"
        assert report.hook.scroll_stopper is True  # 0.82 >= 0.7
        assert report.pacing.bpm == 132
        assert report.pacing.cuts_per_minute == round(132 / 12, 2)
        assert report.pacing.recommended_duration_s == 45
        assert report.structure.arc == ["setup", "build", "payoff"]  # retention >= 0.5
        assert report.structure.act_breaks == [15, 30]
        assert report.structure.retention_curve == [1.0, 0.8, 0.68, 0.5]
        assert report.style.recommended_style == "educational"
        assert report.style.motion_graphics == ["zoom-pulse", "lower-third", "b-roll"]
        assert report.sentiment.overall == "positive"  # hook_score >= 0.5
        assert report.sentiment.target_audience == "ai-productivity"
        assert report.sentiment.emotional_triggers == ["curiosity", "validation"]
        assert "3-step framework" in report.summary
        assert report.viral_score == 82.0
        assert report.confidence == 0.85  # not a fallback id

    def test_fills_defaults_for_empty_arrays(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        pattern = _viral_pattern(style_keywords=[], emotional_triggers=[])
        report = llm_output_to_analysis_report(pattern, _candidate(niche=None, title=None))
        # Defaults kick in
        assert report.hook.first_3_seconds == "Visual hook"
        assert report.hook.emotional_angle == "curiosity"
        assert report.style.recommended_style == "educational"
        assert report.style.motion_graphics == []
        assert report.sentiment.target_audience == "creators"
        assert report.summary == "Viral pattern analysis"

    def test_low_retention_yields_two_act_structure(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        pattern = _viral_pattern(retention_estimate=0.4)
        report = llm_output_to_analysis_report(pattern, _candidate())
        assert report.structure.arc == ["hook", "payoff"]
        assert report.sentiment.overall == "positive"  # hook_score still high

    def test_low_hook_score_yields_neutral_sentiment(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        pattern = _viral_pattern(hook_score=0.3)
        report = llm_output_to_analysis_report(pattern, _candidate())
        assert report.sentiment.overall == "neutral"
        assert report.hook.scroll_stopper is False
        assert report.viral_score == 30.0

    def test_fallback_pattern_id_lowers_confidence(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        pattern = _viral_pattern(id="os_pattern_fallback_xyz")
        report = llm_output_to_analysis_report(pattern, _candidate())
        assert report.confidence == 0.5

    def test_fallback_pattern_id_prefix_lowers_confidence(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        pattern = _viral_pattern(id="fallback_no_transcript")
        report = llm_output_to_analysis_report(pattern, _candidate())
        assert report.confidence == 0.5

    def test_pacing_bpm_defaulted_when_none(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        pattern = _viral_pattern(pacing_bpm=None)
        report = llm_output_to_analysis_report(pattern, _candidate())
        assert report.pacing.bpm == 120
        assert report.pacing.cuts_per_minute == 10.0

    def test_pacing_bpm_clamps_to_upper_bound(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        pattern = _viral_pattern(pacing_bpm=9999)
        report = llm_output_to_analysis_report(pattern, _candidate())
        assert report.pacing.bpm == 400  # PacingInsights bound

    def test_recommended_duration_clamped(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        # Too short
        report = llm_output_to_analysis_report(
            _viral_pattern(), _candidate(duration_seconds=1.0)
        )
        assert report.pacing.recommended_duration_s == 5  # clamped to 5

        # Too long
        report = llm_output_to_analysis_report(
            _viral_pattern(), _candidate(duration_seconds=1000.0)
        )
        assert report.pacing.recommended_duration_s == 180  # clamped to 180

        # Missing
        report = llm_output_to_analysis_report(
            _viral_pattern(), _candidate(duration_seconds=0.0)
        )
        assert report.pacing.recommended_duration_s == 30  # default

    def test_raw_dict_overrides_derived_scalar(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        report = llm_output_to_analysis_report(
            _viral_pattern(),
            _candidate(),
            raw={"summary": "Overridden by rich LLM prompt", "viral_score": 95.5},
        )
        assert report.summary == "Overridden by rich LLM prompt"
        assert report.viral_score == 95.5

    def test_raw_dict_overrides_derived_nested_model(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        report = llm_output_to_analysis_report(
            _viral_pattern(),
            _candidate(),
            raw={
                "style": {
                    "recommended_style": "cinematic-dark",
                    "color_palette": ["#000000", "#ff0066"],
                    "music_genre": "dark-ambient",
                }
            },
        )
        # style.recommended_style + color_palette + music_genre overridden;
        # motion_graphics keeps the derived value
        assert report.style.recommended_style == "cinematic-dark"
        assert report.style.color_palette == ["#000000", "#ff0066"]
        assert report.style.music_genre == "dark-ambient"
        assert report.style.motion_graphics == ["zoom-pulse", "lower-third", "b-roll"]

    def test_raw_model_output_is_stashed_for_debug(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        report = llm_output_to_analysis_report(
            _viral_pattern(),
            _candidate(),
            raw={"hook_score": 0.9, "llm_model": "llama-3.3-70b-versatile"},
        )
        assert report.raw_model_output is not None
        assert report.raw_model_output["llm_model"] == "llama-3.3-70b-versatile"
        assert report.raw_model_output["hook_score"] == 0.9

    def test_to_db_payload_roundtrips_through_from_db_payload(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        report = llm_output_to_analysis_report(_viral_pattern(), _candidate())
        rehydrated = AnalysisReport.from_db_payload(report.to_db_payload())
        assert rehydrated.id == report.id
        assert rehydrated.candidate_id == report.candidate_id
        assert rehydrated.viral_score == report.viral_score
        assert rehydrated.confidence == report.confidence
        assert rehydrated.style.recommended_style == report.style.recommended_style
        assert rehydrated.structure.arc == report.structure.arc

    def test_emotional_triggers_bounded_to_20(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        pattern = _viral_pattern(
            emotional_triggers=[f"trigger_{i}" for i in range(50)]
        )
        report = llm_output_to_analysis_report(pattern, _candidate())
        # Pydantic will accept up to 20 (max_length), so we expect 20 here.
        assert len(report.sentiment.emotional_triggers) == 20

    def test_summary_truncated_to_200_chars(self):
        from src.services.discovery.schemas import llm_output_to_analysis_report

        long_title = "x" * 500
        report = llm_output_to_analysis_report(
            _viral_pattern(), _candidate(title=long_title)
        )
        # _derive_from_pattern truncates to 200, then Pydantic max_length=1000
        # so the 200-char truncation is what we verify.
        assert len(report.summary) == 200


class TestAnalyzeViralPatternTaskGating:
    """``analyze_viral_pattern_task`` Celery task behavior (Phase 10-02)."""

    def _stub_deconstructor(self, monkeypatch, return_value=None):
        """Patch ``base_discovery_service.deep_analyze_viral_patterns`` with
        an async function that returns ``return_value`` (default: a fresh
        ``_viral_pattern()``).

        Note: when setattr-ing a function on an INSTANCE, Python binds it as
        a bound method, so ``self`` is implicit. The stub therefore takes
        only ``candidate``.
        """
        from src.services.discovery import tasks as _tasks

        if return_value is None:
            return_value = _viral_pattern()

        async def _fake(candidate):  # self is implicit when set on an instance
            return return_value

        monkeypatch.setattr(
            _tasks.base_discovery_service,
            "deep_analyze_viral_patterns",
            _fake,
        )

    def test_flag_off_does_not_open_db_session(self, monkeypatch):
        from src.services.discovery import tasks

        # Force flag off
        monkeypatch.setattr(tasks.settings, "ENABLE_PERSISTED_ANALYSIS", False)

        # Track if any DB session is opened
        opened = {"count": 0}

        def _no_session():
            opened["count"] += 1
            raise AssertionError("async_session_factory should not be called")

        # Patch on the tasks module
        monkeypatch.setattr(tasks, "async_session_factory", _no_session)
        self._stub_deconstructor(monkeypatch)

        cand = _candidate()
        task = tasks.analyze_viral_pattern_task
        task.push_request(id="task-test-001")
        try:
            result = task.run(cand.model_dump(mode="json"))
        finally:
            task.pop_request()

        assert result["status"] == "success"
        assert result["candidate_id"] == "cand_test_001"
        assert result["persisted"] is False
        assert "analysis" in result  # mapper ran
        assert opened["count"] == 0  # never opened a session

    def test_flag_on_persists_payload_to_db(self, monkeypatch):
        """With the flag on, the task must write a valid AnalysisReport
        to ContentCandidateDB.analysis_payload."""
        from src.services.discovery import tasks

        monkeypatch.setattr(tasks.settings, "ENABLE_PERSISTED_ANALYSIS", True)

        # Build a fake session that records writes
        class _Row:
            analysis_task_id = None
            analysis_status = None
            analysis_payload = None
            analysis_persisted_at = None
            viral_score_velocity = None
            recommended_style = None
            id = "cand_test_001"

        class _Result:
            def __init__(self, row):
                self._row = row

            def scalar_one_or_none(self):
                return self._row

        class _Session:
            def __init__(self, row):
                self._row = row
                self.committed = False

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def execute(self, stmt):
                return _Result(self._row)

            async def commit(self):
                self.committed = True

            async def rollback(self):
                pass

        # Capture the row that the task actually mutates
        row_holder = {"row": _Row(), "commit_called": False}

        def _factory():
            s = _Session(row_holder["row"])

            # Wrap commit to mark it for the test
            original_commit = s.commit

            async def _commit():
                await original_commit()
                row_holder["commit_called"] = True

            s.commit = _commit
            return s

        monkeypatch.setattr(tasks, "async_session_factory", _factory)
        self._stub_deconstructor(monkeypatch)

        cand = _candidate()
        task = tasks.analyze_viral_pattern_task
        task.push_request(id="task-persist-001")
        try:
            result = task.run(cand.model_dump(mode="json"))
        finally:
            task.pop_request()

        assert result["persisted"] is True
        assert result["analysis_task_id"] == "task-persist-001"
        # Row was mutated
        row = row_holder["row"]
        assert row.analysis_task_id == "task-persist-001"
        assert row.analysis_status == "COMPLETED"
        assert row.analysis_payload is not None
        assert row.analysis_payload["viral_score"] == 82.0
        assert row.analysis_payload["hook"]["scroll_stopper"] is True
        assert row.viral_score_velocity is not None
        assert row.recommended_style == "educational"
        assert row_holder["commit_called"] is True

    def test_flag_on_candidate_not_in_db_skips_persistence(self, monkeypatch):
        from src.services.discovery import tasks

        monkeypatch.setattr(tasks.settings, "ENABLE_PERSISTED_ANALYSIS", True)

        # Empty result
        class _Result:
            def scalar_one_or_none(self):
                return None

        class _Session:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def execute(self, stmt):
                return _Result()

            async def commit(self):
                pass

            async def rollback(self):
                pass

        monkeypatch.setattr(tasks, "async_session_factory", lambda: _Session())
        self._stub_deconstructor(monkeypatch)

        cand = _candidate()
        task = tasks.analyze_viral_pattern_task
        task.push_request(id="task-missing-cand-001")
        try:
            result = task.run(cand.model_dump(mode="json"))
        finally:
            task.pop_request()

        assert result["persisted"] is False
        assert result["status"] == "success"
        assert result["candidate_id"] == "cand_test_001"

    def test_missing_candidate_id_does_not_crash_persistence(self, monkeypatch):
        from src.services.discovery import tasks

        monkeypatch.setattr(tasks.settings, "ENABLE_PERSISTED_ANALYSIS", True)
        self._stub_deconstructor(monkeypatch)

        cand = _candidate(id="")  # missing
        task = tasks.analyze_viral_pattern_task
        task.push_request(id="task-no-id-001")
        try:
            result = task.run(cand.model_dump(mode="json"))
        finally:
            task.pop_request()

        assert result["persisted"] is False
        assert result["status"] == "success"

    def test_returned_dict_is_backward_compatible(self, monkeypatch):
        """Legacy callers (Celery AsyncResult checks) only depend on
        ``status``, ``candidate_id``, ``source_uri``, ``pattern`` — make
        sure those keys are still there."""
        from src.services.discovery import tasks

        monkeypatch.setattr(tasks.settings, "ENABLE_PERSISTED_ANALYSIS", False)
        self._stub_deconstructor(monkeypatch)

        cand = _candidate()
        task = tasks.analyze_viral_pattern_task
        task.push_request(id="task-compat-001")
        try:
            result = task.run(cand.model_dump(mode="json"))
        finally:
            task.pop_request()

        # Legacy keys
        assert result["status"] == "success"
        assert result["candidate_id"] == "cand_test_001"
        assert result["source_uri"] == "https://youtube.com/watch?v=abc123"
        assert "pattern" in result
        # New keys
        assert "persisted" in result
        assert "analysis" in result


# ─────────────────────────────────────────────────────────────────────────────
# Phase 10-03 tests: GET /api/v1/discovery/analysis/{content_id} read endpoint
# ─────────────────────────────────────────────────────────────────────────────


class _FakeContentCandidate:
    """Drop-in stand-in for ``ContentCandidateDB`` that exposes the 10-01
    persistence columns as plain attributes. The route only reads these
    five attributes, so we don't need a real SQLAlchemy model."""

    def __init__(
        self,
        content_id: str,
        *,
        analysis_payload=None,
        analysis_persisted_at=None,
        analyzed_at=None,
    ):
        self.id = content_id
        self.analysis_payload = analysis_payload
        self.analysis_persisted_at = analysis_persisted_at
        self.analyzed_at = analyzed_at


def _build_fake_session(content: _FakeContentCandidate | None):
    """Build a minimal AsyncSession-like object that returns ``content``
    from a ``select(ContentCandidateDB).filter(id=...)`` query."""

    class _ScalarResult:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

    class _FakeSession:
        async def execute(self, stmt):  # noqa: ARG002 - stmt ignored
            return _ScalarResult(content)

        async def commit(self):
            pass

        async def rollback(self):
            pass

    return _FakeSession()


def _override_dependencies(
    app, *, db_session, current_user=None
):  # noqa: ANN001
    """Override ``get_db`` and ``get_current_user`` on the FastAPI app with
    in-memory fakes so we can hit the endpoint without a real database or
    auth backend."""
    from src.api.utils.auth import get_current_user
    from src.api.utils.database import get_db
    from src.api.utils.user_models import UserDB

    if current_user is None:
        current_user = UserDB(
            id=1, email="test@example.com", subscription="free", is_active=True
        )

    async def _fake_db():
        yield db_session

    def _fake_user():
        return current_user

    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[get_current_user] = _fake_user


def _build_test_app():
    """Build a minimal FastAPI app that mounts the discovery router.
    Avoids importing ``src.api.main`` (which needs SECRET_KEY, Redis, etc.)
    by mounting only the router we want to test."""
    from fastapi import FastAPI

    from src.api.routes.discovery import router as discovery_router

    app = FastAPI()
    app.include_router(discovery_router, prefix="/api/v1")
    return app


class TestAnalysisReadEndpoint:
    """GET /api/v1/discovery/analysis/{content_id} read-side endpoint
    (Phase 10-03)."""

    def test_200_returns_persisted_report(self):
        from fastapi.testclient import TestClient


        report = _sample_report(candidate_id="cand_xyz789")
        payload = report.to_db_payload()

        content = _FakeContentCandidate(
            "cand_xyz789",
            analysis_payload=payload,
            analysis_persisted_at=__import__("datetime").datetime(
                2026, 5, 29, 12, 0, 0, tzinfo=__import__("datetime").timezone.utc
            ),
        )
        app = _build_test_app()
        _override_dependencies(app, db_session=_build_fake_session(content))

        client = TestClient(app)
        resp = client.get("/api/v1/discovery/analysis/cand_xyz789")

        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        data = body["data"]
        assert data["status"] == "COMPLETED"
        assert data["analysis"]["candidate_id"] == "cand_xyz789"
        assert data["analysis"]["viral_score"] == 78.5
        assert data["analysis"]["hook"]["scroll_stopper"] is True
        assert data["persisted_at"] is not None
        assert "2026-05-29" in data["persisted_at"]

    def test_404_when_content_row_missing(self):
        from fastapi.testclient import TestClient

        app = _build_test_app()
        _override_dependencies(
            app, db_session=_build_fake_session(content=None)
        )

        client = TestClient(app)
        resp = client.get("/api/v1/discovery/analysis/cand_does_not_exist")

        assert resp.status_code == 404
        assert "Content not found" in resp.json()["detail"]
        assert "cand_does_not_exist" in resp.json()["detail"]

    def test_404_when_payload_is_null(self):
        from fastapi.testclient import TestClient

        content = _FakeContentCandidate(
            "cand_unanalyzed", analysis_payload=None
        )
        app = _build_test_app()
        _override_dependencies(app, db_session=_build_fake_session(content))

        client = TestClient(app)
        resp = client.get("/api/v1/discovery/analysis/cand_unanalyzed")

        assert resp.status_code == 404
        assert "No analysis persisted" in resp.json()["detail"]
        assert "cand_unanalyzed" in resp.json()["detail"]

    def test_persisted_at_prefers_analysis_persisted_at(self):
        """When both columns are set, the 10-01 column wins (newer, more
        precise timestamp)."""
        import datetime

        from fastapi.testclient import TestClient


        report = _sample_report(candidate_id="cand_both_dates")
        newer = datetime.datetime(2026, 5, 29, 12, 0, 0, tzinfo=datetime.timezone.utc)
        older = datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        content = _FakeContentCandidate(
            "cand_both_dates",
            analysis_payload=report.to_db_payload(),
            analysis_persisted_at=newer,
            analyzed_at=older,
        )
        app = _build_test_app()
        _override_dependencies(app, db_session=_build_fake_session(content))

        client = TestClient(app)
        resp = client.get("/api/v1/discovery/analysis/cand_both_dates")
        assert resp.status_code == 200
        assert "2026-05-29" in resp.json()["data"]["persisted_at"]
        assert "2025-01-01" not in resp.json()["data"]["persisted_at"]

    def test_persisted_at_falls_back_to_analyzed_at(self):
        """Legacy rows written before 10-01 only have analyzed_at; the
        endpoint must still return a usable persisted_at."""
        import datetime

        from fastapi.testclient import TestClient


        report = _sample_report(candidate_id="cand_legacy")
        legacy = datetime.datetime(2025, 6, 15, 9, 30, 0, tzinfo=datetime.timezone.utc)
        content = _FakeContentCandidate(
            "cand_legacy",
            analysis_payload=report.to_db_payload(),
            analysis_persisted_at=None,
            analyzed_at=legacy,
        )
        app = _build_test_app()
        _override_dependencies(app, db_session=_build_fake_session(content))

        client = TestClient(app)
        resp = client.get("/api/v1/discovery/analysis/cand_legacy")
        assert resp.status_code == 200
        assert "2025-06-15" in resp.json()["data"]["persisted_at"]

    def test_corrupt_payload_returns_404_not_500(self):
        """A partially-written payload (e.g. interrupted Celery task) must
        surface as 404, not 500 — the UI should treat it as 'analyze again'."""
        from fastapi.testclient import TestClient

        # Missing required nested fields — Pydantic will reject.
        corrupt = {
            "candidate_id": "cand_corrupt",
            "source_uri": "https://example.com",
            # missing hook, pacing, structure, style, sentiment, summary,
            # viral_score, confidence
        }
        content = _FakeContentCandidate("cand_corrupt", analysis_payload=corrupt)
        app = _build_test_app()
        _override_dependencies(app, db_session=_build_fake_session(content))

        client = TestClient(app)
        resp = client.get("/api/v1/discovery/analysis/cand_corrupt")

        assert resp.status_code == 404
        assert "malformed" in resp.json()["detail"].lower()

    def test_persisted_at_is_null_when_both_columns_missing(self):
        from fastapi.testclient import TestClient


        report = _sample_report(candidate_id="cand_no_dates")
        content = _FakeContentCandidate(
            "cand_no_dates",
            analysis_payload=report.to_db_payload(),
            analysis_persisted_at=None,
            analyzed_at=None,
        )
        app = _build_test_app()
        _override_dependencies(app, db_session=_build_fake_session(content))

        client = TestClient(app)
        resp = client.get("/api/v1/discovery/analysis/cand_no_dates")
        assert resp.status_code == 200
        assert resp.json()["data"]["persisted_at"] is None


# ─────────────────────────────────────────────────────────────────────────────
# Phase 10-04 tests: analysis_data threading + analysis_snapshot in video jobs
# ─────────────────────────────────────────────────────────────────────────────


def _build_analysis_data_from_report(
    report: AnalysisReport,
) -> dict:
    """Build the ``analysis_data`` dict using the production helper.

    Delegates to ``src.api.routes.discovery._pack_analysis_data`` so the
    test always exercises the same code path as the endpoint itself.
    """
    from src.api.routes.discovery import _pack_analysis_data

    return _pack_analysis_data(report)


class TestAnalysisDataShape:
    """``analysis_data`` dict contract built from ``AnalysisReport``
    (Phase 10-04)."""

    def test_contains_both_pattern_and_analysis_report(self):
        report = _sample_report()
        data = _build_analysis_data_from_report(report)

        assert "pattern" in data
        assert "analysis_report" in data

    def test_pattern_has_legacy_shape_for_backward_compat(self):
        report = _sample_report()
        data = _build_analysis_data_from_report(report)

        pattern = data["pattern"]
        assert "hook_score" in pattern
        assert "retention_estimate" in pattern
        assert "pacing_bpm" in pattern
        assert "style_keywords" in pattern
        assert "emotional_triggers" in pattern

        # strategy_service reads these exact keys
        assert isinstance(pattern["hook_score"], (int, float))
        assert isinstance(pattern["retention_estimate"], (int, float))
        assert pattern["pacing_bpm"] == 128
        assert pattern["style_keywords"] == ["zoom-pulse", "lower-third"]
        assert pattern["emotional_triggers"] == ["curiosity", "validation"]

    def test_pattern_hook_score_is_08_when_scroll_stopper_true(self):
        report = _sample_report()  # scroll_stopper=True by default
        data = _build_analysis_data_from_report(report)
        assert data["pattern"]["hook_score"] == 0.8

    def test_pattern_hook_score_is_05_when_scroll_stopper_false(self):
        report = _sample_report(
            hook=HookInsights(
                first_3_seconds="slow intro",
                emotional_angle="calm",
                scroll_stopper=False,
            )
        )
        data = _build_analysis_data_from_report(report)
        assert data["pattern"]["hook_score"] == 0.5

    def test_analysis_report_contains_all_insight_groups(self):
        report = _sample_report()
        data = _build_analysis_data_from_report(report)

        ar = data["analysis_report"]
        assert "candidate_id" in ar
        assert "hook" in ar
        assert "pacing" in ar
        assert "structure" in ar
        assert "style" in ar
        assert "sentiment" in ar
        assert "summary" in ar
        assert "viral_score" in ar
        assert "confidence" in ar

    def test_analysis_report_hook_fields_match_report(self):
        report = _sample_report()
        data = _build_analysis_data_from_report(report)

        hook = data["analysis_report"]["hook"]
        assert hook["first_3_seconds"] == "Asks a provocative question"
        assert hook["emotional_angle"] == "curiosity"
        assert hook["scroll_stopper"] is True

    def test_analysis_report_pacing_fields_match_report(self):
        report = _sample_report()
        data = _build_analysis_data_from_report(report)

        pacing = data["analysis_report"]["pacing"]
        assert pacing["bpm"] == 128
        assert pacing["cuts_per_minute"] == 12.0
        assert pacing["recommended_duration_s"] == 45

    def test_analysis_report_structure_arc_is_preserved(self):
        report = _sample_report()
        data = _build_analysis_data_from_report(report)

        structure = data["analysis_report"]["structure"]
        assert structure["arc"] == ["hook", "build", "payoff"]
        assert structure["retention_curve"] == [1.0, 0.85, 0.7, 0.6, 0.55]

    def test_analysis_report_style_recommended_is_educational(self):
        report = _sample_report()
        data = _build_analysis_data_from_report(report)

        style = data["analysis_report"]["style"]
        assert style["recommended_style"] == "educational"

    def test_analysis_report_sentiment_overall_is_positive(self):
        report = _sample_report()
        data = _build_analysis_data_from_report(report)

        sentiment = data["analysis_report"]["sentiment"]
        assert sentiment["overall"] == "positive"

    def test_analysis_report_scores_are_numeric(self):
        report = _sample_report()
        data = _build_analysis_data_from_report(report)

        ar = data["analysis_report"]
        assert isinstance(ar["viral_score"], (int, float))
        assert isinstance(ar["confidence"], (int, float))
        assert 0 <= ar["viral_score"] <= 100
        assert 0 <= ar["confidence"] <= 1

    def test_retention_estimate_defaults_when_curve_too_short(self):
        report = _sample_report(
            structure=StructureInsights(
                arc=["hook"],
                act_breaks=[],
                retention_curve=[1.0],  # too short — no index 2
            )
        )
        data = _build_analysis_data_from_report(report)
        assert data["pattern"]["retention_estimate"] == 0.5


class TestAnalysisSnapshotContract:
    """``analysis_snapshot`` stored in ``VideoJobDB.job_metadata``
    (Phase 10-04)."""

    def test_snapshot_is_full_report_model_dump(self):
        """The snapshot stored in ``extra_metadata.analysis_snapshot``
        must be the full ``AnalysisReport.model_dump(mode="json")`` so
        that any downstream system (debug, audit, re-analyze) can
        reconstruct the exact report."""
        report = _sample_report(candidate_id="cand_snap_001")
        snapshot = report.model_dump(mode="json")

        # Verify the snapshot is a JSON-serializable dict
        assert isinstance(snapshot, dict)
        assert snapshot["candidate_id"] == "cand_snap_001"
        assert snapshot["viral_score"] == 78.5
        assert snapshot["confidence"] == 0.87

        # Verify all insight groups are present
        for key in ("hook", "pacing", "structure", "style", "sentiment"):
            assert key in snapshot, f"Missing {key} in snapshot"
            assert isinstance(snapshot[key], dict)

    def test_snapshot_is_json_serializable(self):
        """The snapshot must survive ``json.dumps`` so it can be stored
        in ``VideoJobDB.job_metadata`` (JSONB)."""
        import json

        report = _sample_report()
        snapshot = report.model_dump(mode="json")
        encoded = json.dumps(snapshot)
        decoded = json.loads(encoded)
        assert decoded["viral_score"] == 78.5

    def test_snapshot_roundtrips_back_to_report(self):
        """A snapshot can be rehydrated into an ``AnalysisReport`` via
        ``from_db_payload`` — useful for debugging and audit.

        ``model_dump(mode="json")`` already serializes ``analyzed_at``
        as an ISO string, so the raw dump is sufficient."""
        report = _sample_report()
        snapshot = report.model_dump(mode="json")
        rehydrated = AnalysisReport.from_db_payload(snapshot)
        assert rehydrated.candidate_id == report.candidate_id
        assert rehydrated.viral_score == report.viral_score
        assert rehydrated.hook.first_3_seconds == report.hook.first_3_seconds

    def test_snapshot_null_when_no_persisted_report(self):
        """When the DB row has no ``analysis_payload``, the ``_pack_analysis_data``
        call is never reached — the create-video endpoint falls back to
        ``analysis_data=None`` and ``analysis_snapshot=None``, preserving
        the pre-10-04 behavior.

        We verify this by confirming the GET endpoint returns 404 in this
        state (proxy: if the read endpoint can't find the report, neither
        can the create-video endpoint)."""
        from fastapi.testclient import TestClient

        content = _FakeContentCandidate(
            "cand_no_report",
            analysis_payload=None,
        )
        app = _build_test_app()
        _override_dependencies(app, db_session=_build_fake_session(content))

        client = TestClient(app)
        resp = client.get("/api/v1/discovery/analysis/cand_no_report")
        assert resp.status_code == 404
        assert "No analysis persisted" in resp.json()["detail"]

    def test_pack_analysis_data_returns_none_pattern_for_false_scroll_stopper(self):
        """Edge case: when scroll_stopper is False, pattern hook_score is 0.5,
        indicating to strategy_service that the hook is average, not strong."""
        report = _sample_report(
            hook=HookInsights(
                first_3_seconds="slow build-up intro",
                emotional_angle="neutral",
                scroll_stopper=False,
            )
        )
        data = _build_analysis_data_from_report(report)
        assert data["pattern"]["hook_score"] == 0.5
        assert data["analysis_report"]["hook"]["scroll_stopper"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Phase 10-06 tests: E2E smoke test — Discovery → Analysis → Video Job pipeline
# ─────────────────────────────────────────────────────────────────────────────


class _FakeVideoJobRecord:
    """Records what ``job_service.create_job`` received.

    The test inspects ``extra_metadata`` and ``analysis_snapshot``
    after the endpoint runs, without touching a real database."""

    def __init__(self):
        self.calls: list[dict] = []

    async def create_job(self, **kwargs):
        self.calls.append(kwargs)
        return None  # Return value unused by route


class _FakeCeleryTask:
    """Records ``download_and_process_task.delay()`` kwargs."""

    def __init__(self):
        self.calls: list[dict] = []

    def delay(self, **kwargs):
        self.calls.append(kwargs)
        return self  # must have .id

    @property
    def id(self):
        return "celery-task-e2e-001"


def _build_e2e_test_app(
    *,
    content: _FakeContentCandidate | None,
) -> tuple:
    """Build a test app with all mocks needed for the E2E smoke test.

    Returns ``(app, fake_job_service, fake_celery_task, patches)`` where
    ``patches`` is a dict of ``unittest.mock.patch`` instances that the
    caller must stop after the test.
    """
    from unittest.mock import patch

    from fastapi import FastAPI

    from src.api.routes.discovery import router as discovery_router

    app = FastAPI()
    app.include_router(discovery_router, prefix="/api/v1")

    # ── Override dependencies ──────────────────────────────────────
    from src.api.utils.auth import get_current_user
    from src.api.utils.database import get_db
    from src.api.utils.user_models import UserDB
    from src.services.payment.credit_service import credit_service

    current_user = UserDB(
        id=1, email="test@example.com", subscription="free", is_active=True
    )

    db_session = _build_fake_session(content)

    async def _fake_db():
        yield db_session

    def _fake_user():
        return current_user

    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[get_current_user] = _fake_user

    # ── Mock credits ───────────────────────────────────────────────
    async def _fake_consume(*a, **kw):
        return True, "ok"

    async def _fake_has_credits(*a, **kw):
        return True

    credit_consume_patch = patch.object(
        credit_service, "consume_credits",
        side_effect=_fake_consume,
    )
    credit_balance_patch = patch.object(
        credit_service, "has_sufficient_credits",
        side_effect=_fake_has_credits,
    )
    credit_consume_patch.start()
    credit_balance_patch.start()

    # ── Mock Celery AsyncResult (task status check) ────────────────
    class _FakeAsyncResult:
        def __init__(self, task_id):
            self.id = task_id

        def ready(self):
            return True

        def successful(self):
            return True

        @property
        def result(self):
            return {
                "status": "success",
                "candidate_id": content.id if content else "cand_unknown",
                "source_uri": "https://example.com/watch?v=abc",
                "pattern": {"hook_score": 0.8},
            }

    # Patch celery_app.AsyncResult globally so that when the discovery
    # route does ``from src.api.utils.celery import celery_app``,
    # ``celery_app.AsyncResult(task_id)`` returns our fake.
    celery_patch = patch(
        "src.api.utils.celery.celery_app.AsyncResult",
        side_effect=_FakeAsyncResult,
    )
    celery_patch.start()

    # ── Mock the Celery task itself ────────────────────────────────
    # The discovery route does a LOCAL import inside the handler:
    #   from src.services.video_engine.tasks import download_and_process_task
    #   task = download_and_process_task.delay(...)
    # We must patch the source module BEFORE the handler runs so our
    # fake_task is what gets imported.
    fake_celery = _FakeCeleryTask()
    task_patch = patch(
        "src.services.video_engine.tasks.download_and_process_task",
        new=fake_celery,
    )
    task_patch.start()

    # ── Mock VideoJobService ───────────────────────────────────────
    fake_job_service = _FakeVideoJobRecord()

    patches = {"celery_app": celery_patch, "celery_task": task_patch, "credits_consume": credit_consume_patch, "credits_balance": credit_balance_patch}

    return app, fake_job_service, fake_celery, patches


class TestAnalysisToVideoE2E:
    """End-to-end smoke test: Discovery → Analysis → Video Job
    (Phase 10-06).

    Verifies that when ``create_video_from_analysis`` is called, the full
    pipeline threads the AnalysisReport into the video job correctly,
    and the ``analysis_snapshot`` is stored in ``extra_metadata``.
    """

    def test_snapshot_attached_e2e(self):
        """Full mock pipeline: AnalysisReport in DB → Celery dispatch
        with analysis_data → job record with analysis_snapshot."""
        import datetime

        from fastapi.testclient import TestClient

        # 1. Build a persisted AnalysisReport
        report = _sample_report(candidate_id="cand_e2e_001")
        payload = report.to_db_payload()

        persited_at = datetime.datetime(
            2026, 6, 12, 10, 0, 0, tzinfo=datetime.timezone.utc
        )

        content = _FakeContentCandidate(
            "cand_e2e_001",
            analysis_payload=payload,
            analysis_persisted_at=persited_at,
        )

        app, fake_job_service, fake_celery, patches = _build_e2e_test_app(
            content=content,
        )

        # Override the job_service dependency on the app
        from src.services.video_engine.job_service import get_video_job_service

        app.dependency_overrides[get_video_job_service] = lambda: fake_job_service

        try:
            client = TestClient(app)
            resp = client.post(
                "/api/v1/discovery/analyze/celery-task-e2e-001/create-video",
                json={
                    "task_id": "celery-task-e2e-001",
                    "niche": "Motivation",
                    "platform": "YouTube Shorts",
                    "style": "Default",
                    "quality_tier": "standard",
                    "content_id": "cand_e2e_001",
                },
            )

            # 2. Assert HTTP 200
            assert resp.status_code == 200, (
                f"Expected 200, got {resp.status_code}: {resp.text}"
            )
            body = resp.json()
            assert body["data"]["status"] == "PROCESSING"
            assert body["data"]["task_id"] == "celery-task-e2e-001"

            # 3. Assert Celery task received analysis_data
            assert len(fake_celery.calls) == 1, (
                f"Expected 1 Celery dispatch, got {len(fake_celery.calls)}"
            )
            celery_kwargs = fake_celery.calls[0]
            assert celery_kwargs["source_uri"] == "https://example.com/watch?v=abc"
            assert celery_kwargs["analysis_data"] is not None

            analysis_data = celery_kwargs["analysis_data"]
            assert "pattern" in analysis_data
            assert "analysis_report" in analysis_data
            assert analysis_data["analysis_report"]["candidate_id"] == "cand_e2e_001"

            # 4. Assert job_service.create_job was called with analysis_snapshot
            assert len(fake_job_service.calls) == 1, (
                f"Expected 1 create_job call, got {len(fake_job_service.calls)}"
            )
            job_kwargs = fake_job_service.calls[0]
            extra_metadata = job_kwargs.get("extra_metadata", {})
            assert extra_metadata.get("analysis_task_id") == "celery-task-e2e-001"

            snapshot = extra_metadata.get("analysis_snapshot")
            assert snapshot is not None, (
                "analysis_snapshot must be present in extra_metadata"
            )
            assert isinstance(snapshot, dict)
            assert snapshot["candidate_id"] == "cand_e2e_001"
            assert snapshot["viral_score"] == 78.5
            assert snapshot["confidence"] == 0.87
            assert "hook" in snapshot
            assert "pacing" in snapshot
            assert "structure" in snapshot
            assert "style" in snapshot
            assert "sentiment" in snapshot
        finally:
            for p in patches.values():
                p.stop()

    def test_snapshot_roundtrips_back_to_report_from_job_metadata(self):
        """The analysis_snapshot in job_metadata must survive
        json.dumps/json.loads and rehydrate via from_db_payload — this
        is the contract that audit/debug/re-analyze systems depend on."""
        import json

        from fastapi.testclient import TestClient

        report = _sample_report(candidate_id="cand_roundtrip_002")
        content = _FakeContentCandidate(
            "cand_roundtrip_002",
            analysis_payload=report.to_db_payload(),
        )

        app, fake_job_service, fake_celery, patches = _build_e2e_test_app(
            content=content,
        )

        from src.services.video_engine.job_service import get_video_job_service

        app.dependency_overrides[get_video_job_service] = lambda: fake_job_service

        try:
            client = TestClient(app)
            resp = client.post(
                "/api/v1/discovery/analyze/celery-task-roundtrip-002/create-video",
                json={
                    "task_id": "celery-task-roundtrip-002",
                    "niche": "AI",
                    "platform": "TikTok",
                    "style": "cinematic",
                    "content_id": "cand_roundtrip_002",
                },
            )

            assert resp.status_code == 200
            assert len(fake_job_service.calls) == 1

            snapshot = fake_job_service.calls[0]["extra_metadata"]["analysis_snapshot"]
        finally:
            for p in patches.values():
                p.stop()

        # Simulate what happens when the JSONB column survives a roundtrip
        encoded = json.dumps(snapshot)
        decoded = json.loads(encoded)

        rehydrated = AnalysisReport.from_db_payload(decoded)
        assert rehydrated.candidate_id == "cand_roundtrip_002"
        assert rehydrated.viral_score == report.viral_score
        assert rehydrated.hook.first_3_seconds == report.hook.first_3_seconds
        assert rehydrated.hook.scroll_stopper == report.hook.scroll_stopper
        assert rehydrated.pacing.bpm == report.pacing.bpm
        assert rehydrated.style.recommended_style == report.style.recommended_style
        assert rehydrated.sentiment.overall == report.sentiment.overall

    def test_celery_fallback_when_no_persisted_report(self):
        """When the DB row exists but has no analysis_payload (legacy
        Celery-only path), the endpoint must still dispatch the task
        but with analysis_data=None and analysis_snapshot=None."""
        from fastapi.testclient import TestClient

        # Content row exists, but no analysis_payload
        content = _FakeContentCandidate(
            "cand_no_payload_003",
            analysis_payload=None,
        )

        app, fake_job_service, fake_celery, patches = _build_e2e_test_app(
            content=content,
        )

        from src.services.video_engine.job_service import get_video_job_service

        app.dependency_overrides[get_video_job_service] = lambda: fake_job_service

        try:
            client = TestClient(app)
            resp = client.post(
                "/api/v1/discovery/analyze/celery-task-fallback-003/create-video",
                json={
                    "task_id": "celery-task-fallback-003",
                    "niche": "Motivation",
                    "platform": "YouTube Shorts",
                },
            )

            # The endpoint should still succeed (backward-compatible Celery path)
            assert resp.status_code == 200
            assert len(fake_celery.calls) == 1
            assert fake_celery.calls[0]["analysis_data"] is None

            # analysis_snapshot must be None in extra_metadata
            assert len(fake_job_service.calls) == 1
            extra = fake_job_service.calls[0]["extra_metadata"]
            assert extra["analysis_snapshot"] is None
        finally:
            for p in patches.values():
                p.stop()

    def test_all_insight_groups_present_in_snapshot(self):
        """The analysis_snapshot must contain all 5 insight groups
        (hook, pacing, structure, style, sentiment) plus summary and scores."""
        from fastapi.testclient import TestClient

        report = _sample_report(candidate_id="cand_groups_004")
        content = _FakeContentCandidate(
            "cand_groups_004",
            analysis_payload=report.to_db_payload(),
        )

        app, fake_job_service, fake_celery, patches = _build_e2e_test_app(
            content=content,
        )

        from src.services.video_engine.job_service import get_video_job_service

        app.dependency_overrides[get_video_job_service] = lambda: fake_job_service

        try:
            client = TestClient(app)
            resp = client.post(
                "/api/v1/discovery/analyze/celery-task-groups-004/create-video",
                json={
                    "task_id": "celery-task-groups-004",
                    "niche": "Fitness",
                    "platform": "YouTube Shorts",
                    "content_id": "cand_groups_004",
                },
            )

            assert resp.status_code == 200

            snapshot = fake_job_service.calls[0]["extra_metadata"]["analysis_snapshot"]
        finally:
            for p in patches.values():
                p.stop()

        # All 5 insight groups present
        for key in ("hook", "pacing", "structure", "style", "sentiment"):
            assert key in snapshot, f"Missing insight group: {key}"
            assert isinstance(snapshot[key], dict), (
                f"{key} should be a dict, got {type(snapshot[key])}"
            )

        # Scalars present
        assert "summary" in snapshot
        assert "viral_score" in snapshot
        assert "confidence" in snapshot
        assert "candidate_id" in snapshot
        assert "source_uri" in snapshot

    def test_content_id_overrides_candidate_id_resolution(self):
        """When ``content_id`` is explicitly provided in the request body
        (10-05), it is used to look up the AnalysisReport even when the
        Celery result's ``candidate_id`` differs.

        This guards against a regression where the create-video endpoint
        fails to thread the persisted report when the frontend sends
        a content_id from the read-side endpoint."""
        from fastapi.testclient import TestClient

        report = _sample_report(candidate_id="cand_explicit_005")
        content = _FakeContentCandidate(
            "cand_explicit_005",
            analysis_payload=report.to_db_payload(),
        )

        app, fake_job_service, fake_celery, patches = _build_e2e_test_app(
            content=content,
        )

        from src.services.video_engine.job_service import get_video_job_service

        app.dependency_overrides[get_video_job_service] = lambda: fake_job_service

        try:
            client = TestClient(app)
            resp = client.post(
                "/api/v1/discovery/analyze/celery-task-override-005/create-video",
                json={
                    "task_id": "celery-task-override-005",
                    "niche": "Gaming",
                    "platform": "TikTok",
                    "content_id": "cand_explicit_005",
                },
            )

            assert resp.status_code == 200
            assert len(fake_celery.calls) == 1

            analysis_data = fake_celery.calls[0]["analysis_data"]
            assert analysis_data is not None
            # The analysis_report.candidate_id matches the content_id, not
            # whatever the Celery result's candidate_id field says.
            assert analysis_data["analysis_report"]["candidate_id"] == "cand_explicit_005"
        finally:
            for p in patches.values():
                p.stop()
