# Video Generation Models - Installation & Usage Guide

## Overview

This document covers all video generation models tested and deployed on the Viral Forge remote server.

## Remote Server Details

| Property | Value |
|----------|-------|
| **Host** | root@220.135.0.171 |
| **Port** | 45672 |
| **SSH Key** | /home/psalmprax/Music/id_rsa |
| **GPU** | Quadro RTX 8000 (48GB VRAM) |
| **Location** | /workspace/remote_ai_group |
| **Disk** | 235GB total |

---

## 1. HunyuanVideo (Tencent)

### Model Info
- **Type**: Text-to-Video (T2V)
- **Size**: ~33GB (480p), ~50GB (720p)
- **VRAM Required**: 16GB+ (24GB+ optimal)
- **Quality**: ⭐⭐⭐⭐⭐
- **HuggingFace**: `hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_t2v`

### Installation

```bash
# SSH to server
ssh -i /home/psalmprax/Music/id_rsa -p 45672 root@220.135.0.171

# Navigate to project
cd /workspace/remote_ai_group
source venv/bin/activate

# Download model (requires ~33GB disk)
python -c "
from huggingface_hub import hf_hub_download
file = hf_hub_download(
    repo_id='hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_t2v',
    filename='*',
    local_dir='.'
)
"
```

### Usage

```python
import torch
from diffusers import DiffusionPipeline
from diffusers.utils import export_to_video

pipe = DiffusionPipeline.from_pretrained(
    'hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_t2v',
    torch_dtype=torch.float16
).to('cuda')

output = pipe(
    prompt='Your prompt here',
    num_inference_steps=25,
    num_frames=49
)

video = output.frames[0]
export_to_video(video, 'output.mp4')
```

### Disk Cleanup

```bash
rm -rf /root/.cache/huggingface/hub/models--hunyuanvideo-community--HunyuanVideo-1.5-Diffusers-480p_t2v
```

---

## 2. LTX-Video (Lightricks)

### Model Info
- **Type**: Text-to-Video (T2V)
- **Size**: ~27GB
- **VRAM Required**: 12GB+
- **Quality**: ⭐⭐⭐⭐
- **HuggingFace**: `Lightricks/LTX-Video`

### Installation

```bash
# Same as HunyuanVideo - model downloads automatically when first used
```

### Usage

```python
import torch
from diffusers import LTXPipeline
from diffusers.utils import export_to_video

pipe = LTXPipeline.from_pretrained(
    'Lightricks/LTX-Video',
    torch_dtype=torch.float16
).to('cuda')

output = pipe(
    prompt='Your prompt here',
    num_inference_steps=10,
    num_frames=17,
    height=512,
    width=512
)

video = output.frames[0]
export_to_video(video, 'output.mp4')
```

---

## 3. Zeroscope

### Model Info
- **Type**: Text-to-Video (T2V)
- **Size**: ~5GB
- **VRAM Required**: 8GB+
- **Quality**: ⭐⭐⭐
- **HuggingFace**: `cerspense/zeroscope_v2_576w`

### Installation

```bash
# Downloads automatically on first use
```

### Usage

```python
import torch
from diffusers import DiffusionPipeline
from diffusers.utils import export_to_video

pipe = DiffusionPipeline.from_pretrained(
    'cerspense/zeroscope_v2_576w',
    torch_dtype=torch.float16
).to('cuda')

output = pipe(
    prompt='Your prompt here',
    num_inference_steps=10,
    num_frames=17,
    height=320,
    width=576
)

video = output.frames[0]
export_to_video(video, 'output.mp4')
```

---

## 4. LTX-2 (Lightricks) - NOT RECOMMENDED

### Model Info
- **Type**: Audio-to-Video (A2V)
- **Size**: ~135GB
- **VRAM Required**: 80GB+ (NOT compatible with RTX 8000)
- **Quality**: ⭐⭐⭐⭐⭐
- **Status**: Requires more VRAM than available

