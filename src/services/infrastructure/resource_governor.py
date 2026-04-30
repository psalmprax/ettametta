import os
import logging
from typing import Any

try:
    import psutil

    _PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    _PSUTIL_AVAILABLE = False
    logging.getLogger("ResourceGovernor").warning(
        "psutil not available - resource limits disabled"
    )

logger = logging.getLogger("ResourceGovernor")


class ResourceGovernor:
    """
    10/10 Production: The Lean Swarm Governor.
    Monitors CPU and memory to enforce adaptive quality degradation.
    """

    def __init__(self, cpu_threshold: float = 85.0, mem_threshold: float = 90.0):
        self.cpu_threshold = cpu_threshold
        self.mem_threshold = mem_threshold

    def get_degradation_mode(self) -> str:
        """
        Returns the degradation mode for high-throughput production.
        Modes: 'STANDARD', 'LITE' (Fast Encodes), 'MINIMAL' (Neural Off).
        """
        if not _PSUTIL_AVAILABLE:
            return "STANDARD"

        cpu_usage = psutil.cpu_percent(interval=None)
        mem_usage = psutil.virtual_memory().percent

        mode = "STANDARD"

        if cpu_usage > self.cpu_threshold or mem_usage > self.mem_threshold:
            mode = "LITE"

        if cpu_usage > 95.0:
            mode = "MINIMAL"

        if mode != "STANDARD":
            logger.warning(
                f"⚠️ [Governor] Resource Saturation! Entering {mode} mode. (CPU: {cpu_usage}%, MEM: {mem_usage}%)"
            )

        return mode

    def get_ffmpeg_threads(self) -> int:
        """Adaptive thread count for FFmpeg to prevent system-wide lag."""
        mode = self.get_degradation_mode()
        cores = os.cpu_count() or 1

        if mode == "MINIMAL":
            return 1
        elif mode == "LITE":
            return max(1, cores // 4)
        return max(1, cores // 2)


base_governor_service = ResourceGovernor()
