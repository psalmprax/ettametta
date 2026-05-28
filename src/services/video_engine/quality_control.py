import logging
import json
import subprocess
from pathlib import Path

logger = logging.getLogger("QualityControl")


class QualityControl:
    """Vision-Based Visual Auditor using FFmpeg probes and frame analysis."""

    def __init__(self):
        pass

    async def audit_video(self, video_path: str, job_id: str) -> dict:
        """Performs a multi-point visual audit of the rendered video."""
        logger.info(f"[QC] Starting audit for {video_path}")

        if not Path(video_path).exists():
            return {"passed": False, "score": 0, "feedback": "Video file not found"}

        try:
            probe = self._probe_video(video_path)
        except Exception as e:
            return {"passed": False, "score": 0, "feedback": f"Probe failed: {e}"}

        score = 10.0
        issues = []

        # Check duration
        duration = float(probe.get("format", {}).get("duration", 0))
        if duration < 0.5:
            score -= 5.0
            issues.append("Video is too short (<0.5s)")
        elif duration > 600:
            score -= 2.0
            issues.append("Video exceeds 10 minutes")

        # Check video stream exists
        video_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
        if not video_streams:
            return {"passed": False, "score": 0, "feedback": "No video stream found"}

        vs = video_streams[0]
        width = int(vs.get("width", 0))
        height = int(vs.get("height", 0))
        if width < 480 or height < 480:
            score -= 2.0
            issues.append(f"Low resolution: {width}x{height}")

        # Check for black frames (corruption indicator)
        try:
            black = self._detect_black_frames(video_path)
            if black > 0.5:
                score -= 3.0
                issues.append(f"Black frames detected ({black:.1f}s)")
        except Exception:
            pass

        # Check audio stream
        audio_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]
        if not audio_streams:
            score -= 1.0
            issues.append("No audio stream")

        # Check bitrate
        bitrate = int(probe.get("format", {}).get("bit_rate", 0))
        if bitrate and bitrate < 500_000:
            score -= 1.0
            issues.append(f"Low bitrate: {bitrate // 1000}kbps")

        score = max(0.0, min(10.0, score))
        passed = score >= 5.0

        report = {
            "passed": passed,
            "score": round(score, 1),
            "duration": duration,
            "resolution": f"{width}x{height}",
            "bitrate_kbps": bitrate // 1000 if bitrate else 0,
            "has_audio": bool(audio_streams),
            "issues": issues,
            "feedback": "; ".join(issues) if issues else "Video meets production standards",
        }
        logger.info(f"[QC] Audit {'passed' if passed else 'FAILED'}: {score}/10")
        return report

    def _probe_video(self, video_path: str) -> dict:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", video_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr}")
        return json.loads(result.stdout)

    def _detect_black_frames(self, video_path: str) -> float:
        result = subprocess.run(
            ["ffmpeg", "-i", video_path, "-vf", "blackdetect=d=0.1:pix_th=0.10", "-an", "-f", "null", "-"],
            capture_output=True, text=True, timeout=60,
        )
        total = 0.0
        for line in result.stderr.split("\n"):
            if "black_start" in line:
                try:
                    parts = line.split("black_duration:")
                    if len(parts) > 1:
                        total += float(parts[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
        return total


base_qc_service = QualityControl()
