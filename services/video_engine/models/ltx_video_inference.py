"""
LTX-Video Inference Module

LTX-Video is an motion-optimized video generation model.
This module enforces a strict 480p resolution maximum.
"""
import torch
import os
import time
import requests
from typing import Tuple, Optional
from api.config import settings

# Model cache
_ltx_pipe = None

def load_ltx_local():
    """Load LTX-Video model"""
    global _ltx_pipe
    
    if _ltx_pipe is not None:
        return _ltx_pipe
    
    print("📥 Loading LTX-Video...", flush=True)
    
    try:
        from diffusers import DiffusionPipeline
        
        _ltx_pipe = DiffusionPipeline.from_pretrained(
            "Lightricks/LTX-Video",
            torch_dtype=torch.float16,
            device_map="balanced",
            low_cpu_mem_usage=True
        )
        
        print("✅ LTX-Video loaded successfully", flush=True)
        return _ltx_pipe
    except Exception as e:
        print(f"⚠️ LTX-Video local not available: {e}", flush=True)
        return None

def generate_ltx(
    prompt: str,
    negative_prompt: str = "low quality, blurry, distorted",
    num_frames: int = 49,
    num_inference_steps: int = 25,
    height: int = 480,
    width: int = 832,
    guidance_scale: float = 3.0,
    output_dir: str = "outputs"
) -> Tuple[str, str]:
    """Generate video using LTX-Video (480p)"""
    # Enforce 480p Maximum
    height = min(height, 480)
    width = min(width, 832)
    
    print(f"🎬 LTX-Video (480p): '{prompt[:50]}...'", flush=True)
    start_time = time.time()
    
    # Real-First: Attempt Remote GPU Node Call
    if settings.RENDER_NODE_URL:
        try:
            return generate_ltx_api(prompt, output_dir, height, width)
        except Exception as e:
            print(f"⚠️ LTX Remote GPU failed ({e}). Falling back...", flush=True)

    # Local Fallback
    pipe = load_ltx_local()
    
    if pipe is None:
        return generate_ltx_dummy(output_dir)
    
    with torch.inference_mode():
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            height=height,
            width=width,
            num_frames=num_frames,
            guidance_scale=guidance_scale
        ).frames[0]
    
    job_id = f"ltx_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)
    
    from diffusers.utils import export_to_video
    export_to_video(result, output_video_path=output_path, fps=24)
    
    elapsed = time.time() - start_time
    print(f"✅ Generated {job_id}.mp4 in {elapsed:.1f}s", flush=True)
    
    return job_id, output_path

def generate_ltx_api(prompt: str, output_dir: str, height: int = 480, width: int = 832) -> Tuple[str, str]:
    """Generate video using LTX API on Remote GPU"""
    job_id = f"ltx_api_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📡 Attempting LTX remote generation via {settings.RENDER_NODE_URL}...", flush=True)
    
    payload = {
        "prompt": prompt, 
        "model": "ltx-video",
        "resolution": "480p",
        "height": height,
        "width": width
    }
    
    headers = {"Content-Type": "application/json"}
    if hasattr(settings, 'INTERNAL_API_TOKEN') and settings.INTERNAL_API_TOKEN:
        headers["Authorization"] = f"Bearer {settings.INTERNAL_API_TOKEN}"
        
    response = requests.post(f"{settings.RENDER_NODE_URL}/generate", json=payload, headers=headers, timeout=120)
    
    if response.status_code == 200:
        if 'video' in response.headers.get('Content-Type', ''):
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ LTX Remote API success for {job_id}", flush=True)
            return job_id, output_path
        else:
            data = response.json()
            dl_url = data.get("download_url")
            if dl_url:
                dl_resp = requests.get(dl_url, timeout=60)
                with open(output_path, 'wb') as f:
                    f.write(dl_resp.content)
                return job_id, output_path
                
    raise Exception(f"Validation or Network failure (Status {response.status_code})")

def generate_ltx_dummy(output_dir: str) -> Tuple[str, str]:
    """Fallback dummy for LTX"""
    job_id = f"ltx_dummy_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    
    try:
        import cv2
        import numpy as np
        out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), 1, (16, 16))
        frame = np.zeros((16, 16, 3), dtype=np.uint8)
        out.write(frame)
        out.release()
    except:
        with open(output_path, "wb") as f:
            f.write(b"fallback mp4 content")
            
    return job_id, output_path
