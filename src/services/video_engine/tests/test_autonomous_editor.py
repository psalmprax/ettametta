"""
Unit tests for the autonomous video editor's ffmpeg assembly.

These tests do NOT run ffmpeg. They mock subprocess.run and inspect the
assembled command line so we can assert the filtergraph is correct for the
multi-clip and multi-audio cases — the scenarios that exposed two offset/index
bugs in the original per-clip render logic.
"""
from unittest.mock import patch

from src.services.video_engine.autonomous_editor import AutonomousVideoEditor


def _entry_text(segment_index: int, path: str, duration: float) -> dict:
    return {
        "segment_index": segment_index,
        "text": f"segment {segment_index}",
        "clip": {"path": path},
        "duration": duration,
        "transition": "cut",
        "effects": [],
    }


async def _assemble(editor, timeline, **kwargs):
    """Return the assembled ffmpeg command (the list passed to subprocess.run)."""
    captured = {}

    def _run(cmd, **kwargs):
        del kwargs
        captured["cmd"] = list(cmd)
        return type("R", (), {"returncode": 0, "stderr": ""})()

    with patch(
        "src.services.video_engine.autonomous_editor.subprocess.run", side_effect=_run
    ):
        with patch(
            "src.services.video_engine.autonomous_editor.asyncio.to_thread",
            side_effect=lambda fn, *a, **k: fn(*a, **k),
        ):
            await editor._render_video(
                timeline,
                caption_file="caps.srt",
                audio_track=kwargs.get("audio_track"),
                background_music=kwargs.get("background_music"),
                style=kwargs.get("style", "smooth"),
                output_filename=kwargs.get("output_filename"),
            )
    return captured["cmd"]


def _filter_complex(cmd: list[str]) -> str:
    i = cmd.index("-filter_complex")
    return cmd[i + 1]


class TestRenderAssembly:
    async def test_three_clip_xfade_offsets_are_correct(self):
        # Durations 5, 4, 6 with T=0.4.
        # clip B offset = 5 - 1*0.4 = 4.600
        # clip C offset = (5 + 4) - 2*0.4 = 8.200
        editor = AutonomousVideoEditor()
        timeline = [
            _entry_text(0, "a.mp4", 5),
            _entry_text(1, "b.mp4", 4),
            _entry_text(2, "c.mp4", 6),
        ]
        cmd = await _assemble(editor, timeline, style="smooth")
        fc = _filter_complex(cmd)

        assert "xfade=transition=fade:duration=0.4:offset=4.600" in fc
        assert "xfade=transition=fade:duration=0.4:offset=8.200" in fc
        # Exactly two xfade nodes + final [vraw]; no stray ';;'.
        assert ";xfade" not in fc and fc.startswith("[0:v]")

    async def test_audio_inputs_index_past_video_inputs(self):
        # 2 video inputs (a.mp4, b.mp4) then audio at indices 2 and 3.
        editor = AutonomousVideoEditor()
        timeline = [
            _entry_text(0, "a.mp4", 5),
            _entry_text(1, "b.mp4", 4),
        ]
        cmd = await _assemble(
            editor,
            timeline,
            style="smooth",
            audio_track="voice.wav",
            background_music="bgm.mp3",
        )
        fc = _filter_complex(cmd)

        # Voiceover must reference [2:a] and bgm [3:a] — NOT a/b video inputs.
        assert "[2:a]" in fc
        assert "[3:a]volume=0.15[bg]" in fc
        assert "amix=inputs=2:duration=longest[aout]" in fc

    async def test_single_clip_concat_includes_input_label(self):
        editor = AutonomousVideoEditor()
        timeline = [_entry_text(0, "a.mp4", 5)]
        cmd = await _assemble(editor, timeline, style="smooth")
        fc = _filter_complex(cmd)
        # The n==1 concat must reference its scaled input, then [vraw].
        assert "[v0]concat=n=1:v=1:a=0[vraw]" in fc

    async def test_no_audio_uses_silent_fill(self):
        editor = AutonomousVideoEditor()
        timeline = [_entry_text(0, "a.mp4", 5), _entry_text(1, "b.mp4", 4)]
        cmd = await _assemble(editor, timeline, style="smooth")
        fc = _filter_complex(cmd)
        assert "anullsrc=channel_layout=stereo:sample_rate=44100[aout]" in fc
