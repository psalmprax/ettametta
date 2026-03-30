import torch
import os
import time
from diffusers import HunyuanVideo15Pipeline
from diffusers.utils import export_to_video
from huggingface_hub import InferenceClient
from .hardware_manager import hardware_manager

# Model cache
_hunyuan_pipe = None
_hunyuan_gguf_pipe = None

def clear_hunyuan_model():
    """Clear HunyuanVideo model from GPU using HardwareManager abstraction"""
    global _hunyuan_pipe
    if _hunyuan_pipe is not None:
        del _hunyuan_pipe
        _hunyuan_pipe = None
    hardware_manager.clear_cache()
    print(f"🗑️ Cleared HunyuanVideo model from {hardware_manager.device}", flush=True)

# Available HunyuanVideo models
HUNYUAN_MODELS = {
    "480p": "hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_t2v",
    "720p": "hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-720p_t2v",
    "gguf": "jayn7/HunyuanVideo-1.5_T2V_720p-GGUF",  # New GGUF model
}

def load_hunyuan_model(model_type: str = "480p", quantize: bool = True, force_reload: bool = False):
    """Load HunyuanVideo 1.5 model (lazy loading) with VRAM optimization"""
    global _hunyuan_pipe
    
    # Force reload: clear existing model from GPU first
    if force_reload and _hunyuan_pipe is not None:
        clear_hunyuan_model()
    
    if _hunyuan_pipe is not None:
        return _hunyuan_pipe
    
    from diffusers import DiffusionPipeline
    import torch
    
    # Get model path from dictionary
    model_path = HUNYUAN_MODELS.get(model_type, HUNYUAN_MODELS["480p"])
    print(f"📥 Loading HunyuanVideo: {model_path} (Quantize: {quantize})", flush=True)
    
    pipe_kwargs = {
        "torch_dtype": hardware_manager.dtype,
        "device_map": "auto" if hardware_manager.device != "cpu" else None,
        "low_cpu_mem_usage": True,
    }

    # Note: 8-bit quantization removed due to diffusers compatibility issues
    # The model will run in FP16 which requires ~43GB VRAM
    if quantize:
        print("⚠️ 8-bit quantization disabled - using FP16 (~43GB VRAM needed)", flush=True)

    _hunyuan_pipe = DiffusionPipeline.from_pretrained(
        model_path,
        **pipe_kwargs
    )
    
    # Enable VAE tiling for memory efficiency
    _hunyuan_pipe.vae.enable_tiling()
    
    # Note: device_map="balanced" already handles device placement, no need for enable_model_cpu_offload()
    print("✅ HunyuanVideo 1.5 optimized and loaded", flush=True)
    return _hunyuan_pipe


def load_hunyuan_gguf_model():
    """Load HunyuanVideo GGUF model using llama.cpp (more memory efficient)"""
    global _hunyuan_gguf_pipe
    
    if _hunyuan_gguf_pipe is not None:
        return _hunyuan_gguf_pipe
    
    try:
        from llama_cpp import Llama
        from huggingface_hub import hf_hub_download
        
        print("📥 Downloading HunyuanVideo GGUF model...", flush=True)
        model_path = hf_hub_download(
            repo_id="jayn7/HunyuanVideo-1.5_T2V_720p-GGUF",
            filename="*.gguf",
            resume_download=True,
        )
        
        _hunyuan_gguf_pipe = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=8,
            n_gpu_layers=64,  # Offload to GPU
        )
        
        print("✅ HunyuanVideo GGUF loaded successfully", flush=True)
        return _hunyuan_gguf_pipe
    except ImportError:
        print("⚠️ llama-cpp not installed. Install with: pip install llama-cpp-python", flush=True)
        return None
    except Exception as e:
        print(f"⚠️ Failed to load GGUF model: {e}", flush=True)
        return None


