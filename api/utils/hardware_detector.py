import os
import logging
from typing import Optional, Dict, Any

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


class HardwareDetector:
    """
    Hardware detection utility for GPU servers.
    Agnostic across NVIDIA CUDA, AMD ROCm, Apple MPS, Intel XPU, DirectML.
    """

    def __init__(self):
        self.device = self._detect_device()
        self.backend = self._detect_backend()
        self.vram_gb = self._detect_vram_gb()

    def set_vram_override(self, vram_gb: int):
        """Override detected VRAM (useful for testing or manual config)."""
        self.vram_gb = vram_gb

    def _detect_device(self) -> str:
        """Determines the best available hardware device."""
        if not TORCH_AVAILABLE:
            return "cpu"
            
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        try:
            import intel_extension_for_pytorch as ipex

            if hasattr(torch, "xpu") and torch.xpu.is_available():
                return "xpu"
        except ImportError:
            pass
        try:
            import torch_directml

            if torch_directml.is_available():
                return "directml"
        except ImportError:
            pass
        return "cpu"

    def _detect_backend(self) -> str:
        """Identifies the specific vendor backend."""
        if not TORCH_AVAILABLE:
            return "Generic/CPU"
            
        if self.device == "cuda":
            if "ROCM" in torch.version.cuda if hasattr(torch.version, "cuda") else "":
                return "AMD/ROCm"
            return "NVIDIA/CUDA"
        if self.device == "mps":
            return "Apple/MPS"
        if self.device == "xpu":
            return "Intel/XPU"
        if self.device == "directml":
            return "Microsoft/DirectML"
        return "Generic/CPU"

    def _detect_vram_gb(self) -> Optional[int]:
        """Detects available GPU VRAM in GB."""
        if not TORCH_AVAILABLE:
            return None
            
        if self.device == "cuda":
            try:
                # Get total VRAM and convert to GB
                total_memory = torch.cuda.get_device_properties(0).total_memory
                return int(total_memory / (1024**3))
            except Exception as e:
                logging.warning(f"Could not detect CUDA VRAM: {e}")
                return None

        elif self.device == "xpu":
            try:
                # Intel XPU detection
                import intel_extension_for_pytorch as ipex

                if hasattr(torch.xpu, "get_device_properties"):
                    props = torch.xpu.get_device_properties(0)
                    if hasattr(props, "total_memory"):
                        return int(props.total_memory / (1024**3))
            except Exception as e:
                logging.warning(f"Could not detect XPU VRAM: {e}")
                return None

        # For other devices, try environment variable override
        return None

    def get_gpu_info(self) -> Dict[str, Any]:
        """Returns comprehensive GPU information."""
        # Check if VRAM was originally detected vs overridden
        originally_detected = self._detect_vram_gb() is not None
        info = {
            "device": self.device,
            "backend": self.backend,
            "vram_gb": self.vram_gb,
            "detected": originally_detected,
            "overridden": self.vram_gb != self._detect_vram_gb()
            if originally_detected
            else False,
        }

        # Add device-specific details
        if TORCH_AVAILABLE and self.device == "cuda":
            try:
                props = torch.cuda.get_device_properties(0)
                info.update(
                    {
                        "gpu_name": props.name,
                        "compute_capability": f"{props.major}.{props.minor}",
                        "multiprocessors": props.multi_processor_count,
                    }
                )
            except:
                pass

        return info

    def get_optimal_vram_per_job(self, optimization_level: str = "safe") -> int:
        """
        Returns optimal VRAM per job based on hardware and optimization level.
        """
        if not self.vram_gb:
            # Fallback values when VRAM can't be detected
            fallback_vram = {
                "safe": 8,
                "medium": 6,
                "extreme": 5,
            }
            return fallback_vram.get(optimization_level, 8)

        # Hardware-specific adjustments
        if self.device == "cuda":
            # NVIDIA GPUs can handle more aggressive optimization
            base_vram = {
                "safe": 8,
                "medium": 6,
                "extreme": 5,
            }
        elif self.device == "xpu":
            # Intel XPU more conservative
            base_vram = {
                "safe": 10,
                "medium": 8,
                "extreme": 7,
            }
        else:
            # Other GPUs conservative
            base_vram = {
                "safe": 12,
                "medium": 10,
                "extreme": 8,
            }

        return base_vram.get(optimization_level, 8)

    def calculate_optimal_slots(self, optimization_level: str = "safe") -> int:
        """
        Calculates optimal concurrent jobs based on detected hardware.
        """
        if not self.vram_gb:
            # Environment variable override or fallback
            env_slots = os.getenv("GPU_QUEUE_SLOTS")
            if env_slots:
                try:
                    return max(1, int(env_slots))
                except ValueError:
                    pass
            return 1  # Conservative fallback

        vram_per_job = self.get_optimal_vram_per_job(optimization_level)
        calculated_slots = max(1, self.vram_gb // vram_per_job)

        # Hardware-specific caps
        if self.device == "cuda":
            max_slots = 4  # NVIDIA can handle more concurrency
        elif self.device == "xpu":
            max_slots = 3  # Intel XPU more conservative
        else:
            max_slots = 2  # Other GPUs conservative

        return min(calculated_slots, max_slots)


# Global instance (will be updated with config overrides)
hardware_detector = HardwareDetector()
