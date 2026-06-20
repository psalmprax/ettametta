
"""
Motion Graphics Service - Any Tier 3 Enhancement

Adds text animations, overlays, and motion graphics to videos.
Disabled by default - enable via ENABLE_MOTION_GRAPHICS=true
"""

import os
import subprocess
import logging
import random
import uuid

logger = logging.getLogger(__name__)


class MotionGraphicsService:
    """
    Any motion graphics enhancement for video processing.
    Adds animated text overlays, titles, and motion graphics.
    """

    # Text animation styles
    ANIMATION_STYLES = [
        "fade_in",
        "slide_up",
        "scale_in",
        "typewriter",
        "bounce",
        "glitch",
    ]

    # Title templates by niche
    NICHE_TITLE_STYLES = {
        "finance": ["professional", "elegant", "minimal"],
        "crypto": ["modern", "digital", "glitch"],
        "motivation": ["epic", "bold", "inspirational"],
        "tech": ["futuristic", "clean", "digital"],
        "luxury": ["elegant", "sophisticated", "gold"],
        "news": ["breaking", "professional", "bold"],
        "default": ["cinematic", "modern", "clean"],
    }

    def __init__(self):
        self.enabled = os.getenv("ENABLE_MOTION_GRAPHICS", "false").lower() == "true"
        self.engine = os.getenv("MOTION_GRAPHICS_ENGINE", "local")

        logger.info(
            f"[MotionGraphics] Initialized - Enabled: {self.enabled}, Engine: {self.engine}"
        )

    def _get_title_style_for_niche(self, niche: str) -> str:
        """Get appropriate title style for a given niche"""
        niche_lower = niche.lower()

        for key, styles in self.NICHE_TITLE_STYLES.items():
            if key in niche_lower:
                return random.choice(styles)

        return random.choice(self.NICHE_TITLE_STYLES["default"])

    async def add_title_sequence(
        self,
        video_path: str,
        title: str,
        subtitle: str | None = None,
        style: str | None = None,
        duration: float = 3.0,
        position: str = "center",  # center, top, bottom
    ) -> str | None:
        """
        Add animated title sequence to video using Remotion.
        """
        if not self.enabled:
            logger.debug("[MotionGraphics] Disabled, skipping title sequence")
            return None

        logger.info(f"[MotionGraphics] Rendering Remotion title - title: {title}")

        try:
            from src.services.video_engine.remotion_service import base_remotion_service

            # Prepare props for Remotion
            props = {
                "title": title,
                "subtitle": subtitle or "",
                "video_uri": video_path,  # We use the existing video as background
            }

            output_name = f"mg_{os.path.basename(video_path)}"
            rendered_path = await base_remotion_service.render_video(
                composition_id="ViralClip", props=props, output_name=output_name
            )

            return rendered_path

        except Exception as e:
            logger.exception(f"[MotionGraphics] Remotion render failed: {e}")
            return None

    async def add_animated_overlay(
        self,
        video_path: str,
        text: str,
        animation_style: str = "fade_in",
        position: str = "bottom",
        timing: list[float] | None = None,
    ) -> str | None:
        """
        Add animated text overlay at specific timestamps.

        Args:
            video_path: Path to input video
            text: Overlay text
            animation_style: Type of animation
            position: Screen position (top, bottom, center)
            timing: list of timestamps when to show overlay

        Returns:
            Path to enhanced video with overlay, or None if disabled
        """
        if not self.enabled:
            logger.debug("[MotionGraphics] Disabled, skipping overlay")
            return None

        logger.info(
            f"[MotionGraphics] Adding overlay - text: {text}, style: {animation_style}"
        )

        try:
            output_path = video_path.replace(".mp4", "_with_overlay.mp4")

            import subprocess

            # Position mapping for ffmpeg drawtext
            pos_map = {
                "top": "x=(w-text_w)/2:y=20",
                "center": "x=(w-text_w)/2:y=(h-text_h)/2",
                "bottom": "x=(w-text_w)/2:y=h-text_h-20",
            }
            position_filter = pos_map.get(animation_style, pos_map["bottom"])

            # Escape special characters for ffmpeg drawtext
            safe_text = text.replace("'", "'\\''").replace(":", "\\:")

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-vf",
                f"drawtext=text='{safe_text}':fontsize=36:fontcolor=white:borderw=2:bordercolor=black:{position_filter}:enable='between(t,0,5)'",
                "-c:a",
                "copy",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(
                    f"[MotionGraphics] Overlay added successfully: {output_path}"
                )
                return output_path
            else:
                logger.warning(
                    f"[MotionGraphics] FFmpeg overlay failed: {result.stderr[:200]}"
                )
                return video_path  # Return original on failure

        except Exception as e:
            logger.exception(f"[MotionGraphics] Error adding overlay: {e}")
            return None

    # Position constants
    _POSITION_MAP = {
        "bottom_right": "x=w-tw-10:y=h-th-10",
        "bottom_left": "x=10:y=h-th-10",
        "top_right": "x=w-tw-10:y=10",
        "top_left": "x=10:y=10",
        "center": "x=(w-tw)/2:y=(h-th)/2",
    }

    def _output_path(self, video_path: str, suffix: str) -> str:
        """Generate a unique output path for an enhanced video."""
        stem = os.path.splitext(video_path)[0]
        return f"{stem}_{suffix}_{uuid.uuid4().hex[:8]}.mp4"

    def _run_ffmpeg(self, cmd: list[str], timeout: int = 120) -> bool:
        """Run an FFmpeg command, returning True on success."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                return True
            logger.warning(f"[MotionGraphics] FFmpeg failed: {result.stderr[:300]}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("[MotionGraphics] FFmpeg timed out")
            return False
        except Exception as e:
            logger.exception(f"[MotionGraphics] FFmpeg error: {e}")
            return False

    async def add_watermark(
        self,
        video_path: str,
        watermark_text: str = "Created with ettametta",
        opacity: float = 0.3,
        position: str = "bottom_right",
        **_kwargs,
    ) -> str | None:
        """
        Add text watermark to video.

        Args:
            video_path: Path to input video
            watermark_text: Watermark text
            opacity: Watermark opacity (0.0 - 1.0)
            position: Screen position (bottom_right, bottom_left, top_right, top_left, center)

        Returns:
            Path to enhanced video with watermark, or original path if disabled
        """
        if not self.enabled:
            return video_path

        logger.info("[MotionGraphics] Adding text watermark")
        output_path = self._output_path(video_path, "watermarked")
        safe_text = watermark_text.replace("'", "'\\''").replace(":", "\\:")
        pos = self._POSITION_MAP.get(position, self._POSITION_MAP["bottom_right"])

        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"drawtext=text='{safe_text}':fontsize=24:fontcolor=white@{opacity}:borderw=1:bordercolor=black@{opacity}:{pos}",
            "-c:a", "copy", output_path,
        ]

        if self._run_ffmpeg(cmd) and os.path.exists(output_path):
            logger.info(f"[MotionGraphics] Text watermark added: {output_path}")
            return output_path
        return video_path

    async def add_image_watermark(
        self,
        video_path: str,
        image_path: str,
        opacity: float = 0.5,
        position: str = "bottom_right",
        scale: float = 0.15,
    ) -> str | None:
        """
        Add image/logo watermark overlay to video.

        Args:
            video_path: Path to input video
            image_path: Path to watermark image (PNG with transparency recommended)
            opacity: Watermark opacity (0.0 - 1.0)
            position: Screen position
            scale: Scale factor relative to video width (0.0 - 1.0)

        Returns:
            Path to enhanced video, or original on failure
        """
        if not os.path.exists(image_path):
            logger.error(f"[MotionGraphics] Watermark image not found: {image_path}")
            return video_path

        logger.info(f"[MotionGraphics] Adding image watermark from {image_path}")
        output_path = self._output_path(video_path, "imgwm")
        pos = self._POSITION_MAP.get(position, self._POSITION_MAP["bottom_right"])

        # Scale the logo relative to video width, apply opacity, overlay
        overlay_filter = (
            f"[1:v]scale=iw*{scale}:ih*{scale},"
            f"format=rgba,colorchannelmixer=aa={opacity}[wm];"
            f"[0:v][wm]overlay={pos}"
        )

        cmd = [
            "ffmpeg", "-y", "-i", video_path, "-i", image_path,
            "-filter_complex", overlay_filter,
            "-map", "0:a?", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "copy", output_path,
        ]

        if self._run_ffmpeg(cmd) and os.path.exists(output_path):
            logger.info(f"[MotionGraphics] Image watermark added: {output_path}")
            return output_path
        return video_path

    async def add_animated_watermark(
        self,
        video_path: str,
        watermark_text: str = "ettametta",
        animation: str = "pulse",
        position: str = "bottom_right",
        opacity: float = 0.4,
    ) -> str | None:
        """
        Add animated watermark with motion effects.

        Args:
            video_path: Path to input video
            watermark_text: Watermark text
            animation: Animation type ('pulse', 'fade_loop', 'slide_in')
            position: Base screen position
            opacity: Base opacity

        Returns:
            Path to enhanced video, or original on failure
        """
        logger.info(f"[MotionGraphics] Adding animated watermark ({animation})")
        output_path = self._output_path(video_path, "animwm")
        safe_text = watermark_text.replace("'", "'\\''").replace(":", "\\:")

        pos = self._POSITION_MAP.get(position, self._POSITION_MAP["bottom_right"])

        if animation == "pulse":
            # Pulsing opacity between base and full
            alpha_expr = f"min(1\\,{opacity}+0.2*sin(2*PI*t/3))"
            vf = (
                f"drawtext=text='{safe_text}':fontsize=24:"
                f"fontcolor=white@'{alpha_expr}':"
                f"borderw=1:bordercolor=black@'{alpha_expr}':"
                f"{pos}"
            )
        elif animation == "fade_loop":
            # Fade in/out cycle every 5 seconds
            alpha_expr = f"if(lt(mod(t\\,5)\\,2)\\, ({opacity}/2)*mod(t\\,5)\\, {opacity}-{opacity}/2*(mod(t\\,5)-2))"
            vf = (
                f"drawtext=text='{safe_text}':fontsize=24:"
                f"fontcolor=white@'{alpha_expr}':"
                f"borderw=1:bordercolor=black@'{alpha_expr}':"
                f"{pos}"
            )
        elif animation == "slide_in":
            # Slide in from right edge
            dur = 1.0
            slide_y = "h-th-10" if "bottom" in position else "10"
            vf = (
                f"drawtext=text='{safe_text}':fontsize=24:"
                f"fontcolor=white@{opacity}:borderw=1:bordercolor=black@{opacity}:"
                f"x='if(lt(t\\,{dur})\\,w-tw-(w-tw)*t/{dur}\\,10)':y={slide_y}"
            )
        else:
            # Default: static fallback
            vf = f"drawtext=text='{safe_text}':fontsize=24:fontcolor=white@{opacity}:borderw=1:bordercolor=black@{opacity}:{pos}"

        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", vf,
            "-c:a", "copy", output_path,
        ]

        if self._run_ffmpeg(cmd) and os.path.exists(output_path):
            logger.info(f"[MotionGraphics] Animated watermark added: {output_path}")
            return output_path
        return video_path

    async def burn_branding(
        self,
        video_path: str,
        brand_config: dict | None = None,
    ) -> str | None:
        """
        Burn full brand package into video: logo + text + optional tagline.

        Args:
            video_path: Path to input video
            brand_config: Dict with keys:
                - logo_path: Path to logo image (optional)
                - brand_name: Brand name text
                - tagline: Tagline text (optional)
                - website: Website URL (optional)
                - position: 'bottom_right' | 'bottom_left' | 'top_right' | 'top_left'
                - opacity: 0.0-1.0

        Returns:
            Path to branded video, or original on failure
        """
        config = brand_config or {}
        logo_path = config.get("logo_path")
        brand_name = config.get("brand_name", "ettametta")
        tagline = config.get("tagline")
        website = config.get("website")
        position = config.get("position", "bottom_right")
        opacity = config.get("opacity", 0.4)

        logger.info(f"[MotionGraphics] Burning branding: {brand_name}")
        output_path = self._output_path(video_path, "branded")

        # Build filter chain
        filters: list[str] = []
        input_map = "[0:v]"
        extra_inputs: list[str] = []
        has_logo = bool(logo_path and os.path.exists(logo_path))

        # Step 1: Logo overlay (if provided)
        if has_logo:
            extra_inputs = ["-i", logo_path]
            pos = self._POSITION_MAP.get(position, self._POSITION_MAP["bottom_right"])
            filters.append(
                f"[1:v]scale=80:-1,format=rgba,colorchannelmixer=aa={opacity}[logo];"
                f"{input_map}[logo]overlay={pos}[v1]"
            )
            input_map = "[v1]"

        # Step 2: Brand name text — use position-derived offsets
        safe_brand = brand_name.replace("'", "'\\''").replace(":", "\\:")
        pos_parts = self._POSITION_MAP.get(position, self._POSITION_MAP["bottom_right"]).split(":")
        text_offset_x = pos_parts[0] if len(pos_parts) >= 2 else "x=w-tw-10"
        text_offset_y = pos_parts[1] if len(pos_parts) >= 2 else "y=h-th-10"
        # Shift text up a bit when logo is also present
        if has_logo and "bottom" in position:
            text_offset_y = "y=h-th-50"
        filters.append(
            f"{input_map}drawtext=text='{safe_brand}':fontsize=18:fontcolor=white@{opacity}:borderw=1:bordercolor=black@{opacity}:{text_offset_x}:{text_offset_y}[v2]"
        )
        input_map = "[v2]"

        # Step 3: Tagline (if provided) — offset below brand name
        if tagline:
            safe_tagline = tagline.replace("'", "'\\''").replace(":", "\\:")
            if "bottom" in position:
                tag_y = "y=h-th-30"
            elif "top" in position:
                tag_y = "y=70"
            else:  # center
                tag_y = "y=h/2+30"
            filters.append(
                f"{input_map}drawtext=text='{safe_tagline}':fontsize=14:fontcolor=white@{opacity * 0.8}:borderw=0:{text_offset_x}:{tag_y}[v_tag]"
            )
            input_map = "[v_tag]"

        # Step 4: Website URL (if provided) — offset furthest from edge
        if website:
            safe_url = website.replace("'", "'\\''").replace(":", "\\:")
            if "bottom" in position:
                url_y = "y=h-th-10"
            elif "top" in position:
                url_y = "y=90"
            else:  # center
                url_y = "y=h/2+50"
            filters.append(
                f"{input_map}drawtext=text='{safe_url}':fontsize=12:fontcolor=white@{opacity * 0.7}:borderw=0:{text_offset_x}:{url_y}[v3]"
            )
            input_map = "[v3]"

        filter_complex = ";".join(filters)

        cmd = ["ffmpeg", "-y", "-i", video_path] + extra_inputs + [
            "-filter_complex", filter_complex,
            "-map", input_map, "-map", "0:a?",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "copy", output_path,
        ]

        if self._run_ffmpeg(cmd, timeout=180) and os.path.exists(output_path):
            logger.info(f"[MotionGraphics] Branding burned: {output_path}")
            return output_path
        return video_path

    def get_available_styles(self) -> list[str]:
        """Get list of available animation styles"""
        return self.ANIMATION_STYLES.copy()

    def get_niche_styles(self, niche: str) -> list[str]:
        """Get available styles for a specific niche"""
        niche_lower = niche.lower()

        for key, styles in self.NICHE_TITLE_STYLES.items():
            if key in niche_lower:
                return styles

        return self.NICHE_TITLE_STYLES["default"]


# Global instance
base_motion_graphics_service = MotionGraphicsService()
