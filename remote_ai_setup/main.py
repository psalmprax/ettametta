import time
import threading
import uuid
import base64
import io
import os
import gc
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
# REQUEST MODELS
# =========================
class VideoRequest(BaseModel):
    prompt: str
    frames: int = 49
    steps: int = 20

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
    return {
        "status": "healthy", 
        "gpu": DEVICE, 
        "gpu_available": torch.cuda.is_available(),
        "vram_allocated": f"{torch.cuda.memory_allocated()/1024**3:.2f}GB" if torch.cuda.is_available() else "0GB"
    }

@app.post("/video")
async def generate_video(req: VideoRequest, bg: BackgroundTasks):
    job_id = f"vid_{uuid.uuid4().hex[:6]}"
    bg.add_task(render_video, job_id, req)
    return {"job_id": job_id, "download": f"/download/{job_id}"}

def render_video(job_id, req):
    try:
        pipe = load_ltx()
        with torch.inference_mode():
            result = pipe(prompt=req.prompt, num_frames=req.frames, num_inference_steps=req.steps)
        frames = result.frames[0]

        out_path = os.path.join(CONTENT_DIR, f"{job_id}.mp4")
        writer = imageio.get_writer(out_path, fps=24)
        for f in frames:
            writer.append_data(np.array(f))
        writer.close()
        print(f"✅ Success: Video saved to {out_path}")
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

@app.get("/download/{job_id}")
async def download(job_id: str):
    for ext in ["mp4", "wav"]:
        path = os.path.join(CONTENT_DIR, f"{job_id}.{ext}")
        if os.path.exists(path):
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

    uvicorn.run(app, host="0.0.0.0", port=8000)
