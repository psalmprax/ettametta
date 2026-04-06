import time
import threading
import uuid
import base64
import io
import os
import gc
import shutil
import asyncio
import warnings
import torch
import imageio
import numpy as np
import soundfile as sf
import traceback
import subprocess
from fastapi import FastAPI, BackgroundTasks, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from diffusers import (
    DiffusionPipeline,
    LTXPipeline,
    LTXImageToVideoPipeline,
    AutoencoderKLLTXVideo,
    LTXVideoTransformer3DModel,
    LTX2VideoTransformer3DModel,
)
from diffusers.models.transformers.transformer_ltx2 import LTX2VideoTransformer3DModel
from diffusers.pipelines.ltx2.latent_upsampler import LTX2LatentUpsamplerModel
from transformers import (
    T5EncoderModel,
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
    BitsAndBytesConfig,
)
from diffusers.utils import export_to_video
import traceback
from PIL import Image
import cv2
import torch.hub
from hardware_manager import hardware_manager
from video_model_manager import model_manager

# GFPGAN and RealESRGAN - optional for face restoration
try:
    from gfpgan import GFPGANer
except ImportError:
    GFPGANer = None
    print("⚠️ GFPGAN not available")

try:
    from realesrgan import RealESRGANer
except ImportError:
    RealESRGANer = None
    print("⚠️ RealESRGAN not available")

# HunyuanVideo support
try:
    from hunyuan_inference import generate_hunyuan_video, clear_hunyuan_model

    HUNYUAN_AVAILABLE = True
except ImportError:
    HUNYUAN_AVAILABLE = False
    print("⚠️ HunyuanVideo not available, skipping import")

try:
    from basicsr.archs.rrdbnet_arch import RRDBNet
except ImportError:
    RRDBNet = None
    print("⚠️ Basicsr not available")

# Patch to handle rope_interpolation_scale parameter
from diffusers.models.transformers.transformer_ltx2 import LTX2VideoTransformer3DModel
import torch

_original_ltx2_forward = LTX2VideoTransformer3DModel.forward


def _patched_ltx2_forward(self, hidden_states, *args, **kwargs):
    # Retrieve injected states
    audio_hs = getattr(self, "_current_audio_hidden_states", None)
    audio_ehs = getattr(self, "_current_audio_encoder_hidden_states", None)
    num_frames = getattr(self, "_current_num_frames", None)
    height = getattr(self, "_current_height", None)
    width = getattr(self, "_current_width", None)
    fps = getattr(self, "_current_fps", 24.0)

    # Final keyword dict
    final_kwargs = kwargs.copy()
    final_kwargs.pop("rope_interpolation_scale", None)

    # Map positional args from LTX-1 pipeline to LTX-2 19B slots
    arg_names = ["timestep", "encoder_hidden_states", "encoder_attention_mask"]
    for val, name in zip(args, arg_names):
        if name not in final_kwargs:
            final_kwargs[name] = val

    # Inject metadata (CRITICAL for 19B RoPE)
    if final_kwargs.get("num_frames") is None:
        final_kwargs["num_frames"] = num_frames if num_frames is not None else 121
    if final_kwargs.get("audio_num_frames") is None:
        final_kwargs["audio_num_frames"] = final_kwargs["num_frames"]
    if final_kwargs.get("height") is None:
        final_kwargs["height"] = height if height is not None else 720
    if final_kwargs.get("width") is None:
        final_kwargs["width"] = width if width is not None else 1280
    if final_kwargs.get("fps") is None:
        final_kwargs["fps"] = fps

    # Inject Audio Conditioning
    if final_kwargs.get("audio_hidden_states") is None:
        final_kwargs["audio_hidden_states"] = (
            audio_hs
            if audio_hs is not None
            else torch.zeros(
                (1, 1, 512), device=hidden_states.device, dtype=hidden_states.dtype
            )
        )

    if final_kwargs.get("audio_encoder_hidden_states") is None:
        final_kwargs["audio_encoder_hidden_states"] = (
            audio_ehs
            if audio_ehs is not None
            else torch.zeros(
                (1, 1, 768), device=hidden_states.device, dtype=hidden_states.dtype
            )
        )

    # Ensure all injected tensors are on the correct device
    device = hidden_states.device
    dtype = hidden_states.dtype

    for k, v in final_kwargs.items():
        if torch.is_tensor(v):
            final_kwargs[k] = v.to(device=device, dtype=dtype)

    return _original_ltx2_forward(self, hidden_states=hidden_states, **final_kwargs)


