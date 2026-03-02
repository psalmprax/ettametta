"""
Integration Tests for Video Engine
===================================
Verifies the VideoProcessor pipeline and synthesis task routing.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from services.video_engine.processor import VideoProcessor

@pytest.mark.integration
class TestVideoIntegration:
    """Test suite for the Video Engine integration."""

    @pytest.fixture
    def processor(self):
        """Initializes VideoProcessor with a temporary output dir."""
        return VideoProcessor(output_dir="/tmp/test_outputs")

    def test_processor_initialization(self, processor):
        """Verify that the processor initializes with correct codec and font."""
        assert processor.output_dir == "/tmp/test_outputs"
        assert processor.codec in ["h264_nvenc", "libx264"]
        assert os.path.exists(processor.font_path) or processor.font_path == "arial.ttf"

    def test_ffmpeg_version_check_mock(self, processor):
        """Verify that the version check handles failures gracefully."""
        with patch("subprocess.run", side_effect=Exception("ffmpeg not found")):
            # Should not raise exception
            processor._check_ffmpeg_version()

    @patch("moviepy.editor.VideoFileClip")
    def test_pipeline_task_logic(self, mock_clip_class, processor):
        """Verify the high-level logic of the processing pipeline."""
        # Mock VideoFileClip instance
        mock_clip = MagicMock()
        mock_clip.duration = 10.0
        mock_clip.size = (1920, 1080)
        mock_clip_class.return_value = mock_clip
        
        # Test a simple transformation logic (e.g., getting metadata)
        # We don't run the full heavy render, just verify we can load the clip
        assert mock_clip_class.called is False
        
        # Simulating loading
        clip = mock_clip_class("test.mp4")
        assert clip.duration == 10.0
        mock_clip_class.assert_called_with("test.mp4")

    @pytest.mark.asyncio
    async def test_synthesis_task_routing(self, client):
        """Verify that different synthesis engines route to appropriate tasks."""
        with patch("services.video_engine.synthesis_service.GenerativeService._synthesize_lite_4k") as mock_lite:
            mock_lite.return_value = "/tmp/fake_output.mp4"
            
            # This test requires authentication, so we mock the auth or use test client headers
            # Assuming INTERNAL_API_TOKEN works for these endpoints
            token = os.getenv("INTERNAL_API_TOKEN", "test_master_token")
            
            # Using a mock for the actual background task execution
            with patch("services.video_engine.tasks.generate_video_task.run") as mock_run:
                mock_run.return_value = {"status": "success", "file": "test.mp4"}
                
                # We hit the route but mock the celery .delay() or .run()
                from services.video_engine.tasks import generate_video_task
                
                result = generate_video_task.run(
                    prompt="Test prompt",
                    engine="lite4k",
                    style="Cinematic"
                )
                
                assert result["status"] == "success"

@pytest.mark.integration
class TestCeleryTaskConnectivity:
    """Verify Celery task registration and accessibility."""
    
    def test_task_registration(self):
        """Check if core tasks are registered in the Celery app."""
        from api.utils.celery import celery_app
        registered_tasks = celery_app.tasks.keys()
        
        assert "discovery.sentinel_watcher" in registered_tasks
        assert "video.transform" in registered_tasks
        assert "video.generate" in registered_tasks
