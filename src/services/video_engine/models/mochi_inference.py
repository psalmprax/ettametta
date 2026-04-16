"""
Mochi-1 Inference Module

Mochi-1 is a state-of-the-art open-source video generation model from Genmo.
Requires ~24GB VRAM.
"""

import torch
import os
import time
from typing import Tuple
from api.config import settings
import requests

# Model cache
_mochi_pipe = None


def load_mochi_model():
    """Load Mochi-1 model"""
    global _mochi_pipe

    if _mochi_pipe is not None:
        return _mochi_pipe

    print("📥 Loading Mochi-1...", flush=True)

    # Mochi requires the diffusers pipeline
    # Note: Genmo released Mochi as a preview - full diffusers support may vary
    try:
        from diffusers import DiffusionPipeline

        _mochi_pipe = DiffusionPipeline.from_pretrained(
            "genmo/mochi-1-preview", torch_dtype=torch.bfloat16
        ).to("cuda")

        _mochi_pipe.enable_model_cpu_offload()
        _mochi_pipe.vae.enable_tiling()

        print("✅ Mochi-1 loaded successfully", flush=True)
        return _mochi_pipe
    except Exception as e:
        print(f"⚠️ Mochi-1 not available: {e}", flush=True)
        # Fallback: use HF Inference API
        return None


def generate_mochi(
    prompt: str,
    negative_prompt: str = "",
    num_frames: int = 30,
    num_inference_steps: int = 40,
    guidance_scale: float = 4.5,
    output_dir: str = "/workspace/remote_ai_group/outputs",
) -> Tuple[str, str]:
    """Generate video using Mochi-1"""
    start_time = time.time()
    print(f"🎬 Mochi-1: '{prompt[:50]}...'", flush=True)
    # Real-First: Attempt Remote GPU Node Call
    if settings.RENDER_NODE_URL:
        try:
            return generate_mochi_api(prompt, output_dir)
        except Exception as e:
            print(
                f"📡 Mochi Remote API failed ({e}). Falling back to local...",
                flush=True,
            )

    pipe = load_mochi_model()
    if pipe is None:
        return generate_mochi_api(prompt, output_dir)

    with torch.inference_mode():
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            num_frames=num_frames,
            guidance_scale=guidance_scale,
        ).frames[0]

    job_id = f"mochi_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)

    # Export
    from diffusers.utils import export_to_video

    export_to_video(result, output_video_path=output_path, fps=8)

    elapsed = time.time() - start_time
    print(f"✅ Generated {job_id}.mp4 in {elapsed:.1f}s", flush=True)

    return job_id, output_path


def generate_mochi_api(prompt: str, output_dir: str) -> Tuple[str, str]:
    """Generate video using Replicate/Fal.ai API or Remote GPU"""
    print(f"☁️ Mochi-1 via API: '{prompt[:50]}...'", flush=True)

    job_id = f"mochi_api_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)

    if not settings.RENDER_NODE_URL:
        raise RuntimeError(
            "RENDER_NODE_URL not configured. Cannot generate Mochi-1 video remotely."
        )

    print(
        f"📡 Attempting Mochi-1 remote generation via {settings.RENDER_NODE_URL}...",
        flush=True,
    )
    payload = {
        "prompt": prompt,
        "model": "genmo/mochi-1-preview",
        "resolution": "480p",
        "width": 848,
        "height": 480,
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
            print(f"✅ Mochi Remote API success for {job_id}", flush=True)
            return job_id, output_path
        else:
            data = response.json()
            dl_url = data.get("download_url")
            if dl_url:
                dl_resp = requests.get(dl_url, timeout=60)
                with open(output_path, "wb") as f:
                    f.write(dl_resp.content)
                print(
                    f"✅ Mochi Remote API (async DL) success for {job_id}", flush=True
                )
                return job_id, output_path

    raise RuntimeError(
        f"Mochi-1 remote generation failed with status {response.status_code}: {response.text[:200]}"
    )
