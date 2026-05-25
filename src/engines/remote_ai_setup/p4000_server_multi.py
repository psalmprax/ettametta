import torch
import os
import asyncio
from pathlib import Path
from typing import Any
from src.engines.remote_ai_setup.p4000_config import generate_animatediff_laptop

async def generate_p4000_video(
    prompt: str,
    model_type: str = "animatediff",
    num_frames: int = 8,
    height: int = 384,
    width: int = 384
) -> dict[str, Any]:
    """
    P4000-optimized video generation for multiple model types.
    Extremely aggressive memory optimizations for 8GB VRAM.
    """

    "cuda" if torch.cuda.is_available() else "cpu"

    # P4000 limits - very conservative
    max_resolution = 384
    max_frames = 8

    # Enforce P4000 limits
    height = min(height, max_resolution)
    width = min(width, max_resolution)
    num_frames = min(num_frames, max_frames)

    print(f"🎬 P4000 {model_type}: {prompt[:50]}...")
    print(f"📐 Resolution: {width}x{height}, Frames: {num_frames}")

    try:
        if model_type == "animatediff":
            return await generate_animatediff_laptop(prompt, num_frames, height, width)

        elif model_type == "ltx_video":
            return await asyncio.to_thread(generate_ltx_p4000, prompt, num_frames, height, width)

        elif model_type == "zeroscope":
            return await asyncio.to_thread(generate_zeroscope_p4000, prompt, num_frames, height, width)

        elif model_type == "lite4k":
            return await asyncio.to_thread(generate_lite4k_p4000, prompt, num_frames, height, width)

        else:
            return {"error": f"Model {model_type} not supported on P4000"}

    except torch.cuda.OutOfMemoryError:
        print("❌ P4000 VRAM exhausted - try lower settings")
        # Emergency cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        return {
            "error": "insufficient_vram",
            "suggestion": "Use 320x320 resolution and 6 frames max"
        }

    except Exception as e:
        print(f"❌ P4000 generation failed: {e}")
        return {"error": str(e)}

def generate_ltx_p4000(prompt: str, num_frames: int = 6, height: int = 320, width: int = 320) -> dict[str, Any]:
    """Ultra-aggressive LTX optimization for P4000"""
    try:
        import importlib
        diffusers = importlib.import_module("diffusers")
        ltx_pipeline_class = diffusers.LTXPipeline
        # Use minimal settings for P4000
        pipe = ltx_pipeline_class.from_pretrained(
            "Lightricks/LTX-Video",
            torch_dtype=torch.float16,
        )

        # Maximum memory optimizations
        pipe.enable_model_cpu_offload()
        pipe.enable_vae_slicing()
        pipe.enable_vae_tiling()

        # Very conservative generation
        result = pipe(
            prompt=prompt,
            num_frames=min(num_frames, 6),  # Very limited
            height=min(height, 320),
            width=min(width, 320),
            num_inference_steps=10,  # Minimal steps
            guidance_scale=6.0,
        )

        # Save and cleanup
        output_path = save_video_p4000(result.frames[0], "ltx")
        cleanup_p4000_memory(pipe)

        return {
            "video_uri": f"/download/{os.path.basename(output_path)}",
            "model": "ltx_video_p4000",
            "resolution": f"{width}x{height}",
            "frames": min(num_frames, 6)
        }

    except Exception as e:
        return {"error": f"LTX P4000 failed: {e}"}

def generate_zeroscope_p4000(prompt: str, num_frames: int = 6, height: int = 320, width: int = 320) -> dict[str, Any]:
    """Ultra-aggressive ZeroScope optimization for P4000"""
    try:
        import importlib
        diffusers = importlib.import_module("diffusers")
        v2v_pipeline_class = diffusers.VideoToVideoSDPipeline

        pipe = v2v_pipeline_class.from_pretrained(
            "cerspense/zeroscope_v2_XL",
            torch_dtype=torch.float16,
        )

        pipe.enable_model_cpu_offload()
        pipe.enable_vae_slicing()

        # Minimal settings
        result = pipe(
            prompt=prompt,
            num_frames=min(num_frames, 6),
            height=min(height, 320),
            width=min(width, 320),
            num_inference_steps=8,
            guidance_scale=7.5,
        )

        output_path = save_video_p4000(result.frames[0], "zeroscope")
        cleanup_p4000_memory(pipe)

        return {
            "video_uri": f"/download/{os.path.basename(output_path)}",
            "model": "zeroscope_p4000",
            "resolution": f"{width}x{height}",
            "frames": min(num_frames, 6)
        }

    except Exception as e:
        return {"error": f"ZeroScope P4000 failed: {e}"}

def generate_lite4k_p4000(prompt: str, num_frames: int = 4, height: int = 256, width: int = 256) -> dict[str, Any]:
    """Ultra-aggressive Lite4K optimization for P4000"""
    try:
        import importlib
        diffusers = importlib.import_module("diffusers")
        sd_pipeline_class = diffusers.StableDiffusionPipeline
        # Use a lightweight model
        pipe = sd_pipeline_class.from_pretrained(
            "stabilityai/sd-turbo",
            torch_dtype=torch.float16,
        )

        pipe.enable_model_cpu_offload()

        # Very minimal video generation
        result = pipe(
            prompt=prompt,
            num_frames=min(num_frames, 4),
            height=min(height, 256),
            width=min(width, 256),
            num_inference_steps=6,
            guidance_scale=5.0,
        )

        output_path = save_video_p4000(result.frames[0], "lite4k")
        cleanup_p4000_memory(pipe)

        return {
            "video_uri": f"/download/{os.path.basename(output_path)}",
            "model": "lite4k_p4000",
            "resolution": f"{width}x{height}",
            "frames": min(num_frames, 4)
        }

    except Exception as e:
        return {"error": f"Lite4K P4000 failed: {e}"}

def save_video_p4000(frames, model_name: str) -> str:
    """Save video with P4000-optimized settings"""
    import importlib
    diffusers_utils = importlib.import_module("diffusers.utils")
    export_to_video = diffusers_utils.export_to_video
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    video_filename = f"p4000_{model_name}_{hash(str(frames)) % 100000}.mp4"
    output_path = output_dir / video_filename

    export_to_video(frames, str(output_path), fps=4)  # Lower FPS for smaller files
    return str(output_path)

def cleanup_p4000_memory(pipe):
    """Aggressive memory cleanup for P4000"""
    del pipe
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

def get_p4000_available_models() -> dict[str, dict[str, Any]]:
    """Get all models that can run on P4000"""
    return {
        "animatediff": {
            "name": "AnimateDiff v1.5",
            "description": "Smooth character animations",
            "max_resolution": "384x384",
            "max_frames": 8,
            "estimated_time": "4-6 min",
            "reliability": "High"
        },
        "ltx_video": {
            "name": "LTX-Video (P4000 Optimized)",
            "description": "High-quality video generation",
            "max_resolution": "320x320",
            "max_frames": 6,
            "estimated_time": "6-8 min",
            "reliability": "Medium"
        },
        "zeroscope": {
            "name": "ZeroScope (P4000 Optimized)",
            "description": "Creative video content",
            "max_resolution": "320x320",
            "max_frames": 6,
            "estimated_time": "5-7 min",
            "reliability": "Medium"
        },
        "lite4k": {
            "name": "Lite4K (P4000 Optimized)",
            "description": "Fast image-to-video",
            "max_resolution": "256x256",
            "max_frames": 4,
            "estimated_time": "3-5 min",
            "reliability": "Medium"
        }
    }