### Notes
- LTX-2 requires audio conditioning
- Needs 80GB+ VRAM (H100/A100)
- RTX 8000 (48GB) is insufficient

---

## 5. ComfyUI Installation

### Installation

```bash
# SSH to server
ssh -i /home/psalmprax/Music/id_rsa -p 45672 root@220.135.0.171

# Clone ComfyUI
cd /workspace
git clone https://github.com/comfyanonymous/ComfyUI.git

# Install dependencies (using existing venv)
/workspace/remote_ai_group/venv/bin/pip install -r requirements.txt

# Start server
cd /workspace/ComfyUI
/workspace/remote_ai_group/venv/bin/python main.py --listen 0.0.0.0 --port 8188
```

### Access
- **URL**: http://220.135.0.171:8188

### Download Models

```bash
# Download Stable Diffusion checkpoints
cd /workspace/ComfyUI/models/checkpoints
/workspace/remote_ai_group/venv/bin/python -c "
from huggingface_hub import hf_hub_download
file = hf_hub_download(
    repo_id='runwayml/stable-diffusion-v1-5',
    filename='v1-5-pruned.safetensors',
    token='hf_your_token'
)
"
```

---

## Disk Management Strategy

### "Download When Needed" Pattern

The server uses a strategy where large models are downloaded only when needed and cleaned up after use.

```bash
# Check disk space
df -h /workspace

# List cached models
du -sh /root/.cache/huggingface/hub/models--*

# Clean up all models except LTX-2 (if you want to keep it cached)
rm -rf /root/.cache/huggingface/hub/models--*
```

### Recommended Setup

| Model | Cache? | Size | Reason |
|-------|--------|------|--------|
| HunyuanVideo 480p | No | 33GB | Download when needed |
| LTX-Video | No | 27GB | Download when needed |
| Zeroscope | No | 5GB | Download when needed |
| LTX-2 | Optional | 135GB | Too large, not usable |

---

## Troubleshooting

### Out of Disk Space
```bash
# Check what's using space
du -sh /workspace/*
du -sh /root/.cache/huggingface/hub/*

# Clean up
rm -rf /root/.cache/huggingface/hub/models--*
```

### Out of VRAM
```bash
# Check GPU memory
nvidia-smi

# Kill existing processes
pkill -f python
```

### Model Download Fails
- Ensure HF_TOKEN is set
- Check network connectivity
- Verify sufficient disk space

---

## API Usage via FastAPI

The remote server runs a FastAPI server that exposes video generation endpoints:

```python
import requests

# Example API call
response = requests.post(
    "http://220.135.0.171:8122/generate",
    json={
        "prompt": "Your prompt",
        "model": "hunyuan"  # or "ltx", "zeroscope"
    }
)
```

---

## Cost Comparison

| Model | Disk Space | VRAM | Speed | Quality |
|-------|------------|------|-------|---------|
| HunyuanVideo | 33GB | 16GB+ | Slow | Best |
| LTX-Video | 27GB | 12GB+ | Medium | Good |
| Zeroscope | 5GB | 8GB+ | Fast | Basic |

---

## Non-Video Models

I have identified the following **5 non-video models** currently on the server:

| Model | Type | Location | Purpose |
|-------|------|----------|---------|
| **Stable Diffusion v1.5** | Image | `/workspace/ComfyUI/models/checkpoints` | Base image generation |
| **SDXL Base 1.0** | Image | `HF Cache: stabilityai/stable-diffusion-xl-base-1.0` | High-res image generation |
| **GFPGAN (Resnet50)** | Restoration | `/workspace/remote_ai_group/gfpgan/weights` | Face restoration / upscaling |
| **GFPGAN (ParseNet)** | Restoration | `/workspace/remote_ai_group/gfpgan/weights` | Face parsing |
| **EnCodec 24kHz** | Audio | `Torch Cache: encodec_24khz` | Audio compression/generation |

---

*Updated: 2026-03-09*
*Author: Viral Forge Team*
