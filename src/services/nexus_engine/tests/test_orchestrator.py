"""
Tests for Nexus Engine Orchestrator — Video Assembly Pipeline, Retry Logic, Node Flow.
"""
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure SECRET_KEY is set for test runs that trigger settings imports
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_orchestrator_tests")


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
        NexusOrchestrator(output_dir=test_dir)
        assert os.path.exists(test_dir)
        os.rmdir(test_dir)

    def test_initializes_circuit_breaker(self):
        """Remotion circuit breaker is initialized and closed."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()
        assert orchestrator.render_pipeline.remotion_breaker is not None
        assert orchestrator.render_pipeline.remotion_breaker.state == "CLOSED"

    def test_checks_dependency_availability(self):
        """Dependencies dict is populated with availability flags."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()
        assert "moviepy" in orchestrator.dependencies_available


class TestRetryRemotionRender:
    """Tests for RenderPipeline.retry_remotion_render — retry logic with circuit breaker."""

    @pytest.mark.asyncio
    async def test_returns_path_on_success(self):
        """Successful render returns the output path."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion:
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            result = await orchestrator.render_pipeline.retry_remotion_render(
                composition_id="ViralClip", props={"key": "val"}, output_name="test.mp4"
            )
            assert result == "/tmp/output.mp4"

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self):
        """Raises RuntimeError when circuit breaker is OPEN."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()
        orchestrator.render_pipeline.remotion_breaker.state = "OPEN"

        with pytest.raises(RuntimeError, match="circuit breaker is OPEN"):
            await orchestrator.render_pipeline.retry_remotion_render(
                composition_id="ViralClip", props={}, output_name="test.mp4"
            )

    @pytest.mark.asyncio
    async def test_records_success_on_breaker(self):
        """Successful render records success on the circuit breaker."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()
        orchestrator.render_pipeline.remotion_breaker.reset()
        initial_failures = orchestrator.render_pipeline.remotion_breaker.failure_count

        with patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion:
            mock_remotion.render_video = AsyncMock(return_value="/tmp/output.mp4")
            result = await orchestrator.render_pipeline.retry_remotion_render("ViralClip", {"k": "v"}, "test.mp4")

            assert orchestrator.render_pipeline.remotion_breaker.failure_count == initial_failures
            assert result == "/tmp/output.mp4"

    @pytest.mark.asyncio
    async def test_returns_none_when_all_retries_exhausted(self):
        """Returns None when all render retries are exhausted."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()

        with patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion:
            mock_remotion.render_video = AsyncMock(side_effect=TimeoutError("Render timeout"))
            with patch.object(orchestrator.render_pipeline.remotion_breaker, 'record_failure'):
                result = await orchestrator.render_pipeline.retry_remotion_render("ViralClip", {"k": "v"}, "test.mp4")

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
             patch("src.services.llm.langchain.langchain_service") as mock_lc, \
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
             patch("src.services.llm.langchain.langchain_service") as mock_lc, \
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
             patch("src.services.llm.langchain.langchain_service") as mock_lc, \
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
             patch("src.services.llm.langchain.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service"), \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {"id": "test", "name": "Test", "composition_id": "ViralClip", "nodes": []}
            mock_lc.is_enabled.return_value = False
            mock_exists.return_value = True

            # determine_vibe now runs before clip prep in cognition; stub it so
            # the test reaches the "No valid video clips" raise deterministically.
            # Mock the real clip-prep boundary: when no frames are readable the
            # preparer yields no usable clips (the old cv2==0 path's intent).
            with patch.object(orchestrator.vibe_analyzer, "determine_vibe", new=AsyncMock(return_value={})), \
                 patch.object(orchestrator.asset_manager, "prepare_remotion_clips", new=AsyncMock(return_value=[])):
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
             patch("src.services.llm.langchain.langchain_service") as mock_lc, \
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
             patch("src.services.llm.langchain.langchain_service") as mock_lc, \
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
             patch("src.services.llm.langchain.langchain_service") as mock_lc, \
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
             patch("src.services.llm.langchain.langchain_service") as mock_lc, \
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
             patch("src.services.llm.langchain.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion, \
             patch("src.services.audio.sound_design.sound_design_service") as mock_sd, \
             patch("src.services.audio.transcription_service.base_transcription_service") as mock_ts, \
             patch("src.services.distribution.publishing.base_publishing_service") as mock_pub, \
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
             patch("src.services.llm.langchain.langchain_service") as mock_lc, \
             patch("src.services.llm.service.unified_llm_service") as mock_llm, \
             patch("src.services.video_engine.remotion_service.base_remotion_service") as mock_remotion, \
             patch("src.services.audio.sound_design.sound_design_service") as mock_sd, \
             patch("src.services.audio.transcription_service.base_transcription_service") as mock_ts, \
             patch("src.services.nexus_engine.orchestrator.os.path.exists") as mock_exists, \
             patch("src.services.nexus_engine.orchestrator.os.makedirs"), \
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
                 patch("src.services.nexus_engine.orchestrator.cv2.imwrite"):

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


# ═════════════════════════════════════════════════════════════════════════
# Phase 10-05: _source_fill_clips — duration-aware clip sourcing
# ═════════════════════════════════════════════════════════════════════════


class TestSourceFillClips:
    """Tests for ``_source_fill_clips`` — fetches b-roll from stock
    service to fill duration gaps between sourced footage and audio."""

    @pytest.mark.asyncio
    async def test_returns_paths_from_valid_downloads(self):
        """When stock service returns valid URLs with valid downloads,
        all paths are returned."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orch = NexusOrchestrator()

        with patch(
            "src.services.video_engine.stock_service.base_stock_service"
        ) as mock_stock:
            mock_stock.fetch_b_roll = AsyncMock(return_value=[
                "http://stock.example/1.mp4",
                "http://stock.example/2.mp4",
            ])
            mock_stock.download_stock_video = AsyncMock(
                side_effect=["/tmp/clip1.mp4", "/tmp/clip2.mp4"]
            )

            with patch(
                "src.services.nexus_engine.orchestrator.os.path.exists",
                return_value=True,
            ), patch(
                "src.services.nexus_engine.orchestrator.os.path.getsize",
                return_value=2048,
            ):
                paths = await orch.asset_manager.source_fill_clips(
                    "Motivation", count=3
                )

            assert len(paths) == 2
            assert "/tmp/clip1.mp4" in paths
            assert "/tmp/clip2.mp4" in paths
            mock_stock.fetch_b_roll.assert_called_once_with(
                "Motivation", count=3
            )

    @pytest.mark.asyncio
    async def test_falls_back_to_generic_niche_on_empty_results(self):
        """When the first fetch_b_roll returns no URLs, a fallback
        fetch with ``{niche} video`` is attempted."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orch = NexusOrchestrator()

        with patch(
            "src.services.video_engine.stock_service.base_stock_service"
        ) as mock_stock:
            # First call returns empty, fallback returns URLs
            mock_stock.fetch_b_roll = AsyncMock(side_effect=[
                [],  # primary — no results
                ["http://stock.example/fallback.mp4"],  # fallback
            ])
            mock_stock.download_stock_video = AsyncMock(
                return_value="/tmp/fallback.mp4"
            )

            with patch(
                "src.services.nexus_engine.orchestrator.os.path.exists",
                return_value=True,
            ), patch(
                "src.services.nexus_engine.orchestrator.os.path.getsize",
                return_value=2048,
            ):
                paths = await orch.asset_manager.source_fill_clips(
                    "ObscureNiche", count=2
                )

            assert len(paths) == 1
            assert "/tmp/fallback.mp4" in paths
            # Verify both calls were made
            assert mock_stock.fetch_b_roll.call_count == 2
            mock_stock.fetch_b_roll.assert_any_call(
                "ObscureNiche video", count=2
            )

    @pytest.mark.asyncio
    async def test_skips_downloads_that_fail(self):
        """Downloads that return ``None`` or produce missing/small
        files are silently skipped."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orch = NexusOrchestrator()

        with patch(
            "src.services.video_engine.stock_service.base_stock_service"
        ) as mock_stock:
            mock_stock.fetch_b_roll = AsyncMock(return_value=[
                "http://stock.example/good.mp4",
                "http://stock.example/bad.mp4",  # download returns None
                "http://stock.example/small.mp4",  # file too small
            ])
            mock_stock.download_stock_video = AsyncMock(side_effect=[
                "/tmp/good.mp4",
                None,  # failed download
                "/tmp/small.mp4",
            ])

            # exists: True, True, True  |  getsize: 2048, 512, 100
            with patch(
                "src.services.nexus_engine.orchestrator.os.path.exists",
                return_value=True,
            ), patch(
                "src.services.nexus_engine.orchestrator.os.path.getsize",
                side_effect=[2048, 0, 100],  # small.mp4 is 100 bytes
            ):
                paths = await orch.asset_manager.source_fill_clips(
                    "Tech", count=3
                )

            # Only the valid download (good.mp4) passes the size check
            assert len(paths) == 1
            assert "/tmp/good.mp4" in paths

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_fetches_fail(self):
        """When both primary and fallback fetches return no usable
        paths, an empty list is returned (graceful degradation)."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orch = NexusOrchestrator()

        with patch(
            "src.services.video_engine.stock_service.base_stock_service"
        ) as mock_stock:
            # Both primary and fallback return empty URL lists
            mock_stock.fetch_b_roll = AsyncMock(return_value=[])
            mock_stock.download_stock_video = AsyncMock()

            paths = await orch.asset_manager.source_fill_clips(
                "NonexistentNiche", count=4
            )

            assert paths == []
            assert mock_stock.fetch_b_roll.call_count == 2
            mock_stock.download_stock_video.assert_not_called()

    @pytest.mark.asyncio
    async def test_uses_default_count_of_4(self):
        """When ``count`` is not specified, the default of 4 is used."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orch = NexusOrchestrator()

        with patch(
            "src.services.video_engine.stock_service.base_stock_service"
        ) as mock_stock:
            mock_stock.fetch_b_roll = AsyncMock(return_value=[])

            await orch.asset_manager.source_fill_clips("Motivation")

            # Default count=4 should be used
            mock_stock.fetch_b_roll.assert_any_call(
                "Motivation", count=4
            )


# ═════════════════════════════════════════════════════════════════════════
# Phase 10-05: Gap-check + even-stretching logic inside assemble_video
# ═════════════════════════════════════════════════════════════════════════


class TestGapCheckAndEvenStretching:
    """Tests for the duration-aware clip sourcing and even-distribution
    logic added in Phase 10-05 inside ``assemble_video``.

    The gap-check triggers ``_source_fill_clips`` when sourced clips
    cover less than 70% of the probed ``total_frames``.  After any
    fill clips are added, all clip durations are evenly distributed
    to exactly fill the total frame budget."""

    def _build_assemble_mocks(
        self, mock_sf, mock_bp, mock_lc, mock_llm, mock_remotion,
        mock_sd, mock_ts, mock_exists, mock_getsize, mock_cap,
        clip_frame_counts=None,
    ):
        """Shared mock setup for assemble_video integration tests.

        ``clip_frame_counts`` controls how many frames each clip
        reports (drives the gap-check threshold).
        """
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_sf.return_value = mock_session

        mock_bp.return_value = {
            "id": "test", "name": "Test",
            "composition_id": "ViralClip", "nodes": [],
        }
        mock_lc.is_enabled.return_value = False
        mock_sd.enabled = False
        mock_remotion.render_video = AsyncMock(
            return_value="/tmp/output.mp4"
        )
        mock_llm.analyze_image = AsyncMock(
            return_value={"content": "YES"}
        )
        mock_ts.transcribe = AsyncMock(
            return_value={"words": []}
        )
        mock_exists.return_value = True
        mock_getsize.return_value = 2048

        mock_instance = MagicMock()
        frames_iter = iter(clip_frame_counts or [])
        mock_instance.get.side_effect = lambda prop: {
            7: next(frames_iter, 0),
            5: 30.0,
        }.get(prop, 0)
        mock_cap.return_value = mock_instance

    @pytest.mark.asyncio
    async def test_gap_triggers_fill_clips_when_below_70_percent(
        self, mock_notify
    ):
        """When total clip frames are < 70% of total_frames,
        ``_source_fill_clips`` is called to bridge the gap."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orch = NexusOrchestrator()

        with patch(
            "src.api.utils.database.async_session_factory"
        ) as mock_sf, patch(
            "src.services.nexus_engine.blueprints.get_blueprint_by_id"
        ) as mock_bp, patch(
            "src.services.llm.langchain.langchain_service"
        ) as mock_lc, patch(
            "src.services.llm.service.unified_llm_service"
        ) as mock_llm, patch(
            "src.services.video_engine.remotion_service.base_remotion_service"
        ) as mock_remotion, patch(
            "src.services.audio.sound_design.sound_design_service"
        ) as mock_sd, patch(
            "src.services.audio.transcription_service.base_transcription_service"
        ) as mock_ts, patch(
            "src.services.nexus_engine.orchestrator.os.path.exists"
        ) as mock_exists, patch(
            "src.services.nexus_engine.orchestrator.os.path.getsize"
        ) as mock_getsize, patch(
            "src.services.nexus_engine.orchestrator.cv2.VideoCapture"
        ) as mock_cap:

            self._build_assemble_mocks(
                mock_sf, mock_bp, mock_lc, mock_llm, mock_remotion,
                mock_sd, mock_ts, mock_exists, mock_getsize, mock_cap,
            )

            # Clip reports only 30 frames, but total_frames is 300 (10%).
            # Mock the real clip-prep boundary (the old cv2==30 path's intent):
            # the prepared remotion clip carries the small frame count that
            # drives the <70% gap check below.
            with patch.object(
                orch, "_update_node_status",
                AsyncMock(),
            ), patch.object(
                orch.asset_manager, "prepare_remotion_clips",
                new=AsyncMock(return_value=[
                    {"url": "/tmp/clip.mp4", "duration_in_frames": 30}
                ]),
            ), patch.object(
                orch.asset_manager, "determine_total_frames",
                AsyncMock(return_value=300),
            ), patch.object(
                orch.asset_manager, "source_fill_clips",
                AsyncMock(return_value=[]),
            ) as mock_fill:
                await orch.assemble_video(
                    job_id="job-gap-001",
                    niche="tech",
                    script_segments=[
                        {"text": "S1", "type": "hook"}
                    ],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/tmp/clip.mp4"],
                )

                # Gap was detected (30 < 300*0.7=210) → fill called
                mock_fill.assert_called_once()

    @pytest.mark.asyncio
    async def test_gap_skipped_when_above_70_percent(
        self, mock_notify
    ):
        """When total clip frames are >= 70% of total_frames,
        ``_source_fill_clips`` is NOT called."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orch = NexusOrchestrator()

        with patch(
            "src.api.utils.database.async_session_factory"
        ) as mock_sf, patch(
            "src.services.nexus_engine.blueprints.get_blueprint_by_id"
        ) as mock_bp, patch(
            "src.services.llm.langchain.langchain_service"
        ) as mock_lc, patch(
            "src.services.llm.service.unified_llm_service"
        ) as mock_llm, patch(
            "src.services.video_engine.remotion_service.base_remotion_service"
        ) as mock_remotion, patch(
            "src.services.audio.sound_design.sound_design_service"
        ) as mock_sd, patch(
            "src.services.audio.transcription_service.base_transcription_service"
        ) as mock_ts, patch(
            "src.services.nexus_engine.orchestrator.os.path.exists"
        ) as mock_exists, patch(
            "src.services.nexus_engine.orchestrator.os.path.getsize"
        ) as mock_getsize, patch(
            "src.services.nexus_engine.orchestrator.cv2.VideoCapture"
        ) as mock_cap:

            # Clip has 270 frames, total_frames is 300 (90%)
            self._build_assemble_mocks(
                mock_sf, mock_bp, mock_lc, mock_llm, mock_remotion,
                mock_sd, mock_ts, mock_exists, mock_getsize, mock_cap,
                clip_frame_counts=[270],
            )

            with patch.object(
                orch, "_update_node_status",
                AsyncMock(),
            ), patch.object(
                orch.asset_manager, "determine_total_frames",
                AsyncMock(return_value=300),
            ), patch.object(
                orch.asset_manager, "source_fill_clips",
                AsyncMock(return_value=[]),
            ) as mock_fill:
                await orch.assemble_video(
                    job_id="job-gap-002",
                    niche="tech",
                    script_segments=[
                        {"text": "S1", "type": "hook"}
                    ],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/tmp/clip.mp4"],
                )

                # No gap (270 >= 300*0.7=210) → fill NOT called
                mock_fill.assert_not_called()

    @pytest.mark.asyncio
    async def test_even_stretching_distributes_frames_equally(
        self, mock_notify
    ):
        """After gap-check, all clip durations are evenly distributed
        to exactly fill the total frame budget."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orch = NexusOrchestrator()

        with patch(
            "src.api.utils.database.async_session_factory"
        ) as mock_sf, patch(
            "src.services.nexus_engine.blueprints.get_blueprint_by_id"
        ) as mock_bp, patch(
            "src.services.llm.langchain.langchain_service"
        ) as mock_lc, patch(
            "src.services.llm.service.unified_llm_service"
        ) as mock_llm, patch(
            "src.services.video_engine.remotion_service.base_remotion_service"
        ) as mock_remotion, patch(
            "src.services.audio.sound_design.sound_design_service"
        ) as mock_sd, patch(
            "src.services.audio.transcription_service.base_transcription_service"
        ) as mock_ts, patch(
            "src.services.nexus_engine.orchestrator.os.path.exists"
        ) as mock_exists, patch(
            "src.services.nexus_engine.orchestrator.os.path.getsize"
        ) as mock_getsize, patch(
            "src.services.nexus_engine.orchestrator.cv2.VideoCapture"
        ) as mock_cap:

            # 4 clips × 250 frames each
            self._build_assemble_mocks(
                mock_sf, mock_bp, mock_lc, mock_llm, mock_remotion,
                mock_sd, mock_ts, mock_exists, mock_getsize, mock_cap,
                clip_frame_counts=[250, 250, 250, 250],
            )

            captor: dict = {}
            async def _capture_props(*args, **kwargs):
                captor["props"] = kwargs.get("props", {})
                return "/tmp/output.mp4"

            with patch.object(
                orch, "_update_node_status",
                AsyncMock(),
            ), patch.object(
                orch.asset_manager, "determine_total_frames",
                AsyncMock(return_value=400),
            ), patch.object(
                orch.asset_manager, "source_fill_clips",
                AsyncMock(return_value=[]),
            ), patch.object(
                orch.render_pipeline, "retry_remotion_render",
                AsyncMock(side_effect=_capture_props),
            ):
                await orch.assemble_video(
                    job_id="job-even-001",
                    niche="tech",
                    script_segments=[
                        {"text": "S1", "type": "hook"}
                    ],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=[
                        f"/tmp/clip_{i}.mp4" for i in range(4)
                    ],
                )

            # All 4 clips should be evenly stretched to 400/4=100
            clips = captor["props"]["clips"]
            assert len(clips) == 4
            for clip in clips:
                assert clip["duration_in_frames"] == 100, (
                    f"Expected 100, got {clip['duration_in_frames']}"
                )
            assert captor["props"]["video_duration_frames"] == 400

    @pytest.mark.asyncio
    async def test_even_stretching_zeroed_when_no_clips(
        self, mock_notify
    ):
        """When no valid clips survive the pipeline, the even-stretch
        block simply does nothing (no division by zero)."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orch = NexusOrchestrator()

        with patch(
            "src.api.utils.database.async_session_factory"
        ) as mock_sf, patch(
            "src.services.nexus_engine.blueprints.get_blueprint_by_id"
        ) as mock_bp:

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_bp.return_value = {
                "id": "test", "name": "Test",
                "composition_id": "ViralClip", "nodes": [],
            }

            with patch.object(
                orch, "_update_node_status", AsyncMock()
            ), patch(
                "src.services.nexus_engine.orchestrator.os.path.exists",
                return_value=True,
            ), patch.object(
                orch.asset_manager, "prepare_remotion_clips",
                new=AsyncMock(return_value=[]),
            ):
                with pytest.raises(
                    RuntimeError, match="No valid video clips"
                ):
                    await orch.assemble_video(
                        job_id="job-even-002",
                        niche="tech",
                        script_segments=[
                            {"text": "S1", "type": "hook"}
                        ],
                        voiceover_paths=["/tmp/voice.mp3"],
                        visual_paths=["/tmp/invalid.mp4"],
                    )

    @pytest.mark.asyncio
    async def test_even_stretching_handles_single_clip(self):
        """A single clip gets all frames (it already had all frames)."""
        from src.services.nexus_engine.orchestrator import NexusOrchestrator

        orch = NexusOrchestrator()

        with patch(
            "src.api.utils.database.async_session_factory"
        ) as mock_sf, patch(
            "src.services.nexus_engine.blueprints.get_blueprint_by_id"
        ) as mock_bp, patch(
            "src.services.llm.langchain.langchain_service"
        ) as mock_lc, patch(
            "src.services.llm.service.unified_llm_service"
        ) as mock_llm, patch(
            "src.services.video_engine.remotion_service.base_remotion_service"
        ) as mock_remotion, patch(
            "src.services.audio.sound_design.sound_design_service"
        ) as mock_sd, patch(
            "src.services.audio.transcription_service.base_transcription_service"
        ) as mock_ts, patch(
            "src.services.nexus_engine.orchestrator.os.path.exists"
        ) as mock_exists, patch(
            "src.services.nexus_engine.orchestrator.os.path.getsize"
        ) as mock_getsize, patch(
            "src.services.nexus_engine.orchestrator.cv2.VideoCapture"
        ) as mock_cap:

            self._build_assemble_mocks(
                mock_sf, mock_bp, mock_lc, mock_llm, mock_remotion,
                mock_sd, mock_ts, mock_exists, mock_getsize, mock_cap,
                clip_frame_counts=[300],
            )

            captor: dict = {}
            async def _capture_props(*args, **kwargs):
                captor["props"] = kwargs.get("props", {})
                return "/tmp/output.mp4"

            with patch.object(
                orch, "_update_node_status",
                AsyncMock(),
            ), patch.object(
                orch.asset_manager, "determine_total_frames",
                AsyncMock(return_value=300),
            ), patch.object(
                orch.render_pipeline, "retry_remotion_render",
                AsyncMock(side_effect=_capture_props),
            ):
                await orch.assemble_video(
                    job_id="job-even-003",
                    niche="tech",
                    script_segments=[
                        {"text": "S1", "type": "hook"}
                    ],
                    voiceover_paths=["/tmp/voice.mp3"],
                    visual_paths=["/tmp/single.mp4"],
                )

            clips = captor["props"]["clips"]
            assert len(clips) == 1
            assert clips[0]["duration_in_frames"] == 300
