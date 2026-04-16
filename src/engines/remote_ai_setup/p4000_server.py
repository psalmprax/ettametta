import os
import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import asyncio
from pathlib import Path

# P4000-specific imports
from animatediff_laptop_inference import generate_animatediff_laptop
from p4000_config import get_p4000_optimization_settings, is_p4000_compatible

app = FastAPI(title="ettametta P4000 AI Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    prompt: str
    duration: int = 4  # Shorter for P4000
    height: int = 384  # P4000 optimized
    width: int = 384   # P4000 optimized
    num_frames: int = 8  # P4000 optimized

@app.on_event("startup")
async def startup_event():
    """P4000-specific startup checks"""
    print("🎯 Starting ettametta P4000 AI Server...")

    # Check GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3

        if "P4000" in gpu_name:
            print(f"✅ Detected NVIDIA P4000 with {vram_gb:.1f}GB VRAM")
            print("🎯 P4000 optimizations applied automatically")

            # Load P4000 config
            p4000_config = get_p4000_optimization_settings()
            print(f"📊 Max resolution: {p4000_config['animation']['max_resolution']}")
            print(f"🎬 Recommended frames: {p4000_config['animation']['recommended_frames']}")
        else:
            print(f"⚠️ GPU detected: {gpu_name} ({vram_gb:.1f}GB VRAM)")
            print("💡 Using laptop-optimized settings")
    else:
        print("❌ No CUDA GPU detected - using CPU (very slow)")

    # Setup ngrok if available
    try:
        from pyngrok import ngrok
        if "NGROK_AUTH_TOKEN" in os.environ:
            ngrok.set_auth_token(os.environ["NGROK_AUTH_TOKEN"])
            public_url = ngrok.connect(8122).public_url
            print(f"🚀 Server accessible at: {public_url}")
            print("💡 Share this URL with your ettametta instance")
        else:
            print("⚠️ NGROK_AUTH_TOKEN not set - server accessible locally only")
            print("💡 Get token from: https://ngrok.com")
    except ImportError:
        print("⚠️ pyngrok not installed - server accessible locally only")

@app.get("/health")
async def health_check():
    """P4000-specific health check"""
    gpu_info = "CPU"
    vram_info = "N/A"

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        gpu_info = f"{gpu_name}"
        vram_info = f"{vram_gb:.1f}GB"

    return {
        "status": "healthy",
        "gpu": gpu_info,
        "vram": vram_info,
        "model": "animatediff_p4000",
        "optimizations": "p4000_8gb",
        "max_resolution": "384x384",
        "recommended_frames": 8
    }

@app.post("/generate_animatediff")
async def generate_animation(request: VideoRequest):
    """Generate animation optimized for P4000 8GB"""
    try:
        print(f"🎬 P4000 generation request: {request.prompt[:50]}...")

        # P4000 compatibility check
        resolution = f"{request.width}x{request.height}"
        compatible, message = is_p4000_compatible(resolution, request.num_frames)

        if not compatible:
            return {
                "error": "p4000_incompatible",
                "message": message,
                "suggestion": "Use 384x384 resolution and max 12 frames"
            }

        # Generate with P4000 optimizations
        result = await generate_animatediff_laptop(
            prompt=request.prompt,
            num_frames=min(request.num_frames, 12),  # P4000 limit
            height=min(request.height, 384),          # P4000 limit
            width=min(request.width, 384)             # P4000 limit
        )

        if "error" in result:
            return result

        return {
            "job_id": f"p4000_{hash(request.prompt) % 10000}",
            "status": "completed",
            "video_url": result.get("video_url"),
            "model": "animatediff_p4000",
            "gpu_optimized": "p4000_8gb",
            "generation_time": result.get("generation_time", "4-6_min"),
            "resolution": result.get("resolution", f"{request.width}x{request.height}"),
            "frames": result.get("frames", request.num_frames)
        }

    except Exception as e:
        print(f"❌ P4000 generation failed: {e}")
        return {"error": str(e)}

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Serve generated video files"""
    file_path = Path("outputs") / filename
    if file_path.exists():
        return FileResponse(file_path, media_type="video/mp4")
    return {"error": "file_not_found"}

@app.get("/p4000_config")
async def get_p4000_config():
    """Get P4000-specific configuration and recommendations"""
    return get_p4000_optimization_settings()

if __name__ == "__main__":
    print("🎯 NVIDIA P4000 8GB AI Video Server")
    print("=" * 50)

    # Show P4000 recommendations
    config = get_p4000_optimization_settings()
    print(f"📊 Max Resolution: {config['animation']['max_resolution']}")
    print(f"🎬 Recommended Frames: {config['animation']['recommended_frames']}")
    print(f"⏱️ Estimated Generation: {config['animation']['estimated_generation_time']}")
    print(f"🧠 VRAM Usage: {config['animation']['estimated_vram_usage']}")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8122)</content>
<parameter name="filePath">remote_ai_setup/update_windows_server.py