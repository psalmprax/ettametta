# Remote AI Server - Complete Status Report

## Server Info
- **SSH**: `ssh -i /home/psalmprax/Music/id_rsa -p 45672 root@220.135.0.171`
- **GPU**: Quadro RTX 8000 (49GB VRAM) - Hardware OK
- **Issue**: CUDA context broken (PyTorch can't access GPU)

---

## 🟢 CURRENT STATUS: WORKING (WITH VRAM LIMITATIONS)

The remote server is currently operational, but the **HunyuanVideo 1.5 (19B)** model is encountering **Out of Memory (OOM)** errors due to its high VRAM requirements (~43GB+).

### Summary Table

| Endpoint | Status | Model | Notes |
|----------|--------|-------|-------|
| `/health` | ✅ Working | - | Shows GPU status OK |
| `/voice` | ✅ Working | SpeechT5 | Audio generation OK |
| `/generate_hunyuan` | ❌ OOM Error | HunyuanVideo-480p | Exceeds 48GB capacity |
| `/generate` | ❌ OOM Error | zeroscope | Impacted by previous model loads |

### Root Cause Analysis
The HunyuanVideo-1.5-Diffusers-480p_t2v model is a **19 billion parameter** model:
- ~38GB VRAM for model weights (FP16)
- Additional memory for activations and processing (requires ~43GB+)
- The **Quadro RTX 8000** (48GB) is right on the edge; context switching and activations push it over the limit.

### Recommendation
Use **quantized models** (4-bit/8-bit) or lighter models like **Stable Video Diffusion (SVD)**. GGUF models via llama-cpp-python are also being explored.

---

## 🎬 AVAILABLE VIDEO MODELS (UPDATED AUDIT)

We currently have **3 active video model architectures** fully implemented, with several legacy/specialized models tracked.

### 1. HunyuanVideo 1.5 (Tencent)
- **Status**: ✅ **ACTIVE & OPTIMIZED**
- **Location**: `hunyuan_inference.py`
- **Capabilities**: 19B Parameter Text-to-Video (T2V).
- **Optimization**: 8-bit Quantization + CPU Offloading (Fits in ~25GB VRAM).
- **Endpoint**: `/generate_hunyuan`

### 2. LTX-2 19B (Lightricks)
- **Status**: ✅ **ACTIVE (PRO ENGINE)**
- **Location**: `main.py` (via `load_ltx_19b_transformer`)
- **Capabilities**: High-end T2V and Image-to-Video (I2V) with:
    - **Audio-Driven Video**: Injects SpeechT5 conditioning into the 19B latent space.
    - **Pro-Mastering**: Integrated Real-ESRGAN (8K) and GFPGAN (Face Restoration).
- **Endpoint**: `/generate` (now defaults to LTX-2)

### 3. AnimateDiff (SDXL / SD 1.5)
- **Status**: ✅ **ACTIVE**
- **Location**: `animatediff_inference.py`
- **Capabilities**: 
    - Text-to-Video (Fast 4-8 step Lightning mode).
    - Image-to-Video (Animating static portraits/landscapes).
- **Note**: Best for lower-latency motion effects.

### 4. Specialized & Legacy Models
- **Wav2Lip**: 🛠️ **PARTIALLY IMPLEMENTED** (Code exists in `main.py-pro`; requires `wav2lip_repo`).
- **Zeroscope**: ⏳ **LEGACY** (Referenced as baseline; superseded by LTX-2/Hunyuan).
- **LTX-1**: 🚫 **REMOVED** (Migrated to LTX-2 19B).
- **SVD (Stable Video Diffusion)**: 🗓️ **PLANNED** (Recommended as fallback for heavy tasks).

---

## 🛠️ UTILITY AI MODELS
- **SpeechT5**: TTS & Audio Conditioning (Active).
- **Moondream2**: Vision-Language Model (VLM) for scene analysis (Active).
- **Llama-3.1-8B**: Scripting and metadata generation (Active).
- **Faster-Whisper**: High-speed transcription (Active).

---

## DISK SPACE
- Total: 235GB
- Used: 118GB  
- Available: 117GB ✅
