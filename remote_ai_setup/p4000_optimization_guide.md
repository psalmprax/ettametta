# NVIDIA P4000 8GB Configuration
# Optimized settings for professional workstation GPU

P4000_CONFIG = {
    "gpu_model": "NVIDIA Quadro P4000",
    "vram_gb": 8,
    "architecture": "Pascal",
    "cuda_compute": "6.1",
    "memory_type": "GDDR5",

    # Animation generation settings
    "animation": {
        "max_resolution": "384x384",  # Optimal for 8GB VRAM
        "recommended_resolution": "384x384",
        "max_frames": 12,
        "recommended_frames": 8,
        "inference_steps": 15,  # Reduced for speed
        "guidance_scale": 7.0,
        "fps": 6,  # Lower FPS for smaller files
        "estimated_generation_time": "4-6 minutes",
        "estimated_vram_usage": "6-7GB"
    },

    # Memory management
    "memory_optimizations": {
        "cpu_offloading": True,
        "vae_slicing": True,
        "vae_tiling": True,
        "attention_slicing": True,
        "torch_compile": False,  # Pascal architecture doesn't benefit much
    },

    # Performance expectations
    "performance": {
        "generation_speed": "slow",  # Compared to RTX series
        "stability": "good",  # Professional GPU
        "compatibility": "excellent",  # Mature drivers
        "daily_capacity": "10-15 videos",
    },

    # Recommendations
    "recommendations": [
        "Use 384x384 resolution for best results",
        "Limit animations to 8-12 frames",
        "Close other GPU-intensive applications",
        "Monitor VRAM usage during generation",
        "Restart system if VRAM fragmentation occurs",
        "Consider upgrading to RTX series for better performance"
    ],

    # PyTorch installation
    "pytorch_install": {
        "cuda_version": "11.8",  # P4000 supports up to CUDA 11.8
        "install_command": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118",
        "alternative_cuda": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
    }
}

def get_p4000_optimization_settings() -> dict:
    """Get P4000-specific optimization settings"""
    return P4000_CONFIG

def is_p4000_compatible(resolution: str, frames: int) -> tuple[bool, str]:
    """Check if settings are compatible with P4000"""
    width, height = map(int, resolution.split('x'))

    if width > 384 or height > 384:
        return False, f"Resolution {resolution} too high for P4000 8GB. Use 384x384 max."

    if frames > 12:
        return False, f"{frames} frames too many for P4000. Use 12 max."

    return True, "Settings compatible with P4000"</content>
<parameter name="filePath">remote_ai_setup/p4000_config.py