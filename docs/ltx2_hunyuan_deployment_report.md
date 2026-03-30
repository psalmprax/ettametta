# LTX-2 19B & HunyuanVideo 1.5: Deployment & Debugging Report

This document outlines the end-to-end process of integrating, debugging, and stabilizing the multi-model video generation engine on the Vast.ai remote rendering node.

## 🚀 Overview

The goal was to upgrade the existing video generation infrastructure to support:
1. **LTX-2 19B**: High-fidelity Audio-to-Video (A2V) generation.
2. **HunyuanVideo 1.5**: State-of-the-art Text-to-Video (T2V) generation.

## 🛠️ Installation & Setup

### Environment
- **Node**: Vast.ai (RTX 6000 Ada / RTX 8000)
- **OS**: Linux (Ubuntu)
- **Runtime**: Python 3.12.3, PyTorch 2.6.0 (Upgraded from 2.5.1 to support SpeechT5/LTX-2).

### Model Configuration
- **LTX-2 19B**: Loaded via `diffusers` with a phase-based streaming strategy to fit the 19B transformer into VRAM while maintaining audio conditioning.
- **HunyuanVideo 1.5**: Integrated using the Diffusers-compatible ID: `hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-720p_t2v`.

---

## 🔍 Debugging & Critical Fixes

### 1. The "RoPE Metadata" TypeError
**Error:** `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`
- **Cause**: The LTX-2 19B transformer's `forward` pass requires explicit spatial and temporal metadata (`num_frames`, `height`, `width`, `fps`) to generate RoPE (Rotary Positional Embedding) coordinates. In the default `diffusers` implementation, these were often `None` when called from standard pipelines.
- **Fix**: Implemented a **Consolidated Forward Patch** in `main.py`. This monkey-patch captures metadata from the pipeline's `__call__` and injects it directly into the transformer attributes before the diffusion loop begins.

### 2. The "Meta-Device" RuntimeError
**Error:** `RuntimeError: Tensor on device meta is not on the expected device cuda:0!`
- **Cause**: To save VRAM, the 19B model parameters are often initialized on the `meta` device and streamed to the GPU. During this process, some input tensors (especially audio conditioning and RoPE scales) remained on the `meta` device, causing a collision when combined with GPU-resident latents.
- **Fix**: Applied **Aggressive Device Casting**. Updated the patched `forward` method to iterate through all keyword arguments and explicitly move every tensor to `hidden_states.device` before calling the original implementation.

### 3. Audio Conditioning for LTX-2
- **Challenge**: LTX-2 is fundamentally designed as an audio-conditioned model. Omitting audio hidden states results in either a crash or corrupted visual output.
- **Solution**: Patched the rendering loop to generate audio embedding using the `SpeechT5` and `EnCodec` pipelines. These embeddings are passed as `audio_hidden_states` and `audio_encoder_hidden_states` into the transformer.

### 4. Infrastructure Stabilization
- **Port Conflicts**: Multiple crashed uvicorn sessions left stale sockets.
- **Solution**: Shifted the production port to **8122** and implemented a surgical `pkill` + `fuser` cleanup script to reclaim control of the rendering ports.
- **Lazy Loading**: Maintained a lazy loading strategy where weights are only streamed into GPU memory upon the first request, allowing the server to idle at ~0GB VRAM until triggered.

---

## ✅ Final Status

- **LTX-2 19B**: Stable, rendering with full audio conditioning and RoPE metadata.
- **HunyuanVideo 1.5**: Stable, accessible via `/generate` with fallback to `fal-ai` if GPU capacity is exceeded.
- **Benchmark**: The `storyboard_composer.py` is fully operational via an SSH tunnel to Port **8122**.

**Current Health Check:**
```json
{
  "status": "healthy",
  "gpu": "cuda",
  "vram_allocated": "36.10GB"
}
```

---
*Report generated on 2026-03-08.*
