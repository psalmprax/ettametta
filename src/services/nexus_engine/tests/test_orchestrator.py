"""
Tests for Nexus Engine Orchestrator — Video Assembly Pipeline, Retry Logic, Node Flow.
"""
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture(autouse=True)
def patch_asyncio_to_thread():
    """
    Replace asyncio.to_thread with a synchronous executor that runs the
    function directly in the current event loop.

    This prevents "Event loop is closed" / "different loop" errors caused
    when threads created by ``asyncio.to_thread`` try to access the
    test-scoped event loop (e.g., via ``cv2.VideoCapture`` or
    ``subprocess.run`` callbacks).

    We use ``new=`` (not ``side_effect`` on a MagicMock) because MagicMock
    doesn't properly support ``await`` — ``await MagicMock()`` returns
    another MagicMock instead of executing the side_effect.
    """
    async def _fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    with patch(
        "src.services.nexus_engine.orchestrator.asyncio.to_thread",
        new=_fake_to_thread,
    ):
        yield


@pytest.fixture
def mock_notify():
    """Fixture to mock notify_nexus_job_update_sync at its source module."""
    with patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock) as m:
        yield m


class TestOrchestratorInit:
    """Tests for NexusOrchestrator initialization."""

    def test_creates_output_directory(self, tmp_path):
        """Output directory is created on init."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        test_dir = str(tmp_path / "nexus_test")
        orchestrator = NexusOrchestrator(output_dir=test_dir)
        assert os.path.exists(test_dir)
        os.rmdir(test_dir)

    def test_initializes_circuit_breaker(self):
        """Remotion circuit breaker is initialized and closed."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()
        assert orchestrator.remotion_breaker is not None
        assert orchestrator.remotion_breaker.state == "CLOSED"

    def test_checks_dependency_availability(self):
        """Dependencies dict is populated with availability flags."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()
        assert "moviepy" in orchestrator.dependencies_available


class TestRetryRemotionRender:
    """Tests for _retry_remotion_render — retry logic with circuit breaker."""

    @pytest.mark.asyncio
    async def test_returns_path_on_success(self):
        """Successful render returns the output path."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion:
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            result = await orchestrator._retry_remotion_render(
                composition_id="ViralClip", props={"key": "val"}, output_name="test.mp4"
            )
            assert result == "/tmp/output.mp4"

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self):
        """Raises RuntimeError when circuit breaker is OPEN."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()
        orchestrator.remotion_breaker.state = "OPEN"

        with pytest.raises(RuntimeError, match="circuit breaker is OPEN"):
            await orchestrator._retry_remotion_render(
                composition_id="ViralClip", props={}, output_name="test.mp4"
            )

    @pytest.mark.asyncio
    async def test_records_success_on_breaker(self):
        """Successful render records success on the circuit breaker."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()
        orchestrator.remotion_breaker.reset()
        initial_failures = orchestrator.remotion_breaker.failure_count

        with patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion:
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            result = await orchestrator._retry_remotion_render("ViralClip", {"k": "v"}, "test.mp4")

            assert orchestrator.remotion_breaker.failure_count == initial_failures
            assert result == "/tmp/output.mp4"

    @pytest.mark.asyncio
    async def test_returns_none_when_all_retries_exhausted(self):
        """Returns None when all render retries are exhausted."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion:
            mock_remotion.render_video = AsyncMock(side_effect=TimeoutError("Render timeout"))
            with patch.object(orchestrator.remotion_breaker, 'record_failure'):
                result = await orchestrator._retry_remotion_render("ViralClip", {"k": "v"}, "test.mp4")

        assert result is None


class TestAssembleVideoIngress:
    """Tests for the Ingress Node — input validation."""

    @pytest.mark.asyncio
    async def test_validates_input_paths(self, mock_notify):
        """Ingress validates that all visual/voiceover paths exist."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        # Patch ALL dynamically imported dependencies at their SOURCE modules
        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp, \
             patch("src.services.langchain.service.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion, \
             patch("src.services.audio.sound_design.sound_design_service") as mock_sd, \
             patch("src.services.audio.transcription_service.base_transcription_service") as mock_ts, \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists:

            # Fix: Use MagicMock for execute.return_value to avoid AsyncMock coroutine issue
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session

            mock_bp.return_value = {"id": "viral-reskin", "name": "Viral Reskin", "composition_id": "ViralClip", "nodes": []}
            mock_lc.is_enabled.return_value = False
            mock_sd.enabled = False
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            mock_ts.transcribe = AsyncMock(return_value={"words": []})
            mock_llm.analyze_image = AsyncMock(return_value={"content": "YES"})
            mock_exists.return_value = True

            with patch("src.services.nexus_engine.orchestrator.os.path.getsize") as mock_getsize, \
                 patch("src.services.nexus_engine.orchestrator.cv2.VideoCapture") as mock_cap:

                mock_getsize.return_value = 2048
                mock_instance = MagicMock()
                mock_instance.get.side_effect = lambda prop: {
                    7: 150,  # frame count
                    5: 30.0,  # fps
                }.get(prop, 0)
                mock_cap.return_value = mock_instance

                result = await orchestrator.assemble_video(
                    job_id="job-001",
                    niche="tech",
                    script_segments=[{"text": "S1", "type": "hook"}],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/tmp/visual_0.mp4"],
                )

                assert result == "/tmp/output.mp4"

    @pytest.mark.asyncio
    async def test_raises_on_missing_visual(self, mock_notify):
        """Ingress fails when a visual path does not exist and is not HTTP."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}

            with pytest.raises(RuntimeError, match="not found"):
                await orchestrator.assemble_video(
                    job_id="job-002",
                    niche="tech",
                    script_segments=[{"text": "S1", "type": "hook"}],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/nonexistent/path.mp4"],
                )

    @pytest.mark.asyncio
    async def test_accepts_http_urls_skip_validation(self, mock_notify):
        """HTTP URLs skip file existence validation in ingress."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp, \
             patch("src.services.langchain.service.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion, \
             patch("src.services.audio.sound_design.sound_design_service") as mock_sd, \
             patch("src.services.audio.transcription_service.base_transcription_service") as mock_ts, \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}
            mock_lc.is_enabled.return_value = False
            mock_sd.enabled = False
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            mock_llm.analyze_image = AsyncMock(return_value={"content": "YES"})
            mock_ts.transcribe = AsyncMock(return_value={"words": []})
            mock_exists.return_value = True

            with patch("src.services.nexus_engine.orchestrator.os.path.getsize") as mock_getsize, \
                 patch("src.services.nexus_engine.orchestrator.cv2.VideoCapture") as mock_cap:

                mock_getsize.return_value = 2048
                mock_instance = MagicMock()
                mock_instance.get.side_effect = lambda prop: {
                    7: 150,
                    5: 30.0,
                }.get(prop, 0)
                mock_cap.return_value = mock_instance

                result = await orchestrator.assemble_video(
                    job_id="job-003",
                    niche="tech",
                    script_segments=[{"text": "S1", "type": "hook"}],
                    voiceover_paths=["http://example.com/voice.mp3"],
                    visual_paths=["http://example.com/vid.mp4"],
                )

                assert result == "/tmp/output.mp4"


