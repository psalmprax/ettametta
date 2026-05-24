"""
FFmpeg Video Transformation Utilities
====================================

Professional-grade video processing using FFmpeg directly for maximum 
performance and flexibility. This replaces MoviePy for core transformations.
"""

import os
import subprocess
import logging
import asyncio
from pathlib import Path
from src.api.config import settings
from src.services.infrastructure.resource_governor import base_governor_service

class FFmpegTransformer:
    def __init__(self, threads: int | None = None, preset: str | None = None):
        # 10/10 Production: Adaptive Core Management
        self.threads = threads or base_governor_service.get_ffmpeg_threads()
        self.preset = preset or ("ultrafast" if base_governor_service.get_degradation_mode() != "STANDARD" else "superfast")
        self._hw_accel = self._detect_hardware_acceleration()
        
        logger_name = "FFmpegTransformer"
        logging.getLogger(logger_name).info(f"🎞️ [FFmpeg] Initialized: {self.threads} threads (Mode: {base_governor_service.get_degradation_mode()})")

    def _detect_hardware_acceleration(self) -> str:
        """Detects the best available hardware encoder."""
        if os.getenv("FORCE_CPU") == "true":
            logging.info("🛠️ [HW-ACCEL] FORCE_CPU detected. Overriding to libx264.")
            return "cpu"
            
        try:
            # Check for NVIDIA NVENC
            res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True)
            if "h264_nvenc" in res.stdout:
                logging.info("🚀 [HW-ACCEL] NVIDIA NVENC detected. Enabling GPU acceleration.")
                return "nvenc"
            elif "h264_qsv" in res.stdout:
                logging.info("🚀 [HW-ACCEL] Intel QSV detected. Enabling Hardware acceleration.")
                return "qsv"
        except Exception:
            pass
        logging.info("🐢 [HW-ACCEL] No GPU acceleration found. Using standard CPU (libx264).")
        return "cpu"

    def _get_encoder_params(self, quality_mode: str = "ELITE") -> tuple[str, str, list[str]]:
        """Returns the best encoder and its optimal parameters based on hardware."""
        if self._hw_accel == "nvenc":
            return "h264_nvenc", "p4", ["-rc:v", "vbr", "-cq", "19" if quality_mode == "ELITE" else "28"]
        elif self._hw_accel == "qsv":
            return "h264_qsv", "veryslow" if quality_mode == "ELITE" else "veryfast", ["-global_quality", "18" if quality_mode == "ELITE" else "28"]
        else:
            return "libx264", "superfast" if quality_mode == "ELITE" else "ultrafast", ["-crf", "23" if quality_mode == "ELITE" else "28"]

    def _run_cmd(self, cmd: list) -> bool:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"[FFmpeg] Command Failed: {' '.join(cmd)}")
            logging.error(f"[FFmpeg] Error: {e.stderr}")
            return False

    def apply_originality(self, input_path: str, output_path: str, mirror: bool = False, zoom: float = 1.05, contrast: float = 1.05, brightness: float = 0.0, start_offset: float = 0.0, duration: float = None, lut_path: str = None, quality_mode: str = "ELITE") -> bool:
        """
        Applies mirroring, zooming, color grading, and optional LUT in a single FFmpeg pass.
        This provides the cinematic 'Ascension' vibe.
        """
        # Complex Filter:
        # scale=1080:1920:force_original_aspect_ratio=increase (fill) -> crop=1080:1920 (center) -> hflip -> eq
        # This ensures all segments are IDENTICAL in resolution for -c copy concat.
        target_w, target_h = 1080, 1920
        filters = [
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h}"
        ]
        
        if mirror:
            filters.append("hflip")
            
        if contrast != 1.0:
            filters.append(f"eq=contrast={contrast}")
            
        if brightness != 0.0:
            filters.append(f"eq=brightness={brightness}")

        # ELITE: LUT Support (Ascension Tier)
        if lut_path and os.path.exists(lut_path):
            filters.append(f"lut3d='{lut_path}'")
        elif lut_path:
            filters.append("curves=preset=vintage")
            
        filter_str = ",".join(filters) if filters else "copy"
        
        # Check for audio presence to prevent mapping errors
        has_audio = self._has_audio(input_path)
        
        if has_audio:
            audio_filter = "[0:a][1:a]amix=inputs=2:duration=first[a]"
        else:
            audio_filter = "[1:a]volume=1.0[a]"

        # Quality mode: We use passed quality_mode unless resource-constrained
        if self.preset == "ultrafast": quality_mode = "FAST"
        encoder, preset, extra_params = self._get_encoder_params(quality_mode)

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_offset),
        ]
        if duration:
            cmd.extend(["-t", str(duration)])
        cmd.extend([
            "-i", input_path,
            "-", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", # Safety Audio
            "-filter_complex", f"[0:v]{','.join(filters)}[v];{audio_filter}",
            "-map", "[v]", "-map", "[a]",
            "-pix_fmt", "yuv420p",
            "-c:v", encoder, "-preset", preset
        ])
        cmd.extend(extra_params)
        cmd.extend([
            "-c:a", "aac", "-b:a", "192k", "-ac", "2",
            output_path
        ])
        
        return self._run_cmd(cmd)

    def generate_thumbnails(self, input_path: str, output_dir: str, count: int = 5) -> list[str]:
        """Extracts high-quality thumbnails for visual analysis"""
        os.makedirs(output_dir, exist_ok=True)
        thumbnails = []
        
        for i in range(count):
            thumb_path = f"{output_dir}/thumb_{i}.jpg"
            # Extract frame at safe intervals (seconds)
            # Default to 2s, 4s, 6s... for short clips, or use absolute time
            time_at = str(i * 2 + 1) # 1s, 3s, 5s...
            cmd = [
                "ffmpeg", "-y", "-ss", time_at, "-i", input_path,
                "-vframes", "1", "-q:v", "2", thumb_path
            ]
            if self._run_cmd(cmd):
                thumbnails.append(thumb_path)
        
        return thumbnails

    def concatenate_videos(self, video_paths: list[str], output_path: str) -> bool:
        """Concatenates multiple video files into one"""
        if not video_paths: return False
        
        # Create temporary file list for ffmpeg
        with open("concat_list.txt", "w") as f:
            for path in video_paths:
                f.write(f"file '{Path(path).absolute()}'\n")
        
        cmd = [
            "ffmpeg", "-y", "-", "concat", "-safe", "0",
            "-i", "concat_list.txt", "-c", "copy", output_path
        ]
        
        success = self._run_cmd(cmd)
        if os.path.exists("concat_list.txt"):
            os.remove("concat_list.txt")
        return success

    def add_background_music(self, video_path: str, music_path: str, output_path: str, music_volume: float = 0.3) -> bool:
        """Mixes background music into the video while keeping original audio (at lower volume)"""
        # 10/10 Resilience: Handle cases where the video has no audio stream
        cmd = [
            "ffmpeg", "-y", "-i", video_path, "-i", music_path,
            "-filter_complex", 
            f"[0:a]volume=1.0[a1];[1:a]volume={music_volume}[a2];[a1][a2]amix=inputs=2:duration=first",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", output_path
        ]
        
        # Check if video has audio stream using ffprobe
        has_audio = self._has_audio(video_path)
        
        if not has_audio:
            # If no audio, just use the music as the only audio source
            cmd = [
                "ffmpeg", "-y", "-i", video_path, "-i", music_path,
                "-filter_complex", f"[1:a]volume={music_volume}[a]",
                "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", output_path
            ]
            
        return self._run_cmd(cmd)

    def _has_audio(self, path: str) -> bool:
        """Verify if a stream has audio"""
        cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return "audio" in result.stdout
        except Exception:
            return False

    def mix_production_audio_with_ducking(self, video_path: str, voiceover_path: str, music_path: str, output_path: str, music_volume: float = 0.25) -> bool:
        """
        Elite Production Mix: Voiceover + Background Music with SMART DUCKING.
        Uses sidechain compression to automatically lower music when the VO is active.
        """
        # sidechaincompress filter:
        # threshold=0.1: Music level at which compression starts
        # ratio=4: How much to lower the music
        # attack=20: How fast the music lowers
        # release=200: How fast the music returns
        cmd = [
            "ffmpeg", "-y",
            "-i", voiceover_path,
            "-i", music_path,
            "-filter_complex",
            f"[1:a]volume={music_volume}[bg];"
            "[bg][0:a]sidechaincompress=threshold=0.1:ratio=4:attack=20:release=200[mixed_audio]",
            "-i", video_path,
            "-map", "2:v", "-map", "[mixed_audio]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            output_path
        ]
        return self._run_cmd(cmd)

    def generate_styled_subtitles(self, segments: list, output_path: str):
        """
        Generates an Advanced Substation Alpha (.ass) file for professional styling.
        Supports per-segment custom positioning, 'Signature' intro styles, and Fades.
        """
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,3,2,2,100,100,300,1
Style: Signature,Arial,90,&H0000FFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,1,4,4,2,100,100,960,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(output_path, "w") as f:
            f.write(header)
            current_time = 0.0
            for i, seg in enumerate(segments):
                start = self._format_ass_time(current_time)
                end = self._format_ass_time(current_time + seg["duration"])
                # Signature style for the first segment or segments marked as HOOK
                style = "Signature" if i == 0 or seg.get("role") == "HOOK" else "Default"
                # Add Fade-in/Fade-out for elite feel
                text = "{{\\fad(300,300)}}" + seg["text"].replace("\n", "\\N")
                f.write(f"Dialogue: 0,{start},{end},{style},,0,0,0,,{text}\n")
                current_time += seg["duration"]

    def _format_ass_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    def generate_word_level_subtitles(self, words: list, output_path: str):
        """
        Generates a 'Viral Style' ASS file with word-by-word highlights.
        This provides the fast-paced, high-engagement look seen on TikTok/Reels.
        """
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,80,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,4,0,2,100,100,960,1
Style: Highlight,Arial,90,&H0000FFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,110,110,0,0,1,4,0,2,100,100,960,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(output_path, "w") as f:
            f.write(header)
            for word_data in words:
                start = self._format_ass_time(word_data["start"])
                end = self._format_ass_time(word_data["end"])
                text = word_data["word"].upper().strip()
                # Use Highlight style for every word as it appears
                f.write(f"Dialogue: 0,{start},{end},Highlight,,0,0,0,,{text}\n")

    def apply_production_render(self, video_path: str, ass_path: str, output_path: str, quality_mode: str = "ELITE") -> bool:
        """Renders final video with ASS subtitle overlay and professional encoding."""
        encoder, preset, extra_params = self._get_encoder_params(quality_mode)

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"subtitles='{ass_path}'",
            "-c:v", encoder, "-preset", preset
        ] + extra_params + [
            "-c:a", "copy",
            output_path
        ]
        return self._run_cmd(cmd)

    def draw_text_overlay(self, input_path: str, output_path: str, text: str, start_time: float = 0, duration: float = 5, position: str = "center") -> bool:
        """Draws a professional text overlay using FFmpeg's drawtext filter."""
        # Escape text for FFmpeg
        safe_text = text.replace("'", "").replace(":", "\\:")
        
        pos_filter = "x=(w-text_w)/2:y=(h-text_h)/2" # center
        if position == "bottom":
            pos_filter = "x=(w-text_w)/2:y=h-text_h-100"
        elif position == "top":
            pos_filter = "x=(w-text_w)/2:y=100"

        drawtext = (
            f"drawtext=text='{safe_text}':fontcolor=white:fontsize=64:box=1:boxcolor=black@0.5:boxborderw=10:"
            f"{pos_filter}:enable='between(t,{start_time},{start_time+duration})'"
        )

        encoder, preset, extra_params = self._get_encoder_params("ELITE")
        
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", drawtext,
            "-c:v", encoder, "-preset", preset
        ] + extra_params + [
            "-c:a", "copy",
            output_path
        ]
        return self._run_cmd(cmd)

    def apply_cinematic_zoom(self, input_path: str, output_path: str, duration: float, zoom_speed: float = 0.001, max_zoom: float = 1.1, quality_mode: str = "ELITE") -> bool:
        """Applies a slow, cinematic Ken Burns zoom effect."""
        # Elite: High-precision zoom
        encoder, preset, extra_params = self._get_encoder_params(quality_mode)
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"zoompan=z='min(zoom+{zoom_speed},{max_zoom})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(duration*30)}:s=1080x1920:fps=30",
            "-c:v", encoder, "-preset", preset
        ] + extra_params + [
            "-c:a", "copy",
            output_path
        ]
        return self._run_cmd(cmd)

    def apply_fast_transform(self, input_path: str, output_path: str, width: int = 1080, height: int = 1920) -> bool:
        """
        Rapid transform for fast-track production. 
        Ensures exact resolution and aspect ratio alignment for seamless fusion.
        """
        # Smart crop: Scale to fill, then crop center
        filter_str = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
        
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", filter_str,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-c:a", "aac", "-b:a", "128k", "-ac", "2", # Ensure consistent audio format too
            output_path
        ]
        return self._run_cmd(cmd)

    def extract_audio(self, input_path: str, output_path: str) -> bool:
        """Extract audio from video file to WAV/MP3"""
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            output_path,
        ]
        return self._run_cmd(cmd)

    def xfade_concatenate(self, video_paths: list[str], output_path: str, transition: str = "fade", trans_duration: float = 0.5) -> bool:
        """Concatenates videos using cinematic transitions (xfade) and audio crossfades."""
        if len(video_paths) < 2: return self.concatenate_videos(video_paths, output_path)
        
        # Get durations
        durations = []
        for path in video_paths:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            durations.append(float(res.stdout.strip() or 0))

        filter_complex = ""
        current_offset = durations[0] - trans_duration
        
        # Build video filtergraph
        import random
        v_inputs = "[0:v][1:v]"
        for i in range(1, len(video_paths)):
            t_type = transition if transition != "random" else random.choice(["fade", "wipeleft", "wiperight", "slideleft", "slideright", "circleopen", "rectcrop"])
            filter_complex += f"{v_inputs}xfade=transition={t_type}:duration={trans_duration}:offset={current_offset}[v{i}];"
            if i < len(video_paths) - 1:
                v_inputs = f"[v{i}][{i+1}:v]"
                current_offset += durations[i] - trans_duration

        # Build audio filtergraph (acrossfade)
        current_a_offset = durations[0] - trans_duration
        a_inputs = "[0:a][1:a]"
        for i in range(1, len(video_paths)):
            filter_complex += f"{a_inputs}acrossfade=d={trans_duration}[a{i}];"
            if i < len(video_paths) - 1:
                a_inputs = f"[a{i}][{i+1}:a]"

        cmd = ["ffmpeg", "-y"]
        for path in video_paths:
            cmd += ["-i", path]
            
        cmd += [
            "-filter_complex", filter_complex,
            "-map", f"[v{len(video_paths)-1}]",
            "-map", f"[a{len(video_paths)-1}]",
            "-c:v", "libx264", "-preset", self.preset, "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ]
        
        return self._run_cmd(cmd)

    async def apply_cinematic_filters(self, input_path: str, output_path: str, title: str = "", subtitle: str = ""):
        """Applies high-quality cinematic filters and titles via FFmpeg."""
        # Use simple but effective filters: 
        # - vignette
        # - drawtext for top title
        # - drawtext for bottom subtitle
        # - hqdn3d (denoise for premium feel)
        # - unsharp (sharpening)
        
        # Clean strings for ffmpeg
        title = title.replace("'", "").replace(":", "")
        subtitle = subtitle.replace("'", "").replace(":", "")
        
        font_path = settings.FONT_PATH if os.path.exists(settings.FONT_PATH) else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        
        # Check if drawtext is actually available in this FFmpeg build
        drawtext_available = False
        try:
            check_cmd = ["ffmpeg", "-filters"]
            proc = await asyncio.create_subprocess_exec(*check_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            if b"drawtext" in stdout:
                drawtext_available = True
        except Exception:
            pass

        if drawtext_available:
            filter_complex = (
                "vignette=angle=0.5, hqdn3d, unsharp, "
                f"drawtext=fontfile='{font_path}':text='{title}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=60:box=1:boxcolor=black@0.5:boxborderw=10, "
                f"drawtext=fontfile='{font_path}':text='{subtitle}':fontcolor=yellow:fontsize=32:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.5:boxborderw=10"
            )
        else:
            logging.warning("[FFmpegTransformer] drawtext filter missing. Skipping title overlays.")
            filter_complex = "vignette=angle=0.5, hqdn3d, unsharp"
        
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", filter_complex,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "copy",
            output_path
        ]
        
        logging.info(f"[FFmpegTransformer] Running: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            logging.error(f"[FFmpegTransformer] Cinematic filters FAILED (Code {process.returncode})")
            logging.error(f"[FFmpegTransformer] Stderr: {stderr.decode()}")
        else:
            logging.info(f"[FFmpegTransformer] Cinematic filters applied successfully to {output_path}")

# Singleton Instance
base_ffmpeg_service = FFmpegTransformer()
