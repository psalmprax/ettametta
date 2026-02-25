import torch
import os, uuid, logging, imageio, numpy as np
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from diffusers import DiffusionPipeline
import uvicorn

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

# Global pipeline
pipe = None

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
