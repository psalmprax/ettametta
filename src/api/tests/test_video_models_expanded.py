import pytest
import requests
import importlib
from unittest.mock import patch, MagicMock
import src.services.video_engine.models.wan_inference as wan_mod
import src.services.video_engine.models.mochi_inference as mochi_mod
import src.services.video_engine.models.hunyuan_inference as hun_mod
import src.services.video_engine.models.ltx_video_inference as ltx_mod
import src.services.video_engine.models.cogvideo_inference as cog_mod

@pytest.fixture
def mock_output_dir(tmp_path):
    d = tmp_path / "outputs"
    d.mkdir()
    return str(d)

class TestVideoModels480p:
    def setup_method(self):
        self.mock_resp = MagicMock(status_code=200, content=b"fake")
        self.mock_resp.headers = {"Content-Type": "video/mp4"}
        # Force reload to ensure top-level imports are fresh for patching
        importlib.reload(wan_mod)
        importlib.reload(mochi_mod)

    def test_wan_payload_enforces_480p(self, mock_output_dir):
        """Verify Wan remote payload contains 480p resolution."""
        with patch.object(wan_mod, "settings") as mock_settings:
            mock_settings.RENDER_NODE_URL = "http://gpu-node:8000"
            with patch.object(wan_mod.requests, "post") as mock_post:
                mock_post.return_value = self.mock_resp
                wan_mod.generate_wan_t2v("A sunset", output_dir=mock_output_dir)
                assert mock_post.called
                payload = mock_post.call_args[1]["json"]
                assert payload["resolution"] == "480p"

    def test_mochi_payload_enforces_480p(self, mock_output_dir):
        """Verify Mochi remote payload contains 480p resolution."""
        with patch.object(mochi_mod, "settings") as mock_settings:
            mock_settings.RENDER_NODE_URL = "http://gpu-node:8000"
            with patch.object(mochi_mod.requests, "post") as mock_post:
                mock_post.return_value = self.mock_resp
                mochi_mod.generate_mochi("A cat", output_dir=mock_output_dir)
                assert mock_post.called
                payload = mock_post.call_args[1]["json"]
                assert payload["resolution"] == "480p"
                assert payload["height"] == 480

    def test_hunyuan_payload_enforces_480p(self, mock_output_dir):
        """Verify Hunyuan remote payload contains 480p resolution."""
        with patch.object(hun_mod, "settings") as mock_settings:
            mock_settings.RENDER_NODE_URL = "http://gpu-node:8000"
            with patch.object(hun_mod.requests, "post") as mock_post:
                mock_post.return_value = self.mock_resp
                hun_mod.generate_hunyuan("A mountain", output_dir=mock_output_dir)
                assert mock_post.called
                payload = mock_post.call_args[1]["json"]
                assert payload["resolution"] == "480p"

    def test_ltx_payload_enforces_480p(self, mock_output_dir):
        """Verify LTX remote payload contains 480p resolution."""
        with patch.object(ltx_mod, "settings") as mock_settings:
            mock_settings.RENDER_NODE_URL = "http://gpu-node:8000"
            with patch.object(ltx_mod.requests, "post") as mock_post:
                mock_post.return_value = self.mock_resp
                ltx_mod.generate_ltx("A city", output_dir=mock_output_dir)
                assert mock_post.called
                payload = mock_post.call_args[1]["json"]
                assert payload["resolution"] == "480p"

    def test_cogvideo_payload_enforces_480p(self, mock_output_dir):
        """Verify CogVideo remote payload contains 480p resolution."""
        with patch.object(cog_mod, "settings") as mock_settings:
            mock_settings.RENDER_NODE_URL = "http://gpu-node:8000"
            with patch.object(cog_mod.requests, "post") as mock_post:
                mock_post.return_value = self.mock_resp
                cog_mod.generate_cogvideo("A space battle", output_dir=mock_output_dir)
                assert mock_post.called
                payload = mock_post.call_args[1]["json"]
                assert payload["resolution"] == "480p"
