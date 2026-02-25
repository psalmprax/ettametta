import torch
import os, uuid, logging, imageio, numpy as np
from typing import Optional, List
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from diffusers import DiffusionPipeline
import uvicorn
import subprocess
from pathlib import Path

# --- COLAB ASYNCIO FIX ---
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

# --- FISH SPEECH IMPORTS (Dynamic) ---
try:
    from fish_speech.utils.schema import TTSRequest
    from fish_speech.inference import TTSInference
except ImportError:
    TTSInference = None

# --- MOONDREAM VLM IMPORTS (Dynamic) ---
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from PIL import Image
    import base64
    from io import BytesIO
except ImportError:
    AutoModelForCausalLM = None

app = FastAPI()

def load_pipeline():
    print("⏳ Loading LTX-Video... (This takes 5-10 minutes)")
    # Using DiffusionPipeline is the recommended way
    pipe = DiffusionPipeline.from_pretrained(
        "Lightricks/LTX-Video", 
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True
    )
    # REQUIRED: This enables sub-16GB memory management
    # For Higher Stability on 12-16GB GPUs use sequential_cpu_offload
    # For performance on 24GB+ use model_cpu_offload
    if torch.cuda.get_device_properties(0).total_memory < 20 * 1024**3:
        print("Using Sequential CPU Offload for low VRAM stability")
        pipe.enable_sequential_cpu_offload()
    else:
        print("Using Model CPU Offload for performance")
        pipe.enable_model_cpu_offload()
        
    return pipe

# Global inference engines
pipe = None
tts_engine = None
vlm_model = None
vlm_tokenizer = None

def load_vlm():
    global vlm_model, vlm_tokenizer
    if vlm_model is not None:
        return vlm_model, vlm_tokenizer
        
    print("⏳ Loading Moondream2 VLM...")
    model_id = "vikhyatk/moondream2"
    revision = "2024-05-20"
    try:
        vlm_model = AutoModelForCausalLM.from_pretrained(
            model_id, trust_remote_code=True, revision=revision
        ).to("cuda" if torch.cuda.is_available() else "cpu")
        vlm_tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
        return vlm_model, vlm_tokenizer
    except Exception as e:
        print(f"⚠️ Failed to load VLM: {e}")
        return None, None

def load_tts():
    print("⏳ Loading Fish Speech 1.5...")
    # This assumes fish-speech is installed in the environment
    # On Colab we will need a !pip install fish-speech
    try:
        engine = TTSInference(model_checkpoint="models/fish-speech-1.5")
        if torch.cuda.is_available():
            engine.to("cuda")
        return engine
    except Exception as e:
        print(f"⚠️ Failed to load TTS: {e}")
        return None

class GenerationRequest(BaseModel):
    prompt: str
    duration_seconds: int = 5

@app.post("/generate")
async def generate(req: GenerationRequest, bg: BackgroundTasks):
    global pipe
    if pipe is None:
        pipe = load_pipeline()
        
    job_id = f"render_{uuid.uuid4().hex[:8]}"
    bg.add_task(render_task, job_id, req.prompt)
    return {"job_id": job_id, "download_url": f"/download/{job_id}"}

class VoiceRequest(BaseModel):
    text: str

@app.post("/voice/generate")
async def generate_voice(req: VoiceRequest):
    global tts_engine
    if tts_engine is None:
        tts_engine = load_tts()
    
    if tts_engine is None:
        return {"error": "TTS Engine failed to load"}

    job_id = f"voice_{uuid.uuid4().hex[:8]}"
    audio_path = f"/content/{job_id}.mp3"
    
    # Run inference (simplified for the node)
    tts_engine.generate(req.text, output_path=audio_path)
    
    return {"job_id": job_id, "download_url": f"/download_audio/{job_id}"}

class VLMRequest(BaseModel):
    image_base64: str
    prompt: Optional[str] = "Describe this image for a video editing strategy, focusing on mood and subjects."

@app.post("/vlm/analyze")
async def analyze_image(req: VLMRequest):
    global vlm_model, vlm_tokenizer
    if vlm_model is None:
        load_vlm()
    
    if vlm_model is None:
        return {"error": "VLM Engine failed to load"}

    try:
        # Decode image
        img_data = base64.b64decode(req.image_base64)
        image = Image.open(BytesIO(img_data))
        
        # Run inference
        enc_image = vlm_model.encode_image(image)
        answer = vlm_model.answer_question(enc_image, req.prompt, vlm_tokenizer)
        
        return {"analysis": answer}
    except Exception as e:
        print(f"❌ VLM Error: {e}")
        return {"error": str(e)}

@app.get("/download_audio/{job_id}")
async def download_audio(job_id: str):
    from fastapi.responses import FileResponse
    path = f"/content/{job_id}.mp3"
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Not found"}

def render_task(job_id, prompt):
    print(f"🎬 Starting generation for: {prompt}")
    try:
        with torch.inference_mode():
            # Memory-safe generation settings
            frames = pipe(
                prompt=prompt, 
                num_frames=121, 
                decode_chunk_size=8,
                num_inference_steps=30
            ).frames[0]
            
        output_path = f"/content/{job_id}.mp4"
        writer = imageio.get_writer(output_path, fps=24)
        for frame in frames:
            writer.append_data(np.array(frame))
        writer.close()
        print(f"✅ Finished: {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

@app.get("/download/{job_id}")
async def download(job_id: str):
    from fastapi.responses import FileResponse
    path = f"/content/{job_id}.mp4"
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Not found"}

if __name__ == "__main__":
    import asyncio
    
    # In environments like Colab/Jupyter, we need to handle the existing event loop
    try:
        # Check if we're in a Jupyter/Colab environment
        try:
            shell = get_ipython().__class__.__name__
            if shell == 'ZMQInteractiveShell':
                import nest_asyncio
                nest_asyncio.apply()
                print("📓 Notebook/Colab environment detected. Patched asyncio.")
        except NameError:
            pass

        # Use uvicorn.run directly; with nest_asyncio, it should no longer crash
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            print("🚀 Running in an existing loop. Starting server with live logs...")
            # Fallback for strict environments
            import nest_asyncio
            nest_asyncio.apply()
            
            config = uvicorn.Config(app=app, host="0.0.0.0", port=8000, loop="asyncio")
            server = uvicorn.Server(config)
            
            # Using await directly in a notebook cell is safer and shows logs
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In Colab/Jupyter, we can't 'run' a new loop, we just use the existing one
                asyncio.ensure_future(server.serve())
            else:
                asyncio.run(server.serve())
            
            print("✅ Server is active! You can now monitor it in this cell.")
        else:
            raise e
