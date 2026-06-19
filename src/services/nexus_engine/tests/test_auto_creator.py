# Databricks notebook source
"""
Tests for Nexus Engine AutoCreator — Script Generation, Pipeline Orchestration, Circuit Breaker.
"""
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

pytestmark = pytest.mark.filterwarnings(
    "ignore::DeprecationWarning",
    "ignore::UserWarning",
    "ignore::FutureWarning",
    "ignore::PendingDeprecationWarning",
    "ignore::sqlalchemy.exc.MovedIn20Warning"
)


class TestStyleAndCtaControls:
    """Tests for user-facing style aliases and CTA overrides."""

    def test_normalize_nexus_style_accepts_aliases(self):
        from src.services.nexus_engine.auto_creator import normalize_nexus_style

        assert normalize_nexus_style("fast") == "FAST_HYPE"
        assert normalize_nexus_style("story") == "HEARTFELT_NARRATIVE"
        assert normalize_nexus_style("reddit-story") == "REDDIT_STORY"
        assert normalize_nexus_style("CINEMATIC_DOC") == "CINEMATIC_DOC"
        assert normalize_nexus_style("unknown") == "CINEMATIC_DOC"

    def test_apply_cta_override_replaces_existing_cta(self):
        from src.services.nexus_engine.auto_creator import AutoCreator

        script = [
            {"type": "hook", "text": "Open strong"},
            {"type": "cta", "text": "Old CTA"},
        ]

        updated = AutoCreator._apply_cta_override(script, "Join the list", "cta")

        assert updated[-1]["text"] == "Join the list"
        assert updated[-1]["type"] == "cta"
        assert script[-1]["text"] == "Old CTA"

    def test_apply_cta_override_appends_when_missing(self):
        from src.services.nexus_engine.auto_creator import AutoCreator

        updated = AutoCreator._apply_cta_override(
            [{"type": "hook", "text": "Open strong"}],
            "Follow for part two",
            "engagement",
        )

        assert updated[-1]["type"] == "engagement"
        assert updated[-1]["text"] == "Follow for part two"

    def test_apply_cta_override_respects_template_duration(self):
        from src.services.nexus_engine.auto_creator import AutoCreator
        from src.services.nexus_engine.cta_templates import get_cta_template

        template = get_cta_template("standard_subscribe")
        assert template is not None

        updated = AutoCreator._apply_cta_override(
            [{"type": "hook", "text": "Open strong"}],
            template.get_default_text(),
            "cta",
            cta_duration=template.duration_seconds,
        )

        assert updated[-1]["duration"] == template.duration_seconds
        assert updated[-1]["text"] == template.get_default_text()


