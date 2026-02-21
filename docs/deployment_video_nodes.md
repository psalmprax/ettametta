# Remote Video Rendering: Deployment Guide

This guide explains how to deploy the *Ettametta Remote Render Node* (`apps/render_node`) across various cloud platforms, ranging from completely free options to highly cost-effective paid solutions.

## Architecture Context
In **Phase 33**, we decoupled the heavy PyTorch/Diffusers video rendering (using models like `ltx-video`) from the core API. 
The core backend now sends a POST request to `RENDER_NODE_URL`. The remote node processes the video on an external GPU and returns the URL.

---

## Option 1: The "Free forever" Route (Google Colab)
*Best for: Testing, hobbyists, zero-budget MVPs. (Note: Colab sessions expire after 12 hours or inactivity).*

1. **Upload the Code**: Zip the `apps/render_node` folder and upload it to your Google Drive.
2. **Open Colab**: Create a new Google Colab Noteobok (change Runtime type to **T4 GPU**).
3. **Mount Drive**:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
4. **Install Dependencies**:
   ```python
   !pip install fastapi uvicorn diffusers transformers accelerate torch imageio
   !pip install pyngrok # Crucial for exposing the local server to the internet
   ```
5. **Start NGrok & The Server**:
   ```python
   import os
   from pyngrok import ngrok
   
   # Set your ngrok auth token (get it free from ngrok.com)
   os.system("ngrok config add-authtoken YOUR_NGROK_TOKEN")
   
   # Open a tunnel to port 8000
   public_url = ngrok.connect(8000).public_url
   print(f"Set this URL in Ettametta settings: {public_url}")
   
   # Run the server
   !cd /content/drive/MyDrive/render_node && uvicorn main:app --host 0.0.0.0 --port 8000
   ```
6. **Connect**: Copy the `public_url` printed in Colab and paste it into your Ettametta settings as `RENDER_NODE_URL`.

---

## Option 2: The "Ultra-Cheap On-Demand" Route (RunPod)
*Best for: Production workloads. You only pay while rendering. (~$0.20 to $0.40 per hour).*

1. **Dashboard**: Go to [RunPod.io](https://runpod.io) and create an account.
2. **Deploy Pod**: Select "Deploy Secure Cloud" -> Choose an RTX 3090 or RTX 4090 template (usually under $0.40/hr).
3. **Select Template**: Choose the `RunPod PyTorch` template.
4. **Expose Ports**: Under "Customize Deployment", click "Edit TCP/HTTP Ports" and add `8000` for HTTP.
5. **Start Pod & Connect**: Once running, click "Connect" -> "Start Web Terminal".
6. **Clone & Run**:
   ```bash
   # In the RunPod terminal
   git clone https://your-repo-url.com/viral_forge.git
   cd viral_forge/apps/render_node
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
7. **Connect**: On the RunPod dashboard for your Pod, click the "Connect" button under Port 8000. It will give you a unique RunPod URL. Paste this into Ettametta.

---

## Option 3: The "Persistent Cheap Compute" Route (Lambda Labs)
*Best for: 24/7 dedicated heavy workloads. Cheapest per-hour dedicated instances.*

1. **Dashboard**: Go to [Lambda Labs Cloud](https://lambdalabs.com/).
2. **Launch Instance**: Select an instance (e.g., 1x RTX A4000 or RTX 6000 Ada).
3. **SSH In**:
   ```bash
   ssh ubuntu@<your-instance-ip>
   ```
4. **Docker Setup**: We provided a `Dockerfile` inside `apps/render_node` specifically for this.
   ```bash
   git clone https://your-repo-url.com/viral_forge.git
   cd viral_forge/apps/render_node
   
   # Build the container (this handles all heavy CUDA dependencies)
   docker build -t ettametta-render-node .
   
   # Run the container, exposing port 8000
   docker run -d --gpus all -p 8000:8000 ettametta-render-node
   ```
5. **Connect**: Your `RENDER_NODE_URL` is simply `http://<your-instance-ip>:8000`. 
   *(Note: For production, put this behind an Nginx reverse proxy with SSL).*
