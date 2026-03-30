# Remote AI Server - HunyuanVideo 1.5 Installation Guide

## Server Information

### Current Server (RTX A6000)
- **Host**: 142.189.180.40
- **Port**: 50512
- **SSH Key**: `/home/psalmprax/Music/id_rsa`
- **GPU**: NVIDIA RTX A6000
- **VRAM**: 48GB (49140 MiB)
- **Driver Version**: 580.105.08
- **CUDA**: 12.4

### Previous Server (Unavailable)
- **Host**: 220.135.0.171
- **Port**: 45672

---

## HunyuanVideo 1.5 Installation (RTX A6000 - 48GB VRAM)

### Prerequisites
- Ubuntu/Linux with NVIDIA GPU
- CUDA 12.4+
- Python 3.10+
- ~40GB+ disk space for models

### Virtual Environment Setup

```bash
# Create virtual environment
python3 -m venv /workspace/remote_ai_group/venv

# Activate virtual environment
source /workspace/remote_ai_group/venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Required Packages (RTX A6000 - 48GB VRAM)

```bash
# Core ML packages
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124

# Transformers and Diffusers
pip install transformers==5.3.0 diffusers==0.37.0 accelerate==1.13.0

# Video processing
pip install imageio==2.37.3 imageio-ffmpeg==0.6.0 av==16.1.0 opencv-python==4.13.0.92

# Audio processing
pip install soundfile==0.13.1

# API server
pip install fastapi==0.135.1 uvicorn==0.41.0 python-multipart==0.0.22

# Utilities
pip install huggingface_hub==1.7.1 safetensors==0.7.0 sentencepiece==0.2.1 tiktoken==0.12.0 tokenizers==0.22.2
```

### Complete Package List

```
Package                  Version
------------------------ ------------
accelerate               1.13.0
annotated-doc            0.0.4
annotated-types          0.7.0
anyio                    4.12.1
av                       16.1.0
certifi                  2026.2.25
cffi                     2.0.0
charset-normalizer       3.4.5
click                    8.3.1
diffusers                0.37.0
fastapi                  0.135.1
filelock                 3.20.0
fsspec                   2025.12.0
h11                      0.16.0
hf-xet                   1.4.2
httpcore                 1.0.9
httpx                    0.28.1
huggingface_hub          1.7.1
idna                     3.11
ImageIO                  2.37.3
imageio-ffmpeg           0.6.0
importlib_metadata       8.7.1
Jinja2                   3.1.6
markdown-it-py           4.0.0
MarkupSafe              3.0.2
mdurl                    0.1.2
mpmath                   1.3.0
networkx                 3.6.1
numpy                    2.3.5
nvidia-cublas-cu12       12.4.5.8
nvidia-cuda-cupti-cu12   12.4.127
nvidia-cuda-nvrtc-cu12   12.4.127
nvidia-cuda-runtime-cu12 12.4.127
nvidia-cudnn-cu12        9.1.0.70
nvidia-cufft-cu12        11.2.1.3
nvidia-curand-cu12       10.3.5.147
nvidia-cusolver-cu12     11.6.1.9
nvidia-cusparse-cu12     12.3.1.170
nvidia-cusparselt-cu12   0.6.2
nvidia-nccl-cu12         2.21.5
nvidia-nvjitlink-cu12    12.4.127
nvidia-nvtx-cu12         12.4.127
opencv-python            4.13.0.92
packaging                26.0
pillow                   12.0.0
pip                      26.0.1
psutil                   7.2.2
pycparser                3.0
pydantic                 2.12.5
pydantic_core            2.41.5
Pygments                 2.19.2
python-multipart         0.0.22
PyYAML                   6.0.3
regex                    2026.2.28
requests                 2.32.5
rich                     14.3.3
safetensors              0.7.0
scipy                    1.17.1
sentencepiece            0.2.1
setuptools               70.2.0
shellingham              1.5.4
soundfile                0.13.1
starlette                0.52.1
sympy                    1.13.1
tiktoken                 0.12.0
tokenizers               0.22.2
torch                    2.6.0+cu124
torchaudio               2.6.0+cu124
torchvision              0.21.0+cu124
tqdm                     4.67.3
transformers             5.3.0
triton                   3.2.0
typer                    0.24.1
typing_extensions        4.15.0
typing-inspection        0.4.2
urllib3                  2.6.3
uvicorn                  0.41.0
zipp                     3.23.0
```

### HuggingFace Cache Setup

```bash
# Set HuggingFace cache to larger disk
export HF_HOME=/workspace/.hf_home
export HF_TOKEN=your_huggingface_token_here
```

### Model Download

The HunyuanVideo 1.5 model will be automatically downloaded from HuggingFace on first run:
- Model: `Tencent/HunyuanVideo-1.5`
- Size: ~20-30GB

### Starting the Server

```bash
# Set environment variables
export HF_HOME=/workspace/.hf_home
export HF_TOKEN=your_huggingface_token_here

# Navigate to project directory
cd /workspace/remote_ai_group

# Start the server in background
nohup ./venv/bin/python -u main.py > server_out.log 2>&1 &

# Check health
curl -s http://127.0.0.1:8122/health
```

### API Endpoints

- **Health**: `GET http://142.189.180.40:8122/health`
- **Generate Video**: `POST http://142.189.180.40:8122/generate`

---

## GPU Requirements by Model

### HunyuanVideo 1.5
- **Minimum VRAM**: 24GB (with optimizations)
- **Recommended VRAM**: 40GB+
- **RTX A6000 (48GB)**: ✅ Works with `device_map="balanced"`

### Known Issues & Solutions

1. **device_map="auto" error**: Use `device_map="balanced"` instead
2. **enable_model_cpu_offload() conflict**: Remove when using `device_map="balanced"`
3. **Disk space**: Set `HF_HOME` to a location with >30GB free space

---

## Testing Results

### RTX A6000 (48GB) - HunyuanVideo 1.5
- **Video Generation**: 121 frames, 35 steps
- **Generation Time**: ~21.5 minutes (1293.2s)
- **VRAM Usage**: ~32GB peak
- **Output Size**: ~642KB

---

## File Locations

### Remote Server
- **Project**: `/workspace/remote_ai_group/`
- **Outputs**: `/workspace/remote_ai_group/outputs/`
- **Logs**: `/workspace/remote_ai_group/server_out.log`
- **Models Cache**: `/workspace/.hf_home/`

### Local (Downloaded Videos)
- **Directory**: `/home/psalmprax/ALL_PROJECTS/viral_forge/remote_videos/`

---

## SSH Connection

```bash
ssh -i /home/psalmprax/Music/id_rsa -o StrictHostKeyChecking=no -o PasswordAuthentication=no -p 50512 root@142.189.180.40
```

## SCP File Transfer

```bash
# Download from remote
scp -i /home/psalmprax/Music/id_rsa -o StrictHostKeyChecking=no -P 50512 root@142.189.180.40:/workspace/remote_ai_group/outputs/hun_loc_1773499536.mp4 /local/path/

# Upload to remote
scp -i /home/psalmprax/Music/id_rsa -o StrictHostKeyChecking=no -P 50512 /local/file.mp4 root@142.189.180.40:/workspace/remote_ai_group/
```
