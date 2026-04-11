import subprocess
import os
import logging
from typing import List, Dict, Optional

class FFmpegTransformer:
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.preset = os.getenv("FFMPEG_PRESET", "superfast")
        self.threads = os.cpu_count() or 4
        logging.info(f"[FFmpeg] Initialized for {self.threads} threads")

    def _run_cmd(self, cmd: List[str]):
        logging.info(f"[FFmpeg] Running command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"[FFmpeg] Error: {e.stderr}")
            return False

    def apply_originality(self, input_path: str, output_path: str, mirror: bool = True, zoom: float = 1.05, contrast: float = 1.05, brightness: float = 0.0) -> bool:
        """
        Applies mirroring, zooming, and color grading in a single FFmpeg pass.
        This is significantly faster than using MoviePy for each transformation.
        """
        # Complex Filter:
        # scale=w:h*zoom (zoom) -> crop=w:h (center crop) -> hflip (mirror) -> eq (contrast/brightness)
        
        # 1. Probe original size to maintain output consistent
        try:
            size_out = subprocess.check_output(probe_cmd).decode('utf-8').strip()
            w, h = size_out.split('x')
        except Exception as e:
            logging.error(f"[FFmpeg] Probe failed for {input_path}: {e}")
            raise RuntimeError(f"FFmpeg Probe failed. Cannot determine video resolution for {input_path}")

        filters = []
        if zoom > 1.0:
            # Scale up then crop center
            new_w, new_h = int(int(w)*zoom), int(int(h)*zoom)
            filters.append(f"scale={new_w}:{new_h},crop={w}:{h}")
        
        if mirror:
            filters.append("hflip")
            
        if contrast != 1.0 or brightness != 0.0:
            filters.append(f"eq=contrast={contrast}:brightness={brightness}")

        filter_str = ",".join(filters) if filters else "copy"
        
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", filter_str,
            "-c:v", "libx264", "-preset", self.preset, "-crf", "23",
            "-c:a", "copy", # Copy audio to avoid re-encoding
            "-threads", str(self.threads),
            output_path
        ]
        
        return self._run_cmd(cmd)

    def fast_concat(self, input_paths: List[str], output_path: str) -> bool:
        """
        Concatenates multiple video files using the FFmpeg concat demuxer.
        If all files have the same codec/resolution, this is instantaneous.
        """
        concat_file = f"temp_concat_{os.urandom(4).hex()}.txt"
        with open(concat_file, "w") as f:
            for p in input_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")
        
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy", # No re-encoding!
            output_path
        ]
        
        success = self._run_cmd(cmd)
        if os.path.exists(concat_file):
            os.remove(concat_file)
        return success

    def add_watermark(self, input_path: str, output_path: str, text: str, font_path: str) -> bool:
        """
        Adds high-performance text watermark at the bottom.
        """
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"drawtext=text='{text}':fontfile='{font_path}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=h-th-20",
            "-c:v", "libx264", "-preset", self.preset,
            "-c:a", "copy",
            output_path
        ]
        return self._run_cmd(cmd)

ffmpeg_transformer = FFmpegTransformer()