LTX2VideoTransformer3DModel.forward = _patched_ltx2_forward
print("✅ LTX2 Consolidated Forward Patch Applied (Audio + Rope fix)")

# Patch LTX Pipelines to accept audio conditioning
from diffusers import LTXPipeline, LTXImageToVideoPipeline


def _patch_pipeline_call(pipeline_class):
    _old_call = pipeline_class.__call__

    def _new_call(self, *args, **kwargs):
        # Extract audio states and metadata if passed to pipeline
        audio_hidden_states = kwargs.pop("audio_hidden_states", None)
        audio_encoder_hidden_states = kwargs.pop("audio_encoder_hidden_states", None)
        num_frames = kwargs.get(
            "num_frames", None
        )  # Keep num_frames in kwargs as pipeline needs it

        # We need to temporarily store these so the patched transformer forward can find them
        if audio_hidden_states is not None:
            self.transformer._current_audio_hidden_states = audio_hidden_states
        if audio_encoder_hidden_states is not None:
            self.transformer._current_audio_encoder_hidden_states = (
                audio_encoder_hidden_states
            )
        if num_frames is not None:
            self.transformer._current_num_frames = num_frames

        # Inject dimensions and FPS
        self.transformer._current_height = kwargs.get("height", 720)
        self.transformer._current_width = kwargs.get("width", 1280)
        self.transformer._current_fps = kwargs.get("fps", 24.0)

        try:
            return _old_call(self, *args, **kwargs)
        finally:
            # Clean up after the entire pipeline call is finished
            for attr in [
                "_current_audio_hidden_states",
                "_current_audio_encoder_hidden_states",
                "_current_num_frames",
                "_current_height",
                "_current_width",
                "_current_fps",
            ]:
                if hasattr(self.transformer, attr):
                    delattr(self.transformer, attr)

    pipeline_class.__call__ = _new_call


# AGGRESSIVE MONKEY PATCHING
import diffusers.models.transformers.transformer_ltx2
from diffusers.models.transformers.transformer_ltx2 import (
    LTX2VideoTransformer3DModel as LTX2Real,
)

# Apply to all known names
for cls in [
    LTX2VideoTransformer3DModel,
    LTX2Real,
    diffusers.models.transformers.transformer_ltx2.LTX2VideoTransformer3DModel,
]:
    cls.forward = _patched_ltx2_forward
    print(
        f"✅ Aggressive Patch applied to {cls.__name__} at {hex(id(cls))}", flush=True
    )

_patch_pipeline_call(LTXPipeline)
_patch_pipeline_call(LTXImageToVideoPipeline)
print(
    "✅ LTX pipelines patched for audio conditioning and metadata pass-through",
    flush=True,
)

# =========================
# ENCODEC AUDIO ENCODER FOR LTX2
# =========================
# We'll generate audio from text using SpeechT5, then encode with EnCodec

encodec_model = None


def load_encodec():
    global encodec_model
    if encodec_model is None:
        print("📥 Loading EnCodec audio encoder...", flush=True)
        from encodec import EncodecModel

        encodec_model = EncodecModel.encodec_model_24khz()
        encodec_model.set_target_bandwidth(6.0)

        device_obj = hardware_manager.get_device_obj()
        if hardware_manager.device != "cpu":
            encodec_model = encodec_model.to(device_obj)
        print(f"✅ EnCodec loaded on {hardware_manager.device}", flush=True)
    return encodec_model


