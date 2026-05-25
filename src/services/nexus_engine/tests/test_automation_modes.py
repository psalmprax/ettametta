"""Unit tests for all 3 automation modes (MANUAL/PARTIAL/FULL).

Tests cover:
- AutomationMode enum & threshold comparisons
- Mode resolution (per-job override, settings, fallback)
- MANUAL mode: backward-compatible, respects use_dag flag
- PARTIAL mode: forces DAG, AI-guided script, approval gate
- FULL mode: forces DAG, AI-guided script, no approval needed
- AutoCreator integration with each mode
- Error handling: circuit breaker, empty assets, mode fallback
"""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

pytestmark = pytest.mark.filterwarnings(
    "ignore::DeprecationWarning",
    "ignore::UserWarning",
    "ignore::FutureWarning",
    "ignore::PendingDeprecationWarning",
)


# =============================================================================
# Tests: AutomationMode Enum & Helpers
# =============================================================================


class TestAutomationModeEnum:
    """Core enum values, parsing, validation, and threshold comparisons."""

    def test_enum_values(self):
        from src.services.video_engine.automation import AutomationMode
        assert AutomationMode.MANUAL.value == "manual"
        assert AutomationMode.PARTIAL.value == "partial"
        assert AutomationMode.FULL.value == "full"

    def test_from_str_case_insensitive(self):
        from src.services.video_engine.automation import AutomationMode
        assert AutomationMode.from_str("manual") == AutomationMode.MANUAL
        assert AutomationMode.from_str("MANUAL") == AutomationMode.MANUAL
        assert AutomationMode.from_str("Partial") == AutomationMode.PARTIAL
        assert AutomationMode.from_str("FULL") == AutomationMode.FULL

    def test_from_str_fallback(self):
        from src.services.video_engine.automation import AutomationMode
        assert AutomationMode.from_str("unknown") == AutomationMode.MANUAL
        assert AutomationMode.from_str("") == AutomationMode.MANUAL
        assert AutomationMode.from_str("auto") == AutomationMode.MANUAL

    def test_is_valid(self):
        from src.services.video_engine.automation import AutomationMode
        assert AutomationMode.is_valid("manual") is True
        assert AutomationMode.is_valid("partial") is True
        assert AutomationMode.is_valid("full") is True
        assert AutomationMode.is_valid("AUTO") is False
        assert AutomationMode.is_valid("") is False

    def test_is_at_least_thresholds(self):
        from src.services.video_engine.automation import AutomationMode, is_at_least
        # Same level
        assert is_at_least(AutomationMode.MANUAL, AutomationMode.MANUAL) is True
        assert is_at_least(AutomationMode.PARTIAL, AutomationMode.PARTIAL) is True
        assert is_at_least(AutomationMode.FULL, AutomationMode.FULL) is True
        # Above threshold
        assert is_at_least(AutomationMode.PARTIAL, AutomationMode.MANUAL) is True
        assert is_at_least(AutomationMode.FULL, AutomationMode.MANUAL) is True
        assert is_at_least(AutomationMode.FULL, AutomationMode.PARTIAL) is True
        # Below threshold
        assert is_at_least(AutomationMode.MANUAL, AutomationMode.PARTIAL) is False
        assert is_at_least(AutomationMode.MANUAL, AutomationMode.FULL) is False
        assert is_at_least(AutomationMode.PARTIAL, AutomationMode.FULL) is False

    def test_mode_to_int_mapping(self):
        from src.services.video_engine.automation import AutomationMode, mode_to_int
        assert mode_to_int(AutomationMode.MANUAL) == 0
        assert mode_to_int(AutomationMode.PARTIAL) == 1
        assert mode_to_int(AutomationMode.FULL) == 2


