# Google Colab Render Node Deployment Guide

This guide explains how to host a high-performance **LTX-Video** rendering node on Google Colab for free and connect it to your **ettametta** OCI production server.

## Overview
Since your OCI instance lacks a GPU, local video synthesis is slow. Google Colab provides free access to powerful GPUs (like the Tesla T4), which we can use to accelerate video generation via an encrypted tunnel.

---

## 1. Google Colab Setup (The GPU Side)

1.  **Open Google Colab**: Navigate to [Google Colab](https://colab.research.google.com/).
2.  **Enable GPU**:
    *   Go to `Runtime` > `Change runtime type`.
    *   Select **T4 GPU** (Hardware Accelerator).
3.  **Deploy the Node**: Copy and paste the following "One-Click" script into a Colab cell and run it:

```python
# --- Ettametta One-Click Colab Render Node ---
!pip install -q diffusers transformers accelerate uvicorn fastapi pyngrok imageio[ffmpeg]

import os
from pyngrok import ngrok
from google.colab import userdata

# 1. SETUP TUNNEL
# Get your token at https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_TOKEN = "YOUR_NGROK_AUTHTOKEN_HERE" 
ngrok.set_auth_token(NGROK_TOKEN)
public_url = ngrok.connect(8000).public_url
print(f"🚀 RENDER_NODE_URL={public_url}")

# 2. RUN RENDER NODE
with open("render_node.py", "w") as f:
    f.write('''
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import os, uuid, logging, imageio, numpy as np
from diffusers import DiffusionPipeline
from PIL import Image

app = FastAPI()
pipe = DiffusionPipeline.from_pretrained("Lightricks/LTX-Video", torch_dtype="float16").to("cuda")

class GenerationRequest(BaseModel):
    prompt: str
    duration_seconds: int = 5

@app.post("/generate")
async def generate(req: GenerationRequest, bg: BackgroundTasks):
    job_id = f"render_{uuid.uuid4().hex[:8]}"
    bg.add_task(render_task, job_id, req.prompt)
    return {"job_id": job_id, "download_url": f"/download/{job_id}"}

def render_task(job_id, prompt):
    frames = pipe(prompt, num_frames=121).frames[0]
    output_path = f"/content/{job_id}.mp4"
    writer = imageio.get_writer(output_path, fps=24)
    for frame in frames:
        writer.append_data(np.array(frame))
    writer.close()

@app.get("/download/{job_id}")
async def download(job_id: str):
    from fastapi.responses import FileResponse
    return FileResponse(f"/content/{job_id}.mp4")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''')

!python render_node.py
```

---

## 2. OCI Server Integration (The Controller Side)

Once the Colab script provides you with a `public_url` (e.g., `https://xxxx-xxxx.ngrok-free.app`):

1.  **Update Environment**:
    Open your `.env` file on the OCI server:
    ```bash
    nano /home/ubuntu/ettametta/.env
    ```
2.  **Add/Update the Render Node URL**:
    ```bash
    RENDER_NODE_URL=https://xxxx-xxxx.ngrok-free.app
    ```
3.  **Restart Services**:
    ```bash
    sudo docker-compose restart api celery_worker
    ```

---

## 3. Maintenance & Limitations

> [!IMPORTANT]
> **Persistence**: Google Colab sessions are not permanent. If you close the browser tab or stay inactive for too long, the tunnel will die. You will need to refresh the Colab URL in your OCI `.env` every few hours.

> [!TIP]
> **Performance**: A Tesla T4 GPU will render 5 seconds of cinematic video in approximately 3-5 minutes, which is 20x faster than your OCI CPU.

---

## 4. Verification
To test the connection, trigger a generative video task from the Dashboard. Check the Celery worker logs on your OCI server:
```bash
docker-compose logs -f celery_worker
```
You should see: `[GenerativeService] Routing synthesis to Remote GPU Node: https://xxxx-xxxx.ngrok-free.app`
