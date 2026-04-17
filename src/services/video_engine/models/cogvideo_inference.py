"""
CogVideoX Inference Module

CogVideoX is an open-source text-to-video model from THUDM.
Enforces a strict 480p resolution maximum.

Quantization Options:
- "fp16": Half-precision (default)
- "int8": INT8 quantization - ~50% less VRAM
- "int4": INT4 quantization - ~75% less VRAM
"""

import torch
import os
import time
import requests
from src.api.config import settings

# Model cache
_cogvideo_pipe = None
_cogvideo_i2v_pipe = None

# Quantization mode
QUANTIZATION_MODE = os.getenv("COGVIDEO_QUANTIZATION", "fp16").lower()


def load_cogvideo_model(model_size: str = "2b", quantization: str = None):
    """Load CogVideoX model with optional quantization"""
    global _cogvideo_pipe

    if _cogvideo_pipe is not None:
        return _cogvideo_pipe

    quant_mode = quantization or QUANTIZATION_MODE
    try:
        from diffusers import CogVideoXPipeline

        # Default to 2b for memory efficiency at 480p
        model_id = "THUDM/CogVideoX-2b" if model_size == "2b" else "THUDM/CogVideoX-5b"
        print(f"📥 Loading CogVideoX {model_size} ({quant_mode})...", flush=True)

        _cogvideo_pipe = CogVideoXPipeline.from_pretrained(
            model_id, torch_dtype=torch.float16
        ).to("cuda")

        _cogvideo_pipe.enable_model_cpu_offload()
        _cogvideo_pipe.vae.enable_tiling()

        # Apply quantization if requested
        if quant_mode in ("int8", "int4"):
            try:
                from torchao.quantization import quantize_
                from torchao.quantization.quant_api import Int8DynActInt8WeightQuantizer

                quantize_(_cogvideo_pipe, Int8DynActInt8WeightQuantizer())
                print(f"🔢 CogVideoX loaded with {quant_mode.upper()}", flush=True)
            except ImportError:
                print("⚠️ torchao not installed, using FP16", flush=True)
        else:
            print(f"✅ CogVideoX {model_size} loaded successfully", flush=True)

        return _cogvideo_pipe
    except Exception as e:
        print(f"⚠️ CogVideoX local not available: {e}", flush=True)
        return None


def generate_cogvideo(
    prompt: str,
    negative_prompt: str = "",
    num_frames: int = 49,
    num_inference_steps: int = 30,
    height: int = 480,
    width: int = 720,
    guidance_scale: float = 6.0,
    model_size: str = "2b",
    output_dir: str = "outputs",
) -> tuple[str, str]:
    """Generate video using CogVideoX (480p)"""
    # Enforce 480p Maximum
    height = min(height, 480)
    width = min(width, 720)

    print(f"🎬 CogVideoX (480p): '{prompt[:50]}...'", flush=True)
    start_time = time.time()

    # Real-First: Attempt Remote GPU Node Call
    if settings.RENDER_NODE_URL:
        try:
            return generate_cogvideo_api(prompt, output_dir, height, width, model_size)
        except Exception as e:
            print(f"⚠️ CogVideoX Remote GPU failed ({e}). Falling back...", flush=True)

    # Local Fallback
    pipe = load_cogvideo_model(model_size)

    if pipe is None:
        return generate_cogvideo_dummy(output_dir)

    with torch.inference_mode():
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            num_frames=num_frames,
            guidance_scale=guidance_scale,
        ).frames[0]

    job_id = f"cogx_{model_size}_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)

    from diffusers.utils import export_to_video

    export_to_video(result, output_video_path=output_path, fps=8)

    elapsed = time.time() - start_time
    print(f"✅ Generated {job_id}.mp4 in {elapsed:.1f}s", flush=True)

    return job_id, output_path


def generate_cogvideo_api(
    prompt: str,
    output_dir: str,
    height: int = 480,
    width: int = 720,
    model_size: str = "2b",
) -> tuple[str, str]:
    """Generate video using CogVideoX API on Remote GPU"""
    job_id = f"cogx_api_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)

    payload = {
        "prompt": prompt,
        "model": f"cogvideox-{model_size}",
        "resolution": "480p",
        "height": height,
        "width": width,
    }

    headers = {"Content-Type": "application/json"}
    if hasattr(settings, "INTERNAL_API_TOKEN") and settings.INTERNAL_API_TOKEN:
        headers["Authorization"] = f"Bearer {settings.INTERNAL_API_TOKEN}"

    response = requests.post(
        f"{settings.RENDER_NODE_URL}/generate",
        json=payload,
        headers=headers,
        timeout=120,
    )

    if response.status_code == 200:
        if "video" in response.headers.get("Content-Type", ""):
            with open(output_path, "wb") as f:
                f.write(response.content)
            return job_id, output_path
        else:
            data = response.json()
            dl_url = data.get("download_url")
            if dl_url:
                dl_resp = requests.get(dl_url, timeout=60)
                with open(output_path, "wb") as f:
                    f.write(dl_resp.content)
                return job_id, output_path

    raise RuntimeError(
        f"CogVideoX remote generation failed with status {response.status_code}: {response.text[:200]}"
    )


def generate_cogvideo_dummy(output_dir: str) -> tuple[str, str]:
    """Raise error instead of generating garbage output"""
    raise RuntimeError(
        "CogVideoX generation failed: neither remote GPU node nor local model available. "
        f"Configure RENDER_NODE_URL or install diffusers + CogVideoX model locally."
    )
