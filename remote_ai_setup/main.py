import time
import threading
import uuid
import base64
import io
import os
import gc
import shutil
import asyncio
import warnings
import torch
import imageio
import numpy as np
import soundfile as sf
import uvicorn
import nest_asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from diffusers import DiffusionPipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from PIL import Image
import cv2
import torch.hub
from gfpgan import GFPGANer
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet

# =========================
# CONFIGURATION
# =========================
warnings.filterwarnings("ignore")
nest_asyncio.apply()

CONTENT_DIR = "/tmp/ai_content"
os.makedirs(CONTENT_DIR, exist_ok=True)

app = FastAPI(title="ettametta Remote AI Engine (LTX + SpeechT5 + Moondream2)")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"📡 Using Device: {DEVICE}")

# =========================
# GLOBALS (Lazy Loading)
# =========================
pipe = None
tts_pipeline = None
speaker_embedding = None
vlm_model = None
vlm_tokenizer = None
whisper_model = None
llm_model = None
llm_tokenizer = None
face_enhancer = None
upscaler_model = None

# =========================
# GPU CLEANUP
# =========================
def clear_gpu():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

# =========================
# LOADERS
# =========================
def load_ltx():
    global pipe
    if pipe is None:
        print("📥 Loading LTX-Video...")
        pipe = DiffusionPipeline.from_pretrained(
            "Lightricks/LTX-Video",
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
        )
        if DEVICE == "cuda":
            pipe.enable_sequential_cpu_offload()
        else:
            pipe.to("cpu")
    return pipe

def load_tts():
    global tts_pipeline, speaker_embedding
    if tts_pipeline is None:
        print("📥 Loading Microsoft SpeechT5 TTS...")
        tts_pipeline = pipeline(
            "text-to-speech",
            model="microsoft/speecht5_tts",
            device=0 if torch.cuda.is_available() else -1
        )
        # Create stable default speaker embedding (512-dim)
        torch.manual_seed(42)
        speaker_embedding = torch.randn(1, 512)
        if torch.cuda.is_available():
            speaker_embedding = speaker_embedding.cuda()
    return tts_pipeline

def load_vlm():
    global vlm_model, vlm_tokenizer
    if vlm_model is None:
        print("📥 Loading Moondream2...")
        clear_gpu()
        model_id = "vikhyatk/moondream2"
        rev = "2024-05-20"
        vlm_model = AutoModelForCausalLM.from_pretrained(
            model_id, trust_remote_code=True, revision=rev
        ).to(DEVICE)
        vlm_tokenizer = AutoTokenizer.from_pretrained(model_id, revision=rev)
    return vlm_model, vlm_tokenizer

def load_whisper():
    global whisper_model
    if whisper_model is None:
        from faster_whisper import WhisperModel
        print("📥 Loading Faster-Whisper (Large-v3)...")
        whisper_model = WhisperModel("large-v3", device=DEVICE, compute_type="float16")
    return whisper_model

def load_llm():
    global llm_model, llm_tokenizer
    if llm_model is None:
        print("📥 Loading Llama-3.1-8B-Instruct (4-bit)...")
        model_id = "unsloth/Meta-Llama-3.1-8B-Instruct" # Using a pre-quantized or light version
        llm_tokenizer = AutoTokenizer.from_pretrained(model_id)
        llm_model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_4bit=True
        )
    return llm_model, llm_tokenizer

# =========================
# LOADERS
# =========================
def load_ltx():
    global pipe
    if pipe is None:
        print("📥 Loading LTX-Video...")
        pipe = DiffusionPipeline.from_pretrained(
            "Lightricks/LTX-Video", torch_dtype=torch.float16, low_cpu_mem_usage=True
        )
        if DEVICE == "cuda": pipe.enable_sequential_cpu_offload()
        else: pipe.to("cpu")
    return pipe

