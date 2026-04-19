"""
HunyuanVideo Inference Module

HunyuanVideo 1.5 is an advanced video generation model.
This module enforces a strict 480p resolution maximum.

Quantization Options:
- "fp16": Half-precision (default) - balanced quality/VRAM
- "int8": INT8 quantization - ~50% less VRAM, minimal quality loss
- "int4": INT4 quantization - ~75% less VRAM, slight quality loss
"""

import torch
import os
import time
import requests
from api.config import settings

# Model cache
_hunyuan_pipe = None

# Quantization mode
QUANTIZATION_MODE = os.getenv("HUNYUAN_QUANTIZATION", "fp16").lower()


def apply_quantization(pipe, quant_mode: str = "int8"):
    """Apply dynamic quantization to pipeline"""
    if quant_mode in ("int8", "int4"):
        # torchao quantization for reduced VRAM
        try:
            from torchao.quantization import quantize_
            from torchao.quantization.quant_api import Int8DynActInt8WeightQuantizer

            quantize_(pipe, Int8DynActInt8WeightQuantizer())
            print(f"🔢 Applied {quant_mode.upper()} quantization", flush=True)
        except ImportError:
            print("⚠️ torchao not installed, using FP16", flush=True)
    return pipe


def load_hunyuan_local(quantization: str = None):
    """Load HunyuanVideo 1.5 model (480p version) with optional quantization"""
    global _hunyuan_pipe

    if _hunyuan_pipe is not None:
        return _hunyuan_pipe

    quant_mode = quantization or QUANTIZATION_MODE
    print(f"📥 Loading HunyuanVideo 480p ({quant_mode})...", flush=True)

    try:
        from diffusers import DiffusionPipeline

        # We use the 480p optimized version
        _hunyuan_pipe = DiffusionPipeline.from_pretrained(
            "hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_t2v",
            torch_dtype=torch.float16,
            device_map="balanced",
            low_cpu_mem_usage=True,
        )

        _hunyuan_pipe.vae.enable_tiling()

        # Apply quantization if requested
        if quant_mode in ("int8", "int4"):
            _hunyuan_pipe = apply_quantization(_hunyuan_pipe, quant_mode)
            print(f"✅ HunyuanVideo loaded with {quant_mode.upper()}", flush=True)
        else:
            print("✅ HunyuanVideo 480p loaded successfully", flush=True)

        return _hunyuan_pipe
    except Exception as e:
        print(f"⚠️ HunyuanVideo local not available: {e}", flush=True)
        return None


def generate_hunyuan(
    prompt: str,
    negative_prompt: str = "",
    num_frames: int = 49,
    num_inference_steps: int = 25,
    height: int = 480,
    width: int = 832,
    output_dir: str = "outputs",
) -> tuple[str, str]:
    """Generate video using HunyuanVideo (480p)"""
    # Enforce 480p Maximum
    height = min(height, 480)
    width = min(width, 848)  # Allow slightly more width for Mochi-style 16:9

    print(f"🎬 HunyuanVideo (480p): '{prompt[:50]}...'", flush=True)
    start_time = time.time()

    # Real-First: Attempt Remote GPU Node Call
    if settings.RENDER_NODE_URL:
        try:
            return generate_hunyuan_api(prompt, output_dir, height, width)
        except Exception as e:
            print(f"⚠️ Hunyuan Remote GPU failed ({e}). Falling back...", flush=True)

    # Local Fallback
    pipe = load_hunyuan_local()

    if pipe is None:
        return generate_hunyuan_dummy(output_dir)

    with torch.inference_mode():
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            height=height,
            width=width,
            num_frames=num_frames,
        ).frames[0]

    job_id = f"hun_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)

    from diffusers.utils import export_to_video

    export_to_video(result, output_video_path=output_path, fps=24)

    elapsed = time.time() - start_time
    print(f"✅ Generated {job_id}.mp4 in {elapsed:.1f}s", flush=True)

    return job_id, output_path


def generate_hunyuan_api(
    prompt: str, output_dir: str, height: int = 480, width: int = 832
) -> tuple[str, str]:
    """Generate video using Hunyuan API on Remote GPU"""
    job_id = f"hun_api_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)

    print(
        f"📡 Attempting Hunyuan remote generation via {settings.RENDER_NODE_URL}...",
        flush=True,
    )

    payload = {
        "prompt": prompt,
        "model": "hunyuan-video",
        "resolution": "480p",
        "height": height,
        "width": width,
    }

    headers = {
        "Content-Type": "application/json",
        "x-worker-token": settings.AI_CLUSTER_SECRET,
    }

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
            print(f"✅ Hunyuan Remote API success for {job_id}", flush=True)
            return job_id, output_path
        else:
            data = response.json()
            dl_url = data.get("download_url")
            if dl_url:
                dl_resp = requests.get(dl_url, timeout=60)
                with open(output_path, "wb") as f:
                    f.write(dl_resp.content)
                return job_id, output_path

    raise Exception(f"Validation or Network failure (Status {response.status_code})")


def generate_hunyuan_dummy(output_dir: str) -> tuple[str, str]:
    """Raise error instead of generating garbage output"""
    raise RuntimeError(
        "HunyuanVideo generation failed: neither remote GPU node nor local model available. "
        f"Configure RENDER_NODE_URL or install diffusers + HunyuanVideo model locally."
    )
