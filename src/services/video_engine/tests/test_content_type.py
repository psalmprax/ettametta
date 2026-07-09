"""
Unit tests for frame-based content-type classification.

Covers:
- VLMService.analyze_content_type aggregation (talking_head / tutorial_demo /
  person_heavy / scene / poor_quality mapping) without touching VLM/ffmpeg.
- VideoEligibilityChecker.check_eligibility content-type branching, including
  the previously-dead `person_present` branch that was realigned to the
  producer's real `person_heavy` vocabulary.
"""
from unittest.mock import patch

import pytest

from src.services.video_engine.vlm_service import VLMService
from src.services.video_engine.video_eligibility import VideoEligibilityChecker


def _frame(activity: str, visible: bool = True, broll: bool = True) -> dict:
    return {
        "person_visible": visible,
        "person_activity": activity,
        "usable_as_broll": broll,
        "visual_content": "office",
        "mood": "professional",
    }


class TestAnalyzeContentType:
    """Aggregation logic ported from the deleted VideoContentAnalyzer."""

    @pytest.fixture
    def service(self):
        with patch("src.services.video_engine.vlm_service.get_secret", return_value=None):
            with patch("src.services.video_engine.vlm_service.settings") as s:
                s.DEFAULT_VLM_MODEL = "gemini-1.5-flash"
                s.RENDER_NODE_URL = None
                return VLMService()

    async def test_talking_head_when_three_plus_speaking_frames(self, service):
        frames = [
            _frame("speaking_to_camera"),
            _frame("speaking_to_camera"),
            _frame("speaking_to_camera"),
            _frame("demonstrating"),
            _frame("demonstrating"),
        ]
        with patch.object(service, "_sample_keyframes", return_value=["f0", "f1", "f2", "f3", "f4"]):
            with patch.object(service, "_classify_person_activity", return_value=frames):
                result = await service.analyze_content_type("dummy.mp4")
        assert result["content_type"] == "talking_head"
        assert result["usable"] is False
        assert result["has_visible_speaker"] is True

    async def test_tutorial_demo_with_two_demonstrating(self, service):
        frames = [
            _frame("demonstrating"),
            _frame("demonstrating"),
            _frame("concept_explaining"),
            _frame("screen_recording"),
            _frame("none"),
        ]
        with patch.object(service, "_sample_keyframes", return_value=["f0"] * 5):
            with patch.object(service, "_classify_person_activity", return_value=frames):
                result = await service.analyze_content_type("dummy.mp4")
        assert result["content_type"] == "tutorial_demo"
        assert result["usable"] is True

    async def test_person_heavy_dominant_person_no_demo(self, service):
        frames = [
            _frame("none", visible=True),
            _frame("none", visible=True),
            _frame("none", visible=True),
            _frame("none", visible=True),
            _frame("speaking_to_camera", visible=True),
        ]
        with patch.object(service, "_sample_keyframes", return_value=["f0"] * 5):
            with patch.object(service, "_classify_person_activity", return_value=frames):
                result = await service.analyze_content_type("dummy.mp4")
        # 4/5 visible (>=0.6) and good_count==0 -> person_heavy
        assert result["content_type"] == "person_heavy"
        assert result["usable"] is True

    async def test_no_keyframes_returns_safe_default(self, service):
        with patch.object(service, "_sample_keyframes", return_value=[]):
            result = await service.analyze_content_type("dummy.mp4")
        assert result["content_type"] == "unknown"
        assert result["usable"] is True


class TestEligibilityContentType:
    """The content-type gate now matches VLMService's emitted vocabulary."""

    def _base_video(self, content_type: str) -> dict:
        # Full marks everywhere except content_type, so the branch is isolated.
        return {
            "content_type": content_type,
            "visual_quality": 10,
            "resolution_height": 2160,
            "duration": 30,
            "is_old": False,
            "has_watermark": False,
            "has_text_overlay": False,
        }

    def test_talking_head_rejected(self):
        result = VideoEligibilityChecker().check_eligibility(self._base_video("talking_head"))
        assert result["eligible"] is False
        assert "TALKING_HEAD" in result["rejection_reasons"]

    def test_person_heavy_warned_not_rejected(self):
        # Realigned from the dead `person_present` branch: warn, stay eligible.
        result = VideoEligibilityChecker().check_eligibility(self._base_video("person_heavy"))
        assert result["eligible"] is True
        warning_codes = {w["code"] for w in result["warnings"]}
        assert "NO_DEMONSTRATION" in warning_codes

    def test_demo_and_scene_pass(self):
        for ctype in ("tutorial_demo", "scene"):
            result = VideoEligibilityChecker().check_eligibility(self._base_video(ctype))
            assert "content_type" in result["passed_checks"]

    def test_unknown_content_type_does_not_silently_reject(self):
        # Unknown value should not trip a blocking rejection on content-type.
        result = VideoEligibilityChecker().check_eligibility(self._base_video("something_else"))
        assert "TALKING_HEAD" not in result["rejection_reasons"]
