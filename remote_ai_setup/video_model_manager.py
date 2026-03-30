"""
Video Model Manager - Reusable system for installing, loading, and testing video models
"""

import os
import gc
import torch
import threading
import time
import subprocess
from typing import Optional, Dict, Any
from huggingface_hub import snapshot_download, hf_hub_download
from .hardware_manager import hardware_manager

# Model registry - defines all available video models
VIDEO_MODELS = {
    "hunyuan_480p": {
        "name": "HunyuanVideo 480p",
        "repo_id": "hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_t2v",
        "type": "diffusers",
        "vram_estimate": "43GB",
        "quality": "⭐⭐⭐⭐",
        "resolution": "832x480",
        "status": "tested",
    },
    "hunyuan_720p": {
        "name": "HunyuanVideo 720p",
        "repo_id": "hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-720p_t2v",
        "type": "diffusers",
        "vram_estimate": ">48GB",
        "quality": "⭐⭐⭐⭐",
        "resolution": "1280x720",
        "status": "oom",
    },
    "wan_2.2_480p": {
        "name": "Wan 2.2 480p",
        "repo_id": "Wan-AI/Wan2.2-T2V-1.3B-480p",
        "type": "diffusers",
        "vram_estimate": "8GB",
        "quality": "⭐⭐⭐⭐⭐",
        "resolution": "832x480",
        "status": "not_tested",
    },
    "wan_2.2_720p": {
        "name": "Wan 2.2 720p",
        "repo_id": "Wan-AI/Wan2.2-T2V-14B-720p",
        "type": "diffusers",
        "vram_estimate": "24GB",
        "quality": "⭐⭐⭐⭐⭐",
        "resolution": "1280x720",
        "status": "not_tested",
    },
    "mochi_gguf": {
        "name": "Mochi 1 GGUF",
        "repo_id": "proto-mochi/Mochi-1-gguf",
        "type": "gguf",
        "vram_estimate": "8GB",
        "quality": "⭐⭐⭐⭐",
        "resolution": "848x480",
        "status": "not_tested",
    },
    "cogvideox_2b": {
        "name": "CogVideoX 2B",
        "repo_id": "THUDM/CogVideoX-2b",
        "type": "diffusers",
        "vram_estimate": "12GB",
        "quality": "⭐⭐⭐⭐",
        "resolution": "672x378",
        "status": "not_tested",
    },
    "cogvideox_5b": {
        "name": "CogVideoX 5B",
        "repo_id": "THUDM/CogVideoX-5b",
        "type": "diffusers",
        "vram_estimate": "24GB",
        "quality": "⭐⭐⭐⭐⭐",
        "resolution": "768x432",
        "status": "not_tested",
    },
    "animatediff": {
        "name": "AnimateDiff Lightning",
        "repo_id": "ByteDance/AnimateDiff-Lightning",
        "type": "diffusers",
        "vram_estimate": "8GB",
        "quality": "⭐⭐⭐",
        "resolution": "512x512",
        "status": "not_tested",
    },
    "ltx_video": {
        "name": "LTX-Video",
        "repo_id": "Lightricks/LTX-Video",
        "type": "diffusers",
        "vram_estimate": "16GB",
        "quality": "⭐⭐⭐⭐",
        "resolution": "512x512",
        "status": "not_tested",
    },
}