def load_enhancers(upscale_factor=2):
    global face_enhancer, upscaler_model
    if face_enhancer is None:
        print("📥 Loading GFPGAN (Face Restoration)...")
        face_enhancer = GFPGANer(
            model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth',
            upscale=1, arch='clean', channel_multiplier=2, bg_upsampler=None
        )
    if upscaler_model is None:
        print(f"📥 Loading Real-ESRGAN (x{upscale_factor})...")
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        upscaler_model = RealESRGANer(
            scale=4, model_path='https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
            model=model, tile=400, tile_pad=10, pre_pad=0, half=True if DEVICE == "cuda" else False
        )
    return face_enhancer, upscaler_model

def load_tts():
    global tts_pipeline, speaker_embedding
    if tts_pipeline is None:
        print("📥 Loading Microsoft SpeechT5 TTS...")
        tts_pipeline = pipeline("text-to-speech", model="microsoft/speecht5_tts", device=0 if torch.cuda.is_available() else -1)
        torch.manual_seed(42)
        speaker_embedding = torch.randn(1, 512).to(DEVICE)
    return tts_pipeline

def load_vlm():
    global vlm_model, vlm_tokenizer
    if vlm_model is None:
        print("📥 Loading Moondream2...")
        clear_gpu()
        model_id = "vikhyatk/moondream2"
        vlm_model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, revision="2024-05-20").to(DEVICE)
        vlm_tokenizer = AutoTokenizer.from_pretrained(model_id, revision="2024-05-20")
    return vlm_model, vlm_tokenizer

def load_whisper():
    global whisper_model
    if whisper_model is None:
        from faster_whisper import WhisperModel
        print("📥 Loading Faster-Whisper (Large-v3)...")
        whisper_model = WhisperModel("large-v3", device=DEVICE, compute_type="float16")
    return whisper_model

def load_llm():
    global llm_model, llm_tokenizer
    if llm_model is None:
        print("📥 Loading Llama-3.1-8B-Instruct (4-bit)...")
        model_id = "unsloth/Meta-Llama-3.1-8B-Instruct"
        llm_tokenizer = AutoTokenizer.from_pretrained(model_id)
        llm_model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto", load_in_4bit=True)
    return llm_model, llm_tokenizer

# =========================
# REQUEST MODELS
# =========================
class VideoRequest(BaseModel):
    prompt: str
    image_base64: str = None
    frames: int = 121
    steps: int = 35
    upscale_factor: int = 4   # 2 or 4 for Real-ESRGAN
    enhance_face: bool = True  # Enable GFPGAN

class VoiceRequest(BaseModel):
    text: str

class VLMRequest(BaseModel):
    image_base64: str
    prompt: str = "Describe this image."

class LLMRequest(BaseModel):
    prompt: str
    system_prompt: str = "You are a specialized AI assistant for ettametta."
    max_tokens: int = 512

# =========================
# ENDPOINTS
# =========================
@app.get("/health")
async def health():
    total, used, free = shutil.disk_usage("/")
    return {
        "status": "healthy", 
        "gpu": DEVICE, 
        "gpu_available": torch.cuda.is_available(),
        "vram_allocated": f"{torch.cuda.memory_allocated()/1024**3:.2f}GB" if torch.cuda.is_available() else "0GB",
        "disk_free": f"{free/1024**3:.2f}GB",
        "disk_used_percent": f"{(used/total)*100:.1f}%"
    }

@app.post("/video")
async def generate_video(req: VideoRequest, bg: BackgroundTasks):
    job_id = f"vid_{uuid.uuid4().hex[:6]}"
    bg.add_task(render_video, job_id, req)
    return {"job_id": job_id, "download": f"/download/{job_id}"}