def generate_audio_conditioning(text_prompt, num_frames=121):
    """
    Generate real audio conditioning for LTX-2 19B.
    Returns (audio_hidden_states, audio_encoder_hidden_states)
    """
    print(f"🎵 Generating audio conditioning for: {text_prompt[:50]}...", flush=True)
    tts = load_tts()
    enc = load_encodec()

    with torch.no_grad():
        # 1. TTS Generation
        speech = tts(
            text_prompt, forward_params={"speaker_embeddings": speaker_embedding}
        )
        audio_data = (
            torch.from_numpy(speech["audio"]).float().unsqueeze(0).unsqueeze(0)
        )  # (1, 1, T)
        if model_manager.device != "cpu":
            audio_data = audio_data.to(model_manager.device)

        # 2. EnCodec Latents (audio_hidden_states)
        # EnCodec expects (batch, channels, time)
        encoded_frames = enc.encode(audio_data)
        # audio_codes = encoded_frames[0][0] # (batch, num_codebooks, time)
        # For LTX-2, typically we want the continuous latent representation BEFORE quantization
        # or the projected quantized embed.
        # Here we use a projection of the codes as a baseline.
        audio_emb = encoded_frames[0][0].float()  # (1, K, T)
        audio_emb = audio_emb.permute(0, 2, 1)  # (1, T, K)

        # Project to LTX-2 dimensions (512 and 768)
        # This is a simplified projection; real LTX2 might use specific layers.
        B, T_audio, K = audio_emb.shape
        # Interpolate T_audio to match video frames if needed, or let model handle temporal cross-attn

        # Mocking the dual states with the correct dimensions
        audio_hidden_states = torch.nn.functional.interpolate(
            audio_emb.permute(0, 2, 1), size=(num_frames,), mode="linear"
        ).permute(0, 2, 1)  # (1, num_frames, K)

        if audio_hidden_states.shape[-1] != 512:
            proj = (
                torch.nn.Linear(audio_hidden_states.shape[-1], 512)
                .to(audio_hidden_states.device)
                .to(audio_hidden_states.dtype)
            )
            audio_hidden_states = proj(audio_hidden_states)

        audio_encoder_hidden_states = torch.nn.functional.pad(
            audio_hidden_states, (0, 768 - 512)
        )  # (1, num_frames, 768)

        print(
            f"   ✅ Audio conditioning ready: {audio_hidden_states.shape}, {audio_encoder_hidden_states.shape}",
            flush=True,
        )
        return audio_hidden_states, audio_encoder_hidden_states


# Ensure required directories exist
os.makedirs("/workspace/remote_ai_group/outputs", exist_ok=True)

# =========================
# CONFIGURATION
# =========================
warnings.filterwarnings("ignore")
# nest_asyncio removed for stability

# --- STORAGE ORCHESTRATION ---
DEFAULT_DISK = os.environ.get("AI_CONTENT_DIR", "/workspace")
CONTENT_DIR = os.path.join(DEFAULT_DISK, "ai_content")
os.makedirs(CONTENT_DIR, exist_ok=True)

app = FastAPI(title="ettametta Remote AI Engine (LTX + SpeechT5 + Moondream2)")

# --- CONNECTIVITY STABILIZATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://149.104.110.122.sslip.io:7200",
        "http://149.104.110.122:7200",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVICE = hardware_manager.device
print(f"📡 Using Device: {DEVICE} ({hardware_manager.backend})")

HAS_NVENC = model_manager.encoder == "h264_nvenc"
BEST_ENCODER = model_manager.encoder
print(f"🎞️ Hardware Encoding: {BEST_ENCODER}")

# --- SECURITY MIDDLEWARE ---
from fastapi import Header

WORKER_SECRET = os.environ.get("AI_CLUSTER_SECRET")


async def verify_worker_token(x_worker_token: str = Header(None)):
    if WORKER_SECRET and x_worker_token != WORKER_SECRET:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Unauthorized AI Worker Action")


def hardware_export_to_video(frames, output_path, fps=24):
    """Export frames to video using the best available hardware encoder"""
    print(f"🚀 Exporting via {BEST_ENCODER} to {output_path}...", flush=True)
    try:
        import numpy as np

        first_frame = np.array(frames[0])
        h, w = first_frame.shape[:2]

        # Dynamic Encoder Settings
        codec_args = ["-c:v", BEST_ENCODER]
        if BEST_ENCODER == "h264_nvenc":
            codec_args += ["-preset", "p4", "-tune", "hq", "-b:v", "10M"]
        elif BEST_ENCODER == "libx264":
            codec_args += ["-preset", "superfast", "-crf", "23"]
        else:
            codec_args += ["-b:v", "10M"]

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            f"{w}x{h}",
            "-pix_fmt",
            "rgb24",
            "-r",
            str(fps),
            "-i",
            "-",
            *codec_args,
            "-pix_fmt",
            "yuv420p",
            output_path,
        ]

        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for frame in frames:
            process.stdin.write(np.array(frame).astype("uint8").tobytes())
        process.stdin.close()
        process.wait()
        print(f"✅ {BEST_ENCODER} Export Complete")
    except Exception as e:
        print(f"⚠️ Hardware Export failed: {e}, falling back to slow export")
        from diffusers.utils import export_to_video

        return export_to_video(frames, output_path, fps=fps)