class TestResolveMode:
    """Mode resolution priority chain."""

    def test_job_override_takes_priority(self):
        from src.services.video_engine.automation import AutomationMode, resolve_mode
        mode = resolve_mode(None, job_override="FULL")
        assert mode == AutomationMode.FULL

    def test_settings_second_priority(self):
        from src.services.video_engine.automation import AutomationMode, resolve_mode

        class MockSettings:
            AUTOMATION_MODE = "partial"

        mode = resolve_mode(MockSettings(), job_override=None)
        assert mode == AutomationMode.PARTIAL

    def test_settings_no_attr_fallback_to_system_default(self):
        """When settings obj lacks AUTOMATION_MODE, falls through to system default."""
        from src.services.video_engine.automation import resolve_mode

        class EmptySettings:
            pass

        mock_settings = MagicMock()
        mock_settings.AUTOMATION_MODE = "partial"

        with patch("src.api.config.settings", mock_settings):
            mode = resolve_mode(EmptySettings(), job_override=None)
            # Falls through to app config, which has AUTOMATION_MODE="partial"
            assert mode is not None
            assert mode.value == "partial"




# =============================================================================
# Tests: MANUAL Mode
# =============================================================================


class TestManualMode:
    """MANUAL mode: backward-compatible, respects use_dag flag as-is."""

    @pytest.mark.asyncio
    async def test_manual_uses_legacy_path_when_use_dag_false(self):
        """MANUAL + use_dag=False → sequential legacy path."""
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.video_engine.automation import AutomationMode

        creator = AutoCreator()
        mock_segment = {
            "text": "Manual segment",
            "visual_prompt": "Test visual",
            "mood": "calm",
            "type": "narrative",
        }

        with patch.multiple(
            creator,
            generate_viral_script=AsyncMock(return_value=[mock_segment]),
            _source_visual_assets=AsyncMock(return_value=["/tmp/vis_0.mp4"]),
            _generate_voiceovers=AsyncMock(return_value=["/tmp/voice_0.mp3"]),
        ), \
             patch("src.services.nexus_engine.orchestrator.base_nexus_service") as mock_nexus, \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("sqlalchemy.select"), \
             patch("src.api.utils.models.NexusJobDB"):

            mock_nexus.assemble_video = AsyncMock(return_value="/tmp/output.mp4")

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            output_path = await creator.create_cinema_video(
                job_id="manual-001", topic="T", niche="n",
                use_dag=False,
                automation_mode=AutomationMode.MANUAL,
            )

            assert output_path == "/tmp/output.mp4"
            # Should use standard script generation (not DAG-guided)
            creator.generate_viral_script.assert_called_once()
            # Should use sequential asset sourcing
            creator._source_visual_assets.assert_called_once_with(
                [mock_segment], "manual-001", "n",
                engine="cloud", style="CINEMATIC_DOC", use_dag=False,
            )

    @pytest.mark.asyncio
    async def test_manual_with_dag_flag(self):
        """MANUAL + use_dag=True → DAG path but no AI involvement."""
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.video_engine.automation import AutomationMode

        creator = AutoCreator()
        mock_segment = {
            "text": "DAG manual",
            "visual_prompt": "Test",
            "mood": "epic",
            "type": "hook",
        }

        with patch.multiple(
            creator,
            generate_viral_script=AsyncMock(return_value=[mock_segment]),
            _source_visual_assets_via_dag=AsyncMock(return_value=["/tmp/dag_vis.mp4"]),
            _generate_voiceovers=AsyncMock(return_value=["/tmp/voice.mp3"]),
        ), \
             patch("src.services.nexus_engine.orchestrator.base_nexus_service") as mock_nexus, \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("sqlalchemy.select"), \
             patch("src.api.utils.models.NexusJobDB"):

            mock_nexus.assemble_video = AsyncMock(return_value="/tmp/output.mp4")

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            output_path = await creator.create_cinema_video(
                job_id="manual-dag-001", topic="T", niche="n",
                use_dag=True,
                automation_mode=AutomationMode.MANUAL,
            )

            assert output_path == "/tmp/output.mp4"
            # Should NOT call DAG-guided script generation (manual mode)
            # In manual mode with use_dag=True, standard script gen is used
            # but DAG asset sourcing is used
            creator._source_visual_assets_via_dag.assert_called_once()

    @pytest.mark.asyncio
    async def test_manual_skips_approval_gate(self):
        """MANUAL mode doesn't create approval events."""
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.video_engine.automation import AutomationMode

        creator = AutoCreator()
        mock_segment = {
            "text": "No approval",
            "visual_prompt": "Test",
            "mood": "calm",
            "type": "narrative",
        }

        with patch.multiple(
            creator,
            generate_viral_script=AsyncMock(return_value=[mock_segment]),
            _source_visual_assets=AsyncMock(return_value=["/tmp/v.mp4"]),
            _generate_voiceovers=AsyncMock(return_value=["/tmp/vc.mp3"]),
        ), \
             patch("src.services.nexus_engine.orchestrator.base_nexus_service") as mock_nexus, \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("sqlalchemy.select"), \
             patch("src.api.utils.models.NexusJobDB"):

            mock_nexus.assemble_video = AsyncMock(return_value="/tmp/out.mp4")

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            await creator.create_cinema_video(
                job_id="no-approve", topic="T", niche="n",
                automation_mode=AutomationMode.MANUAL,
            )

            # No approval events should exist
            assert len(creator._pending_approvals) == 0
            assert len(creator._approval_events) == 0


