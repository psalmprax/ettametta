# GPU Server Agnostic Configuration

This system automatically detects GPU hardware and optimizes VRAM usage for video generation across different GPU servers using the proven optimization hierarchy:

## 🥇 Optimization Priority (Most Effective First)

1. **Efficient Attention (xFormers)** - BEST overall, reduces VRAM + speeds up
2. **Resolution + Frame Tuning** - Biggest practical win (480p, 8-12 frames)
3. **FP16 Precision** - 40-50% VRAM reduction, no quality loss
4. **VAE Slicing/Tiling** - Prevents memory spikes, slight slowdown
5. **Quantization (INT8/INT4)** - Only if needed, quality trade-offs
6. **CPU Offloading** - Last resort, very slow

## 🎬 Animation Models Available

**AnimateDiff**: Specialized for smooth character animations and consistent motion
- **VRAM**: 8GB (optimized)
- **Best for**: Character animations, smooth movement, consistent motion
- **Format**: 512x512 square videos, 16 frames
- **Quality**: High frame coherence, fluid animation

**Other models with animation capabilities:**
- **LTX-Video**: Good motion, fast generation
- **Mochi**: Fluid movement, complex motion
- **CogVideo**: Professional animation quality
- **ZeroScope**: Creative animations

## Auto-Detection

The system automatically detects:
- GPU type (NVIDIA CUDA, AMD ROCm, Apple MPS, Intel XPU, DirectML)
- Available VRAM
- Optimal concurrent job slots

## Configuration Options

### Environment Variables (recommended for production)

```bash
# Force specific VRAM amount (overrides auto-detection)
GPU_FORCE_VRAM_GB=24

# Set optimization level
GPU_OPTIMIZATION_LEVEL=safe  # safe, medium, extreme

# Override calculated queue slots
GPU_QUEUE_SLOTS=2

# Debug mode
DEBUG=false
```

### Configuration Examples

#### NVIDIA RTX 4090 (24GB VRAM)
```bash
GPU_OPTIMIZATION_LEVEL=safe  # 6-8GB per job → 3-4 concurrent jobs
# Auto-detected: 24GB VRAM → 3 concurrent video generation jobs
```

#### NVIDIA RTX 3060 (8GB VRAM)
```bash
GPU_OPTIMIZATION_LEVEL=safe  # 6-8GB per job → 1 concurrent job
# Auto-detected: 8GB VRAM → 1 concurrent video generation job
```

#### Intel Arc GPU (with XPU)
```bash
GPU_FORCE_VRAM_GB=16  # If auto-detection fails
GPU_OPTIMIZATION_LEVEL=medium  # More conservative for XPU
```

## Hardware-Specific Optimizations

### NVIDIA CUDA
- Uses FP16/INT8 quantization
- xFormers attention optimization
- VAE tiling/slicing enabled
- Up to 4 concurrent jobs on high-VRAM GPUs

### AMD ROCm
- Similar to CUDA but with ROCm-specific optimizations
- VAE tiling/slicing for memory efficiency

### Intel XPU
- More conservative VRAM allocation
- Optimized for Intel Arc GPUs
- Lower concurrency limits

### Apple MPS / DirectML
- CPU fallback with optimized single-job performance
- Minimal concurrency (1 job max)

## Monitoring

Check GPU detection and queue slots:

```python
from api.config import settings

print("GPU Info:", settings.GPU_HARDWARE_INFO)
print("Effective Slots:", settings.EFFECTIVE_GPU_QUEUE_SLOTS)
print("VRAM GB:", settings.DETECTED_GPU_VRAM_GB)
```

## Troubleshooting

### VRAM Not Detected
If GPU VRAM isn't auto-detected, set `GPU_FORCE_VRAM_GB` manually:

```bash
export GPU_FORCE_VRAM_GB=16
```

### Override Queue Slots
For custom concurrency control:

```bash
export GPU_QUEUE_SLOTS=1  # Force single job regardless of VRAM
```

### Hardware Detection Issues
Check logs for hardware detection warnings. The system will fall back to conservative defaults if detection fails.

## 🚀 Quality Enhancement (Real-ESRGAN)

Enable post-processing enhancement for better quality without high VRAM usage:

```python
# Generate with quality enhancement
video = await generate_video(
    prompt="A cinematic scene...",
    engine="ltx-video",
    enhance_quality=True  # Enables Real-ESRGAN upscaling
)
```

**Benefits:**
- Generate at 480p (low VRAM) + upscale to 4K (high quality)
- Better final results than pushing one model too far
- Post-processing approach avoids quantization artifacts

## ⚡ Pro Strategy Implementation

The system implements the "generate cheap + enhance" approach:

1. **Low-VRAM Generation**: 480p, 8-12 frames, FP16 + xFormers
2. **Quality Enhancement**: Real-ESRGAN x4 upscaling
3. **Result**: High quality output with optimal VRAM usage