# Universal Remote AI Server - Installation Guide

This guide provides instructions for deploying the Viral Forge Remote AI engine on any server with a GPU (NVIDIA, AMD, Apple, or Intel) or high-performance CPU.

## Supported Environments
- **OS**: Ubuntu/Debian, RHEL/Fedora/CentOS, macOS
- **Hardware**: 
  - 🟢 **NVIDIA**: CUDA 11.8 - 12.4+
  - 🟠 **AMD**: ROCm 6.0 - 6.2+
  - 🔵 **Apple**: M1/M2/M3/M4 (MPS)
  - ⚪ **Intel**: ARC/Data Center (XPU)
  - 📜 **CPU**: AVX2/AVX512 (Fallback)

---

## 1. Quick Start (Recommended)

The easiest way to install is using the universal installer script which auto-detects your OS and hardware.

```bash
# Clone the setup to your remote server
# (Or SCP the remote_ai_setup folder)

cd remote_ai_setup

# Run the universal installer
chmod +x install.sh
./install.sh
```

---

## 2. Manual Installation Steps

If you prefer to install manually, follow these logical steps:

### Step A: System Dependencies
- **Ubuntu**: `sudo apt install python3-venv ffmpeg libnuma-dev`
- **macOS**: `brew install ffmpeg sox`
- **RHEL**: `sudo dnf install python3 ffmpeg`

### Step B: Hardware-Specific PyTorch
Install the version of PyTorch that matches your GPU:

- **NVIDIA (CUDA 12.4)**:
  `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124`
- **AMD (ROCm 6.2)**:
  `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2`
- **Apple Silicon (MPS)**:
  `pip install torch torchvision torchaudio`
- **Intel (XPU)**:
  `pip install torch torchvision torchaudio intel-extension-for-pytorch==2.5.0`

### Step C: Core Requirements
```bash
pip install -r requirements.txt
```

---

## 3. Configuration & Startup

### Environment Variables
Set your HuggingFace cache to a disk with at least 50GB of free space.

```bash
export HF_HOME=/path/to/large/disk/.hf_home
export HF_TOKEN=your_huggingface_token_here
```

### Starting the Engine
```bash
# Activate environment
source venv/bin/activate

# Start the API server
python3 main.py
```

---

## 4. Hardware Verification

To verify that your GPU is correctly detected, check the `/health` endpoint or run the helper script:

```bash
python3 check_hardware.py
```

**Expected Result (Example for NVIDIA):**
```
NVIDIA Detection: True
AMD/ROCm Detection: False
Recommended: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

---

## 5. Security Note
By default, the server listens on **Port 8000**. Ensure your firewall allows this port or use an SSH tunnel:
`ssh -L 8000:localhost:8000 user@remote-ip`