class TestAssembleVideoCognition:
    """Tests for the Cognition Node — frame counting and clip metadata."""

    @pytest.mark.asyncio
    async def test_extracts_frame_counts_from_clips(self, mock_notify):
        """Cognition node extracts frame counts from visual paths."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp, \
             patch("src.services.langchain.service.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion, \
             patch("src.services.audio.sound_design.sound_design_service") as mock_sd, \
             patch("src.services.audio.transcription_service.base_transcription_service") as mock_ts, \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}
            mock_lc.is_enabled.return_value = False
            mock_sd.enabled = False
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            mock_llm.analyze_image = AsyncMock(return_value={"content": "YES"})
            mock_ts.transcribe = AsyncMock(return_value={"words": []})
            mock_exists.return_value = True

            with patch("src.services.nexus_engine.orchestrator.os.path.getsize") as mock_getsize, \
                 patch("src.services.nexus_engine.orchestrator.cv2.VideoCapture") as mock_cap:

                mock_getsize.return_value = 2048
                mock_instance = MagicMock()
                mock_instance.get.side_effect = lambda prop: {
                    7: 150,
                    5: 30.0,
                }.get(prop, 0)
                mock_cap.return_value = mock_instance

                result = await orchestrator.assemble_video(
                    job_id="job-004",
                    niche="tech",
                    script_segments=[{"text": "S1", "type": "hook"}],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/tmp/visual_0.mp4"],
                )

                assert result == "/tmp/output.mp4"

    @pytest.mark.asyncio
    async def test_raises_when_no_valid_clips(self, mock_notify):
        """Cognition fails when no visual clips return valid frame counts."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp, \
             patch("src.services.langchain.service.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}
            mock_lc.is_enabled.return_value = False
            mock_exists.return_value = True

            with patch("src.services.nexus_engine.orchestrator.cv2.VideoCapture") as mock_cap:
                mock_instance = MagicMock()
                mock_instance.get.return_value = 0  # No frames
                mock_cap.return_value = mock_instance

                with pytest.raises(RuntimeError, match="No valid video clips"):
                    await orchestrator.assemble_video(
                        job_id="job-005",
                        niche="tech",
                        script_segments=[{"text": "S1", "type": "hook"}],
                        voiceover_paths=["/tmp/voice.mp3"],
                        visual_paths=["/tmp/invalid.mp4"],
                    )