# =========================
# GLOBALS (Lazy Loading)
# =========================
pipe = None
tts_pipeline = None
speaker_embedding = None
vlm_model = None
vlm_tokenizer = None
whisper_model = None
llm_model = None
llm_tokenizer = None
face_enhancer = None
upscaler_model = None


# =========================
# HARDWARE CLEANUP
# =========================
def clear_gpu():
    hardware_manager.clear_cache()


def clear_hunyuan_model():
    """Clear HunyuanVideo model from GPU to free memory"""
    global _hunyuan_pipe
    if _hunyuan_pipe is not None:
        del _hunyuan_pipe
        _hunyuan_pipe = None
    clear_gpu()
    print("🗑️ Cleared HunyuanVideo model from GPU", flush=True)


# =========================
# LOADERS
# =========================
# Legacy LTX-1 removed for LTX-2 19B migration

# --- Utility Loaders (Legacy) ---
# Moved to centralized VideoModelManager for Smart VRAM protection

# =========================
# LOADERS
# =========================
# Global Model Cache
GLOBAL_MODELS = {"t2v": None, "i2v": None, "upscale": None}


def load_ltx_base_components():
    """Phase 0: Shared components (VAE, Tokenizer, Scheduler)"""
    if "base" in GLOBAL_MODELS and GLOBAL_MODELS["base"] is not None:
        return GLOBAL_MODELS["base"]

    print("📥 Loading LTX-2 base components (VAE, Tokenizer)...", flush=True)
    from transformers import T5Tokenizer

    tokenizer = T5Tokenizer.from_pretrained(
        "Lightricks/LTX-Video", subfolder="tokenizer"
    )
    vae = AutoencoderKLLTXVideo.from_pretrained(
        "Lightricks/LTX-Video",
        subfolder="vae",
        torch_dtype=hardware_manager.dtype,
        local_files_only=False,
    ).to(hardware_manager.get_device_obj())
    vae.enable_tiling()
    vae.enable_slicing()
    from diffusers import FlowMatchEulerDiscreteScheduler

    scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained(
        "Lightricks/LTX-Video", subfolder="scheduler"
    )

    res = (tokenizer, vae, scheduler)
    GLOBAL_MODELS["base"] = res
    return res


def encode_prompt_ltx2(prompt, negative_prompt, tokenizer):
    """Phase 1: Encode with T5 then EVICT from VRAM"""
    print(f"📥 Phase 1: Encoding with T5 ('{prompt[:40]}')...", flush=True)
    from transformers import T5EncoderModel

    t5 = T5EncoderModel.from_pretrained(
        "Lightricks/LTX-Video",
        subfolder="text_encoder",
        torch_dtype=hardware_manager.dtype,
    ).to(hardware_manager.get_device_obj())

    # Also need the projection layer: 4096 -> 3840 for LTX-2
    text_projection = (
        torch.nn.Linear(4096, 3840, bias=False)
        .to(hardware_manager.dtype)
        .to(hardware_manager.get_device_obj())
    )

    def get_embeds(p):
        inputs = tokenizer(
            p,
            return_tensors="pt",
            padding="max_length",
            max_length=128,
            truncation=True,
        ).to(DEVICE)
        with torch.no_grad():
            output = t5(inputs.input_ids, attention_mask=inputs.attention_mask)
            hidden = output.last_hidden_state
            projected = text_projection(hidden)
        return projected, inputs.attention_mask

    p_embeds, p_mask = get_embeds(prompt)
    n_embeds, n_mask = get_embeds(negative_prompt)

    print("🧹 Phase 1 Complete. Evicting T5 & Projection Layer...", flush=True)
    del t5, text_projection
    clear_gpu()
    import gc

    gc.collect()
    return p_embeds, p_mask, n_embeds, n_mask


