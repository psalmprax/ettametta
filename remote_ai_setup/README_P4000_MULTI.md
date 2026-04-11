import os
import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import asyncio
from pathlib import Path

# P4000 multi-model support
from p4000_multi_model_inference import (
    generate_p4000_video,
    get_p4000_available_models
)
from p4000_config import get_p4000_optimization_settings

app = FastAPI(title="ettametta P4000 Multi-Model AI Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    prompt: str
    model: str = "animatediff"  # animatediff, ltx_video, zeroscope, lite4k
    duration: int = 4
    height: int = 384
    width: int = 384
    num_frames: int = 8

@app.on_event("startup")
async def startup_event():
    """P4000 multi-model startup checks"""
    print("🎯 Starting ettametta P4000 Multi-Model AI Server...")
    print("🎨 Supports: AnimateDiff, LTX-Video, ZeroScope, Lite4K")

    # Check GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3

        if "P4000" in gpu_name:
            print(f"✅ Detected NVIDIA P4000 with {vram_gb:.1f}GB VRAM")
            print("🎯 P4000 multi-model optimizations applied")

            # Show available models
            models = get_p4000_available_models()
            print(f"📋 Available models: {len(models)}")
            for model_id, info in models.items():
                print(f"   • {model_id}: {info['name']} ({info['max_resolution']})")
        else:
            print(f"⚠️ GPU detected: {gpu_name} ({vram_gb:.1f}GB VRAM)")
            print("💡 Using laptop optimizations (not P4000-specific)")
    else:
        print("❌ No CUDA GPU detected")

    # Setup ngrok if available
    try:
        from pyngrok import ngrok
        if "NGROK_AUTH_TOKEN" in os.environ:
            ngrok.set_auth_token(os.environ["NGROK_AUTH_TOKEN"])
            public_url = ngrok.connect(8122).public_url
            print(f"🚀 Server accessible at: {public_url}")
            print("💡 Share this URL with your ettametta instance")
        else:
            print("⚠️ NGROK_AUTH_TOKEN not set")
            print("💡 Server accessible locally at: http://localhost:8122")
    except ImportError:
        print("⚠️ pyngrok not installed")
        print("💡 Server accessible locally at: http://localhost:8122")

@app.get("/health")
async def health_check():
    """P4000 multi-model health check"""
    gpu_info = "CPU"
    vram_info = "N/A"
    p4000_optimized = False

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        gpu_info = f"{gpu_name}"
        vram_info = f"{vram_gb:.1f}GB"
        p4000_optimized = "P4000" in gpu_name

    return {
        "status": "healthy",
        "gpu": gpu_info,
        "vram": vram_info,
        "models_available": list(get_p4000_available_models().keys()),
        "p4000_optimized": p4000_optimized,
        "max_resolution": "384x384 (AnimateDiff), 320x320 (others)",
        "server_type": "p4000_multi_model"
    }

@app.post("/generate_video")
async def generate_video(request: VideoRequest):
    """Generate video with any P4000-compatible model"""
    try:
        print(f"🎬 P4000 {request.model}: {request.prompt[:50]}...")

        # Validate model
        available_models = get_p4000_available_models()
        if request.model not in available_models:
            return {
                "error": f"Model {request.model} not available on P4000",
                "available_models": list(available_models.keys())
            }

        # Generate with selected model
        result = await generate_p4000_video(
            prompt=request.prompt,
            model_type=request.model,
            num_frames=request.num_frames,
            height=request.height,
            width=request.width
        )

        if "error" in result:
            return result

        return {
            "job_id": f"p4000_{request.model}_{hash(request.prompt) % 10000}",
            "status": "completed",
            "video_url": result.get("video_url"),
            "model": f"{request.model}_p4000",
            "gpu_optimized": "p4000_8gb",
            "resolution": result.get("resolution", f"{request.width}x{request.height}"),
            "frames": result.get("frames", request.num_frames),
            "p4000_multi_model": True,
            "available_models": list(available_models.keys())
        }

    except Exception as e:
        print(f"❌ P4000 multi-model generation failed: {e}")
        return {"error": str(e)}

@app.get("/models")
async def get_available_models():
    """Get all P4000-compatible models with details"""
    return get_p4000_available_models()

@app.get("/model/{model_id}")
async def get_model_info(model_id: str):
    """Get detailed info for specific model"""
    models = get_p4000_available_models()
    if model_id in models:
        return models[model_id]
    return {"error": f"Model {model_id} not found"}

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Serve generated video files"""
    file_path = Path("outputs") / filename
    if file_path.exists():
        return FileResponse(file_path, media_type="video/mp4")
    return {"error": "file_not_found"}

@app.get("/p4000_status")
async def get_p4000_status():
    """Get real-time P4000 multi-model status"""
    if torch.cuda.is_available():
        vram_used = torch.cuda.memory_allocated(0) / 1024**3
        vram_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        vram_free = vram_total - vram_used

        return {
            "gpu_name": torch.cuda.get_device_name(0),
            "vram_total_gb": round(vram_total, 1),
            "vram_used_gb": round(vram_used, 1),
            "vram_free_gb": round(vram_free, 1),
            "vram_usage_percent": round((vram_used / vram_total) * 100, 1),
            "p4000_optimized": "P4000" in torch.cuda.get_device_name(0),
            "available_models": list(get_p4000_available_models().keys()),
            "cuda_version": torch.version.cuda,
            "server_type": "multi_model"
        }
    else:
        return {"error": "No CUDA GPU detected"}

if __name__ == "__main__":
    print("🎯 NVIDIA Quadro P4000 Multi-Model AI Server")
    print("=" * 55)
    print("🎨 Supporting multiple video generation models")
    print()

    # Show available models
    models = get_p4000_available_models()
    print(f"📋 Available Models ({len(models)}):")
    for model_id, info in models.items():
        print(f"   • {model_id}: {info['name']}")
        print(f"     └─ {info['max_resolution']}, {info['max_frames']} frames, {info['estimated_time']}")
    print()

    # Show P4000 recommendations
    config = get_p4000_optimization_settings()
    print(f"🎯 P4000 Recommendations:")
    print(f"   • Best model: AnimateDiff (most reliable)")
    print(f"   • Max resolution: {config['animation']['max_resolution']}")
    print(f"   • Optimal frames: {config['animation']['recommended_frames']}")
    print(f"   • VRAM usage: {config['animation']['estimated_vram_usage']}")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8122)</content>
<parameter name="filePath">remote_ai_setup/p4000_server_multi.py