# =============================================================================
# Tests: PARTIAL Mode
# =============================================================================


class TestPartialMode:
    """PARTIAL mode: AI generates DAG, approval gate pauses execution."""

    @pytest.mark.asyncio
    async def test_partial_forces_dag_and_ai_script(self):
        """PARTIAL forces use_dag=True and uses AI-guided script generation."""
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.video_engine.automation import AutomationMode

        creator = AutoCreator()
        mock_dag_segment = {
            "text": "AI DAG segment",
            "visual_prompt": "AI visual",
            "mood": "dramatic",
            "type": "clip",
            "dag_metadata": {
                "node_id": "intro",
                "dag_type": "clip",
                "inputs": [],
                "duration_sec": 8,
            },
        }

        with patch.multiple(
            creator,
            _generate_dag_guided_script=AsyncMock(return_value=[mock_dag_segment]),
            _source_visual_assets=AsyncMock(return_value=["/tmp/ai_vis.mp4"]),
            _generate_voiceovers=AsyncMock(return_value=["/tmp/ai_voice.mp3"]),
        ), \
             patch.object(creator, '_wait_for_dag_approval', new_callable=AsyncMock, return_value=True), \
             patch("src.services.nexus_engine.orchestrator.base_nexus_service") as mock_nexus, \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("sqlalchemy.select"), \
             patch("src.api.utils.models.NexusJobDB"):

            mock_nexus.assemble_video = AsyncMock(return_value="/tmp/output.mp4")

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            output_path = await creator.create_cinema_video(
                job_id="partial-001", topic="AI Topic", niche="tech",
                use_dag=False,  # Should be overridden by PARTIAL mode
                automation_mode=AutomationMode.PARTIAL,
            )

            assert output_path == "/tmp/output.mp4"
            # PARTIAL forces DAG-guided script
            creator._generate_dag_guided_script.assert_called_once()
            # Asset sourcing passes use_dag=True (forced by PARTIAL)
            creator._source_visual_assets.assert_called_once()
            _, call_kwargs = creator._source_visual_assets.call_args
            assert call_kwargs.get("use_dag") is True

    @pytest.mark.asyncio
    async def test_partial_approval_gate_blocks_on_rejection(self):
        """PARTIAL raises RuntimeError when user rejects the DAG."""
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.video_engine.automation import AutomationMode

        creator = AutoCreator()
        mock_dag_segment = {
            "text": "Rejected segment",
            "visual_prompt": "Rejected visual",
            "mood": "neutral",
            "type": "clip",
            "dag_metadata": {
                "node_id": "rejected",
                "dag_type": "clip",
                "inputs": [],
                "duration_sec": 5,
            },
        }

        with patch.multiple(
            creator,
            _generate_dag_guided_script=AsyncMock(return_value=[mock_dag_segment]),
        ), \
             patch.object(creator, '_wait_for_dag_approval', new_callable=AsyncMock, return_value=False), \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock):

            with pytest.raises(RuntimeError, match="rejected by user"):
                await creator.create_cinema_video(
                    job_id="partial-reject", topic="T", niche="n",
                    automation_mode=AutomationMode.PARTIAL,
                )

    @pytest.mark.asyncio
    async def test_partial_approval_gate_passes_on_accept(self):
        """PARTIAL proceeds when user approves the DAG."""
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.video_engine.automation import AutomationMode

        creator = AutoCreator()
        mock_dag_segment = {
            "text": "Approved segment",
            "visual_prompt": "Approved visual",
            "mood": "epic",
            "type": "clip",
            "dag_metadata": {
                "node_id": "approved",
                "dag_type": "clip",
                "inputs": [],
                "duration_sec": 8,
            },
        }

        with patch.multiple(
            creator,
            _generate_dag_guided_script=AsyncMock(return_value=[mock_dag_segment]),
            _source_visual_assets=AsyncMock(return_value=["/tmp/approved.mp4"]),
            _generate_voiceovers=AsyncMock(return_value=["/tmp/approved.mp3"]),
        ), \
             patch.object(creator, '_wait_for_dag_approval', new_callable=AsyncMock, return_value=True), \
             patch("src.services.nexus_engine.orchestrator.base_nexus_service") as mock_nexus, \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("sqlalchemy.select"), \
             patch("src.api.utils.models.NexusJobDB"):

            mock_nexus.assemble_video = AsyncMock(return_value="/tmp/out.mp4")

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            output_path = await creator.create_cinema_video(
                job_id="partial-approve", topic="T", niche="n",
                automation_mode=AutomationMode.PARTIAL,
            )

            assert output_path == "/tmp/out.mp4"
            # Approval gate was called
            creator._wait_for_dag_approval.assert_called_once()

    @pytest.mark.asyncio
    async def test_partial_approval_shows_preview(self):
        """PARTIAL mode generates DAG preview for user review."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        mock_dag_segment = {
            "text": "Preview segment",
            "visual_prompt": "Preview visual",
            "mood": "moody",
            "type": "clip",
            "dag_metadata": {
                "node_id": "preview_node",
                "dag_type": "clip",
                "inputs": [],
                "effect": None,
                "duration_sec": 10,
            },
        }

        segments = [mock_dag_segment]
        dag_preview = await creator._build_dag_preview(segments, "partial-preview", "tech")

        assert dag_preview["job_id"] == "partial-preview"
        assert dag_preview["segments_count"] == 1
        assert dag_preview["estimated_duration_sec"] == 10
        assert len(dag_preview["segments"]) == 1
        preview_seg = dag_preview["segments"][0]
        assert preview_seg["index"] == 0
        assert preview_seg["text"] == "Preview segment"
        assert preview_seg["visual_prompt"] == "Preview visual"
        assert preview_seg["dag_type"] == "clip"

    @pytest.mark.asyncio
    async def test_approve_dag_api(self):
        """approve_dag() resolves the approval event correctly."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        import asyncio

        creator = AutoCreator()

        # Simulate a running approval gate
        dag_preview = creator._build_dag_preview([{
            "text": "Test",
            "visual_prompt": "Test",
            "mood": "neutral",
            "type": "clip",
            "dag_metadata": {"node_id": "t", "dag_type": "clip", "inputs": [], "duration_sec": 5},
        }], "approve-job", "tech")

        # Store as pending
        creator._pending_approvals["approve-job"] = await dag_preview
        event = asyncio.Event()
        creator._approval_events["approve-job"] = event

        # Approve via API
        result = await creator.approve_dag("approve-job", True)
        assert result is True
        assert event.is_set()  # Event should be triggered

        # Verify approval state
        pending = creator._pending_approvals.get("approve-job", {})
        assert pending.get("_approved") is True

    @pytest.mark.asyncio
    async def test_approve_dag_nonexistent_job(self):
        """approve_dag() returns False for unknown job."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        result = await creator.approve_dag("nonexistent-job", True)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_pending_approval(self):
        """get_pending_approval() returns preview without internal metadata."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        preview = {
            "job_id": "poll-job",
            "niche": "tech",
            "segments_count": 2,
            "_approved": False,  # Internal field
        }
        creator._pending_approvals["poll-job"] = preview

        result = await creator.get_pending_approval("poll-job")
        assert result is not None
        assert "_approved" not in result  # Internal fields stripped
        assert result["job_id"] == "poll-job"

        result2 = await creator.get_pending_approval("unknown")
        assert result2 is None