class TestGenerateViralScript:
    """Tests for AutoCreator.generate_viral_script — script generation with retries."""

    @pytest.mark.asyncio
    async def test_generates_segments_for_topic(self):
        """Happy path: generates segments from topic/niche with style config."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        mock_segment = {
            "text": "Welcome to AI insights",
            "visual_prompt": "Futuristic AI city",
            "mood": "inspirational",
            "type": "narrative"
        }

        with patch.object(creator, '_generate_script_part', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = [mock_segment] * 6
            segments = await creator.generate_viral_script(
                topic="AI Revolution",
                niche="technology",
                duration_seconds=60,
                style="CINEMATIC_DOC"
            )

        assert len(segments) == 6
        assert segments[0]["text"] == "Welcome to AI insights"
        assert segments[0]["type"] == "narrative"
        mock_gen.assert_called_once()

    @pytest.mark.asyncio
    async def test_splits_into_chapters_by_duration(self):
        """Long durations are split into multiple chapters with context carry-over."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        mock_segment = {
            "text": "Chapter content",
            "visual_prompt": "Visual",
            "mood": "neutral",
            "type": "narrative"
        }

        with patch.object(creator, '_generate_script_part', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = [mock_segment] * 6
            segments = await creator.generate_viral_script(
                topic="Deep Dive",
                niche="education",
                duration_seconds=180,  # 3 chapters
                style="ULTIMATE_TUTORIAL"
            )

        assert len(segments) == 18  # 3 chapters * 6 segments
        assert mock_gen.call_count == 3

    @pytest.mark.asyncio
    async def test_passes_context_between_chapters(self):
        """Each chapter receives context from the previous chapter's last segment."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch.object(creator, '_generate_script_part', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = [{
                "text": "Last segment of chapter",
                "visual_prompt": "v",
                "mood": "m",
                "type": "narrative"
            }] * 6

            await creator.generate_viral_script(
                topic="Test", niche="general", duration_seconds=120, style="HEARTFELT_NARRATIVE"
            )

            # Second call should include context from first chapter's last segment
            call_args = mock_gen.call_args_list
            assert len(call_args) == 2
            second_context = call_args[1].kwargs.get("context", "")
            assert "Last segment of chapter" in second_context

    @pytest.mark.asyncio
    async def test_raises_when_no_segments_generated(self):
        """All chapters returning empty lists should raise RuntimeError."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch.object(creator, '_generate_script_part', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = []

            with pytest.raises(RuntimeError, match="returned no segments"):
                await creator.generate_viral_script(
                    topic="Empty", niche="niche", duration_seconds=60
                )

    @pytest.mark.asyncio
    async def test_retry_on_generation_failure(self):
        """_generate_script_part failures are retried (tenacity decorator on caller)."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch.object(creator, '_generate_script_part', new_callable=AsyncMock) as mock_gen:
            mock_gen.side_effect = [Exception("API Error"), [{"text": "Retry worked", "visual_prompt": "v", "mood": "m", "type": "narrative"}]]

            segments = await creator.generate_viral_script(
                topic="Retry Test", niche="general", duration_seconds=60
            )

            assert len(segments) == 1
            assert mock_gen.call_count == 2


class TestGenerateScriptPart:
    """Tests for AutoCreator._generate_script_part — individual chapter generation."""

    @pytest.mark.asyncio
    async def test_calls_intelligence_hub_with_style(self):
        """Calls base_intelligence_service.chat with correct prompt and style."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch("src.services.llm.intelligence_hub.base_intelligence_service") as mock_intel:
            mock_intel.chat = AsyncMock(return_value={
                "response": json.dumps({"segments": [{
                    "text": "Script",
                    "visual_prompt": "Vision",
                    "mood": "moody",
                    "type": "narrative"
                }]})
            })

            segments = await creator._generate_script_part(
                topic="AI", niche="tech", duration=60, chapter_info="Chapter 1",
                style="CINEMATIC_DOC"
            )

            assert len(segments) == 1
            assert segments[0]["text"] == "Script"
            mock_intel.chat.assert_called_once()

            _, kwargs = mock_intel.chat.call_args
            assert kwargs["json_mode"] is True
            assert kwargs["complexity"] == "high"

    @pytest.mark.asyncio
    async def test_parses_list_response(self):
        """Handles LLM returning a list directly instead of {'segments': [...]}."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch("src.services.llm.intelligence_hub.base_intelligence_service") as mock_intel:
            mock_intel.chat = AsyncMock(return_value={
                "response": json.dumps([{
                    "text": "Direct list",
                    "visual_prompt": "vp",
                    "mood": "m",
                    "type": "hook"
                }])
            })

            segments = await creator._generate_script_part(
                topic="T", niche="n", duration=30, chapter_info="C1"
            )

            assert len(segments) == 1
            assert segments[0]["text"] == "Direct list"

    @pytest.mark.asyncio
    async def test_parses_dict_with_script_key(self):
        """Handles LLM returning {'script': [...]} instead of {'segments': [...]}."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch("src.services.llm.intelligence_hub.base_intelligence_service") as mock_intel:
            mock_intel.chat = AsyncMock(return_value={
                "response": json.dumps({"script": [{
                    "text": "From script key",
                    "visual_prompt": "vp",
                    "mood": "m",
                    "type": "body"
                }]})
            })

            segments = await creator._generate_script_part(
                topic="T", niche="n", duration=30, chapter_info="C1"
            )

            assert len(segments) == 1
            assert segments[0]["text"] == "From script key"

    @pytest.mark.asyncio
    async def test_raises_on_api_error(self):
        """API errors propagate as exceptions."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch("src.services.llm.intelligence_hub.base_intelligence_service") as mock_intel:
            mock_intel.chat = AsyncMock(side_effect=ConnectionError("API unreachable"))

            with pytest.raises(ConnectionError, match="API unreachable"):
                await creator._generate_script_part(
                    topic="T", niche="n", duration=30, chapter_info="C1"
                )


class TestCreateCinemaVideo:
    """Tests for AutoCreator.create_cinema_video — full pipeline orchestration."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self):
        """CircuitBreaker raises RuntimeError when OPEN."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        creator.breaker.state = "OPEN"  # Force circuit open

        with pytest.raises(RuntimeError, match="temporarily unavailable"):
            await creator.create_cinema_video(
                job_id="job-001", topic="T", niche="n"
            )

    @pytest.mark.asyncio
    async def test_full_pipeline_happy_path(self):
        """Full pipeline: ingress → cognition → synthesis → egress with output path."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        mock_segment = {
            "text": "Test segment",
            "visual_prompt": "Test visual",
            "mood": "calm",
            "type": "narrative"
        }

        with patch.multiple(
            creator,
            generate_viral_script=AsyncMock(return_value=[mock_segment]),
            _source_visual_assets=AsyncMock(return_value=["/tmp/vis_0.mp4"]),
            _generate_voiceovers=AsyncMock(return_value=["/tmp/voice_0.mp3"]),
        ), \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("sqlalchemy.select"), \
             patch("src.api.utils.models.NexusJobDB"), \
             patch("src.services.nexus_engine.orchestrator.base_nexus_service") as mock_nexus:

            mock_nexus.assemble_video = AsyncMock(return_value="/tmp/output.mp4")

            # DB session mock
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            output_path = await creator.create_cinema_video(
                job_id="job-001", topic="AI", niche="tech",
                style="CINEMATIC_DOC"
            )

            assert output_path == "/tmp/output.mp4"
            mock_nexus.assemble_video.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_with_existing_script(self):
        """Uses provided script instead of generating one."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        script = [{
            "text": "Provided script",
            "visual_prompt": "Provided visual",
            "mood": "exciting",
            "type": "hook"
        }]

        with patch.object(creator, 'generate_viral_script', new_callable=AsyncMock) as mock_gen, \
             patch.object(creator, '_source_visual_assets', new_callable=AsyncMock, return_value=["/tmp/v.mp4"]), \
             patch.object(creator, '_generate_voiceovers', new_callable=AsyncMock, return_value=["/tmp/vc.mp3"]), \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.api.utils.models.NexusJobDB"), \
             patch("sqlalchemy.select"):

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            with patch("src.services.nexus_engine.orchestrator.base_nexus_service") as mock_nexus:
                mock_nexus.assemble_video = AsyncMock(return_value="/tmp/output.mp4")

                await creator.create_cinema_video(
                    job_id="job-002", topic="AI", niche="tech",
                    script=script
                )

                # Should NOT call generate_viral_script when script is provided
                mock_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_pipeline_fails_without_visuals(self):
        """Pipeline raises ValueError when no visual assets sourced."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch.object(creator, 'generate_viral_script', new_callable=AsyncMock, return_value=[{"text": "t", "visual_prompt": "v", "mood": "m", "type": "n"}]), \
             patch.object(creator, '_source_visual_assets', new_callable=AsyncMock, return_value=[]), \
             patch.object(creator, '_generate_voiceovers', new_callable=AsyncMock, return_value=["/tmp/v.mp3"]), \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock):

            with pytest.raises(ValueError, match="Asset sourcing failed"):
                await creator.create_cinema_video(
                    job_id="job-003", topic="AI", niche="tech"
                )

    @pytest.mark.asyncio
    async def test_assembly_failure_records_circuit_failure(self):
        """Circuit breaker records failure when assembly fails."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        assert creator.breaker.state == "CLOSED"

        with patch.object(creator, '_create_cinema_video_inner', new_callable=AsyncMock, side_effect=RuntimeError("Assembly failed")), \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock):

            with pytest.raises(RuntimeError, match="Assembly failed"):
                await creator.create_cinema_video(
                    job_id="job-004", topic="T", niche="n"
                )

            # Circuit breaker should have recorded the failure
            assert creator.breaker.failure_count >= 1

    @pytest.mark.asyncio
    async def test_saves_output_to_db_at_egress(self):
        """Output path is saved to NexusJobDB.job_metadata at egress."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch.multiple(
            creator,
            generate_viral_script=AsyncMock(return_value=[{"text": "t", "visual_prompt": "v", "mood": "m", "type": "n"}]),
            _source_visual_assets=AsyncMock(return_value=["/tmp/v.mp4"]),
            _generate_voiceovers=AsyncMock(return_value=["/tmp/vc.mp3"]),
        ), \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.api.utils.models.NexusJobDB"), \
             patch("sqlalchemy.select"):

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session
            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            with patch("src.services.nexus_engine.orchestrator.base_nexus_service") as mock_nexus:
                mock_nexus.assemble_video = AsyncMock(return_value="/tmp/output.mp4")

                await creator.create_cinema_video(
                    job_id="job-005", topic="T", niche="n"
                )

            # Verify output path was saved in the second DB interaction (egress save)
            assert mock_job.job_metadata.get("output_path") == "/tmp/output.mp4"