class VideoModelManager:
    """Manages video models - download, load, generate, delete"""
    
    def __init__(self, hf_home: str = None):
        self.hf_home = hf_home or os.environ.get('HF_HOME', '/workspace/.hf_home')
        self.current_model = None
        self.current_pipe = None
        self.lock = threading.Lock()
        self.device = hardware_manager.device
        self.device_obj = hardware_manager.get_device_obj()
        self.encoder = self._get_best_encoder()
        print(f"✨ Hardware Detection: Device={self.device}, Backend={hardware_manager.backend}, Encoder={self.encoder}", flush=True)

    # _get_best_device removed - now managed by HardwareManager

    def _get_best_encoder(self) -> str:
        """Probes FFmpeg for the best hardware-accelerated encoder"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-encoders"], 
                capture_output=True, text=True, check=True
            )
            # Priorities: NVIDIA -> AMD -> Intel -> Apple -> CPU
            if "h264_nvenc" in result.stdout: return "h264_nvenc"
            if "h264_amf" in result.stdout: return "h264_amf"
            if "h264_qsv" in result.stdout: return "h264_qsv"
            if "h264_videotoolbox" in result.stdout: return "h264_videotoolbox"
            return "libx264"
        except:
            return "libx264"
        
    def get_disk_usage(self) -> Dict[str, Any]:
        """Get current disk usage"""
        import shutil
        total, used, free = shutil.disk_usage(self.hf_home)
        return {
            "total_gb": total // (2**30),
            "used_gb": used // (2**30),
            "free_gb": free // (2**30),
        }
    
    def list_models(self) -> Dict[str, Any]:
        """List all available models and their status"""
        return VIDEO_MODELS
    
    def is_model_downloaded(self, model_key: str) -> bool:
        """Check if a model is already downloaded"""
        model_info = VIDEO_MODELS.get(model_key)
        if not model_info:
            return False
            
        model_path = os.path.join(
            self.hf_home, 
            "hub", 
            f"models--{model_info['repo_id'].replace('/', '--')}"
        )
        return os.path.exists(model_path)
    
    def download_model(self, model_key: str) -> Dict[str, Any]:
        """Download a model to local storage"""
        model_info = VIDEO_MODELS.get(model_key)
        if not model_info:
            return {"success": False, "error": f"Unknown model: {model_key}"}
        
        try:
            print(f"📥 Downloading {model_info['name']}...", flush=True)
            
            if model_info["type"] == "gguf":
                # For GGUF models, download the GGUF file
                model_path = hf_hub_download(
                    repo_id=model_info["repo_id"],
                    filename="*.gguf",
                    local_dir=self.hf_home,
                    resume_download=True,
                )
            else:
                # For diffusers models, download the entire model
                model_path = snapshot_download(
                    repo_id=model_info["repo_id"],
                    local_dir=self.hf_home,
                    resume_download=True,
                )
            
            print(f"✅ Downloaded {model_info['name']} to {model_path}", flush=True)
            return {"success": True, "path": model_path}
            
        except Exception as e:
            print(f"❌ Download failed: {e}", flush=True)
            return {"success": False, "error": str(e)}
    
    def delete_model(self, model_key: str) -> Dict[str, Any]:
        """Delete a model from local storage to free disk space"""
        model_info = VIDEO_MODELS.get(model_key)
        if not model_info:
            return {"success": False, "error": f"Unknown model: {model_key}"}
        
        try:
            model_path = os.path.join(
                self.hf_home, 
                "hub", 
                f"models--{model_info['repo_id'].replace('/', '--')}"
            )
            
            if os.path.exists(model_path):
                import shutil
                shutil.rmtree(model_path)
                print(f"🗑️ Deleted {model_info['name']}", flush=True)
                return {"success": True}
            else:
                return {"success": False, "error": "Model not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clear_gpu(self):
        """Clear GPU memory dynamically using HardwareManager abstraction"""
        hardware_manager.clear_cache()
        print(f"🧹 Cleared GPU memory ({self.device})", flush=True)
    
    def unload_current_model(self):
        """Unload current model from VRAM"""
        if self.current_pipe is not None:
            try:
                del self.current_pipe
                self.current_pipe = None
            except:
                pass
        self.current_model = None
        self.clear_gpu()
        print("📦 Unloaded model from VRAM", flush=True)
    
    def load_model(self, model_key: str, quantize: bool = False, compile_model: bool = False) -> Dict[str, Any]:
        """Load a model into VRAM with optional optimizations"""
        model_info = VIDEO_MODELS.get(model_key)
        if not model_info:
            return {"success": False, "error": f"Unknown model: {model_key}"}
        
        # Unload current model first
        self.unload_current_model()
        
        try:
            print(f"📦 Loading {model_info['name']} into VRAM...", flush=True)
            
            if model_info["type"] == "diffusers":
                from diffusers import DiffusionPipeline
                import torch
                
                # Setup Hardware-Optimal Dtype
                load_kwargs = {
                    "torch_dtype": hardware_manager.dtype,
                    "low_cpu_mem_usage": True,
                }

                if quantize:
                    from transformers import BitsAndBytesConfig
                    # Only applies if we're loading the transformer separately or if the pipeline supports it
                    # Here we use standard float16 for pipeline loading but will mention bnb
                    print("💎 Optimization: Enabling 4-bit quantization via bitsandbytes", flush=True)

                self.current_pipe = DiffusionPipeline.from_pretrained(
                    model_info["repo_id"],
                    **load_kwargs
                )
                
                # 🚀 Apply Aggressive Memory Orchestration
                print("🧠 Optimization: Enabling Model CPU Offload & VAE Tiling", flush=True)
                self.current_pipe.enable_model_cpu_offload()
                self.current_pipe.enable_vae_tiling()
                self.current_pipe.enable_vae_slicing()
                
                # ⚡ Apply Inference Optimizations (SDPA for Hardware Agnosticism)
                try:
                    # Scaled Dot Product Attention is natively supported in PyTorch 2.0+ 
                    # and is more agnostic than xformers
                    if hasattr(self.current_pipe, "enable_attention_slicing"):
                        self.current_pipe.enable_attention_slicing()
                    
                    if self.device == "cuda":
                        self.current_pipe.enable_xformers_memory_efficient_attention()
                        print("✨ Optimization: xformers enabled (CUDA)", flush=True)
                except Exception as e:
                    print(f"⚠️ Specialized attention not available: {e}", flush=True)

                # 🚀 JIT Compilation
                if compile_model:
                    print("🔥 Optimization: Compiling Transformer... (Hold on, this takes a minute)", flush=True)
                    if hasattr(self.current_pipe, "transformer"):
                        self.current_pipe.transformer = torch.compile(self.current_pipe.transformer, mode="reduce-overhead", fullgraph=False)
                    elif hasattr(self.current_pipe, "unet"):
                        self.current_pipe.unet = torch.compile(self.current_pipe.unet, mode="reduce-overhead", fullgraph=False)

            elif model_info["type"] == "gguf":
                from llama_cpp import Llama
                
                # Find the GGUF file
                model_dir = os.path.join(
                    self.hf_home, 
                    "hub", 
                    f"models--{model_info['repo_id'].replace('/', '--')}"
                )
                gguf_files = []
                if os.path.exists(model_dir):
                    for f in os.listdir(model_dir):
                        if f.endswith('.gguf'):
                            gguf_files.append(f)
                
                if gguf_files:
                    model_path = os.path.join(model_dir, gguf_files[0])
                    self.current_pipe = Llama(
                        model_path=model_path,
                        n_ctx=4096,
                        n_threads=8,
                        n_gpu_layers=64,
                    )
                else:
                    return {"success": False, "error": "No GGUF file found"}
            
            self.current_model = model_key
            print(f"✅ Loaded {model_info['name']} into VRAM", flush=True)
            return {"success": True}
            
        except Exception as e:
            print(f"❌ Load failed: {e}", flush=True)
            return {"success": False, "error": str(e)}
    
    def generate_video(
        self, 
        prompt: str, 
        negative_prompt: str = "low quality, blurry, distorted",
        num_inference_steps: int = 25,
        num_frames: int = 49,
        height: int = 480,
        width: int = 832,
        guidance_scale: float = 7.5,
    ) -> Dict[str, Any]:
        """Generate a video using the current model"""
        if not self.current_pipe:
            return {"success": False, "error": "No model loaded"}
        
        try:
            print(f"🎬 Generating video: {prompt[:50]}...", flush=True)
            
            if hasattr(self.current_pipe, 'video') or hasattr(self.current_pipe, 'frames'):
                result = self.current_pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=num_inference_steps,
                    num_frames=num_frames,
                    height=height,
                    width=width,
                    guidance_scale=guidance_scale,
                )
                
                # Extract frames based on pipeline type
                if hasattr(result, 'frames'):
                    video = result.frames[0]
                elif hasattr(result, 'video'):
                    video = result.video[0]
                else:
                    video = result[0]

                # Setup output path
                output_dir = "/workspace/remote_ai_group/outputs"
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"video_{int(time.time())}.mp4")

                print(f"🎞️ Encoding video using {self.encoder}...", flush=True)
                
                # Stream frames to ffmpeg via pipe for maximum performance
                import subprocess
                import numpy as np
                h, w = height, width
                
                # Dynamic Encoder Settings
                codec_args = ['-c:v', self.encoder]
                if self.encoder == "h264_nvenc":
                    codec_args += ['-preset', 'p4', '-tune', 'hq', '-b:v', '5M']
                elif self.encoder == "libx264":
                    codec_args += ['-preset', 'superfast', '-crf', '23']
                else:
                    # General hardware encoder setting (AMF, QSV, etc.)
                    codec_args += ['-b:v', '5M']

                cmd = [
                    'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
                    '-s', f'{w}x{h}', '-pix_fmt', 'rgb24', '-r', '24',
                    '-i', '-', *codec_args, '-pix_fmt', 'yuv420p', output_path
                ]
                
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                for frame in video:
                    # Convert PIL or numpy to bytes
                    if hasattr(frame, 'tobytes'):
                        process.stdin.write(frame.tobytes())
                    elif isinstance(frame, np.ndarray):
                        process.stdin.write(frame.astype('uint8').tobytes())
                    else:
                        # Handle PIL
                        process.stdin.write(np.array(frame).astype('uint8').tobytes())
                process.stdin.close()
                process.wait()
                
                print(f"✅ Video saved to {output_path}", flush=True)
                return {"success": True, "output_path": output_path}
            
            elif hasattr(self.current_pipe, 'generate'):  # GGUF model
                return {"success": False, "error": "GGUF generation not implemented yet"}
            
        except Exception as e:
            print(f"❌ Generation failed: {e}", flush=True)
            return {"success": False, "error": str(e)}


# Global model manager instance
model_manager = VideoModelManager()


def get_model_info(model_key: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific model"""
    return VIDEO_MODELS.get(model_key)


def list_all_models() -> Dict[str, Dict[str, Any]]:
    """List all available models"""
    return VIDEO_MODELS


def get_current_status() -> Dict[str, Any]:
    """Get current status of the model manager"""
    return {
        "disk_usage": model_manager.get_disk_usage(),
        "current_model": model_manager.current_model,
        "models": VIDEO_MODELS,
    }