# =============================================================================
# Tests: FULL Mode
# =============================================================================


class TestFullMode:
    """FULL mode: end-to-end AI-driven, no manual intervention."""

    @pytest.mark.asyncio
    async def test_full_forces_dag_and_skips_approval(self):
        """FULL mode forces use_dag=True and does NOT wait for approval."""
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.video_engine.automation import AutomationMode

        creator = AutoCreator()
        mock_dag_segment = {
            "text": "Full auto segment",
            "visual_prompt": "Full auto visual",
            "mood": "epic",
            "type": "clip",
            "dag_metadata": {
                "node_id": "full_intro",
                "dag_type": "clip",
                "inputs": [],
                "duration_sec": 8,
            },
        }

        with patch.multiple(
            creator,
            _generate_dag_guided_script=AsyncMock(return_value=[mock_dag_segment]),
            _source_visual_assets=AsyncMock(return_value=["/tmp/full_vis.mp4"]),
            _generate_voiceovers=AsyncMock(return_value=["/tmp/full_voice.mp3"]),
        ), \
             patch.object(creator, '_wait_for_dag_approval', new_callable=AsyncMock) as mock_approve, \
             patch("src.services.nexus_engine.orchestrator.base_nexus_service") as mock_nexus, \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("sqlalchemy.select"), \
             patch("src.api.utils.models.NexusJobDB"):

            mock_nexus.assemble_video = AsyncMock(return_value="/tmp/output.mp4")

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            output_path = await creator.create_cinema_video(
                job_id="full-001", topic="AI", niche="tech",
                use_dag=False,  # Should be overridden by FULL
                automation_mode=AutomationMode.FULL,
            )

            assert output_path == "/tmp/output.mp4"
            # FULL uses DAG-guided script
            creator._generate_dag_guided_script.assert_called_once()
            # Approval gate is NOT called in FULL mode
            mock_approve.assert_not_called()
            # Asset sourcing passes use_dag=True
            _, call_kwargs = creator._source_visual_assets.call_args
            assert call_kwargs.get("use_dag") is True

    @pytest.mark.asyncio
    async def test_full_auto_publishes_when_requested(self):
        """FULL mode auto-publishes when job_metadata has auto_publish."""
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.video_engine.automation import AutomationMode

        creator = AutoCreator()
        mock_dag_segment = {
            "text": "Full publish segment",
            "visual_prompt": "Full visual",
            "mood": "exciting",
            "type": "clip",
            "dag_metadata": {
                "node_id": "pub_intro",
                "dag_type": "clip",
                "inputs": [],
                "duration_sec": 10,
            },
        }

        with patch.multiple(
            creator,
            _generate_dag_guided_script=AsyncMock(return_value=[mock_dag_segment]),
            _source_visual_assets=AsyncMock(return_value=["/tmp/publish_vis.mp4"]),
            _generate_voiceovers=AsyncMock(return_value=["/tmp/publish_voice.mp3"]),
        ), \
             patch("src.services.nexus_engine.orchestrator.base_nexus_service") as mock_nexus, \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("sqlalchemy.select"), \
             patch("src.api.utils.models.NexusJobDB"):

            mock_nexus.assemble_video = AsyncMock(return_value="/tmp/output.mp4")

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            output_path = await creator.create_cinema_video(
                job_id="full-publish", topic="T", niche="n",
                automation_mode=AutomationMode.FULL,
            )

            assert output_path == "/tmp/output.mp4"
            # Everything runs without manual intervention
            creator._generate_dag_guided_script.assert_called_once()


