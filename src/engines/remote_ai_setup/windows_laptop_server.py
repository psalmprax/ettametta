# Windows Laptop Video Model Setup with Ngrok

## Prerequisites

### Hardware Requirements
- **GPU**: NVIDIA RTX 3060/4060/3060 Ti or better (8GB+ VRAM)
- **RAM**: 16GB+ system RAM
- **Storage**: 50GB+ free space for models
- **OS**: Windows 10/11

### Software Requirements
- Python 3.10-3.11 (avoid 3.12+ due to compatibility issues)
- Git
- CUDA 11.8 or 12.1 (if using NVIDIA)

## 1. Install Python and Dependencies

### Install Miniconda (Recommended)
```bash
# Download from: https://docs.conda.io/en/latest/miniconda.html
# Create environment
conda create -n ettametta-ai python=3.11
conda activate ettametta-ai
```

### Install PyTorch (CUDA Version)
```bash
# For CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# For CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Install Core Dependencies
```bash
pip install fastapi uvicorn pyngrok
pip install transformers diffusers accelerate huggingface_hub safetensors
pip install opencv-python pillow imageio imageio-ffmpeg
```

## 2. Setup the Remote AI Server

### Clone and Prepare
```bash
cd remote_ai_setup
pip install -r requirements.txt
```

### Create Windows-Specific Config
Create `windows_config.py`:

```python
import os

# Windows-specific paths
os.environ["HF_HOME"] = "C:\\Users\\YourName\\.hf_cache"

# Laptop-optimized settings
LAPTOP_MODELS = {
    "animatediff_v15": {
        "name": "AnimateDiff V1.5 (Laptop Optimized)",
        "repo_id": "guoyww/AnimateDiff",
        "type": "diffusers",
        "vram_estimate": "6GB",  # Optimized for laptops
    }
}

# Ngrok settings
NGROK_AUTH_TOKEN = "your_ngrok_token_here"  # Get from https://ngrok.com
EXPOSE_PORT = 8122
```

## 3. Create Laptop-Optimized Server

Create `windows_laptop_server.py`:

```python
import os
import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok
import uvicorn
from pydantic import BaseModel

app = FastAPI(title="ettametta Laptop AI Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    prompt: str
    duration: int = 4  # Shorter for laptops

@app.on_event("startup")
async def startup_event():
    """Setup ngrok tunnel"""
    if "NGROK_AUTH_TOKEN" in os.environ:
        ngrok.set_auth_token(os.environ["NGROK_AUTH_TOKEN"])

    # Create tunnel
    public_url = ngrok.connect(8122).public_url
    print(f"🚀 Server accessible at: {public_url}")
    print("💡 Share this URL with your ettametta instance")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "vram": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB" if torch.cuda.is_available() else "N/A",
        "model": "animatediff_laptop"
    }

@app.post("/generate_animatediff")
async def generate_animation(request: VideoRequest):
    """Generate short animation optimized for laptop"""
    try:
        # Laptop-optimized generation
        from animatediff_inference import generate_animatediff_laptop

        result = await generate_animatediff_laptop(
            prompt=request.prompt,
            num_frames=16,  # Shorter animation
            height=512,
            width=512
        )

        return {
            "job_id": f"laptop_{hash(request.prompt) % 10000}",
            "status": "completed",
            "video_uri": result.get("video_uri"),
            "model": "animatediff_laptop"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8122)
```

## 4. Create Laptop-Optimized AnimateDiff

Create `animatediff_laptop_inference.py`:

```python
import torch
from diffusers import AnimateDiffPipeline, DDIMScheduler, MotionAdapter
from diffusers.utils import export_to_video
import os

def generate_animatediff_laptop(prompt, num_frames=16, height=512, width=512):
    """Laptop-optimized AnimateDiff generation"""

    # Use CPU offloading to save VRAM
    pipe = AnimateDiffPipeline.from_pretrained(
        "guoyww/animatediff-motion-adapter-v1-5-2",
        torch_dtype=torch.float16
    ).to("cuda" if torch.cuda.is_available() else "cpu")

    # Enable CPU offloading for laptops
    pipe.enable_model_cpu_offload()
    pipe.enable_vae_slicing()

    # Laptop-optimized scheduler
    pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)

    # Generate with laptop constraints
    result = pipe(
        prompt=prompt,
        negative_prompt="low quality, blurry, distorted",
        num_frames=num_frames,
        height=height,
        width=width,
        num_inference_steps=20,  # Fewer steps for speed
        guidance_scale=7.5,
        generator=torch.manual_seed(42)
    )

    # Save video
    output_path = f"outputs/laptop_animation_{hash(prompt)}.mp4"
    os.makedirs("outputs", exist_ok=True)

    export_to_video(result.frames[0], output_path, fps=8)  # Lower FPS for smaller files

    return {"video_uri": f"http://localhost:8122/download/{os.path.basename(output_path)}"}

@app.get("/download/{filename}")
async def download_file(filename: str):
    return FileResponse(f"outputs/{filename}")
```

## 5. Setup Ngrok for External Access

### Install Ngrok
```bash
# Download from: https://ngrok.com/download
# Or install via chocolatey: choco install ngrok
```

### Configure Ngrok
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### Create Ngrok Startup Script
Create `start_laptop_server.bat`:

```batch
@echo off
cd /d %~dp0

REM Activate conda environment
call conda activate ettametta-ai

REM Set environment variables
set HF_HOME=C:\Users\%USERNAME%\.hf_cache
set NGROK_AUTH_TOKEN=your_ngrok_token_here

REM Start the server
python windows_laptop_server.py
```

## 6. Connect to ettametta

### Update ettametta Config
In your ettametta `api/config.py`, add:

```python
# Laptop AI server
LAPTOP_AI_URL = "https://your-ngrok-url.ngrok.io"  # From ngrok output
```

### Update Synthesis Service
In `services/video_engine/synthesis_service.py`, add laptop support:

```python
# Add to local_gpu_engines or create separate laptop section
elif engine == "animatediff_laptop":
    return await self._generate_laptop_animatediff(prompt, aspect_ratio)
```

## 7. Usage

### Start Your Laptop Server
```bash
# Double-click start_laptop_server.bat
# Or run: python windows_laptop_server.py
```

### Test Connection
```bash
curl https://your-ngrok-url.ngrok.io/health
```

### Generate Videos
From ettametta:
```python
video = await synthesize_video(
    prompt="A cat dancing on a laptop",
    engine="animatediff_laptop"
)
```

## Performance Expectations

### RTX 3060 (8GB):
- **Generation time**: 2-3 minutes per video
- **Quality**: Good 512x512 animations
- **Daily capacity**: 20-30 videos

### RTX 4060 (8GB):
- **Generation time**: 1-2 minutes per video
- **Quality**: Better animations
- **Daily capacity**: 40-50 videos

## Troubleshooting

### Common Issues:
1. **CUDA out of memory**: Reduce resolution to 384x384
2. **Slow generation**: Enable `--cpu-offload` in pipeline
3. **Ngrok disconnects**: Use `ngrok tcp 8122` for persistent tunnels

### Optimization Tips:
- Use shorter prompts (under 50 words)
- Keep animations under 16 frames
- Close other GPU-intensive applications

This setup gives you a **personal AI video generation server** running on your Windows laptop with global access via ngrok! 🎬✨</content>
<parameter name="filePath">remote_ai_setup/windows_laptop_setup.md