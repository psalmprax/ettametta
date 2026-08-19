"""
Video Generation Models Package

Local and Remote video generation models for ettametta.
"""
from .cogvideo_inference import generate_cogvideo
from .mochi_inference import generate_mochi
from .wan_inference import generate_wan_t2v, generate_wan_v2v
from .animatediff_inference import generate_animatediff, generate_from_image_animatediff
from .hunyuan_inference import generate_hunyuan
from .ltx_video_inference import generate_ltx

__all__ = [
    "generate_cogvideo",
    "generate_mochi",
    "generate_wan_t2v",
    "generate_wan_v2v",
    "generate_animatediff",
    "generate_from_image_animatediff",
    "generate_hunyuan",
    "generate_ltx"
]
