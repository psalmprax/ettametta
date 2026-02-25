# LTX-2 Video Synthesis Lifecycle

This document details the sequence of events during a video generation request within the Ettametta ecosystem.

## 1. Request Initiation (Local Ettametta API)
- **Endpoint**: `POST /api/synthesis/generate`
- **Payload**: JSON containing `prompt` and `duration_seconds`.
- **Logic**: The API reads `RENDER_NODE_URL` from the environment and forwards the request via the ngrok/RunPod tunnel.

## 2. Job Handshake (Remote GPU Node)
- **FastAPI Endpoint**: `POST /generate` on the remote node.
- **Immediate Response**: Node generates a unique `job_id` (e.g., `v_a1b2c3`) and returns it.
- **Asynchronous Execution**: The render task is added to a `BackgroundTasks` queue to prevent HTTP timeouts.

## 3. Model Materialization (Weight Loading)
- **Library**: `diffusers.DiffusionPipeline`.
- **Memory Strategy**: 
    - **Low System RAM**: Uses `low_cpu_mem_usage=True`.
    - **Low VRAM (<20GB)**: `pipe.enable_sequential_cpu_offload()` moves layers to GPU one-by-one.
    - **High VRAM (24GB+)**: `pipe.enable_model_cpu_offload()` for balanced speed.

## 4. Diffusion Inference (The AI Core)
- **Text Encoding**: Prompt converted to embeddings.
- **Inference Steps**: 30 steps of denoising visual latents.
- **Latent Space**: Generation happens in compressed latent space to save memory.
- **VAE Decoding**: Latents are expanded into 121 raw pixel frames (100% materialization).

## 5. Post-Processing & Encoding
- **Assembly**: `imageio` captures raw frames.
- **MP4 Stitched**: Compressed at 24fps.
- **Cleanup**: `gc.collect()` and `torch.cuda.empty_cache()` are triggered to prevent memory leaks between jobs.

## 6. Retrieval (Download)
- **Local Fetch**: Ettametta API calls `GET /download/{job_id}` via the tunnel.
- **Storage**: The video is stored locally in the Ettametta asset registry and served to the UI.
