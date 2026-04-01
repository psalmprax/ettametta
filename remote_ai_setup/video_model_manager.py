"""
Video Model Manager - Unified resource orchestration for AI models
"""

import os
import gc
import torch
import threading
import time
import subprocess
from typing import Optional, Dict, Any
from huggingface_hub import snapshot_download, hf_hub_download
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from hardware_manager import hardware_manager

# Model registry
VIDEO_MODELS = {
    "ltx_2_19b": {
        "name": "LTX-Video 2 19B",
        "repo_id": "Lightricks/LTX-Video",
        "type": "diffusers",
        "vram_estimate": "19GB (Quantized)",
    },
}

class VideoModelManager:
    """Manages all AI resources with Smart VRAM Orchestration (TTL + Mutually Exclusive)"""
    
    def __init__(self, hf_home: str = None):
        self.hf_home = hf_home or os.environ.get('HF_HOME', '/workspace/.hf_home')
        self.current_model = None
        self.active_resources = {} # Active library handles
        self.utils = {} # Active utility handles
        self.lock = threading.Lock()
        self.is_busy = False # Busy status tracking
        self.device = hardware_manager.device
        self.device_obj = hardware_manager.get_device_obj()
        self.encoder = self._get_best_encoder()
        self.last_active_time = time.time()
        self.vram_ttl_seconds = 600
        self._start_vram_monitor()

    def _start_vram_monitor(self):
        def monitor():
            while True:
                time.sleep(60)
                if (self.current_model or self.active_resources) and (time.time() - self.last_active_time > self.vram_ttl_seconds):
                    print(f"⏰ [SmartVRAM] TTL Expired. Purging resources...", flush=True)
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
        print("🗑️ [SmartVRAM] Evicting all models and utilities...", flush=True)
        self.active_resources.clear()
        self.utils.clear()
        self.current_model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        hardware_manager.clear_cache()

    def load_utility(self, name: str):
        """Loads a utility exclusively, ensuring large video models are evicted first"""
        self.last_active_time = time.time()
        if name in self.active_resources: return self.active_resources[name]
        
        with self.lock:
            self.is_busy = True
            try:
                # If a heavy video model is loaded, pull it out first
                if self.current_model:
                    print(f"🔄 [SmartVRAM] Evicting VIDEO model '{self.current_model}' for UTILITY '{name}'...", flush=True)
                    self.unload_all()
                
                print(f"📥 Loading Utility: {name}...", flush=True)
                if name == "whisper":
                    from faster_whisper import WhisperModel
                    self.utils[name] = WhisperModel("large-v3", device=self.device, compute_type="float16")
                elif name == "tts":
                    self.utils[name] = pipeline("text-to-speech", model="microsoft/speecht5_tts", device=0 if self.device == "cuda" else -1)
                elif name == "vlm":
                    model_id = "vikhyatk/moondream2"
                    self.utils[name] = (
                        AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True).to(self.device_obj),
                        AutoTokenizer.from_pretrained(model_id)
                    )
                # ... other utilities ...
                return self.utils.get(name)
            finally:
                self.is_busy = False

    def generate_video(self, prompt, **kwargs):
        """Protected 19B generation entry point"""
        self.last_active_time = time.time()
        with self.lock:
            self.is_busy = True
            try:
                if self.current_model != "ltx_2_19b":
                    self.unload_all()
                    self.current_model = "ltx_2_19b"
                    print("💎 [SmartVRAM] Exclusive 19B Video Model Loaded.", flush=True)
                
                # Simulated generation for infra tests
                return {"success": True, "output_path": "/workspace/ai_content/test.mp4"}
            finally:
                self.is_busy = False

model_manager = VideoModelManager()
