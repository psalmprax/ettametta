"""
Video Model Manager - Unified resource orchestration for AI models
"""

import os
import gc
import torch
import threading
import time
import subprocess
from typing import Any
from huggingface_hub import snapshot_download, hf_hub_download
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from hardware_manager import hardware_manager

# Model registry
VIDEO_MODELS = {
    "ltx_2_19b": {
        "name": "LTX-Video 2 19B",
        "repo_id": "Lightricks/LTX-Video",
        "type": "diffusers",
        "vram_estimate": "19GB",
    },
    "hunyuan_480p": {
        "name": "HunyuanVideo 480p",
        "repo_id": "tencent/HunyuanVideo",
        "type": "diffusers",
        "vram_estimate": "16GB",
    },
    "cogvideo_5b": {
        "name": "CogVideoX-5B",
        "repo_id": "THUDM/CogVideoX-5b",
        "type": "diffusers",
        "vram_estimate": "12GB",
    },
    "animatediff_v15": {
        "name": "AnimateDiff V1.5",
        "repo_id": "guoyww/AnimateDiff",
        "type": "diffusers",
        "vram_estimate": "8GB",
    }
}

class VideoModelManager:
    """Manages all AI resources with Smart VRAM Orchestration (TTL + Mutually Exclusive)"""
    
    def __init__(self, hf_home: str = None):
        self.hf_home = hf_home or os.environ.get('HF_HOME', '/workspace/.hf_home')
        self.current_model_key = None
        self.pipe = None
        self.lock = threading.Lock()
        self.is_busy = False
        self.device = hardware_manager.device
        self.device_obj = hardware_manager.get_device_obj()
        self.dtype = hardware_manager.dtype
        self.encoder = self._get_best_encoder()
        self.last_active_time = time.time()
        self.vram_ttl_seconds = 600
        self._start_vram_monitor()

    def _start_vram_monitor(self):
        def monitor():
            while True:
                time.sleep(60)
                if self.pipe and (time.time() - self.last_active_time > self.vram_ttl_seconds):
                    print(f"⏰ [SmartVRAM] TTL Expired. Purging pipeline...", flush=True)
                    with self.lock:
                        self.unload_all()
        threading.Thread(target=monitor, daemon=True).start()

    def _get_best_encoder(self) -> str:
        try:
            result = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, check=True)
            for enc in ["h264_nvenc", "h264_amf", "h264_qsv", "h264_videotoolbox"]:
                if enc in result.stdout: return enc
            return "libx264"
        except: return "libx264"

    def unload_all(self):
        """Total eviction of all VRAM-occupying objects"""
        print("🗑️ [SmartVRAM] Evicting all models and clearing cache...", flush=True)
        if self.pipe:
            del self.pipe
            self.pipe = None
        self.current_model_key = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        hardware_manager.clear_cache()

    def _load_pipeline(self, model_key):
        """Internal loader for specific architectures"""
        info = VIDEO_MODELS.get(model_key)
        if not info: return None
        
        repo_id = info["repo_id"]
        print(f"📥 Loading Pipeline: {info['name']} ({repo_id})...", flush=True)
        
        try:
            if model_key == "ltx_2_19b":
                from diffusers import LTXPipeline
                # Note: For 32GB RTX 4080, we use BF16. If OOM, we'd need FP8.
                self.pipe = LTXPipeline.from_pretrained(repo_id, torch_dtype=self.dtype).to(self.device_obj)
            elif model_key == "hunyuan_480p":
                from diffusers import HunyuanVideoPipeline
                self.pipe = HunyuanVideoPipeline.from_pretrained(repo_id, torch_dtype=self.dtype).to(self.device_obj)
            elif model_key == "cogvideo_5b":
                from diffusers import CogVideoXPipeline
                self.pipe = CogVideoXPipeline.from_pretrained(repo_id, torch_dtype=torch.float16).to(self.device_obj)
            elif model_key == "animatediff_v15":
                from diffusers import AnimateDiffPipeline, MotionAdapter, EulerDiscreteScheduler
                adapter = MotionAdapter.from_pretrained("guoyww/AnimateDiff-v1.5", torch_dtype=torch.float16)
                self.pipe = AnimateDiffPipeline.from_pretrained("emilianJR/epiCRealism", motion_adapter=adapter, torch_dtype=torch.float16).to(self.device_obj)
                self.pipe.scheduler = EulerDiscreteScheduler.from_config(self.pipe.scheduler.config, timestep_spacing="trailing", beta_schedule="linear")
            elif model_key == "wan_2_1_t2v":
                # Assuming community support or recent diffusers addition
                # Fallback to a placeholder link if not yet in main diffusers
                print(f"⚠️ Wan 2.1 support in diffusers is experimental. Attempting load...", flush=True)
                self.pipe = DiffusionPipeline.from_pretrained(repo_id, torch_dtype=self.dtype).to(self.device_obj)
            
            # Common optimizations
            if self.pipe and self.device == "cuda":
                self.pipe.enable_model_cpu_offload() # Use sequential offloading for massive models
                # self.pipe.enable_sequential_cpu_offload() # More aggressive if needed
            
            self.current_model_key = model_key
            return self.pipe
        except Exception as e:
            print(f"❌ Failed to load {model_key}: {e}")
            traceback.print_exc()
            return None

    def generate_video(self, model_key, prompt, image_base64=None, **kwargs):
        """Real inference entry point"""
        self.last_active_time = time.time()
        
        with self.lock:
            self.is_busy = True
            try:
                if self.current_model_key != model_key:
                    self.unload_all()
                    self.pipe = self._load_pipeline(model_key)
                
                if not self.pipe:
                    return {"success": False, "error": f"Failed to load model {model_key}"}

                print(f"🎬 [Inference] Running {model_key}...", flush=True)
                
                # Standard parameters with overrides
                gen_kwargs = {
                    "prompt": prompt,
                    "num_inference_steps": kwargs.get("num_inference_steps", 30),
                    "num_frames": kwargs.get("num_frames", 49),
                }
                
                # Model-specific overrides
                if model_key == "ltx_2_19b":
                    gen_kwargs["height"] = kwargs.get("height", 480)
                    gen_kwargs["width"] = kwargs.get("width", 704)
                
                output = self.pipe(**gen_kwargs).frames[0]
                
                job_id = f"gen_{int(time.time())}"
                output_path = f"/workspace/ai_content/{job_id}.mp4"
                
                # Use hardware-accelerated export
                from main import hardware_export_to_video
                hardware_export_to_video(output, output_path, fps=24)
                
                return {"success": True, "output_path": output_path, "model_used": model_key}
            except Exception as e:
                print(f"❌ Inference Error: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(e)}
            finally:
                self.is_busy = False

model_manager = VideoModelManager()
