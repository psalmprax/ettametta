import torch
from diffusers import AnimateDiffPipeline, DDIMScheduler
from diffusers.utils import export_to_video
import os
import asyncio
from pathlib import Path

async def generate_animatediff_laptop(prompt, num_frames=16, height=512, width=512):
    """
    Laptop-optimized AnimateDiff generation with memory management
    """

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if device == "cuda" else torch.float32

    print(f"🎬 Loading AnimateDiff on {device}...")

    # Load pipeline with memory optimizations
    pipe = AnimateDiffPipeline.from_pretrained(
        "guoyww/animatediff-motion-adapter-v1-5-2",
        torch_dtype=torch_dtype,
    )

    # Memory optimizations for laptops
    if device == "cuda":
        pipe.enable_model_cpu_offload()  # Offload to CPU when not in use
        pipe.enable_vae_slicing()        # Process VAE in slices
        pipe.enable_vae_tiling()         # Tile VAE for large images

    # Faster scheduler for laptops
    pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)

    print(f"🎯 Generating animation: {prompt[:50]}...")

    # Generate with laptop-optimized settings
    with torch.no_grad():
        result = pipe(
            prompt=prompt,
            negative_prompt="low quality, blurry, distorted, static, ugly",
            num_frames=num_frames,
            height=height,
            width=width,
            num_inference_steps=20,  # Fewer steps for speed
            guidance_scale=7.5,
            generator=torch.manual_seed(42)
        )

    # Save video
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    video_filename = f"laptop_animation_{hash(prompt) % 100000}.mp4"
    output_path = output_dir / video_filename

    print(f"💾 Exporting video to {output_path}...")

    # Export with laptop-optimized settings
    export_to_video(
        result.frames[0],
        str(output_path),
        fps=8  # Lower FPS for smaller files
    )

    # Clean up memory
    del pipe, result
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print(f"✅ Animation complete: {output_path}")

    return {
        "video_url": f"/download/{video_filename}",
        "local_path": str(output_path),
        "frames": num_frames,
        "resolution": f"{width}x{height}"
    }</content>
<parameter name="filePath">remote_ai_setup/animatediff_laptop_inference.py