class TestPublishJob:
    """Tests for AutoCreator.publish_job — publishing to platforms."""

    @pytest.mark.asyncio
    async def test_publishes_to_requested_platforms(self):
        """Publishes to each requested platform and returns results."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.api.utils.models.NexusJobDB"), \
             patch("sqlalchemy.select"):

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session

            mock_job = MagicMock()
            mock_job.user_id = "user-1"
            mock_job.job_metadata = {
                "output_path": "/tmp/output.mp4",
                "topic": "AI Revolution"
            }
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            with patch("src.services.distribution.publishing.base_publishing_service") as mock_pub:
                mock_pub.publish_to_platform = AsyncMock(return_value={"status": "published", "url": "https://youtube.com/watch?v=123"})

                results = await creator.publish_job("job-001", platforms=["youtube", "instagram"])

                assert results["youtube"]["status"] == "published"
                assert results["instagram"]["status"] == "published"
                assert mock_pub.publish_to_platform.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_partial_platform_failure(self):
        """One platform failing doesn't prevent others from being published."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.api.utils.models.NexusJobDB"), \
             patch("sqlalchemy.select"):

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session

            mock_job = MagicMock()
            mock_job.user_id = "user-1"
            mock_job.job_metadata = {"output_path": "/tmp/output.mp4"}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            with patch("src.services.distribution.publishing.base_publishing_service") as mock_pub:
                mock_pub.publish_to_platform = AsyncMock(side_effect=[
                    {"status": "published"},
                    Exception("Instagram API down")
                ])

                results = await creator.publish_job("job-002", platforms=["youtube", "instagram"])

                assert results["youtube"]["status"] == "published"
                assert results["instagram"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_raises_when_job_not_ready(self):
        """Raises ValueError when job has no output_path."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.api.utils.models.NexusJobDB"), \
             patch("sqlalchemy.select"):

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session

            mock_job = MagicMock()
            mock_job.job_metadata = {}  # No output_path
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            with pytest.raises(ValueError, match="not ready for publishing"):
                await creator.publish_job("job-003")

    @pytest.mark.asyncio
    async def test_saves_publish_results_to_db(self):
        """Publish results are persisted to job_metadata."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()

        with patch("src.api.utils.database.async_session_factory") as mock_sf, \
             patch("src.api.utils.models.NexusJobDB"), \
             patch("sqlalchemy.select"):

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_sf.return_value = mock_session

            mock_job = MagicMock()
            mock_job.user_id = "user-1"
            mock_job.job_metadata = {"output_path": "/tmp/output.mp4"}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            with patch("src.services.distribution.publishing.base_publishing_service") as mock_pub:
                mock_pub.publish_to_platform = AsyncMock(return_value={"status": "published"})

                await creator.publish_job("job-004", platforms=["youtube"])

            assert mock_job.job_metadata["publish_results"]["youtube"]["status"] == "published"


class TestHelperMethods:
    """Tests for AutoCreator helper methods — _source_visual_assets, _generate_voiceovers."""

    @pytest.mark.asyncio
    async def test_source_visual_assets(self):
        """Fetches and downloads stock video for each segment's visual_prompt."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        creator._vision_audit = AsyncMock(return_value={"passed": True, "score": 90})
        segments = [
            {"text": "S1", "visual_prompt": "Sunset beach", "mood": "calm", "type": "hook"},
            {"text": "S2", "visual_prompt": "Mountain peaks", "mood": "epic", "type": "body"},
        ]

        with patch("src.services.video_engine.stock_service.base_stock_service") as mock_stock:
            mock_stock.fetch_b_roll = AsyncMock(side_effect=[
                ["https://example.com/v1.mp4"],
                ["https://example.com/v2.mp4"],
            ])
            mock_stock.download_stock_video = AsyncMock(side_effect=[
                "/tmp/stock_1.mp4",
                "/tmp/stock_2.mp4",
            ])

            paths = await creator._source_visual_assets(segments, "job-001", "nature", engine="cloud", style="CINEMATIC_DOC")

            assert len(paths) == 2
            assert paths[0] == "/tmp/stock_1.mp4"
            assert paths[1] == "/tmp/stock_2.mp4"
            assert mock_stock.fetch_b_roll.call_count == 2
            assert mock_stock.download_stock_video.call_count == 2

    @pytest.mark.asyncio
    async def test_source_visual_assets_handles_empty_results(self):
        """Skips segments where no stock footage is returned."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        segments = [
            {"text": "S1", "visual_prompt": "Rare thing", "mood": "m", "type": "hook"},
        ]

        with patch("src.services.video_engine.stock_service.base_stock_service") as mock_stock:
            mock_stock.fetch_b_roll = AsyncMock(return_value=[])
            mock_stock.download_stock_video = AsyncMock(return_value=None)

            paths = await creator._source_visual_assets(segments, "job-001", "niche", engine="cloud", style="CINEMATIC_DOC")

            assert len(paths) == 0

    @pytest.mark.asyncio
    async def test_generate_voiceovers(self):
        """Generates voiceover for each segment with text."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        segments = [
            {"text": "Hello world", "visual_prompt": "v", "mood": "m", "type": "hook"},
            {"text": "Second line", "visual_prompt": "v", "mood": "m", "type": "body"},
        ]

        with patch("src.services.audio.voiceover.base_voiceover_service") as mock_voice:
            mock_voice.generate_voiceover = AsyncMock(side_effect=[
                "/tmp/voice_1.mp3",
                "/tmp/voice_2.mp3",
            ])

            paths = await creator._generate_voiceovers(segments, "job-001")

            assert len(paths) == 2
            assert paths[0] == "/tmp/voice_1.mp3"
            assert paths[1] == "/tmp/voice_2.mp3"
            assert mock_voice.generate_voiceover.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_voiceovers_skips_empty_text(self):
        """Skips segments with no text content."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        segments = [
            {"text": "", "visual_prompt": "v", "mood": "m", "type": "hook"},
            {"text": "Real text", "visual_prompt": "v", "mood": "m", "type": "body"},
        ]

        with patch("src.services.audio.voiceover.base_voiceover_service") as mock_voice:
            mock_voice.generate_voiceover = AsyncMock(return_value="/tmp/voice.mp3")

            paths = await creator._generate_voiceovers(segments, "job-001")

            assert len(paths) == 1  # Only the segment with text