def render_video(job_id, req):
    try:
        # 1. Diffusion Pass
        pipe_local = load_ltx()
        print(f"🎨 Rendering Video ({req.frames} frames): {req.prompt}")
        
        negative_prompt = "low quality, animation, cartoon, cgi, 3d, render, blur, distorted, text, watermark, grainy, flicker, low resolution, bad anatomy, stylized"
        guidance_scale = 4.0
        
        image_obj = None
        if req.image_base64:
            print("📸 Processing Reference Image for I2V...")
            img_data = base64.b64decode(req.image_base64)
            image_obj = Image.open(io.BytesIO(img_data)).convert("RGB")

        realism_keywords = ["human", "person", "man", "woman", "elder", "portrait", "face", "real", "photorealistic", "photo"]
        if any(k in req.prompt.lower() for k in realism_keywords):
            print("📸 Injecting 4K Ultra-Real Photo details...")
            req.prompt += ", raw photo, 8k resolution, cinematic 35mm lens, f/1.8, bokeh, extreme skin textures, Fujifilm, highly detailed skin pores, cinematic grain, sharp focus, dslr"
            guidance_scale = 6.0  # Boosted for 4K micro-details

        with torch.inference_mode():
            if image_obj:
                result = pipe_local(
                    prompt=req.prompt, image=image_obj, negative_prompt=negative_prompt,
                    num_frames=req.frames, num_inference_steps=req.steps, guidance_scale=guidance_scale
                )
            else:
                result = pipe_local(
                    prompt=req.prompt, negative_prompt=negative_prompt,
                    num_frames=req.frames, num_inference_steps=req.steps, guidance_scale=guidance_scale
                )
        frames = result.frames[0]

        # 2. Refinement Pass (Phase 91: 4K Upgrade)
        if req.upscale_factor > 1 or req.enhance_face:
            print(f"✨ Post-Processing Refinement (GFPGAN / {req.upscale_factor}x Real-ESRGAN)...")
            global pipe
            pipe = None # Unload from global to free VRAM for 4K upscale
            clear_gpu()
            
            face_restorer, upscaler = load_enhancers(upscale_factor=req.upscale_factor)
            enhanced_frames = []
            for i, frame in enumerate(frames):
                img_bgr = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
                if req.enhance_face:
                    try: _, _, img_bgr = face_restorer.enhance(img_bgr, has_aligned=False, only_center_face=False, paste_back=True)
                    except: pass
                if req.upscale_factor > 1:
                    try: img_bgr, _ = upscaler.enhance(img_bgr, outscale=req.upscale_factor)
                    except: pass
                enhanced_frames.append(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
                if i % 10 == 0: print(f"   Processed {i}/{len(frames)} frames...")
            
            frames = enhanced_frames
            global face_enhancer, upscaler_model
            face_enhancer = None
            upscaler_model = None
            clear_gpu()

        # 3. Encoding Pass
        out_path = os.path.join(CONTENT_DIR, f"{job_id}.mp4")
        print(f"🎬 High-Fidelity Encoding: {len(frames)} frames to {out_path}...")
        
        # Optimized for 4K Ultra-Realism (CRF 16 Lossless, Slower Preset, YUV420P)
        writer = imageio.get_writer(
            out_path, 
            fps=24, 
            codec='libx264', 
            ffmpeg_params=['-crf', '16', '-preset', 'slower', '-pix_fmt', 'yuv420p']
        )
        for i, f in enumerate(frames):
            img_array = np.array(f)
            if img_array.dtype != np.uint8:
                img_array = (img_array * 255).astype(np.uint8)
            writer.append_data(img_array)
        writer.close()
        
        file_size = os.path.getsize(out_path) / 1024
        print(f"✅ Success: Cinematic Video saved to {out_path} ({file_size:.1f} KB)")
    except Exception as e:
        print(f"❌ Error (Video): {e}")

@app.post("/voice")
async def generate_voice(req: VoiceRequest):
    clear_gpu()
    tts = load_tts()
    job_id = f"aud_{uuid.uuid4().hex[:6]}"
    path = os.path.join(CONTENT_DIR, f"{job_id}.wav")

    try:
        with torch.no_grad():
            speech = tts(
                req.text,
                forward_params={"speaker_embeddings": speaker_embedding}
            )
            sf.write(path, speech["audio"], speech["sampling_rate"])
        print(f"✅ Success: Audio saved to {path}")
        return {"job_id": job_id, "download": f"/download/{job_id}"}
    except Exception as e:
        print(f"❌ Error (TTS): {e}")
        return {"error": str(e)}

@app.post("/vlm")
async def analyze(req: VLMRequest):
    clear_gpu()
    model, tokenizer = load_vlm()
    try:
        img = Image.open(io.BytesIO(base64.b64decode(req.image_base64)))
        enc = model.encode_image(img)
        answer = model.answer_question(enc, req.prompt, tokenizer)
        return {"analysis": answer}
    except Exception as e:
        print(f"❌ Error (VLM): {e}")
        return {"error": str(e)}

@app.post("/transcribe")
async def transcribe(bg: BackgroundTasks, file_path: str = None):
    """
    In a full production setup, this would handle file uploads.
    For this remote node, we can point it to a file generated/downloaded locally.
    """
    if not file_path or not os.path.exists(file_path):
        return {"error": "File not found"}
        
    clear_gpu()
    model = load_whisper()
    try:
        segments, info = model.transcribe(file_path, beam_size=5)
        results = []
        for segment in segments:
            results.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
        return {"language": info.language, "segments": results}
    except Exception as e:
        print(f"❌ Error (Whisper): {e}")
        return {"error": str(e)}

@app.post("/llm")
async def text_gen(req: LLMRequest):
    # Unload large models if needed to prevent OOM
    # In a 16GB environment, we might need to unload LTX before loading Llama
    global pipe
    if pipe is not None:
        print("💾 Unloading LTX-Video to free VRAM for LLM...")
        pipe = None
        clear_gpu()

    model, tokenizer = load_llm()
    try:
        messages = [
            {"role": "system", "content": req.system_prompt},
            {"role": "user", "content": req.prompt},
        ]
        input_ids = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(DEVICE)
        
        outputs = model.generate(
            input_ids, 
            max_new_tokens=req.max_tokens, 
            do_sample=True, 
            temperature=0.7
        )
        response = tokenizer.decode(outputs[0][input_ids.shape[-1]:], skip_special_tokens=True)
        return {"response": response}
    except Exception as e:
        print(f"❌ Error (LLM): {e}")
        return {"error": str(e)}

def delete_file(path: str):
    """Background task to delete a file after download."""
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"🗑️ Deleted downloaded file: {path}")
        except Exception as e:
            print(f"⚠️ Failed to delete {path}: {e}")

