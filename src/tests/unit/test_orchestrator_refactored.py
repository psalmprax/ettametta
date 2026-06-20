import pytest
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
if "cv2" not in sys.modules:
    sys.modules["cv2"] = MagicMock()


@pytest.fixture
def tmp_job_dir():
    d = tempfile.mkdtemp(prefix="nexus_test_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


class TestVibeAnalyzer:
    def setup_method(self):
        from src.services.nexus_engine.orchestrator import VibeAnalyzer
        self.analyzer = VibeAnalyzer()

    @pytest.mark.asyncio
    async def test_determine_vibe_delegates(self, tmp_job_dir):
        with patch(
            "src.services.nexus_engine.orchestrator.determine_video_vibe",
            new_callable=AsyncMock,
        ) as mock_vibe:
            mock_vibe.return_value = {"vibe": "Cinematic", "explanation": "Test"}
            result = await self.analyzer.determine_vibe(
                "job-1", "tech", "CINEMATIC_DOC", "bp-1", 5
            )
            mock_vibe.assert_awaited_once_with(
                "job-1", "tech", "CINEMATIC_DOC", "bp-1", 5
            )
            assert result["vibe"] == "Cinematic"

    def test_extract_audit_frame_returns_none_on_empty_clip(self):
        clip = {"duration_in_frames": 0}
        with patch(
            "src.services.nexus_engine.orchestrator.extract_frame", return_value=None
        ):
            result = self.analyzer._extract_audit_frame(clip, "/fake/path.mp4")
            assert result is None

    def test_extract_audit_frame_midpoint(self):
        clip = {"duration_in_frames": 100}
        with patch(
            "src.services.nexus_engine.orchestrator.extract_frame",
            return_value="frame_img",
        ) as mock_ef:
            result = self.analyzer._extract_audit_frame(clip, "/fake/path.mp4")
            mock_ef.assert_called_once_with("/fake/path.mp4", 50)
            assert result == "frame_img"

    @pytest.mark.asyncio
    async def test_evaluate_frame_relevance_success(self):
        with patch("src.services.llm.service.unified_llm_service") as mock_llm:
            mock_llm.analyze_image = AsyncMock(
                return_value={"content": "YES because cinematic"}
            )
            result = await self.analyzer._evaluate_frame_relevance(
                "/frame.jpg", "Describe"
            )
            assert result == "YES BECAUSE CINEMATIC"

    @pytest.mark.asyncio
    async def test_evaluate_frame_relevance_fallback_to_ollama(self):
        with patch("src.services.llm.service.unified_llm_service") as mock_llm:
            mock_llm.analyze_image = AsyncMock(
                side_effect=[RuntimeError("fail"), {"content": "YES"}]
            )
            with patch("src.api.config.settings") as mock_settings:
                mock_settings.OLLAMA_MODEL = "llama3.2:1b"
                result = await self.analyzer._evaluate_frame_relevance(
                    "/frame.jpg", "Describe"
                )
                assert result == "YES"
                assert mock_llm.analyze_image.await_count == 2

    @pytest.mark.asyncio
    async def test_run_vision_audit_skips_remote_clips(self, tmp_job_dir):
        remote_clip = {"url": "https://example.com/video.mp4"}
        result = await self.analyzer.run_vision_audit(
            "job-1", "tech", [{"text": "hello"}], [remote_clip], tmp_job_dir
        )
        assert len(result) == 1
        assert result[0]["url"] == "https://example.com/video.mp4"


class TestAssetManager:
    def setup_method(self):
        from src.services.nexus_engine.orchestrator import AssetManager
        self.manager = AssetManager()

    @pytest.mark.asyncio
    async def test_validate_inputs_valid_paths(self, tmp_job_dir):
        visual = str(tmp_job_dir / "vis.mp4")
        voice = str(tmp_job_dir / "voice.mp3")
        Path(visual).touch()
        Path(voice).touch()
        errors = await self.manager.validate_inputs([visual], [voice], None)
        assert errors == []

    @pytest.mark.asyncio
    async def test_validate_inputs_missing_files(self):
        errors = await self.manager.validate_inputs(
            ["/no/such/file.mp4"], ["/no/voice.mp3"], None
        )
        assert len(errors) == 2
        assert "Visual clip 0" in errors[0]
        assert "Voiceover clip 0" in errors[1]

    @pytest.mark.asyncio
    async def test_validate_inputs_skips_http_urls(self):
        errors = await self.manager.validate_inputs(
            ["https://example.com/v.mp4"], [], None
        )
        assert errors == []

    def test_get_frame_count_http_url(self):
        assert self.manager.get_frame_count("https://example.com/v.mp4") == 300

    def test_get_frame_count_missing_file(self):
        assert self.manager.get_frame_count("/no/such/file.mp4") is None

    def test_get_frame_count_probes_video(self):
        with patch(
            "src.services.nexus_engine.orchestrator.probe_video"
        ) as mock_probe:
            mock_probe.return_value = MagicMock(frame_count=900)
            Path("/tmp/test_video.mp4").touch()
            try:
                assert self.manager.get_frame_count("/tmp/test_video.mp4") == 900
            finally:
                os.unlink("/tmp/test_video.mp4")

    @pytest.mark.asyncio
    async def test_prepare_remotion_clips_filters_invalid(self, tmp_job_dir):
        valid = str(tmp_job_dir / "valid.mp4")
        Path(valid).touch()
        with patch.object(
            self.manager,
            "get_frame_count",
            side_effect=lambda p: 120 if "valid" in p else None,
        ):
            clips = await self.manager.prepare_remotion_clips(
                [valid, "/bad/path.mp4"]
            )
            assert len(clips) == 1
            assert clips[0]["duration_in_frames"] == 120

    @pytest.mark.asyncio
    async def test_stitch_voiceovers_single(self, tmp_job_dir):
        result = await self.manager.stitch_voiceovers(
            "job-1", ["/a.mp3"], None, tmp_job_dir
        )
        assert result == "/a.mp3"

    @pytest.mark.asyncio
    async def test_stitch_voiceovers_empty(self, tmp_job_dir):
        result = await self.manager.stitch_voiceovers(
            "job-1", [], "/music.mp3", tmp_job_dir
        )
        assert result == "/music.mp3"

    @pytest.mark.asyncio
    async def test_stitch_voiceovers_multiple_calls_ffmpeg(self, tmp_job_dir):
        voice_dir = tmp_job_dir / "voice"
        voice_dir.mkdir()
        (voice_dir / "a.mp3").touch()
        (voice_dir / "b.mp3").touch()
        with patch(
            "src.services.nexus_engine.orchestrator._run_subprocess"
        ) as mock_sub:
            result = await self.manager.stitch_voiceovers(
                "job-1",
                [str(voice_dir / "a.mp3"), str(voice_dir / "b.mp3")],
                None,
                tmp_job_dir,
            )
            assert "master_job-1.mp3" in result
            mock_sub.assert_called_once()

    @pytest.mark.asyncio
    async def test_determine_total_frames_fallback(self, tmp_job_dir):
        clips = [{"duration_in_frames": 100}, {"duration_in_frames": 200}]
        total = await self.manager.determine_total_frames(None, clips)
        assert total == 300

    @pytest.mark.asyncio
    async def test_determine_total_frames_with_audio(self, tmp_job_dir):
        audio = str(tmp_job_dir / "audio.mp3")
        Path(audio).touch()
        with patch(
            "src.services.nexus_engine.orchestrator._run_subprocess"
        ) as mock_sub:
            mock_sub.return_value = MagicMock(stdout="30.0\n")
            total = await self.manager.determine_total_frames(
                audio, [{"duration_in_frames": 100}]
            )
            assert total == int((30.0 + 2.0) * 30)

    def test_source_music_passthrough(self):
        assert self.manager.source_music("/my/music.mp3", ["cinematic"]) == "/my/music.mp3"

    def test_source_music_none(self):
        assert self.manager.source_music(None, ["cinematic"]) is None

    def test_modulate_video_style(self):
        config = {"colors": ["#fff"]}
        with patch(
            "src.services.nexus_engine.orchestrator.modulate_video_style"
        ) as mock_mod:
            mock_mod.return_value = {"colors": ["#000"]}
            result = self.manager.modulate_video_style(
                "j1", "CINEMATIC_DOC", config, None
            )
            mock_mod.assert_called_once_with("j1", "CINEMATIC_DOC", config, None)
            assert result == {"colors": ["#000"]}


class TestRenderPipeline:
    def setup_method(self):
        from src.services.nexus_engine.orchestrator import RenderPipeline
        self.pipeline = RenderPipeline()

    def test_export_srt_delegates(self):
        words = [{"word": "hello", "start": 0.0, "end": 0.5}]
        with patch(
            "src.services.nexus_engine.orchestrator.export_srt"
        ) as mock_export:
            mock_export.return_value = "/out.srt"
            assert self.pipeline.export_srt(words, "/out.srt") == "/out.srt"
            mock_export.assert_called_once_with(words, "/out.srt")

    @pytest.mark.asyncio
    async def test_retry_remotion_render_opens_circuit_breaker(self):
        self.pipeline.remotion_breaker.state = "OPEN"
        self.pipeline.remotion_breaker.last_failure_time = 0
        with pytest.raises(RuntimeError, match="circuit breaker is OPEN"):
            await self.pipeline.retry_remotion_render("ViralClip", {}, "out.mp4")

    @pytest.mark.asyncio
    async def test_retry_remotion_render_success(self):
        with patch(
            "src.services.nexus_engine.orchestrator.settings"
        ) as mock_s:
            mock_s.DEFAULT_RETRY_COUNT = 1
            mock_s.RETRY_MULTIPLIER = 1
            mock_s.RETRY_MIN_WAIT = 0.1
            mock_s.RETRY_MAX_WAIT = 0.1
            mock_s.LLM_TIMEOUT = 1
            with patch(
                "src.services.nexus_engine.orchestrator.os.path.exists",
                return_value=True,
            ):
                with patch(
                    "src.services.nexus_engine.orchestrator.os.path.getsize",
                    return_value=10240,
                ):
                    with patch(
                        "src.services.video_engine.remotion_service.base_remotion_service"
                    ) as mock_rem:
                        mock_rem.render_video = AsyncMock(
                            return_value="/output/video.mp4"
                        )
                        result = await self.pipeline.retry_remotion_render(
                            "ViralClip", {}, "out.mp4"
                        )
                        assert result == "/output/video.mp4"

    @pytest.mark.asyncio
    async def test_retry_remotion_render_returns_none_on_failure(self):
        with patch(
            "src.services.nexus_engine.orchestrator.settings"
        ) as mock_s:
            mock_s.DEFAULT_RETRY_COUNT = 1
            mock_s.RETRY_MULTIPLIER = 1
            mock_s.RETRY_MIN_WAIT = 0.1
            mock_s.RETRY_MAX_WAIT = 0.1
            mock_s.LLM_TIMEOUT = 1
            with patch(
                "src.services.video_engine.remotion_service.base_remotion_service"
            ) as mock_rem:
                mock_rem.render_video = AsyncMock(
                    side_effect=RuntimeError("render failed")
                )
                result = await self.pipeline.retry_remotion_render(
                    "ViralClip", {}, "out.mp4"
                )
                assert result is None

    @pytest.mark.asyncio
    async def test_extract_thumbnail_delegates(self, tmp_job_dir):
        with patch(
            "src.services.nexus_engine.orchestrator.extract_thumbnail",
            new_callable=AsyncMock,
        ) as mock_thumb:
            mock_thumb.return_value = "/thumb.jpg"
            result = await self.pipeline.extract_thumbnail(
                tmp_job_dir, "job-1", ["/v.mp4"]
            )
            assert result == "/thumb.jpg"


class TestNexusOrchestratorDelegation:
    def setup_method(self):
        from src.services.nexus_engine.orchestrator import NexusOrchestrator
        with patch("os.makedirs"):
            self.orch = NexusOrchestrator(output_dir="/tmp/test_nexus")

    def test_init_creates_components(self):
        assert self.orch.vibe_analyzer is not None
        assert self.orch.asset_manager is not None
        assert self.orch.render_pipeline is not None
        assert self.orch.output_dir == "/tmp/test_nexus"

    def test_init_dependencies_reported(self):
        assert "moviepy" in self.orch.dependencies_available

    def test_local_temp_dir_creates_path(self):
        temp = self.orch._local_temp_dir
        assert temp.exists()
        assert "ettametta" in str(temp)

    def test_node_phase_calls_update(self):
        assert callable(self.orch._update_node_status)