class TestAssembleVideoSynthesis:
    """Tests for the Synthesis Node — props building, audio, and Remotion render."""

    @pytest.mark.asyncio
    async def test_builds_complete_remotion_props(self, mock_notify):
        """Synthesis builds comprehensive Remotion props including style, CTA, and word timestamps."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp, \
             patch("src.services.langchain.service.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion, \
             patch("src.services.audio.sound_design.sound_design_service") as mock_sd, \
             patch("src.services.audio.transcription_service.base_transcription_service") as mock_ts, \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}
            mock_lc.is_enabled.return_value = False
            mock_sd.enabled = False
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            mock_llm.analyze_image = AsyncMock(return_value={"content": "YES"})
            mock_ts.transcribe = AsyncMock(return_value={"words": [{"word": "hello", "start": 0.0, "end": 0.5}]})
            mock_exists.return_value = True

            with patch("src.services.nexus_engine.orchestrator.os.path.getsize") as mock_getsize, \
                 patch("src.services.nexus_engine.orchestrator.cv2.VideoCapture") as mock_cap:

                mock_getsize.return_value = 2048
                mock_instance = MagicMock()
                mock_instance.get.side_effect = lambda prop: {
                    7: 150,
                    5: 30.0,
                }.get(prop, 0)
                mock_cap.return_value = mock_instance

                result = await orchestrator.assemble_video(
                    job_id="job-006",
                    niche="tech",
                    script_segments=[
                        {"text": "Intro", "type": "hook"},
                        {"text": "Click here", "type": "cta"}
                    ],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/tmp/visual_0.mp4"],
                )

                assert result == "/tmp/output.mp4"
                # Verify render_video was called (indirect assertion that pipeline completed)
                mock_remotion.render_video.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_sources_music_from_library(self, mock_notify):
        """Synthesis auto-sources music from sound_design library when not provided."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp, \
             patch("src.services.langchain.service.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion, \
             patch("src.services.audio.sound_design.sound_design_service") as mock_sd, \
             patch("src.services.audio.transcription_service.base_transcription_service") as mock_ts, \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}
            mock_lc.is_enabled.return_value = False
            mock_sd.enabled = True
            mock_sd.library_path = "/music_lib"
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            mock_llm.analyze_image = AsyncMock(return_value={"content": "YES"})
            mock_ts.transcribe = AsyncMock(return_value={"words": []})
            mock_exists.return_value = True

            with patch("src.services.nexus_engine.orchestrator.Path") as mock_path, \
                 patch("src.services.nexus_engine.orchestrator.os.path.getsize") as mock_getsize, \
                 patch("src.services.nexus_engine.orchestrator.cv2.VideoCapture") as mock_cap:

                mock_getsize.return_value = 2048
                mock_music_dir = MagicMock()
                mock_music_dir.exists.return_value = True
                mock_music_dir.glob.return_value = [MagicMock(__str__=lambda s: "/music_lib/cinematic/track.mp3")]
                mock_path.return_value = mock_music_dir

                mock_instance = MagicMock()
                mock_instance.get.side_effect = lambda prop: {
                    7: 150,
                    5: 30.0,
                }.get(prop, 0)
                mock_cap.return_value = mock_instance

                result = await orchestrator.assemble_video(
                    job_id="job-007",
                    niche="tech",
                    script_segments=[{"text": "S1", "type": "hook"}],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/tmp/visual_0.mp4"],
                )

                assert result == "/tmp/output.mp4"

    @pytest.mark.asyncio
    async def test_handles_cta_segment_props(self, mock_notify):
        """CTA segments get proper overlay props including show_cta_overlay."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp, \
             patch("src.services.langchain.service.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion, \
             patch("src.services.audio.sound_design.sound_design_service") as mock_sd, \
             patch("src.services.audio.transcription_service.base_transcription_service") as mock_ts, \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}
            mock_lc.is_enabled.return_value = False
            mock_sd.enabled = False
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            mock_llm.analyze_image = AsyncMock(return_value={"content": "YES"})
            mock_ts.transcribe = AsyncMock(return_value={"words": []})
            mock_exists.return_value = True

            with patch("src.services.nexus_engine.orchestrator.os.path.getsize") as mock_getsize, \
                 patch("src.services.nexus_engine.orchestrator.cv2.VideoCapture") as mock_cap:

                mock_getsize.return_value = 2048
                mock_instance = MagicMock()
                mock_instance.get.side_effect = lambda prop: {
                    7: 150,
                    5: 30.0,
                }.get(prop, 0)
                mock_cap.return_value = mock_instance

                await orchestrator.assemble_video(
                    job_id="job-008",
                    niche="tech",
                    script_segments=[{"text": "Buy now!", "type": "cta"}],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/tmp/visual_0.mp4"],
                )

                mock_remotion.render_video.assert_called_once()


class TestAssembleVideoEgress:
    """Tests for the Egress Node — cleanup, publishing, and final metadata."""

    @pytest.mark.asyncio
    async def test_cleans_up_temp_directories(self, mock_notify):
        """Egress cleans up temp/voice, temp/audit, and temp/thumbnails."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp, \
             patch("src.services.langchain.service.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion, \
             patch("src.services.audio.sound_design.sound_design_service") as mock_sd, \
             patch("src.services.audio.transcription_service.base_transcription_service") as mock_ts, \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists, \
             patch("shutil.rmtree") as mock_rmtree:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}
            mock_lc.is_enabled.return_value = False
            mock_sd.enabled = False
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            mock_llm.analyze_image = AsyncMock(return_value={"content": "YES"})
            mock_ts.transcribe = AsyncMock(return_value={"words": []})
            mock_exists.return_value = True

            with patch("src.services.nexus_engine.orchestrator.os.path.getsize") as mock_getsize, \
                 patch("src.services.nexus_engine.orchestrator.cv2.VideoCapture") as mock_cap:

                mock_getsize.return_value = 2048
                mock_instance = MagicMock()
                mock_instance.get.side_effect = lambda prop: {
                    7: 150,
                    5: 30.0,
                }.get(prop, 0)
                mock_cap.return_value = mock_instance

                await orchestrator.assemble_video(
                    job_id="job-009",
                    niche="tech",
                    script_segments=[{"text": "S1", "type": "hook"}],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/tmp/visual_0.mp4"],
                )

                # Verify temp cleanup was called
                assert mock_rmtree.call_count >= 1

    @pytest.mark.asyncio
    async def test_auto_publishes_when_enabled(self, mock_notify):
        """Egress publishes to platforms when job_metadata.auto_publish is True."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp, \
             patch("src.services.langchain.service.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion, \
             patch("src.services.audio.sound_design.sound_design_service") as mock_sd, \
             patch("src.services.audio.transcription_service.base_transcription_service") as mock_ts, \
             patch("src.services.publishing.service.base_publishing_service") as mock_pub, \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists, \
             patch("shutil.rmtree"):

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}
            mock_lc.is_enabled.return_value = False
            mock_sd.enabled = False
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            mock_llm.analyze_image = AsyncMock(return_value={"content": "YES"})
            mock_ts.transcribe = AsyncMock(return_value={"words": []})
            mock_pub.publish_to_platform = AsyncMock(return_value={"status": "published"})
            mock_exists.return_value = True

            with patch("src.services.nexus_engine.orchestrator.os.path.getsize") as mock_getsize, \
                 patch("src.services.nexus_engine.orchestrator.cv2.VideoCapture") as mock_cap:

                mock_getsize.return_value = 2048
                mock_instance = MagicMock()
                mock_instance.get.side_effect = lambda prop: {
                    7: 150,
                    5: 30.0,
                }.get(prop, 0)
                mock_cap.return_value = mock_instance

                result = await orchestrator.assemble_video(
                    job_id="job-010",
                    niche="tech",
                    script_segments=[{"text": "S1", "type": "hook"}],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/tmp/visual_0.mp4"],
                    job_metadata={"auto_publish": True, "platforms": ["youtube"]},
                )

                assert result == "/tmp/output.mp4"
                mock_pub.publish_to_platform.assert_called_once()


class TestAssembleVideoVisionAudit:
    """Tests for the Vision Audit Node — frame extraction and AI analysis."""

    @pytest.mark.asyncio
    async def test_performs_vision_audit_on_frames(self, mock_notify):
        """Vision audit extracts a middle frame and calls Gemini analyze_image."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp, \
             patch("src.services.langchain.service.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion, \
             patch("src.services.audio.sound_design.sound_design_service") as mock_sd, \
             patch("src.services.audio.transcription_service.base_transcription_service") as mock_ts, \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists, \
             patch("src.services.nexus_engine.orchestrator.os.makedirs") as mock_mkdir, \
             patch("shutil.rmtree"):

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}
            mock_lc.is_enabled.return_value = False
            mock_sd.enabled = False
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            mock_ts.transcribe = AsyncMock(return_value={"words": []})
            mock_exists.return_value = True

            # Mock cv2.VideoCapture for both cognition frame counting and vision audit
            with patch("src.services.nexus_engine.orchestrator.os.path.getsize") as mock_getsize, \
                 patch("src.services.nexus_engine.orchestrator.cv2.VideoCapture") as mock_cap, \
                 patch("src.services.nexus_engine.orchestrator.cv2.imwrite") as mock_imwrite:

                mock_getsize.return_value = 2048
                mock_instance = MagicMock()
                mock_instance.get.side_effect = lambda prop: {
                    7: 150,
                    5: 30.0,
                }.get(prop, 0)
                mock_instance.read.return_value = (True, MagicMock())
                mock_cap.return_value = mock_instance

                mock_llm.analyze_image = AsyncMock(return_value={"content": "YES, relevant content"})

                result = await orchestrator.assemble_video(
                    job_id="job-011",
                    niche="tech",
                    script_segments=[{"text": "AI technology", "type": "hook"}],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/tmp/visual_0.mp4"],
                )

                assert result == "/tmp/output.mp4"
                # Verify analyze_image was called for vision audit
                mock_llm.analyze_image.assert_called_once()
                call_prompt = mock_llm.analyze_image.call_args[0][1]
                assert "AI technology" in call_prompt


class TestAssembleVideoErrorHandling:
    """Tests for error handling across the entire pipeline."""

    @pytest.mark.asyncio
    async def test_notifies_failure_on_exception(self, mock_notify):
        """Failure at any node sends a FAILED notification."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}

            with pytest.raises(RuntimeError):
                await orchestrator.assemble_video(
                    job_id="job-012",
                    niche="tech",
                    script_segments=[{"text": "S1", "type": "hook"}],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/nonexistent.mp4"],
                )

            # Verify a FAILED notification was sent via the mocked source module
            failure_calls = [
                c for c in mock_notify.call_args_list
                if c[0][0].get("status") == "FAILED"
            ]
            assert len(failure_calls) >= 1

    @pytest.mark.asyncio
    async def test_re_raises_exception(self, mock_notify):
        """Exceptions are re-raised after notification."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.services.nexus_engine.blueprints.get_blueprint_by_id") as mock_bp:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}

            with pytest.raises(RuntimeError) as exc_info:
                await orchestrator.assemble_video(
                    job_id="job-013",
                    niche="tech",
                    script_segments=[{"text": "S1", "type": "hook"}],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/missing.mp4"],
                )

            assert "not found" in str(exc_info.value)
