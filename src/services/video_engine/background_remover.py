"""
Background Remover Service
==========================

Background removal using FFmpeg chromakey/colorkey, rembg (ML-based),
or solid-color replacement.
"""

import asyncio
import os
import subprocess
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


class BackgroundRemover:
    def __init__(self, output_dir: str = "data/storage/outputs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.enabled = os.getenv("BACKGROUND_REMOVAL_ENABLED", "false").lower() == "true"

    def remove_background(
        self,
        video_path: str,
        output_path: str | None = None,
        method: str = "auto",
        color: str = "green",
        replace_color: str | None = None,
        similarity: float = 0.3,
        blend: float = 0.1,
    ) -> str | None:
        """Remove background from video.

        Args:
            video_path: Input video file path.
            output_path: Output file path (auto-generated if None).
            method: Removal method ('auto', 'chromakey', 'colorkey', 'rembg').
                     'auto' tries rembg first, falls back to chromakey.
            color: Background color to remove ('green', 'blue', or hex like '#00FF00').
            replace_color: Hex color to use as replacement background (None = transparent).
            similarity: How similar colors must be to the key color (0.0-1.0).
            blend: Blending factor at edges (0.0-1.0).
        """
        if not os.path.exists(video_path):
            logger.error(f"[BackgroundRemover] Input not found: {video_path}")
            return None

        if not self.enabled:
            logger.debug("[BackgroundRemover] Disabled, skipping")
            return None

        if output_path is None:
            name = Path(video_path).stem
            output_path = os.path.join(self.output_dir, f"bg_removed_{name}_{uuid.uuid4().hex[:8]}.mp4")

        if method == "auto":
            result = self._remove_rembg(video_path, output_path)
            if result:
                return result
            logger.info("[BackgroundRemover] rembg unavailable, falling back to chromakey")
            method = "chromakey"

        if method == "rembg":
            result = self._remove_rembg(video_path, output_path)
            if result:
                return result
            logger.warning("[BackgroundRemover] rembg failed")
            return None

        # FFmpeg chromakey / colorkey
        return self._remove_chromakey(
            video_path, output_path, method=method, color=color,
            replace_color=replace_color, similarity=similarity, blend=blend,
        )

    async def remove_background_async(self, video_path: str, **kwargs) -> str | None:
        """Async wrapper around remove_background for use in async contexts."""
        return await asyncio.to_thread(self.remove_background, video_path, **kwargs)

    def _remove_rembg(self, video_path: str, output_path: str) -> str | None:
        """ML-based background removal using rembg (onnxruntime)."""
        try:
            from rembg import remove
            from PIL import Image
            import cv2
            import numpy as np

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None

            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            tmp_out = output_path.replace(".mp4", "_alpha.mp4")
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(tmp_out, fourcc, fps, (w, h))

            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                # Convert BGR → RGB → PIL → rembg → back
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb)
                result = remove(pil_img)
                # Composite onto white or transparent
                bg = Image.new("RGBA", result.size, (0, 0, 0, 0))
                composite = Image.alpha_composite(bg, result).convert("RGB")
                out_frame = cv2.cvtColor(np.array(composite), cv2.COLOR_RGB2BGR)
                writer.write(out_frame)
                frame_count += 1

            cap.release()
            writer.release()

            if frame_count == 0:
                return None

            # Re-mux with original audio
            cmd = [
                "ffmpeg", "-y", "-i", tmp_out, "-i", video_path,
                "-map", "0:v", "-map", "1:a?",
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-pix_fmt", "yuv420p", "-c:a", "copy",
                output_path,
            ]
            self._run_cmd(cmd)

            # Cleanup temp
            if os.path.exists(tmp_out):
                os.remove(tmp_out)

            if os.path.exists(output_path):
                logger.info(f"[BackgroundRemover] rembg background removed: {output_path}")
                return output_path
            return None

        except ImportError:
            logger.debug("[BackgroundRemover] rembg not installed")
            return None
        except Exception as e:
            logger.warning(f"[BackgroundRemover] rembg error: {e}")
            return None

    def _remove_chromakey(
        self,
        video_path: str,
        output_path: str,
        method: str = "chromakey",
        color: str = "green",
        replace_color: str | None = None,
        similarity: float = 0.3,
        blend: float = 0.1,
    ) -> str | None:
        """FFmpeg-based chromakey/colorkey background removal."""
        key_color = self._resolve_color(color)
        if key_color is None:
            logger.error(f"[BackgroundRemover] Unknown color: {color}")
            return None

        if method == "colorkey":
            filter_str = f"colorkey=0x{key_color}:{similarity}:{blend}"
        else:
            filter_str = f"chromakey=0x{key_color}:{similarity}:{blend}"

        if replace_color:
            replace_hex = self._normalize_hex(replace_color)
            if replace_hex:
                filter_str = f"color=c=0x{replace_hex}:s=1[vbg];[0:v]{filter_str}[vfg];[vbg][vfg]overlay"
            else:
                logger.warning(f"[BackgroundRemover] Invalid replace_color: {replace_color}, using transparent")

        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", filter_str,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            output_path,
        ]

        if self._run_cmd(cmd):
            logger.info(f"[BackgroundRemover] Background removed: {output_path}")
            return output_path

        logger.error(f"[BackgroundRemover] FFmpeg chromakey failed for {video_path}")
        return None

    def _resolve_color(self, color: str) -> str | None:
        """Resolve color name or hex to 6-digit hex string."""
        color_map = {
            "green": "00FF00",
            "blue": "0000FF",
            "red": "FF0000",
            "white": "FFFFFF",
            "black": "000000",
        }
        normalized = color.lower().strip()
        if normalized in color_map:
            return color_map[normalized]
        cleaned = normalized.lstrip("#")
        if len(cleaned) == 6 and all(c in "0123456789abcdefABCDEF" for c in cleaned):
            return cleaned.upper()
        return None

    def _normalize_hex(self, color: str) -> str | None:
        """Normalize a color to 6-digit uppercase hex."""
        normalized = color.lower().strip().lstrip("#")
        if len(normalized) == 6 and all(c in "0123456789abcdef" for c in normalized):
            return normalized.upper()
        return None

    def _run_cmd(self, cmd: list) -> bool:
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"[BackgroundRemover] Command failed: {' '.join(cmd)}")
            logger.error(f"[BackgroundRemover] Error: {e.stderr}")
            return False
        except Exception as e:
            logger.exception(f"[BackgroundRemover] Unexpected error: {e}")
            return False


base_background_remover = BackgroundRemover()
