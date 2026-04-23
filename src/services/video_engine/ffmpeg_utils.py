"""
FFmpeg Video Transformation Utilities
====================================

Professional-grade video processing using FFmpeg directly for maximum 
performance and flexibility. This replaces MoviePy for core transformations.
"""

import os
import subprocess
import logging
from pathlib import Path
from src.api.config import settings
from src.services.infrastructure.resource_governor import base_resource_governor

class FFmpegTransformer:
    def __init__(self, threads: int | None = None, preset: str | None = None):
        # 10/10 Production: Adaptive Core Management
        self.threads = threads or base_resource_governor.get_ffmpeg_threads()
        self.preset = preset or ("ultrafast" if base_resource_governor.get_degradation_mode() != "STANDARD" else "superfast")
        self._hw_accel = self._detect_hardware_acceleration()
        
        logger_name = "FFmpegTransformer"
        logging.getLogger(logger_name).info(f"🎞️ [FFmpeg] Initialized: {self.threads} threads (Mode: {base_resource_governor.get_degradation_mode()})")

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
            return "libx264", "slow" if quality_mode == "ELITE" else "ultrafast", ["-crf", "18" if quality_mode == "ELITE" else "28"]

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
            audio_filter = f"[0:a][1:a]amix=inputs=2:duration=first[a]"
        else:
            audio_filter = f"[1:a]volume=1.0[a]"

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
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", # Safety Audio
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
            # Extract frame at different percentages
            time_at = f"{i * 20}%"
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
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
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
        except:
            return False

    def mix_production_audio(self, video_path: str, voiceover_path: str, music_path: str, output_path: str, music_volume: float = 0.15) -> bool:
        """
        Elite Production Mix: Combines visuals with Voiceover and Background Music.
        Discards existing segment audio to ensure professional narration clarity.
        """
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", voiceover_path,
            "-i", music_path,
            "-filter_complex",
            f"[1:a]volume=1.0[vo];[2:a]volume={music_volume}[bg];[vo][bg]amix=inputs=2:duration=first",
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
                text = f"{{\\fad(300,300)}}" + seg["text"].replace("\n", "\\N")
                f.write(f"Dialogue: 0,{start},{end},{style},,0,0,0,,{text}\n")
                current_time += seg["duration"]

    def _format_ass_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

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

    def apply_fast_transform(self, input_path: str, output_path: str) -> bool:
        """Rapid transform for fast-track production."""
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-c:a", "copy",
            output_path
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

# Singleton Instance
base_ffmpeg_transformer = FFmpegTransformer()
