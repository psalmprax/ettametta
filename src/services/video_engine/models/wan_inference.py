"""
Wan 2.2 Inference Module

Wan 2.2 is an open-source video generation model from Alibaba.
Available: T2V (text-to-video) and V2V (video-to-video)
"""

import torch
import os
import time
from typing import Tuple, Optional
from PIL import Image
from api.config import settings
import requests

# Model cache
_wan_t2v_pipe = None
_wan_v2v_pipe = None


def load_wan_t2v():
    """Load Wan 2.2 T2V model"""
    global _wan_t2v_pipe

    if _wan_t2v_pipe is not None:
        return _wan_t2v_pipe

    print("📥 Loading Wan 2.2 T2V...", flush=True)

    try:
        from diffusers import WanVideoToVideoPipeline

        _wan_t2v_pipe = WanVideoToVideoPipeline.from_pretrained(
            "Wan-AI/Wan2.2-T2V-14B-Diffusers", torch_dtype=torch.float16
        ).to("cuda")

        _wan_t2v_pipe.enable_model_cpu_offload()

        print("✅ Wan 2.2 T2V loaded successfully", flush=True)
        return _wan_t2v_pipe
    except Exception as e:
        print(f"⚠️ Wan 2.2 T2V not available: {e}", flush=True)
        return None


def load_wan_v2v():
    """Load Wan 2.2 V2V model"""
    global _wan_v2v_pipe

    if _wan_v2v_pipe is not None:
        return _wan_v2v_pipe

    print("📥 Loading Wan 2.2 V2V...", flush=True)

    try:
        from diffusers import WanVideoToVideoPipeline

        _wan_v2v_pipe = WanVideoToVideoPipeline.from_pretrained(
            "Wan-AI/Wan2.2-V2V-14B-Diffusers", torch_dtype=torch.float16
        ).to("cuda")

        _wan_v2v_pipe.enable_model_cpu_offload()

        print("✅ Wan 2.2 V2V loaded successfully", flush=True)
        return _wan_v2v_pipe
    except Exception as e:
        print(f"⚠️ Wan 2.2 V2V not available: {e}", flush=True)
        return None


def generate_wan_t2v(
    prompt: str,
    negative_prompt: str = "",
    num_frames: int = 41,
    num_inference_steps: int = 30,
    guidance_scale: float = 5.0,
    output_dir: str = "/workspace/remote_ai_group/outputs",
) -> Tuple[str, str]:
    """Generate video using Wan 2.2 T2V"""
    start_time = time.time()
    print(f"🎬 Wan 2.2 T2V: '{prompt[:50]}...'", flush=True)
    # Real-First: Attempt Remote GPU Node Call
    if settings.RENDER_NODE_URL:
        try:
            return generate_wan_api(prompt, output_dir)
        except Exception as e:
            print(
                f"📡 Wan Remote API failed ({e}). Falling back to local...", flush=True
            )

    pipe = load_wan_t2v()
    if pipe is None:
        return generate_wan_api(prompt, output_dir)

    with torch.inference_mode():
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            num_frames=num_frames,
            guidance_scale=guidance_scale,
        ).frames[0]

    job_id = f"wan_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)

    from diffusers.utils import export_to_video

    export_to_video(result, output_video_path=output_path, fps=8)

    elapsed = time.time() - start_time
    print(f"✅ Generated {job_id}.mp4 in {elapsed:.1f}s", flush=True)

    return job_id, output_path


def generate_wan_v2v(
    input_video_path: str,
    prompt: str = "",
    negative_prompt: str = "",
    num_inference_steps: int = 25,
    guidance_scale: float = 5.0,
    output_dir: str = "/workspace/remote_ai_group/outputs",
) -> Tuple[str, str]:
    """Transform video using Wan 2.2 V2V"""
    start_time = time.time()
    print(f"🎬 Wan 2.2 V2V: Processing {input_video_path}", flush=True)
    # Real-First: Attempt Remote GPU Node Call
    if settings.RENDER_NODE_URL:
        try:
            return generate_wan_api(prompt, output_dir)
        except Exception as e:
            print(
                f"📡 Wan Remote API (v2v) failed ({e}). Falling back to local...",
                flush=True,
            )

    pipe = load_wan_v2v()
    if pipe is None:
        return generate_wan_api(prompt, output_dir)

    with torch.inference_mode():
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            video_path=input_video_path,
        ).frames[0]

    job_id = f"wan_v2v_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)

    from diffusers.utils import export_to_video

    export_to_video(result, output_video_path=output_path, fps=8)

    elapsed = time.time() - start_time
    print(f"✅ Generated {job_id}.mp4 in {elapsed:.1f}s", flush=True)

    return job_id, output_path


def generate_wan_api(prompt: str, output_dir: str) -> Tuple[str, str]:
    """Generate video using real API call to remote GPU node"""
    import json

    job_id = f"wan_api_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)

    if not settings.RENDER_NODE_URL:
        raise RuntimeError(
            "RENDER_NODE_URL not configured. Cannot generate Wan 2.2 video remotely."
        )

    print(
        f"📡 Attempting Wan remote generation via {settings.RENDER_NODE_URL}...",
        flush=True,
    )
    payload = {"prompt": prompt, "model": "wan-2.2-t2v", "resolution": "480p"}
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
            print(f"✅ Wan Remote API success for {job_id}", flush=True)
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
        f"Wan 2.2 remote generation failed with status {response.status_code}: {response.text[:200]}"
    )