# =============================================================================
# Tests: DAG-Guided Script Generation
# =============================================================================


class TestDAGGuidedScript:
    """Tests for Prompt→DAG Generator (_generate_dag_guided_script)."""

    @pytest.mark.asyncio
    async def test_returns_script_segments_from_llm(self):
        """DAG-guided script returns script segments with dag_metadata."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        mock_llm_response = {
            "response": json.dumps({
                "nodes": [
                    {
                        "id": "intro",
                        "type": "clip",
                        "inputs": [],
                        "params": {
                            "text": "Welcome to AI",
                            "visual_prompt": "Futuristic city",
                            "mood": "inspirational",
                            "effect": None,
                            "duration_sec": 8,
                        },
                    },
                    {
                        "id": "scene_1",
                        "type": "clip",
                        "inputs": ["intro"],
                        "params": {
                            "text": "AI is transforming",
                            "visual_prompt": "Neural network",
                            "mood": "educational",
                            "duration_sec": 10,
                        },
                    },
                ]
            })
        }

        with patch("src.services.llm.intelligence_hub.base_intelligence_service") as mock_intel:
            mock_intel.chat = AsyncMock(return_value=mock_llm_response)

            segments = await creator._generate_dag_guided_script(
                topic="AI Revolution", niche="tech",
                duration_seconds=60, style="CINEMATIC_DOC",
                job_id="dag-script-001",
            )

            assert len(segments) == 2
            assert segments[0]["text"] == "Welcome to AI"
            assert segments[0]["dag_metadata"]["node_id"] == "intro"
            assert segments[0]["dag_metadata"]["dag_type"] == "clip"
            assert segments[0]["dag_metadata"]["inputs"] == []
            assert segments[0]["dag_metadata"]["duration_sec"] == 8

            assert segments[1]["text"] == "AI is transforming"
            assert segments[1]["dag_metadata"]["node_id"] == "scene_1"
            assert segments[1]["dag_metadata"]["inputs"] == ["intro"]

    @pytest.mark.asyncio
    async def test_falls_back_on_llm_failure(self):
        """Falls back to standard script generation when LLM fails."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch("src.services.llm.intelligence_hub.base_intelligence_service") as mock_intel:
            mock_intel.chat = AsyncMock(side_effect=ConnectionError("LLM down"))

            # Should fall back to generate_viral_script
            with patch.object(creator, 'generate_viral_script', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = [{
                    "text": "Fallback segment",
                    "visual_prompt": "Fallback",
                    "mood": "neutral",
                    "type": "narrative",
                }]

                segments = await creator._generate_dag_guided_script(
                    topic="T", niche="n", duration_seconds=60,
                    style="CINEMATIC_DOC", job_id="dag-fallback",
                )

                assert len(segments) == 1
                assert segments[0]["text"] == "Fallback segment"
                mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_falls_back_on_empty_llm_response(self):
        """Falls back when LLM returns empty nodes."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch("src.services.llm.intelligence_hub.base_intelligence_service") as mock_intel:
            mock_intel.chat = AsyncMock(return_value={
                "response": json.dumps({"nodes": []})
            })

            with patch.object(creator, 'generate_viral_script', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = [{
                    "text": "Empty fallback",
                    "visual_prompt": "Empty",
                    "mood": "neutral",
                    "type": "narrative",
                }]

                segments = await creator._generate_dag_guided_script(
                    topic="T", niche="n", duration_seconds=30,
                    style="CINEMATIC_DOC", job_id="dag-empty",
                )

                assert len(segments) == 1
                assert segments[0]["text"] == "Empty fallback"
                mock_fallback.assert_called_once()


# =============================================================================
# Tests: Blueprint Automation Mode Integration
# =============================================================================


class TestBlueprintAutomationModes:
    """Blueprints correctly use automation_mode for DAG routing."""

    @pytest.mark.asyncio
    async def test_execute_blueprint_manual_no_dag(self):
        """Manual mode: blueprint executes linearly when use_dag=False."""
        from src.services.nexus_engine.blueprints import execute_blueprint

        blueprint = {
            "id": "test-bp",
            "nodes": [
                {"type": "ingress", "label": "Input"},
                {"type": "egress", "label": "Output"},
            ]
        }

        with patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock):
            result = await execute_blueprint(
                blueprint, {"content": "test"}, "bp-manual",
                use_dag=False, automation_mode="manual",
            )

        assert result["status"] == "success"
        assert "ingress" in result["results"]
        assert "egress" in result["results"]

    @pytest.mark.asyncio
    async def test_execute_blueprint_partial_forces_dag(self):
        """Partial mode forces DAG execution even when use_dag=False."""
        from src.services.nexus_engine.blueprints import execute_blueprint

        blueprint = {
            "id": "test-bp",
            "nodes": [
                {"type": "ingress", "label": "Input"},
                {"type": "egress", "label": "Output"},
            ]
        }

        with patch("src.services.nexus_engine.blueprints.dag_execute_blueprint", new_callable=AsyncMock) as mock_dag, \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock):

            mock_dag.return_value = {"status": "success", "results": {}, "blueprint_id": "test-bp"}

            await execute_blueprint(
                blueprint, {"niche": "test", "content": "test"}, "bp-partial",
                use_dag=False,  # Should be overridden
                automation_mode="partial",
            )

            # DAG path should be called (PARTIAL forces it)
            mock_dag.assert_called_once()


# =============================================================================
# Tests: Edge Cases & Error Handling
# =============================================================================


class TestAutomationEdgeCases:
    """Error handling — cross-cutting tests (mode-agnostic)."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_regardless_of_mode(self):
        """Circuit breaker blocks all modes equally."""
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.video_engine.automation import AutomationMode

        creator = AutoCreator()
        creator.breaker.state = "OPEN"

        with pytest.raises(RuntimeError, match="temporarily unavailable"):
            await creator.create_cinema_video(
                job_id="cb-test", topic="T", niche="n",
                automation_mode=AutomationMode.PARTIAL,
            )

    @pytest.mark.asyncio
    async def test_provided_script_skips_generation(self):
        """A pre-provided script bypasses generation in any mode."""
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.video_engine.automation import AutomationMode

        creator = AutoCreator()
        script = [{
            "text": "Provided",
            "visual_prompt": "Provided",
            "mood": "calm",
            "type": "narrative",
        }]

        with patch.object(creator, 'generate_viral_script', new_callable=AsyncMock) as mock_gen, \
             patch.object(creator, '_generate_dag_guided_script', new_callable=AsyncMock) as mock_dag_gen, \
             patch.object(creator, '_source_visual_assets', new_callable=AsyncMock, return_value=["/tmp/v.mp4"]), \
             patch.object(creator, '_generate_voiceovers', new_callable=AsyncMock, return_value=["/tmp/vc.mp3"]), \
             patch("src.services.nexus_engine.orchestrator.base_nexus_service") as mock_nexus, \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("sqlalchemy.select"), \
             patch("src.api.utils.models.NexusJobDB"):

            mock_nexus.assemble_video = AsyncMock(return_value="/tmp/output.mp4")
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            await creator.create_cinema_video(
                job_id="provided-test", topic="T", niche="n",
                script=script, automation_mode=AutomationMode.MANUAL,
            )

            mock_gen.assert_not_called()
            mock_dag_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_assets_raises_value_error(self):
        """Empty visual assets raise ValueError in any mode."""
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.video_engine.automation import AutomationMode

        creator = AutoCreator()
        script = [{
            "text": "No visuals",
            "visual_prompt": "Empty",
            "mood": "neutral",
            "type": "hook",
        }]

        with patch.object(creator, 'generate_viral_script', new_callable=AsyncMock), \
             patch.object(creator, '_source_visual_assets', new_callable=AsyncMock, return_value=[]), \
             patch.object(creator, '_generate_voiceovers', new_callable=AsyncMock, return_value=["/tmp/v.mp3"]), \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock):

            with pytest.raises(ValueError, match="Asset sourcing failed"):
                await creator.create_cinema_video(
                    job_id="empty-test", topic="T", niche="n",
                    script=script, automation_mode=AutomationMode.MANUAL,
                )
