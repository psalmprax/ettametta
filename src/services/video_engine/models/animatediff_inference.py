"""
AnimateDiff Inference Module for ettametta

AnimateDiff adds motion to Stable Diffusion images.
Supports SDXL and SD 1.5 with various motion adapters.
"""
import torch
import os
import time
from PIL import Image
from diffusers import (
    StableDiffusionXLPipeline,
    StableDiffusionPipeline,
    MotionAdapter,
    EulerDiscreteScheduler
)
from diffusers.utils import export_to_video

# Model cache
_sdxl_pipe = None
_sd15_pipe = None
_motion_adapter = None


def load_motion_adapter(model_type: str = "sdxl"):
    """Load AnimateDiff motion adapter"""
    global _motion_adapter
    
    if _motion_adapter is not None:
        return _motion_adapter
    
    motion_path = "guoyww/animatediff-sdxl-lightning" if model_type == "sdxl" else "guoyww/animatediff-motion-adapter-v1-5-2"
    
    print(f"📥 Loading AnimateDiff Motion Adapter ({model_type})...", flush=True)
    
    _motion_adapter = MotionAdapter.from_pretrained(
        motion_path,
        torch_dtype=torch.float16
    ).to("cuda")
    
    print("✅ Motion Adapter loaded", flush=True)
    return _motion_adapter


def load_sdxl_animatediff():
    """Load SDXL with AnimateDiff"""
    global _sdxl_pipe
    
    if _sdxl_pipe is not None:
        return _sdxl_pipe
    
    from diffusers import AutoPipelineForText2Image
    
    print("📥 Loading SDXL + AnimateDiff...", flush=True)
    
    motion_adapter = load_motion_adapter("sdxl")
    
    _sdxl_pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=torch.float16,
        variant="fp16"
    )
    
    _sdxl_pipe.motion_adapter = motion_adapter
    _sdxl_pipe = _sdxl_pipe.to("cuda")
    _sdxl_pipe.scheduler = EulerDiscreteScheduler.from_config(_sdxl_pipe.scheduler.config)
    _sdxl_pipe.enable_vae_slicing()
    _sdxl_pipe.enable_vae_tiling()
    
    print("✅ SDXL + AnimateDiff loaded", flush=True)
    return _sdxl_pipe


def load_sd15_animatediff():
    """Load SD 1.5 with AnimateDiff"""
    global _sd15_pipe
    
    if _sd15_pipe is not None:
        return _sd15_pipe
    
    from diffusers import AutoPipelineForText2Image
    
    print("📥 Loading SD 1.5 + AnimateDiff...", flush=True)
    
    motion_adapter = load_motion_adapter("sd15")
    
    _sd15_pipe = AutoPipelineForText2Image.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16,
        variant="fp16"
    )
    
    _sd15_pipe.motion_adapter = motion_adapter
    _sd15_pipe = _sd15_pipe.to("cuda")
    _sd15_pipe.scheduler = EulerDiscreteScheduler.from_config(_sd15_pipe.scheduler.config)
    _sd15_pipe.enable_vae_slicing()
    
    print("✅ SD 1.5 + AnimateDiff loaded", flush=True)
    return _sd15_pipe


def generate_animatediff(
    prompt: str,
    negative_prompt: str = "",
    num_frames: int = 16,
    num_inference_steps: int = 20,
    guidance_scale: float = 7.5,
    model_type: str = "sdxl",  # "sdxl" or "sd15"
    output_dir: str = "/workspace/remote_ai_group/outputs"
) -> tuple[str, str]:
    """Generate animated video using AnimateDiff"""
    print(f"🎬 AnimateDiff ({model_type}): '{prompt[:50]}...'", flush=True)
    start_time = time.time()
    
    if model_type == "sdxl":
        pipe = load_sdxl_animatediff()
        height, width = 1024, 1024
    else:
        pipe = load_sd15_animatediff()
        height, width = 512, 512
    
    with torch.inference_mode():
        output = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            height=height,
            width=width,
            num_frames=num_frames,
        )
    
    frames = output.frames[0] if hasattr(output, 'frames') else output.images
    
    job_id = f"ad_{model_type}_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)
    
    export_to_video(frames, output_video_path=output_path, fps=8)
    
    elapsed = time.time() - start_time
    print(f"✅ Generated {job_id}.mp4 ({num_frames} frames) in {elapsed:.1f}s", flush=True)
    
    return job_id, output_path


def generate_from_image_animatediff(
    image_path: str,
    prompt: str = "",
    negative_prompt: str = "",
    num_frames: int = 16,
    num_inference_steps: int = 20,
    guidance_scale: float = 7.5,
    strength: float = 0.8,
    output_dir: str = "/workspace/remote_ai_group/outputs"
) -> tuple[str, str]:
    """Animate a static image"""
    print(f"🎬 AnimateDiff Image Animation: {image_path}", flush=True)
    start_time = time.time()
    
    init_image = Image.open(image_path).convert("RGB")
    init_image = init_image.resize((1024, 1024))
    
    pipe = load_sdxl_animatediff()
    
    with torch.inference_mode():
        output = pipe(
            prompt=prompt,
            image=init_image,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            strength=strength,
            num_frames=num_frames,
        )
    
    frames = output.frames[0] if hasattr(output, 'frames') else output.images
    
    job_id = f"ad_img_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)
    
    export_to_video(frames, output_video_path=output_path, fps=8)
    
    elapsed = time.time() - start_time
    print(f"✅ Generated animated video in {elapsed:.1f}s", flush=True)
    
    return job_id, output_path
