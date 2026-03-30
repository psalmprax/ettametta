# Video Models Testing Results (RTX A6000 - 48GB VRAM)

## Summary
Tested multiple video generation models on the remote server with RTX A6000 (48GB VRAM).

## Test Results

### ✅ WORKING MODELS (Fit in 48GB VRAM)

| Model | VRAM Used | Status | Notes |
|-------|-----------|--------|-------|
| **AnimateDiff** | 2.58 GB | ✅ Works | Lightest model! |
| **CogVideoX-2b** | 14.61 GB | ✅ Works | Lightweight, fast |
| **Wan 2.1 T2V 1.3B** | 15.35 GB | ✅ Works | Good quality |
| **Mochi** | 30.29 GB | ✅ Works | High quality |
| **HunyuanVideo 480p** | ~20 GB | ✅ Works | Best quality/size ratio |

### ❌ FAILED MODELS

| Model | Reason | VRAM Needed |
|-------|--------|-------------|
| **HunyuanVideo 720p** | OOM Error | >48GB |
| **LTX-Video/LTX-2** | Disk space (204GB model) | N/A |
| **Wan 2.2 I2V 14B** | OOM Error | >48GB |

## Server Details
- **GPU**: NVIDIA RTX A6000 (48GB VRAM)
- **Disk**: 204GB free (after LTX-2 deletion)
- **Location**: 142.189.180.40:50512
- **Port**: 8122 (API server)

## Recommended Models (Sorted by VRAM Usage)

1. **AnimateDiff** (2.58GB) - Lightest, fastest
2. **CogVideoX-2b** (14.61GB) - Lightweight
3. **Wan 2.1 T2V 1.3B** (15.35GB) - Good balance
4. **Mochi** (30.29GB) - High quality
5. **HunyuanVideo 480p** (~20GB) - Best quality

## Usage Examples

### AnimateDiff
```python
from diffusers import DiffusionPipeline, MotionAdapter
adapter = MotionAdapter.from_pretrained('guoyww/animatediff-motion-adapter-v1-5-2', torch_dtype=torch.float16)
pipe = DiffusionPipeline.from_pretrained('runwayml/stable-diffusion-v1-5', motion_adapter=adapter, torch_dtype=torch.float16).to('cuda')
```

### CogVideoX-2b
```python
from diffusers import CogVideoXPipeline
pipe = CogVideoXPipeline.from_pretrained('zai-org/CogVideoX-2b', torch_dtype=torch.float16).to('cuda')
```

### Wan 2.1 T2V 1.3B
```python
from diffusers import WanPipeline
pipe = WanPipeline.from_pretrained('Wan-AI/Wan2.1-T2V-1.3B-Diffusers', torch_dtype=torch.float16).to('cuda')
```

### Mochi
```python
from diffusers import MochiPipeline
pipe = MochiPipeline.from_pretrained('genmo/mochi-1-preview', torch_dtype=torch.float16).to('cuda')
```

### HunyuanVideo
```python
from diffusers import HunyuanVideoPipeline
pipe = HunyuanVideoPipeline.from_pretrained('hunyuanvideo-community/HunyuanVideo', torch_dtype=torch.float16).to('cuda')
```