def load_ltx_19b_transformer():
    """Phase 2: Stream 19B Transformer (38GB BF16)"""
    if "transformer" in GLOBAL_MODELS and GLOBAL_MODELS["transformer"] is not None:
        print("✅ Utilizing cached 19B Transformer.", flush=True)
        return GLOBAL_MODELS["transformer"]

    print("📥 Phase 2: Streaming 19B Transformer (Meta-to-GPU)...", flush=True)
    # Use HF_HOME environment variable for model cache location
    import os

    # Priority: Env Var > Best Disk Fallback > Static Default
    hf_home = os.environ.get(
        "HF_HOME",
        os.path.join(
            os.environ.get("AI_CONTENT_DIR", "/workspace"), ".cache/huggingface/hub"
        ),
    )
    model_uri = f"{hf_home}/models--Lightricks--LTX-2/snapshots/47da56e2ad66ce4125a9922b4a8826bf407f9d0a/ltx-2-19b-dev-fp4.safetensors"
    transformer_config = LTX2VideoTransformer3DModel.load_config(
        "Lightricks/LTX-2", subfolder="transformer"
    )

    from accelerate import init_empty_weights

    with init_empty_weights():
        transformer = LTX2VideoTransformer3DModel(**transformer_config).to(
            hardware_manager.dtype
        )

    from safetensors import safe_open

    model_keys = list(transformer.state_dict().keys())

    with safe_open(model_uri, framework="pt", device="cpu") as f:
        sd_keys = f.keys()
        has_prefix = any(k.startswith("model.diffusion_model.") for k in sd_keys)
        count = 0
        for k in model_keys:
            sd_key = f"model.diffusion_model.{k}" if has_prefix else k
            if sd_key in sd_keys:
                tensor = (
                    f.get_tensor(sd_key)
                    .to(hardware_manager.dtype)
                    .to(hardware_manager.get_device_obj())
                )
                module_path = k.split(".")
                parent = transformer
                for attr in module_path[:-1]:
                    parent = getattr(parent, attr)
                setattr(
                    parent,
                    module_path[-1],
                    torch.nn.Parameter(tensor, requires_grad=False),
                )
                del tensor
                count += 1
                if count % 200 == 0:
                    print(
                        f"✅ Streamed {count}/{len(model_keys)} parameters...",
                        flush=True,
                    )

    # Defensive: Move any remaining meta tensors to DEVICE
    for name, p in transformer.named_parameters():
        if p.device.type == "meta":
            module_path = name.split(".")
            parent = transformer
            for attr in module_path[:-1]:
                parent = getattr(parent, attr)
            setattr(
                parent,
                module_path[-1],
                torch.nn.Parameter(
                    torch.empty(p.shape, dtype=hardware_manager.dtype).to(
                        hardware_manager.get_device_obj()
                    ),
                    requires_grad=False,
                ),
            )
    for name, b in transformer.named_buffers():
        if b.device.type == "meta":
            module_path = name.split(".")
            parent = transformer
            for attr in module_path[:-1]:
                parent = getattr(parent, attr)
            setattr(
                parent,
                module_path[-1],
                torch.empty(b.shape, dtype=hardware_manager.dtype).to(
                    hardware_manager.get_device_obj()
                ),
            )

    print("🚀 19B Transformer live.", flush=True)

    # ⚡ JIT Compilation for 19B Transformer
    try:
        print("🔥 Optimization: Compiling 19B Transformer (Phase 2)...", flush=True)
        transformer = torch.compile(
            transformer, mode="reduce-overhead", fullgraph=False
        )
        print("✅ Compilation Triggered.")
    except Exception as e:
        print(f"⚠️ Compilation failed: {e}")

    GLOBAL_MODELS["transformer"] = transformer
    return transformer


def load_enhancers(upscale_factor=2):
    global face_enhancer, upscaler_model
    if face_enhancer is None:
        print("📥 Loading GFPGAN (Face Restoration)...")
        face_enhancer = GFPGANer(
            model_path="https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth",
            upscale=1,
            arch="clean",
            channel_multiplier=2,
            bg_upsampler=None,
        )
    if upscaler_model is None:
        print(f"📥 Loading Real-ESRGAN (Multi-Pass for x{upscale_factor})...")
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4,
        )
        upscaler_model = RealESRGANer(
            scale=4,  # Still use x4 model but we will multi-pass if needed
            model_path="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
            model=model,
            tile=400,
            tile_pad=10,
            pre_pad=0,
            half=True if hardware_manager.device in ["cuda", "xpu"] else False,
        )
    return face_enhancer, upscaler_model


