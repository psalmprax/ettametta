"""Subtitle generation and burning for video content."""

from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SubtitleCue:
    index: int
    start_seconds: float
    end_seconds: float
    text: str


@dataclass
class SubtitleTrack:
    language: str
    cues: list[SubtitleCue] = field(default_factory=list)
    format: str = "srt"

    def to_srt(self) -> str:
        lines = []
        for cue in self.cues:
            start = self._format_time(cue.start_seconds)
            end = self._format_time(cue.end_seconds)
            lines.append(f"{cue.index}")
            lines.append(f"{start} --> {end}")
            lines.append(cue.text)
            lines.append("")
        return "\n".join(lines)

    def to_ass(self) -> str:
        header = (
            "[Script Info]\n"
            "Title: Ettametta Subtitles\n"
            "ScriptType: v4.00+\n"
            "PlayResX: 1920\n"
            "PlayResY: 1080\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
            "-1,0,0,0,100,100,0,0,1,2,2,2,20,20,50,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )
        events = []
        for cue in self.cues:
            start = self._format_ass_time(cue.start_seconds)
            end = self._format_ass_time(cue.end_seconds)
            events.append(
                f"Dialogue: 0,{start},{end},Default,,0,0,0,,{cue.text}"
            )
        return header + "\n".join(events) + "\n"

    @staticmethod
    def _format_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _format_ass_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


class SubtitleService:
    def __init__(self) -> None:
        self._whisper_available: Optional[bool] = None

    def _check_whisper(self) -> bool:
        if self._whisper_available is None:
            try:
                import whisper  # noqa: F401
                self._whisper_available = True
            except ImportError:
                self._whisper_available = False
                logger.info("openai-whisper not installed; using stub transcription")
        return self._whisper_available

    async def generate_subtitles(
        self,
        video_path: str,
        language: str = "en",
    ) -> SubtitleTrack:
        if self._check_whisper():
            return await self._generate_with_whisper(video_path, language)
        return await self._generate_stub(video_path, language)

    async def _generate_with_whisper(
        self, video_path: str, language: str
    ) -> SubtitleTrack:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(video_path, language=language)
        cues = []
        for i, seg in enumerate(result["segments"], 1):
            cues.append(
                SubtitleCue(
                    index=i,
                    start_seconds=seg["start"],
                    end_seconds=seg["end"],
                    text=seg["text"].strip(),
                )
            )
        return SubtitleTrack(language=language, cues=cues)

    async def _generate_stub(
        self, video_path: str, language: str
    ) -> SubtitleTrack:
        logger.warning("Stub subtitle generation — whisper not available")
        return SubtitleTrack(
            language=language,
            cues=[
                SubtitleCue(
                    index=1,
                    start_seconds=0.0,
                    end_seconds=5.0,
                    text="[Auto-generated subtitle placeholder]",
                )
            ],
        )

    async def burn_subtitles(
        self,
        video_path: str,
        subtitle_track: SubtitleTrack,
        style: str = "default",
    ) -> str:
        import asyncio

        suffix = f".{subtitle_track.format}"
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False, mode="w"
        ) as f:
            if subtitle_track.format == "ass":
                f.write(subtitle_track.to_ass())
            else:
                f.write(subtitle_track.to_srt())
            subtitle_path = f.name

        output_path = video_path.rsplit(".", 1)[0] + "_subtitled.mp4"
        fonts_dir = Path(__file__).parent / "fonts"
        force_style = ""
        if style == "bold":
            force_style = ",Bold=1,Fontsize=52"
        elif style == "minimal":
            force_style = ",FontSize=36,PrimaryColour=&H00CCCCCC"

        if subtitle_track.format == "ass":
            vf = f"ass='{subtitle_path}'"
        else:
            vf = (
                f"subtitles='{subtitle_path}'"
                f":force_style='{force_style}'" if force_style
                else f"subtitles='{subtitle_path}'"
            )

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", vf,
            "-c:a", "copy",
            output_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg subtitle burn failed: {stderr.decode()}")
        return output_path


base_subtitle_service = SubtitleService()
