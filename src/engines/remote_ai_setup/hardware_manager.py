import os
import gc
import torch
import logging

class HardwareManager:
    """
    Universal Hardware Abstraction Layer (HAL) for AI inference.
    Supports NVIDIA (CUDA), AMD (ROCm), Apple (MPS), Intel (XPU), and DirectML.
    """

    def __init__(self):
        self.device = self._detect_device()
        self.backend = self._detect_backend()
        self.dtype = self._detect_optimal_dtype()

        logging.info(f"[HardwareManager] Initialized with Device: {self.device}, Backend: {self.backend}, Dtype: {self.dtype}")

    def _detect_device(self) -> str:
        """Determines the best available hardware device."""
        # 0. Forced CPU Override (Hardening)
        if os.getenv("FORCE_CPU") == "true":
            return "cpu"

        # 1. NVIDIA / AMD (ROCm)
        if torch.cuda.is_available():
            return "cuda"

        # 2. Apple Silicon (Metal Performance Shaders)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"

        # 3. Intel GPU (XPU)
        try:
            import intel_extension_for_pytorch as ipex
            if hasattr(torch, "xpu") and torch.xpu.is_available():
                return "xpu"
        except ImportError:
            pass

        # 4. DirectML (Windows / AMD / Intel)
        try:
            import torch_directml
            if torch_directml.is_available():
                return "directml"
        except ImportError:
            pass

        # 5. CPU Fallback
        return "cpu"

    def _detect_backend(self) -> str:
        """Identifies the specific vendor backend."""
        if self.device == "cuda":
            if "ROCM" in torch.version.cuda if hasattr(torch.version, 'cuda') else "":
                return "AMD/ROCm"
            return "NVIDIA/CUDA"
        if self.device == "mps":
            return "Apple/MPS"
        if self.device == "xpu":
            return "Intel/XPU"
        if self.device == "directml":
            return "Microsoft/DirectML"
        return "Generic/CPU"

    def _detect_optimal_dtype(self) -> torch.dtype:
        """Determines the most stable high-performance dtype for the hardware."""
        if self.device == "cuda":
            # Check for BFloat16 support (Ampere+ or ROCm)
            if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
                return torch.bfloat16
            return torch.float16

        if self.device == "mps":
            # MPS currently prefers float16 but some ops require float32
            return torch.float16

        if self.device == "xpu":
            return torch.bfloat16

        return torch.float32

    def get_device_obj(self):
        """Returns the actual torch.device object."""
        if self.device == "directml":
            import torch_directml
            return torch_directml.device()
        return torch.device(self.device)

    def clear_cache(self):
        """Triggers hardware-specific memory management/garbage collection."""
        gc.collect()

        if self.device == "cuda":
            torch.cuda.empty_cache()
            if hasattr(torch.cuda, "synchronize"):
                torch.cuda.synchronize()

        elif self.device == "mps":
            if hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
                torch.mps.empty_cache()

        elif self.device == "xpu":
            if hasattr(torch, "xpu") and hasattr(torch.xpu, "empty_cache"):
                torch.xpu.empty_cache()

        logging.debug(f"[HardwareManager] Memory cache cleared for {self.device}")

    def get_telemetry(self) -> dict:
        """Returns hardware-specific telemetry for the /health endpoint."""
        data = {
            "device": self.device,
            "backend": self.backend,
            "dtype": str(self.dtype),
        }

        if self.device == "cuda":
            data["vram_allocated"] = f"{torch.cuda.memory_allocated()/1024**3:.2f}GB"
            data["vram_reserved"] = f"{torch.cuda.memory_reserved()/1024**3:.2f}GB"
            data["gpu_name"] = torch.cuda.get_device_name(0)

        return data

# Singleton instance
hardware_manager = HardwareManager()