def cleanup_old_files(max_age_hours=24):
    """Periodic cleanup of old files in CONTENT_DIR."""
    while True:
        try:
            print(f"🧹 Running TTL Cleanup (Age > {max_age_hours}h)...")
            now = time.time()
            for f in os.listdir(CONTENT_DIR):
                path = os.path.join(CONTENT_DIR, f)
                if os.path.isfile(path):
                    if now - os.path.getmtime(path) > (max_age_hours * 3600):
                        os.remove(path)
                        print(f"🧹 Purged stale file: {f}")
        except Exception as e:
            print(f"⚠️ Cleanup Error: {e}")
        time.sleep(3600) # Run every hour

@app.get("/download/{job_id}")
async def download(job_id: str, bg: BackgroundTasks):
    for ext in ["mp4", "wav"]:
        path = os.path.join(CONTENT_DIR, f"{job_id}.{ext}")
        if os.path.exists(path):
            bg.add_task(delete_file, path)
            return FileResponse(path)
    return {"error": "File not found"}

# =========================
# STARTUP
# =========================
if __name__ == "__main__":
    import sys
    print("🚀 ettametta Remote AI Engine starting...")
    
    try:
        from pyngrok import ngrok
        ngrok.set_auth_token("3A2lY17VmZc4OjOK3YjT843iJgW_4KCSDY1bRAHvyFtLkgJbh")
        
        # Disconnect any existing tunnels to avoid ERR_NGROK_334
        tunnels = ngrok.get_tunnels()
        for t in tunnels:
            print(f"🛑 Closing existing tunnel: {t.public_url}")
            ngrok.disconnect(t.public_url)
            
        public_url = ngrok.connect(8000).public_url
        print(f"🌍 Public Access: {public_url}")
        print(f"🏥 Health Check: {public_url}/health")
    except Exception as e:
        print(f"⚠️ Ngrok Connection Failed: {e}")
        print("💡 Server will still be accessible via local network/Vast.ai port.")

    # Start TTL Cleanup Thread
    threading.Thread(target=cleanup_old_files, daemon=True).start()

    uvicorn.run(app, host="0.0.0.0", port=8000)
