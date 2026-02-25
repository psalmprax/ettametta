# LTX-2 Cloud Deployment Plan (RunPod/Vast.ai)

The Colab standard environment is insufficient for the 28GB LTX-Video model. Transitioning to a dedicated GPU host (RunPod/Vast.ai) ensures stability and higher performance.

## Proposed Strategy

### 1. Hardware Requirement
- **GPU**: NVIDIA RTX 3090, 4090, or A100.
- **Minimum VRAM**: 24GB (to avoid aggressive offloading and speed up rendering).

### 2. Software Stack
- **Base Image**: `runpod/pytorch:2.2.1-py3.10-cuda12.1.1-devel` (or similar stable PyTorch image).
- **Network**: Ngrok for the tunnel, or RunPod's `TCP Port 8000` mapping.

### 3. Implementation Files
- `scripts/cloud_render_node.py`: A hardened version of the synthesis server.
- `scripts/setup_cloud_node.sh`: One-click setup script for the terminal.

## Verification
- Deploy on a RunPod "Pod".
- Test synthesis latency (Expected: < 2 mins for 5s video).
