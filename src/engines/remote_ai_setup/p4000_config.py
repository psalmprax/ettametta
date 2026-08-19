import torch
from diffusers import AnimateDiffPipeline, DDIMScheduler
from diffusers.utils import export_to_video
from pathlib import Path
from typing import Any

async def generate_animatediff_laptop(prompt: str, num_frames: int = 16, height: int = 512, width: int = 512) -> dict[str, Any]:
    """
    Laptop-optimized AnimateDiff generation with memory management for P4000 8GB GPU.

    Optimizations for limited VRAM:
    - CPU offloading enabled
    - VAE slicing/tiling
    - Lower resolution (384p for P4000)
    - Fewer inference steps
    - Memory cleanup after generation
    """

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if device == "cuda" else torch.float32

    # P4000 optimization: Use 384p instead of 512p for 8GB VRAM
    if height > 384 or width > 384:
        print(f"⚠️ Reducing resolution for P4000 8GB VRAM: {height}x{width} → 384x384")
        height = width = 384

    print(f"🎬 Loading AnimateDiff on {device} (P4000 optimized)...")

    try:
        # Load pipeline with P4000-specific optimizations
        pipe = AnimateDiffPipeline.from_pretrained(
            "guoyww/animatediff-motion-adapter-v1-5-2",
            torch_dtype=torch_dtype,
        )

        # Critical memory optimizations for P4000
        if device == "cuda":
            pipe.enable_model_cpu_offload()  # Offload to CPU when not in use
            pipe.enable_vae_slicing()        # Process VAE in slices
            pipe.enable_vae_tiling()         # Tile VAE for large images

        # Faster scheduler for P4000
        pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)

        print(f"🎯 Generating P4000-optimized animation: {prompt[:50]}...")

        # P4000-optimized generation parameters
        with torch.no_grad():
            result = pipe(
                prompt=prompt,
                negative_prompt="low quality, blurry, distorted, static, ugly, low resolution",
                num_frames=min(num_frames, 12),  # Limit frames for P4000
                height=height,
                width=width,
                num_inference_steps=15,  # Reduced for speed/memory
                guidance_scale=7.0,     # Slightly lower for stability
                generator=torch.manual_seed(42)
            )

        # Save video with P4000 optimizations
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        video_filename = f"p4000_animation_{hash(prompt) % 100000}.mp4"
        output_path = output_dir / video_filename

        print(f"💾 Exporting P4000-optimized video to {output_path}...")

        # Export with laptop-optimized settings
        export_to_video(
            result.frames[0],
            str(output_path),
            fps=6  # Lower FPS for smaller files on P4000
        )

        # Aggressive memory cleanup for P4000
        del pipe, result
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()  # Ensure cleanup completes

        print(f"✅ P4000 animation complete: {output_path}")

        return {
            "video_uri": f"/download/{video_filename}",
            "local_path": str(output_path),
            "frames": min(num_frames, 12),
            "resolution": f"{width}x{height}",
            "gpu_optimized": "p4000_8gb",
            "generation_time": "estimated_4-6_min"
        }

    except torch.cuda.OutOfMemoryError:
        print("❌ P4000 VRAM exhausted. Try lower resolution or restart.")
        # Emergency cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return {"error": "insufficient_vram", "suggestion": "reduce_resolution_or_restart"}

    except Exception as e:
        print(f"❌ P4000 generation failed: {e}")
        return {"error": str(e)}

def get_p4000_recommendations() -> dict[str, Any]:
    """Get P4000-specific recommendations"""
    return {
        "max_resolution": "384x384",
        "recommended_frames": 12,
        "max_inference_steps": 15,
        "estimated_vram_usage": "6-7GB",
        "generation_time": "4-6 minutes",
        "tips": [
            "Close other GPU applications",
            "Use 384p resolution for best results",
            "Limit to 12 frames maximum",
            "Restart PC if VRAM issues persist"
        ]
    }