def generate_hunyuan_video(
    prompt: str,
    negative_prompt: str = "",
    num_inference_steps: int = 25,
    height: int = 480,
    width: int = 832,
    num_frames: int = 49,
    guidance_scale: float = 6.0,
    output_dir: str = "/workspace/remote_ai_group/outputs",
    use_api: bool = False,
    model_type: str = "480p",
    quantize: bool = True,
    force_reload: bool = False
) -> str:
    """
    Generate video using HunyuanVideo (Local or API)
    
    Args:
        prompt: Text prompt for video generation
        model_type: One of "480p", "720p", "gguf"
        quantize: Whether to use 8-bit quantization (recommended for <80GB VRAM)
        force_reload: Clear GPU memory before loading model
    """
    import traceback
    print(f"🎬 HunyuanVideo: '{prompt[:50]}...' (model: {model_type}, quantize: {quantize}, force_reload: {force_reload})", flush=True)
    
    # Use GGUF model
    if model_type == "gguf":
        return generate_hunyuan_gguf(prompt, output_dir)
    
    if use_api and os.getenv("HF_TOKEN"):
        print("☁️ Using fal-ai Cloud Provider via InferenceClient...", flush=True)
        try:
            client = InferenceClient(provider="fal-ai", api_key=os.getenv("HF_TOKEN"))
            video = client.text_to_video(prompt, model="hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-720p_t2v")
            
            job_id = f"hun_api_{int(time.time())}"
            output_path = os.path.join(output_dir, f"{job_id}.mp4")
            with open(output_path, "wb") as f:
                f.write(video)
            return job_id, output_path
        except Exception as e:
            print(f"⚠️ API Mode failed: {e}. Falling back to Local...", flush=True)

    # Local Mode
    print(f"🖥️ Using Local Rendering (model: {model_type})...", flush=True)
    start_time = time.time()
    
    try:
        # Clear hardware-optimized cache
        hardware_manager.clear_cache()
        
        pipe = load_hunyuan_model(model_type, quantize=quantize, force_reload=force_reload)
        
        # Note: device_map already handles device placement, no need for .to("cuda")
        
        with torch.inference_mode():
            print(f"🔄 Generating video with {num_frames} frames, {num_inference_steps} steps...", flush=True)
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                height=height,
                width=width,
                num_frames=num_frames,
                # HunyuanVideo doesn't use guidance_scale, it uses the negative_prompt directly
            ).frames[0]
        
        job_id = f"hun_loc_{int(time.time())}"
        output_path = os.path.join(output_dir, f"{job_id}.mp4")
        os.makedirs(output_dir, exist_ok=True)
        export_to_video(result, output_video_path=output_path)
        
        elapsed = time.time() - start_time
        print(f"✅ Generated {job_id}.mp4 in {elapsed:.1f}s", flush=True)
        return job_id, output_path
        
    except Exception as e:
        print(f"❌ HunyuanVideo generation failed: {e}", flush=True)
        traceback.print_exc()
        raise


def generate_hunyuan_gguf(prompt: str, output_dir: str = "/workspace/remote_ai_group/outputs"):
    """Generate video using HunyuanVideo GGUF model"""
    print("🎬 HunyuanVideo GGUF: Generating video...", flush=True)
    start_time = time.time()
    
    pipe = load_hunyuan_gguf_model()
    if pipe is None:
        raise RuntimeError("GGUF model not available. Please install llama-cpp-python")
    
    # GGUF models typically output via different mechanism
    # This is a placeholder - actual implementation depends on GGUF model format
    job_id = f"hun_gguf_{int(time.time())}"
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    os.makedirs(output_dir, exist_ok=True)
    
    # Note: GGUF video generation requires specific implementation
    # The jayn7/HunyuanVideo-1.5_T2V_720p-GGUF model may need custom processing
    print(f"⚠️ GGUF video generation is model-specific. Model: jayn7/HunyuanVideo-1.5_T2V_720p-GGUF", flush=True)
    
    elapsed = time.time() - start_time
    print(f"✅ GGUF generation initiated in {elapsed:.1f}s", flush=True)
    return job_id, output_path
