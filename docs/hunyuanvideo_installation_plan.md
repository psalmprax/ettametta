# HunyuanVideo & LTX-2 Multi-Model Installation Plan

## Overview
This project supports two video generation models:
- **HunyuanVideo**: Tencent's state-of-the-art text-to-video model
- **LTX-2**: Lightricks audio-to-video model (requires audio conditioning)

## Architecture
```
                    ┌─────────────────┐
                    │  FastAPI Server │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
     │ /generate   │ │ /generate   │ │ /generate   │
     │ (auto-      │ │ hunyuan     │ │ ltx2        │
     │  select)    │ │ (T2V)       │ │ (A2V)       │
     └─────────────┘ └─────────────┘ └─────────────┘
              │              │              │
              ▼              ▼              ▼
     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
     │ Auto-select │ │ Hunyuan    │ │ LTX-2       │
     │ based on   │ │ Video      │ │ + Audio     │
     │ input      │ │ Pipeline   │ │ Encoder     │
     └─────────────┘ └─────────────┘ └─────────────┘
```

## Model Specifications
- **Type**: Text-to-Video (T2V)
- **VRAM Required**: 16GB+ (optimal with 24GB+)
- **Quality**:⭐⭐⭐⭐⭐ (top-tier open-source)
- **Repository**: https://github.com/Tencent-Hunyuan/HunyuanVideo

## Prerequisites
- NVIDIA GPU with CUDA 12+
- Python 3.10+
- ~50GB disk space for model weights
- Current remote server: root@220.135.0.171:45672

## Installation Steps

### Step 1: Install Dependencies
```bash
# Install PyTorch with CUDA support
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install core dependencies
pip install diffusers transformers accelerate safetensors

# Install additional dependencies
pip install omegaconf einops decord opencv-python
```

### Step 2: Clone Repository
```bash
cd /workspace
git clone https://github.com/Tencent-Hunyuan/HunyuanVideo.git
cd HunyuanVideo
```

### Step 3: Download Model Weights
The model requires several components:
- ` hunyuanvideo_腾视` - Main model weights (~20GB)
- Config files

Weights can be downloaded from Hugging Face:
```bash
# Using huggingface-cli
huggingface-cli download Tencent-Hunyuan/HunyuanVideo --local-dir ./models/HunyuanVideo
```

### Step 4: Create Inference Script
Create `/workspace/remote_ai_group/hunyuan_inference.py`:

```python
import torch
from diffusers import HunyuanVideoPipeline, HunyuanVideoSDPipeline
from diffusers.utils import export_to_video

# Use SD version for lower VRAM (12GB) or full for best quality (24GB+)
pipe = HunyuanVideoSDPipeline.from_pretrained(
    "Tencent/HunyuanVideo",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe.to("cuda")

# Generate video
prompt = "A beautiful sunset over the ocean"
video = pipe(
    prompt,
    num_inference_steps=30,
    height=512,
    width=512,
    num_frames=73,
    guidance_scale=7.5
).frames[0]

# Save
output_path = export_to_video(video, output_video_path="output.mp4")
```

### Step 5: Create FastAPI Integration
Add `/generate_hunyuan` endpoint to main.py:

```python
@app.post("/generate_hunyuan")
async def generate_hunyuan(req: GenerateRequest):
    """HunyuanVideo generation endpoint"""
    # Load model if not cached
    if hunyuan_pipe is None:
        hunyuan_pipe = load_hunyuan_model()
    
    video = hunyuan_pipe(
        prompt=req.prompt,
        num_inference_steps=req.steps or 30,
        height=req.height or 512,
        width=req.width or 512,
        num_frames=req.frames or 73,
        guidance_scale=req.guidance_scale or 7.5
    )
    
    # Save and return video path
    return {"video_path": save_video(video)}
```

## API Endpoints

### POST /generate_hunyuan
```json
{
  "prompt": "A cat walking in the snow",
  "num_inference_steps": 30,
  "height": 512,
  "width": 512,
  "num_frames": 73,
  "guidance_scale": 7.5
}
```

### GET /models
List available models (for switching between LTX-2 and HunyuanVideo)

## Memory Optimization
- Use `torch.compile()` for faster inference
- Enable VAE tiling for long videos
- Use fp16 for reduced memory footprint

## Troubleshooting

### OOM Errors
- Reduce num_frames to 49
- Use SD (standard definition) pipeline
- Enable model offloading

### Slow Generation
- Use torch.compile
- Increase batch size if VRAM allows
- Use SSD for model storage

## Next Steps
1. Install dependencies on remote server
2. Download model weights (~20GB)
3. Create inference script
4. Add FastAPI endpoints
5. Test with sample prompts

## Timeline Estimate
- Dependencies: 10 minutes
- Model download: 30-60 minutes (depends on internet)
- Integration: 20 minutes
- Testing: 10 minutes
- **Total**: ~1.5 hours