class TestCircuitBreakerIntegration:
    """Tests for CircuitBreaker integration with AutoCreator."""

    def test_init_creates_breaker(self):
        """AutoCreator initializes with a closed circuit breaker."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        assert creator.breaker is not None
        assert creator.breaker.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_success_records_success_on_breaker(self):
        """Successful pipeline records success on the circuit breaker."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        initial_failures = creator.breaker.failure_count

        with patch.object(creator, '_create_cinema_video_inner', new_callable=AsyncMock, return_value="/tmp/output.mp4"), \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock):

            await creator.create_cinema_video(job_id="job-001", topic="T", niche="n")

            # Failure count should not have increased
            assert creator.breaker.failure_count == initial_failures

    @pytest.mark.asyncio
    async def test_three_failures_opens_circuit(self):
        """Three consecutive failures open the circuit breaker."""
        from src.services.nexus_engine.auto_creator import AutoCreator

        creator = AutoCreator()
        creator.breaker.failure_threshold = 3

        with patch.object(creator, '_create_cinema_video_inner', new_callable=AsyncMock, side_effect=RuntimeError("fail")), \
             patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock):

            for i in range(3):
                try:
                    await creator.create_cinema_video(job_id=f"job-{i}", topic="T", niche="n")
                except RuntimeError:
                    pass

            # Circuit should be open after 3 failures
            assert creator.breaker.state == "OPEN"