def load_tts():
    global tts_pipeline, speaker_embedding
    if tts_pipeline is None:
        print("📥 Loading Microsoft SpeechT5 TTS...")
        tts_pipeline = pipeline(
            "text-to-speech",
            model="microsoft/speecht5_tts",
            device=0 if model_manager.device == "cuda" else -1,
        )
        torch.manual_seed(42)
        speaker_embedding = torch.randn(1, 512).to(DEVICE)
    return tts_pipeline


def load_vlm():
    global vlm_model, vlm_tokenizer
    if vlm_model is None:
        print("📥 Loading Moondream2...")
        clear_gpu()
        model_id = "vikhyatk/moondream2"
        vlm_model = AutoModelForCausalLM.from_pretrained(
            model_id, trust_remote_code=True, revision="2024-05-20"
        ).to(DEVICE)
        vlm_tokenizer = AutoTokenizer.from_pretrained(model_id, revision="2024-05-20")
    return vlm_model, vlm_tokenizer


def load_whisper():
    global whisper_model
    if whisper_model is None:
        from faster_whisper import WhisperModel

        print("📥 Loading Faster-Whisper (Large-v3)...")
        whisper_model = WhisperModel("large-v3", device=DEVICE, compute_type="float16")
    return whisper_model


def load_llm():
    global llm_model, llm_tokenizer
    if llm_model is None:
        print("📥 Loading Llama-3.1-8B-Instruct (4-bit)...")
        model_id = "unsloth/Meta-Llama-3.1-8B-Instruct"
        llm_tokenizer = AutoTokenizer.from_pretrained(model_id)
        if hardware_manager.device == "cuda":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            llm_model = AutoModelForCausalLM.from_pretrained(
                model_id, quantization_config=bnb_config, device_map="auto"
            )
        else:
            # Non-NVIDIA fallback: Load in high precision or use HAL-optimal dtype
            llm_model = AutoModelForCausalLM.from_pretrained(
                model_id, torch_dtype=hardware_manager.dtype, device_map="auto"
            )
    return llm_model, llm_tokenizer


# =========================
# REQUEST MODELS
# =========================
class VideoRequest(BaseModel):
    prompt: str
    image_base64: str = None
    frames: int = 121
    steps: int = 35
    upscale_factor: int = 4  # 2 or 4 for Real-ESRGAN
    enhance_face: bool = True  # Enable GFPGAN
    likeness_strength: float = 1.0  # Conditioning scale for I2V
    face_enhance_weight: float = 0.5  # 0.0 to 1.0 for GFPGAN intensity
    quantize: bool = True  # Enable 8-bit quantization for HunyuanVideo
    force_reload: bool = False  # Clear GPU memory before loading model


class VoiceRequest(BaseModel):
    text: str


class VLMRequest(BaseModel):
    image_base64: str
    prompt: str = "Describe this image."


class LLMRequest(BaseModel):
    prompt: str
    system_prompt: str = "You are a specialized AI assistant for ettametta."
    max_tokens: int = 512


# =========================
# ENDPOINTS
# =========================
@app.on_event("startup")
async def startup_event():
    """Skip eager loading to avoid OOM - model loads lazily on first request."""
    print("🚀 AI Engine ready (Lazy Loading Mode)...")
    print("💡 Model will load on first video request.")

    # Start Push Heartbeat back to Gateway
    threading.Thread(target=push_heartbeat_loop, daemon=True).start()


