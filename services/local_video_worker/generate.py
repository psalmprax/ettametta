import os
from celery import Celery
import logging
# We only import Diffusers if this worker is actually started in the PyTorch container
try:
    from diffusers import DiffusionPipeline
except ImportError:
    DiffusionPipeline = None

# Configure Celery to connect to our existing Redis broker
app = Celery('local_video_worker', broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# Basic configuration
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/workspace/output")
MODEL_ID = os.getenv("MODEL_ID", "ltx-video")

# Global pipe reference to avoid reloading model for every task
pipe = None

def init_pipeline():
    global pipe
    if pipe is None and DiffusionPipeline is not None:
        logging.info(f"Loading DiffusionPipeline: {MODEL_ID}")
        try:
            pipe = DiffusionPipeline.from_pretrained(MODEL_ID)
            # Optional: pipe.to("cuda") if not handled automatically
        except Exception as e:
            logging.error(f"Failed to load diffusion pipeline: {e}")

@app.task(name="video.synthesize_local")
def synthesize_local_task(prompt: str, duration_seconds: int = 5) -> str:
    """
    Synthesizes a short video clip using local GPU infrastructure.
    Returns the absolute path to the generated .mp4 file.
    """
    if DiffusionPipeline is None:
        error_msg = "Diffusers library not installed. Cannot run local synthesis."
        logging.error(error_msg)
        return error_msg

    init_pipeline()
    
    if pipe is None:
        error_msg = "Pipeline failed to initialize."
        logging.error(error_msg)
        return error_msg
        
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Calculate frames based on requested duration (assume 24 fps)
    num_frames = duration_seconds * 24
    
    logging.info(f"Synthesizing {duration_seconds}s ({num_frames} frames) for prompt: {prompt[:30]}...")
    
    try:
        # Generate video utilizing diffusers
        video_result = pipe(prompt, num_frames=num_frames).frames
        
        # Save output
        import uuid
        filename = f"clip_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        # Depending on the exact model output, saving mechanisms differ.
        # Often it requires a helper function to export to mp4.
        # Assuming the pipeline returns an object with a save() method:
        try:
            video_result.save(output_path)
        except AttributeError:
             # Fallback if the object is just a tensor/list of images
             import imageio
             from PIL import Image
             import numpy as np
             
             # Convert frames to numpy arrays if necessary, then write
             if isinstance(video_result, list):
                 writer = imageio.get_writer(output_path, fps=24)
                 for frame in video_result:
                     if isinstance(frame, Image.Image):
                         writer.append_data(np.array(frame))
                     else:
                         writer.append_data(frame)
                 writer.close()
             else:
                  raise ValueError("Unexpected output format from pipeline")

        logging.info(f"Video saved to {output_path}")
        return output_path
        
    except Exception as e:
        error_msg = f"Synthesis failed: {str(e)}"
        logging.error(error_msg)
        return error_msg

if __name__ == '__main__':
    # Initialize pipeline only when worker starts
    init_pipeline()
    app.start()
