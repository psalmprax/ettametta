import torch
from diffusers import DiffusionPipeline, AutoPipelineForText2Image, AutoPipelineForImage2Video
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MODELS = {
    "T2V_HUNYUAN": "tencent/HunyuanVideo",
    "T2V_LTX": "Lightricks/LTX-Video",
    "ANIMATEDIFF": "guoyww/AnimateDiff",
    "SVD": "stabilityai/stable-video-diffusion-img2vid-xt",
    "VLM_MOONDREAM": "vikhyatk/moondream2",
    "LLM_LLAMA_8B": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "WHISPER": "openai/whisper-large-v3",
    "TTS_FISH": "fish-speech/fish-speech-1.5",
    "UPSCALE_ESRGAN": "ai-forever/Real-ESRGAN",
    "FACE_GFPGAN": "TencentARC/GFPGAN"
}

def warmup():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8 else torch.float16
    
    print(f"🔥 [Warmup] Starting Model Pre-flight (Device: {device}, Dtype: {dtype})")
    
    # 1. Video Models
    print("🎬 [Warmup] Pulling Video Synthesis Engines...")
    try:
        DiffusionPipeline.from_pretrained(MODELS["T2V_LTX"], torch_dtype=dtype)
        print("✅ LTX-Video Ready")
    except Exception as e:
        print(f"⚠️ LTX-Video Skip: {e}")

    try:
        AutoPipelineForText2Image.from_pretrained(MODELS["T2V_HUNYUAN"], torch_dtype=dtype)
        print("✅ HunyuanVideo Ready")
    except Exception as e:
        print(f"⚠️ Hunyuan Skip: {e}")

    # 2. Intelligence Models
    print("🧠 [Warmup] Pulling Visual Intelligence...")
    try:
        AutoModelForCausalLM.from_pretrained(MODELS["VLM_MOONDREAM"], trust_remote_code=True)
        print("✅ Moondream2 Ready")
    except Exception as e:
        print(f"⚠️ Moondream Skip: {e}")

    # 3. Audio & Speech
    print("🎙️ [Warmup] Pulling Voice & Transcription...")
    try:
        # Generic check for whisper via transformers
        from transformers import pipeline
        pipeline("automatic-speech-recognition", model=MODELS["WHISPER"])
        print("✅ Whisper Large-v3 Ready")
    except Exception as e:
        print(f"⚠️ Whisper Skip: {e}")

    print("\n🎉 [Warmup] All models cached in HF_HOME!")

if __name__ == "__main__":
    warmup()
