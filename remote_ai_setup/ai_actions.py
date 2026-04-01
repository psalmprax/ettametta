"""
AI Core Actions - Implementation of specific generation and analysis tasks
"""

import os
import io
import base64
import torch
import uuid
import soundfile as sf
from PIL import Image
from video_model_manager import model_manager
from hardware_manager import hardware_manager

CONTENT_DIR = "/workspace/ai_content"
os.makedirs(CONTENT_DIR, exist_ok=True)

def action_render_video(job_id, req):
    print(f"🎨 [Action] Executing Video Rendering for Job {job_id}...", flush=True)
    result = model_manager.generate_video(
        prompt=req.prompt,
        image_base64=req.image_base64,
        num_frames=int(req.frames),
        steps=int(req.steps)
    )
    return result

def action_generate_voice(text):
    tts = model_manager.load_utility("tts")
    job_id = f"aud_{uuid.uuid4().hex[:6]}"
    path = os.path.join(CONTENT_DIR, f"{job_id}.wav")
    
    # Default stable embedding for SpeechT5
    speaker_emb = torch.randn(1, 512).to(hardware_manager.get_device_obj())
    with torch.no_grad():
        speech = tts(text, forward_params={"speaker_embeddings": speaker_emb})
        sf.write(path, speech["audio"], speech["sampling_rate"])
    return {"job_id": job_id, "path": path}

def action_analyze_vlm(image_base64, prompt):
    vlm, tok = model_manager.load_utility("vlm")
    img = Image.open(io.BytesIO(base64.b64decode(image_base64)))
    # Note: moondream2 specific methods
    enc = vlm.encode_image(img)
    answer = vlm.answer_question(enc, prompt, tok)
    return {"analysis": answer}

def action_transcription(file_path):
    model = model_manager.load_utility("whisper")
    segments, info = model.transcribe(file_path, beam_size=5)
    results = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
    return {"language": info.language, "segments": results}