def push_heartbeat_loop():
    """Persistent Push Heartbeat to circumvent Firewalls on Vast.ai / RunPod"""
    gateway_url = os.environ.get("AI_GATEWAY_URL")
    if not gateway_url:
        print("⚠️ No AI_GATEWAY_URL configured, skipping Push Heartbeat", flush=True)
        return

    cluster_secret = os.environ.get("AI_CLUSTER_SECRET")
    # Identify our own public IP/Port if possible, or use one explicitly passed
    my_public_url = os.environ.get("AI_NODE_PUBLIC_URL")

    if not my_public_url:
        # Fallback to local reachability if no public URL provided
        import socket

        try:
            hostname = socket.gethostname()
            ip_addr = socket.gethostbyname(hostname)
            my_public_url = f"http://{ip_addr}:19675"
        except:
            my_public_url = "http://175.155.64.174:19675"

    print(
        f"💓 Heartbeat loop started for: {my_public_url} -> {gateway_url}", flush=True
    )

    import httpx

    while True:
        try:
            hardware = hardware_manager.get_telemetry()
            payload = {
                "url": my_public_url,
                "busy": model_manager.is_busy,
                "current_model": model_manager.current_model_key
                or (
                    list(model_manager.utils.keys())[0] if model_manager.utils else None
                ),
                "hardware": hardware,
                "status": "ready",
            }
            headers = {"X-Worker-Token": cluster_secret} if cluster_secret else {}

            with httpx.Client(timeout=10.0) as client:
                full_url = f"{gateway_url}/pulse"
                resp = client.post(full_url, json=payload, headers=headers)
                print(
                    f"💓 [Heartbeat] Sent to {full_url}, Status: {resp.status_code}",
                    flush=True,
                )
                if resp.status_code == 200:
                    pass  # Success
                else:
                    print(
                        f"⚠️ Heartbeat rejected ({resp.status_code}): {resp.text}",
                        flush=True,
                    )
        except Exception as e:
            print(f"⚠️ Heartbeat critical failure: {e}", flush=True)
            import traceback

            traceback.print_exc()

        time.sleep(10)  # 10 second pulse


@app.get("/health")
async def health_check():
    """Basic health check with model status"""
    busy = False
    current_model = None

    # Check if any models are currently loaded
    try:
        # This is a lightweight check - don't load models just for health
        current_model = getattr(model_manager, "current_model", None) or "none"
        busy = getattr(orchestrator, "busy", False)
    except:
        current_model = "initializing"
        busy = False

    return {
        "status": "healthy" if not busy else "busy",
        "busy": busy,
        "current_model": current_model,
        "hardware": hardware_manager.get_hardware_info(),
    }


render_lock = threading.Lock()

from job_orchestrator import orchestrator


@app.post("/generate")
async def generate_video(request: VideoRequest, x_worker_token: str = Header(None)):
    await verify_worker_token(x_worker_token)
    job_id = orchestrator.add_job("video", "ltx_2_19b", request)
    return {"job_id": job_id, "status": "queued", "model": "ltx_2_19b"}


@app.post("/generate_hunyuan")
async def hunyuan_endpoint(request: VideoRequest, x_worker_token: str = Header(None)):
    await verify_worker_token(x_worker_token)
    job_id = orchestrator.add_job("video", "hunyuan_480p", request)
    return {"job_id": job_id, "status": "queued", "model": "hunyuan_480p"}


@app.post("/voice")
async def generate_voice_endpoint(
    req: VoiceRequest, x_worker_token: str = Header(None)
):
    await verify_worker_token(x_worker_token)
    job_id = orchestrator.add_job("voice", "tts", req)
    return {"job_id": job_id, "status": "queued"}


@app.post("/vlm")
async def analyze_vlm_endpoint(req: VLMRequest, x_worker_token: str = Header(None)):
    await verify_worker_token(x_worker_token)
    job_id = orchestrator.add_job("vlm", "vlm", req)
    return {"job_id": job_id, "status": "queued"}


@app.post("/transcribe")
async def transcribe_endpoint(
    file_path: str = None, x_worker_token: str = Header(None)
):
    await verify_worker_token(x_worker_token)
    if not file_path:
        return {"error": "No file path"}
    job_id = orchestrator.add_job("transcribe", "whisper", {"file_path": file_path})
    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
async def get_job_status(job_id: str, x_worker_token: str = Header(None)):
    await verify_worker_token(x_worker_token)
    return orchestrator.get_job_status(job_id)


# --- Legacy Endpoints (Moved to ai_actions.py) ---


def delete_file(path: str):
    """Background task to delete a file after download."""
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"🗑️ Deleted downloaded file: {path}")
        except Exception as e:
            print(f"⚠️ Failed to delete {path}: {e}")


def cleanup_old_files(max_age_hours=24):
    """Periodic cleanup of old files in CONTENT_DIR."""
    while True:
        try:
            print(f"🧹 Running TTL Cleanup (Age > {max_age_hours}h)...")
            now = time.time()
            for f in os.listdir(CONTENT_DIR):
                path = os.path.join(CONTENT_DIR, f)
                if os.path.isfile(path):
                    if now - os.path.getmtime(path) > (max_age_hours * 3600):
                        os.remove(path)
                        print(f"🧹 Purged stale file: {f}")
        except Exception as e:
            print(f"⚠️ Cleanup Error: {e}")
        time.sleep(3600)  # Run every hour


