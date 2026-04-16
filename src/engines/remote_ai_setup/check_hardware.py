import os
import sys
import subprocess
import shutil

def is_nvidia_gpu():
    return shutil.which("nvidia-smi") is not None

def is_amd_gpu():
    return shutil.which("rocm-smi") is not None

def is_apple_silicon():
    import platform
    return platform.system() == "Darwin" and platform.machine() == "arm64"

def is_intel_gpu():
    try:
        # Corrected: Check for Intel and VGA on the SAME line to avoid virtual/integrated false positives
        result = subprocess.run(["lspci"], capture_output=True, text=True)
        intel_vga_lines = [line for line in result.stdout.splitlines() if "Intel Corporation" in line and ("VGA" in line or "Display" in line)]
        return len(intel_vga_lines) > 0
    except:
        return False

def get_torch_install_command():
    """Returns the optimal pip install command for the current hardware."""
    
    # 1. Apple Silicon (MPS)
    if is_apple_silicon():
        print("🍏 [Hardware] Apple Silicon detected. Using MPS-optimized Torch.", file=sys.stderr)
        return "pip install torch torchvision torchaudio"

    # 2. NVIDIA (CUDA)
    if is_nvidia_gpu():
        print("🟢 [Hardware] NVIDIA GPU detected. Using CUDA 124-optimized Torch.", file=sys.stderr)
        # Default to CUDA 12.4 for modern GPUs
        return "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124"

    # 3. AMD (ROCm)
    if is_amd_gpu():
        print("🔴 [Hardware] AMD GPU detected. Using ROCm 6.2-optimized Torch.", file=sys.stderr)
        # Default to ROCm 6.2 (latest stable)
        return "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2"

    # 4. Intel (XPU)
    if is_intel_gpu():
        print("🔵 [Hardware] Intel GPU detected. Using IPEX-optimized Torch.", file=sys.stderr)
        # Needs Intel Extension for PyTorch
        return "pip install torch torchvision torchaudio intel-extension-for-pytorch==2.5.0"

    # 5. CPU Fallback
    print("⚪ [Hardware] No compatible GPU detected. Falling back to CPU-only Torch.", file=sys.stderr)
    return "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--pip":
        print(get_torch_install_command())
    else:
        # Debug Info
        print(f"NVIDIA Detection: {is_nvidia_gpu()}")
        print(f"AMD/ROCm Detection: {is_amd_gpu()}")
        print(f"Apple Silicon Detection: {is_apple_silicon()}")
        print(f"Intel GPU Detection: {is_intel_gpu()}")
        print(f"\nRecommended: {get_torch_install_command()}")
