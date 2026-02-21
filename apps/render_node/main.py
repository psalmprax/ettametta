from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import os
import logging
import uuid
import uuid

# Fast setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RenderNode")

app = FastAPI(title="Ettametta Remote Render Node")

# Load model pipeline gracefully
try:
    from diffusers import DiffusionPipeline
    MODEL_ID = os.getenv("MODEL_ID", "ltx-video")
    pipe = DiffusionPipeline.from_pretrained(MODEL_ID)
    logger.info(f"Successfully loaded {MODEL_ID}")
except ImportError:
    pipe = None
    logger.warning("Diffusers not installed. Running in mock mode.")

class GenerationRequest(BaseModel):
    prompt: str
    duration_seconds: int = 5
    resolution: str = "720p"

class PersonaRequest(BaseModel):
    image_url: str
    text: str
    voice_id: str = "default"

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/output")

def _generate_video(job_id: str, request: GenerationRequest):
    """Background task to synthesize and save video via Diffusers"""
    output_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
    
    if pipe is None:
        # For testing the API without a GPU
        with open(output_path, "w") as f:
            f.write("mock video data")
        logger.info(f"Mock video generated at {output_path}")
        return

    num_frames = request.duration_seconds * 24
    logger.info(f"Generating {num_frames} frames for: {request.prompt}")
    
    try:
        video_result = pipe(request.prompt, num_frames=num_frames).frames
        # Diffusers typically exports to an object with .save() or requires an export utility
        try:
            video_result.save(output_path)
        except AttributeError:
             import imageio
             import numpy as np
             from PIL import Image
             if isinstance(video_result, list):
                 writer = imageio.get_writer(output_path, fps=24)
                 for frame in video_result:
                     if isinstance(frame, Image.Image):
                         writer.append_data(np.array(frame))
                     else:
                         writer.append_data(frame)
                 writer.close()
        logger.info(f"Render complete: {output_path}")
    except Exception as e:
        logger.error(f"Render failed: {e}")

@app.post("/generate")
async def generate_video(request: GenerationRequest, background_tasks: BackgroundTasks):
    """
    Receives prompt from OpenClaw/ettametta, immediately returns a job ID,
    and starts building the video on the GPU in the background.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    job_id = f"render_{uuid.uuid4().hex[:8]}"
    
    # Process heavily on background GPU
    background_tasks.add_task(_generate_video, job_id, request)
    
    return {
        "status": "processing",
        "job_id": job_id,
        "message": "Render dispatched to GPU",
        "download_url": f"/download/{job_id}" # Ready once processing completes
    }

@app.get("/download/{job_id}")
async def download_video(job_id: str):
    """Serve the completed file back to the main Ettametta server"""
    from fastapi.responses import FileResponse
    path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
    if os.path.exists(path):
        return FileResponse(path, media_type="video/mp4")
    return {"status": "processing_or_not_found"}

def _animate_persona(job_id: str, request: PersonaRequest):
    """Background task to simulate deepfake rendering"""
    output_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
    logger.info(f"Simulating persona animation for {request.image_url} speaking '{request.text[:30]}'")
    
    # In production, this would call SadTalker / LivePortrait
    with open(output_path, "w") as f:
        f.write("mock persona video data")
    logger.info(f"Mock persona video generated at {output_path}")

@app.post("/animate-persona")
async def animate_persona(request: PersonaRequest, background_tasks: BackgroundTasks):
    """
    Receives image + text, kicks off deepfake animation.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    job_id = f"persona_{uuid.uuid4().hex[:8]}"
    
    background_tasks.add_task(_animate_persona, job_id, request)
    
    return {
        "status": "processing",
        "job_id": job_id,
        "message": "Persona animation dispatched to GPU",
        "download_url": f"/download/{job_id}"
    }

if __name__ == "__main__":
    import uvicorn
    # Typically running on 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