@app.get("/download/{job_id}")
async def download(
    job_id: str, bg: BackgroundTasks, x_worker_token: str = Header(None)
):
    await verify_worker_token(x_worker_token)
    print(f"📥 Download requested: {job_id}")
    for ext in ["mp4", "wav"]:
        path = os.path.join(CONTENT_DIR, f"{job_id}.{ext}")
        if os.path.exists(path):
            file_size = os.path.getsize(path) / (1024 * 1024)
            print(f"✅ Serving file: {path} ({file_size:.2f} MB)")
            # bg.add_task(delete_file, path) # DISABLED: Causes issues with large file downloads
            return FileResponse(
                path, media_type=f"video/{ext}", filename=f"{job_id}.{ext}"
            )

    # Log what files ARE available for debugging
    available = os.listdir(CONTENT_DIR)
    print(f"⚠️ File not found: {job_id}. Available: {available[:10]}...")
    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail="File not found")


# =====================================================
# VIDEO MODEL MANAGER ENDPOINTS
# =====================================================

from video_model_manager import model_manager, VIDEO_MODELS


@app.get("/models")
async def list_models(x_worker_token: str = Header(None)):
    """List all available video models"""
    await verify_worker_token(x_worker_token)
    return {
        "models": VIDEO_MODELS,
        "disk_usage": model_manager.get_disk_usage(),
    }


@app.get("/models/{model_key}")
async def get_model_info(model_key: str):
    """Get info about a specific model"""
    from video_model_manager import get_model_info

    info = get_model_info(model_key)
    if not info:
        return {"error": "Model not found"}
    return {
        "info": info,
        "downloaded": model_manager.is_model_downloaded(model_key),
    }


@app.post("/models/{model_key}/download")
async def download_model(model_key: str):
    """Download a model to local storage"""
    result = model_manager.download_model(model_key)
    return result


@app.post("/models/{model_key}/delete")
async def delete_model(model_key: str):
    """Delete a model from local storage"""
    result = model_manager.delete_model(model_key)
    return result


@app.post("/models/{model_key}/load")
async def load_model(model_key: str):
    """Load a model into VRAM"""
    result = model_manager.load_model(model_key)
    return result


@app.post("/models/unload")
async def unload_model():
    """Unload current model from VRAM"""
    model_manager.unload_current_model()
    return {"status": "unloaded"}


@app.post("/models/{model_key}/generate")
async def generate_with_model(
    model_key: str,
    prompt: str,
    negative_prompt: str = "low quality, blurry, distorted",
    num_inference_steps: int = 25,
    num_frames: int = 49,
    height: int = 480,
    width: int = 832,
    guidance_scale: float = 7.5,
):
    """Generate a video with the loaded model"""
    result = model_manager.generate_video(
        model_key=model_key,
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=num_inference_steps,
        num_frames=num_frames,
        height=height,
        width=width,
        guidance_scale=guidance_scale,
    )
    return result


@app.post("/generate_animatediff")
async def generate_animatediff(
    prompt: str,
    negative_prompt: str = "low quality, blurry, distorted",
    num_inference_steps: int = 25,
    num_frames: int = 16,  # AnimateDiff defaults to shorter clips
    height: int = 512,
    width: int = 512,
    guidance_scale: float = 7.5,
):
    """Specific entry for AnimateDiff animation workflows"""
    return model_manager.generate_video(
        model_key="animatediff_v15",
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=num_inference_steps,
        num_frames=num_frames,
        height=height,
        width=width,
        guidance_scale=guidance_scale,
    )


# =========================
# STARTUP
# =========================
if __name__ == "__main__":
    import sys

    print("🚀 ettametta Remote AI Engine starting...")

    # Ngrok disabled for infra-grind
    # try:
    #     ...
    # except Exception as e:
    #     ...

    # Start TTL Cleanup Thread
    threading.Thread(target=cleanup_old_files, daemon=True).start()

    import uvicorn
    import time

    port = int(os.environ.get("PORT", 8122))
    time.sleep(2)
    print(f"🚀 AI Engine binding to Port {port}...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port)

# =====================================================
# END
# =====================================================

# =====================================================
# END
# =====================================================
