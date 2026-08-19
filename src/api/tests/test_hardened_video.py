import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock
from src.api.config import settings
from src.services.video_engine.models.wan_inference import generate_wan_api
from src.services.video_engine.models.mochi_inference import generate_mochi_api
from src.services.video_engine.processor import VideoProcessor

@pytest.fixture
def mock_video_dir(tmp_path):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return str(output_dir)

@pytest.mark.anyio
class TestHardenedVideoInference:
    def test_wan_api_request_structure(self, mock_video_dir):
        """Test that Wan API sends the correct payload to the remote GPU node."""
        mock_prompt = "A sunset over the mountains"

        with patch.object(settings, "RENDER_NODE_URL", "http://gpu-node:8000"):
            with patch("requests.post") as mock_post:
                mock_post.return_value = MagicMock(
                    status_code=200,
                    headers={"Content-Type": "video/mp4"},
                    content=b"fake-video-bytes"
                )

                job_id, path = generate_wan_api(mock_prompt, mock_video_dir)

                assert "wan_api_" in job_id
                assert os.path.exists(path)

                # Check payload
                _, kwargs = mock_post.call_args
                assert kwargs["json"]["prompt"] == mock_prompt
                assert kwargs["json"]["model"] == "wan-2.2-t2v"

    def test_mochi_api_request_structure(self, mock_video_dir):
        """Test that Mochi API sends the correct payload to the remote GPU node."""
        mock_prompt = "A cat running in a field"

        with patch.object(settings, "RENDER_NODE_URL", "http://gpu-node:8000"):
            with patch("requests.post") as mock_post:
                mock_post.return_value = MagicMock(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    json=lambda: {"download_url": "http://gpu-node/dl/test.mp4"}
                )
                with patch("requests.get") as mock_get:
                    mock_get.return_value = MagicMock(status_code=200, content=b"fake-video-bytes")

                    job_id, path = generate_mochi_api(mock_prompt, mock_video_dir)

                    assert "mochi_api_" in job_id
                    assert os.path.exists(path)
                    assert mock_get.called

@pytest.mark.anyio
class TestHardenedVideoProcessor:
    async def test_assemble_story_downloads_assets(self, tmp_path):
        """Test that VideoProcessor downloads remote assets during assembly."""
        processor = VideoProcessor()
        output_path = str(tmp_path / "final.mp4")

        # scenes should be a list directly
        scenes = [
            {"video_uri": "http://example.com/scene1.mp4", "audio_uri": "http://example.com/audio1.mp3"},
            {"video_uri": "http://example.com/scene2.mp4", "audio_uri": "http://example.com/audio2.mp3"}
        ]

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(status_code=200, content=b"fake-asset-data")

            # Mock moviepy to avoid real processing
            with patch("moviepy.video.io.VideoFileClip.VideoFileClip", MagicMock()):
                with patch("moviepy.video.compositing.concatenate_videoclips", MagicMock()) as mock_concat:
                    mock_final = MagicMock()
                    mock_concat.return_value = mock_final

                    # Also mock AudioFileClip as it's imported inside the method
                    with patch("moviepy.audio.io.AudioFileClip.AudioFileClip", MagicMock()):
                        try:
                            await processor.assemble_story(scenes, output_path)
                        except Exception:
                            pass

                        assert mock_get.call_count >= 2
                        args, _ = mock_get.call_args_list[0]
                        assert "http://example.com/scene1.mp4" in args[0]
