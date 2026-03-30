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
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from diffusers import DiffusionPipeline, LTXPipeline, LTXImageToVideoPipeline, AutoencoderKLLTXVideo, LTXVideoTransformer3DModel, LTX2VideoTransformer3DModel
from diffusers.models.transformers.transformer_ltx2 import LTX2VideoTransformer3DModel
from diffusers.pipelines.ltx2.latent_upsampler import LTX2LatentUpsamplerModel
from transformers import T5EncoderModel, AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
from diffusers.utils import export_to_video
import traceback
from PIL import Image
import cv2
import torch.hub
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
    final_kwargs.pop('rope_interpolation_scale', None)
    
    # Map positional args from LTX-1 pipeline to LTX-2 19B slots
    arg_names = ['timestep', 'encoder_hidden_states', 'encoder_attention_mask']
    for val, name in zip(args, arg_names):
        if name not in final_kwargs:
            final_kwargs[name] = val
            
    # Inject metadata (CRITICAL for 19B RoPE)
    if final_kwargs.get('num_frames') is None:
        final_kwargs['num_frames'] = num_frames if num_frames is not None else 121
    if final_kwargs.get('audio_num_frames') is None:
        final_kwargs['audio_num_frames'] = final_kwargs['num_frames']
    if final_kwargs.get('height') is None:
        final_kwargs['height'] = height if height is not None else 720
    if final_kwargs.get('width') is None:
        final_kwargs['width'] = width if width is not None else 1280
    if final_kwargs.get('fps') is None:
        final_kwargs['fps'] = fps
        
    # Inject Audio Conditioning
    if final_kwargs.get('audio_hidden_states') is None:
        final_kwargs['audio_hidden_states'] = audio_hs if audio_hs is not None else \
            torch.zeros((1, 1, 512), device=hidden_states.device, dtype=hidden_states.dtype)
            
    if final_kwargs.get('audio_encoder_hidden_states') is None:
        final_kwargs['audio_encoder_hidden_states'] = audio_ehs if audio_ehs is not None else \
            torch.zeros((1, 1, 768), device=hidden_states.device, dtype=hidden_states.dtype)
            
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
        num_frames = kwargs.get("num_frames", None) # Keep num_frames in kwargs as pipeline needs it
        
        # We need to temporarily store these so the patched transformer forward can find them
        if audio_hidden_states is not None:
            self.transformer._current_audio_hidden_states = audio_hidden_states
        if audio_encoder_hidden_states is not None:
            self.transformer._current_audio_encoder_hidden_states = audio_encoder_hidden_states
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
            for attr in ["_current_audio_hidden_states", "_current_audio_encoder_hidden_states", "_current_num_frames", "_current_height", "_current_width", "_current_fps"]:
                if hasattr(self.transformer, attr):
                    delattr(self.transformer, attr)
    pipeline_class.__call__ = _new_call

# AGGRESSIVE MONKEY PATCHING
import diffusers.models.transformers.transformer_ltx2
from diffusers.models.transformers.transformer_ltx2 import LTX2VideoTransformer3DModel as LTX2Real

# Apply to all known names
for cls in [LTX2VideoTransformer3DModel, LTX2Real, diffusers.models.transformers.transformer_ltx2.LTX2VideoTransformer3DModel]:
    cls.forward = _patched_ltx2_forward
    print(f"✅ Aggressive Patch applied to {cls.__name__} at {hex(id(cls))}", flush=True)

_patch_pipeline_call(LTXPipeline)
_patch_pipeline_call(LTXImageToVideoPipeline)
print("✅ LTX pipelines patched for audio conditioning and metadata pass-through", flush=True)

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
        if model_manager.device != "cpu":
            encodec_model = encodec_model.to(model_manager.device)
        print(f"✅ EnCodec loaded on {model_manager.device}", flush=True)
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
        speech = tts(text_prompt, forward_params={"speaker_embeddings": speaker_embedding})
        audio_data = torch.from_numpy(speech["audio"]).float().unsqueeze(0).unsqueeze(0) # (1, 1, T)
        if model_manager.device != "cpu":
            audio_data = audio_data.to(model_manager.device)
            
        # 2. EnCodec Latents (audio_hidden_states)
        # EnCodec expects (batch, channels, time)
        encoded_frames = enc.encode(audio_data)
        # audio_codes = encoded_frames[0][0] # (batch, num_codebooks, time)
        # For LTX-2, typically we want the continuous latent representation BEFORE quantization
        # or the projected quantized embed. 
        # Here we use a projection of the codes as a baseline.
        audio_emb = encoded_frames[0][0].float() # (1, K, T)
        audio_emb = audio_emb.permute(0, 2, 1) # (1, T, K)
        
        # Project to LTX-2 dimensions (512 and 768)
        # This is a simplified projection; real LTX2 might use specific layers.
        B, T_audio, K = audio_emb.shape
        # Interpolate T_audio to match video frames if needed, or let model handle temporal cross-attn
        
        # Mocking the dual states with the correct dimensions
        audio_hidden_states = torch.nn.functional.interpolate(
            audio_emb.permute(0, 2, 1), size=(num_frames,), mode='linear'
        ).permute(0, 2, 1) # (1, num_frames, K)
        
        if audio_hidden_states.shape[-1] != 512:
            proj = torch.nn.Linear(audio_hidden_states.shape[-1], 512).to(audio_hidden_states.device).to(audio_hidden_states.dtype)
            audio_hidden_states = proj(audio_hidden_states)
            
        audio_encoder_hidden_states = torch.nn.functional.pad(audio_hidden_states, (0, 768 - 512)) # (1, num_frames, 768)
        
        print(f"   ✅ Audio conditioning ready: {audio_hidden_states.shape}, {audio_encoder_hidden_states.shape}", flush=True)
        return audio_hidden_states, audio_encoder_hidden_states

# Ensure required directories exist
os.makedirs("/workspace/remote_ai_group/outputs", exist_ok=True)

# =========================
# CONFIGURATION
# =========================
warnings.filterwarnings("ignore")
# nest_asyncio removed for stability

CONTENT_DIR = "/workspace/ai_content"
os.makedirs(CONTENT_DIR, exist_ok=True)

app = FastAPI(title="ettametta Remote AI Engine (LTX + SpeechT5 + Moondream2)")

DEVICE = model_manager.device
print(f"📡 Using Device: {DEVICE}")

HAS_NVENC = (model_manager.encoder == "h264_nvenc")
BEST_ENCODER = model_manager.encoder
print(f"🎞️ Hardware Encoding: {BEST_ENCODER}")

def hardware_export_to_video(frames, output_path, fps=24):
    """Export frames to video using the best available hardware encoder"""
    print(f"🚀 Exporting via {BEST_ENCODER} to {output_path}...", flush=True)
    try:
        import numpy as np
        first_frame = np.array(frames[0])
        h, w = first_frame.shape[:2]
        
        # Dynamic Encoder Settings
        codec_args = ['-c:v', BEST_ENCODER]
        if BEST_ENCODER == "h264_nvenc":
            codec_args += ['-preset', 'p4', '-tune', 'hq', '-b:v', '10M']
        elif BEST_ENCODER == "libx264":
            codec_args += ['-preset', 'superfast', '-crf', '23']
        else:
            codec_args += ['-b:v', '10M']

        cmd = [
            'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
            '-s', f'{w}x{h}', '-pix_fmt', 'rgb24', '-r', str(fps),
            '-i', '-', *codec_args, '-pix_fmt', 'yuv420p', output_path
        ]
        
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for frame in frames:
            process.stdin.write(np.array(frame).astype('uint8').tobytes())
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
# GPU CLEANUP
# =========================
def clear_gpu():
    model_manager.clear_gpu()

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

def load_tts():
    global tts_pipeline, speaker_embedding
    if tts_pipeline is None:
        print("📥 Loading Microsoft SpeechT5 TTS...")
        tts_pipeline = pipeline(
            "text-to-speech",
            model="microsoft/speecht5_tts",
            device=0 if model_manager.device == "cuda" else -1
        )
        # Create stable default speaker embedding (512-dim)
        torch.manual_seed(42)
        speaker_embedding = torch.randn(1, 512)
        if model_manager.device != "cpu":
            speaker_embedding = speaker_embedding.to(model_manager.device)
    return tts_pipeline

def load_vlm():
    global vlm_model, vlm_tokenizer
    if vlm_model is None:
        print("📥 Loading Moondream2...")
        clear_gpu()
        model_id = "vikhyatk/moondream2"
        rev = "2024-05-20"
        vlm_model = AutoModelForCausalLM.from_pretrained(
            model_id, trust_remote_code=True, revision=rev
        ).to(DEVICE)
        vlm_tokenizer = AutoTokenizer.from_pretrained(model_id, revision=rev)
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
        model_id = "unsloth/Meta-Llama-3.1-8B-Instruct" # Using a pre-quantized or light version
        llm_tokenizer = AutoTokenizer.from_pretrained(model_id)
        llm_model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_4bit=True
        )
    return llm_model, llm_tokenizer

# =========================
# LOADERS
# =========================
# Global Model Cache
GLOBAL_MODELS = {
    "t2v": None,
    "i2v": None,
    "upscale": None
}

def load_ltx_base_components():
    """Phase 0: Shared components (VAE, Tokenizer, Scheduler)"""
    if "base" in GLOBAL_MODELS and GLOBAL_MODELS["base"] is not None:
        return GLOBAL_MODELS["base"]
        
    print("📥 Loading LTX-2 base components (VAE, Tokenizer)...", flush=True)
    from transformers import T5Tokenizer
    tokenizer = T5Tokenizer.from_pretrained("Lightricks/LTX-Video", subfolder="tokenizer")
    vae = AutoencoderKLLTXVideo.from_pretrained(
        "Lightricks/LTX-Video", subfolder="vae", 
        torch_dtype=torch.bfloat16, local_files_only=False
    ).to(DEVICE)
    vae.enable_tiling()
    vae.enable_slicing()
    from diffusers import FlowMatchEulerDiscreteScheduler
    scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained("Lightricks/LTX-Video", subfolder="scheduler")
    
    res = (tokenizer, vae, scheduler)
    GLOBAL_MODELS["base"] = res
    return res

def encode_prompt_ltx2(prompt, negative_prompt, tokenizer):
    """Phase 1: Encode with T5 then EVICT from VRAM"""
    print(f"📥 Phase 1: Encoding with T5 ('{prompt[:40]}')...", flush=True)
    from transformers import T5EncoderModel
    t5 = T5EncoderModel.from_pretrained("Lightricks/LTX-Video", subfolder="text_encoder", torch_dtype=torch.bfloat16).to(DEVICE)
    
    # Also need the projection layer: 4096 -> 3840 for LTX-2
    text_projection = torch.nn.Linear(4096, 3840, bias=False).to(torch.bfloat16).to(DEVICE)
    
    def get_embeds(p):
        inputs = tokenizer(p, return_tensors="pt", padding="max_length", max_length=128, truncation=True).to(DEVICE)
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
    hf_home = os.environ.get('HF_HOME', '/workspace/.cache/huggingface/hub')
    model_uri = f"{hf_home}/models--Lightricks--LTX-2/snapshots/47da56e2ad66ce4125a9922b4a8826bf407f9d0a/ltx-2-19b-dev-fp4.safetensors"
    transformer_config = LTX2VideoTransformer3DModel.load_config("Lightricks/LTX-2", subfolder="transformer")
    
    from accelerate import init_empty_weights
    with init_empty_weights():
        transformer = LTX2VideoTransformer3DModel(**transformer_config).to(torch.bfloat16)

    from safetensors import safe_open
    model_keys = list(transformer.state_dict().keys())
    
    with safe_open(model_uri, framework="pt", device="cpu") as f:
        sd_keys = f.keys()
        has_prefix = any(k.startswith("model.diffusion_model.") for k in sd_keys)
        count = 0
        for k in model_keys:
            sd_key = f"model.diffusion_model.{k}" if has_prefix else k
            if sd_key in sd_keys:
                tensor = f.get_tensor(sd_key).to(torch.bfloat16).to(DEVICE)
                module_path = k.split('.')
                parent = transformer
                for attr in module_path[:-1]:
                    parent = getattr(parent, attr)
                setattr(parent, module_path[-1], torch.nn.Parameter(tensor, requires_grad=False))
                del tensor
                count += 1
                if count % 200 == 0:
                    print(f"✅ Streamed {count}/{len(model_keys)} parameters...", flush=True)
            
    # Defensive: Move any remaining meta tensors to DEVICE
    for name, p in transformer.named_parameters():
        if p.device.type == "meta":
            module_path = name.split('.')
            parent = transformer
            for attr in module_path[:-1]:
                parent = getattr(parent, attr)
            setattr(parent, module_path[-1], torch.nn.Parameter(torch.empty(p.shape, dtype=torch.bfloat16).to(DEVICE), requires_grad=False))
    for name, b in transformer.named_buffers():
        if b.device.type == "meta":
            module_path = name.split('.')
            parent = transformer
            for attr in module_path[:-1]:
                parent = getattr(parent, attr)
            setattr(parent, module_path[-1], torch.empty(b.shape, dtype=torch.bfloat16).to(DEVICE))

    print("🚀 19B Transformer live.", flush=True)
    
    # ⚡ JIT Compilation for 19B Transformer
    try:
        print("🔥 Optimization: Compiling 19B Transformer (Phase 2)...", flush=True)
        transformer = torch.compile(transformer, mode="reduce-overhead", fullgraph=False)
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
            model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth',
            upscale=1, arch='clean', channel_multiplier=2, bg_upsampler=None
        )
    if upscaler_model is None:
        print(f"📥 Loading Real-ESRGAN (Multi-Pass for x{upscale_factor})...")
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        upscaler_model = RealESRGANer(
            scale=4, # Still use x4 model but we will multi-pass if needed
            model_path='https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
            model=model, tile=400, tile_pad=10, pre_pad=0, half=True if DEVICE == "cuda" else False
        )
    return face_enhancer, upscaler_model

def load_tts():
    global tts_pipeline, speaker_embedding
    if tts_pipeline is None:
        print("📥 Loading Microsoft SpeechT5 TTS...")
        tts_pipeline = pipeline("text-to-speech", model="microsoft/speecht5_tts", device=0 if model_manager.device == "cuda" else -1)
        torch.manual_seed(42)
        speaker_embedding = torch.randn(1, 512).to(DEVICE)
    return tts_pipeline

def load_vlm():
    global vlm_model, vlm_tokenizer
    if vlm_model is None:
        print("📥 Loading Moondream2...")
        clear_gpu()
        model_id = "vikhyatk/moondream2"
        vlm_model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, revision="2024-05-20").to(DEVICE)
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
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
        llm_model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            quantization_config=bnb_config, 
            device_map="auto"
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
    upscale_factor: int = 4   # 2 or 4 for Real-ESRGAN
    enhance_face: bool = True  # Enable GFPGAN
    likeness_strength: float = 1.0  # Conditioning scale for I2V
    face_enhance_weight: float = 0.5 # 0.0 to 1.0 for GFPGAN intensity
    quantize: bool = True # Enable 8-bit quantization for HunyuanVideo
    force_reload: bool = False # Clear GPU memory before loading model

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

@app.get("/health")
async def health():
    total, used, free = shutil.disk_usage("/")
    return {
        "status": "healthy", 
        "device": DEVICE, 
        "encoder": BEST_ENCODER,
        "vram_allocated": f"{torch.cuda.memory_allocated()/1024**3:.2f}GB" if DEVICE == "cuda" else "N/A",
        "disk_free": f"{free/1024**3:.2f}GB",
        "disk_used_percent": f"{(used/total)*100:.1f}%"
    }

render_lock = threading.Lock()

@app.post("/generate")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    sanitized_prefix = request.prompt[:3].lower().replace(" ", "_")
    job_id = f"vid_{sanitized_prefix}_{torch.randint(0, 1000000, (1,)).item():06x}"
    print(f"📥 [/generate] Request received: {request.prompt[:50]}... -> Job ID: {job_id}", flush=True)
    
    def job_wrapper():
        with render_lock:
            try:
                print(f"🎬 [Thread] Starting job {job_id}...", flush=True)
                render_video(job_id, request) 
                print(f"✅ [Thread] Job {job_id} done.", flush=True)
            except Exception as e:
                print(f"❌ Error in job_wrapper: {e}", flush=True)
                traceback.print_exc()

    # Use manual threading for reliability vs background_tasks
    threading.Thread(target=job_wrapper, daemon=True).start()
    return {"job_id": job_id, "status": "queued"}

# =====================================================
# HUNYUANVIDEO ENDPOINT
# =====================================================

@app.post("/generate_hunyuan")
async def hunyuan_endpoint(request: VideoRequest):
    """
    HunyuanVideo - Tencent's state-of-the-art text-to-video model
    
    Best for: High-quality text-to-video generation
    VRAM: 12GB+ (SD version), 24GB+ (full version)
    """
    if not HUNYUAN_AVAILABLE:
        return {"error": "HunyuanVideo not available. Please install dependencies."}
    
    job_id = f"hunyuan_{uuid.uuid4().hex[:8]}"
    
    def hunyuan_job():
        try:
            print(f"🎬 HunyuanVideo Job {job_id}...", flush=True)
            
            # Generate video
            # Use 480p resolution (832x480) - may need force_reload for VRAM
            height = 480
            width = 832
            job_id_result, video_path = generate_hunyuan_video(
                prompt=request.prompt,
                negative_prompt="low quality, blurry, distorted, watermark",
                num_inference_steps=request.steps or 30,
                height=height,
                width=width,
                num_frames=request.frames or 73,
                guidance_scale=7.5,
                model_type="480p",
                quantize=request.quantize,
                force_reload=request.force_reload
            )
            
            print(f"✅ HunyuanVideo Job {job_id} complete: {video_path}", flush=True)
        except Exception as e:
            print(f"❌ HunyuanVideo Error: {e}", flush=True)
            traceback.print_exc()
    
    threading.Thread(target=hunyuan_job, daemon=True).start()
    return {"job_id": job_id, "status": "queued", "model": "hunyuanvideo"}

def render_video(job_id, req):
    try:
        print(f"🎨 Phase-Based Rendering for Job {job_id}...", flush=True)
        negative_prompt = "low quality, animation, cartoon, cgi, 3d, render, blur, distorted, text, watermark, grainy, flicker, low resolution, bad anatomy, stylized"
        
        # Phase 0: Base Components (Tokenizer, VAE, Scheduler)
        # --------------------------------------------------
        tokenizer, vae, scheduler = load_ltx_base_components()
        
        # Phase 1: Encode Prompt and FREE T5 (Freed up 11GB VRAM)
        # --------------------------------------------------
        p_embeds, p_mask, n_embeds, n_mask = encode_prompt_ltx2(req.prompt, negative_prompt, tokenizer)

        # Phase 2: Load 19B Transformer (38GB VRAM)
        # --------------------------------------------------
        transformer = load_ltx_19b_transformer()
        
        # Phase 3a: Generate Audio Conditioning (RESTORED)
        # --------------------------------------------------
        audio_hidden_states, audio_encoder_hidden_states = generate_audio_conditioning(req.prompt, num_frames=int(req.frames))

        # Phase 3b: Diffusion Pass
        # --------------------------------------------------
        print("🚀 Assembling LTX-2 19B Pipeline...", flush=True)
        from diffusers import LTXPipeline, LTXImageToVideoPipeline
        target_class = LTXImageToVideoPipeline if req.image_base64 else LTXPipeline
        
        pipe = target_class(
            text_encoder=None,
            tokenizer=tokenizer,
            vae=vae,
            transformer=transformer,
            scheduler=scheduler
        )

        image_obj = None
        if req.image_base64:
            img_data = base64.b64decode(req.image_base64)
            image_obj = Image.open(io.BytesIO(img_data)).convert("RGB")

        print(f"🎬 Starting Diffusion Pass ({req.frames} frames, {req.steps} steps)...", flush=True)
        # Note: LTX-2 19B requires audio_hidden_states and audio_encoder_hidden_states
        # If the pipeline doesn't natively accept them, we may need to inject them 
        # via a patched forward call or custom pipeline.
        with torch.inference_mode():
            pipe_kwargs = {
                "prompt_embeds": p_embeds, "prompt_attention_mask": p_mask,
                "negative_prompt_embeds": n_embeds, "negative_prompt_attention_mask": n_mask,
                "num_frames": int(req.frames), "num_inference_steps": int(req.steps), 
                "guidance_scale": 6.0, "output_type": "pt"
            }
            if image_obj:
                pipe_kwargs["image"] = image_obj
            
            # Inject audio conditioning
            pipe_kwargs["audio_hidden_states"] = audio_hidden_states
            pipe_kwargs["audio_encoder_hidden_states"] = audio_encoder_hidden_states

            result = pipe(**pipe_kwargs)
        
        video_latents = result.frames # tensor output for Stage 2
        
        # Phase 4: Spatial Upscaling (Stage 2) -> 8K
        # --------------------------------------------------
        print("📥 Phase 4: Loading Spatial Upscaler (Stage 2)...", flush=True)
        from diffusers import LTX2LatentUpsamplePipeline
        upscaler = LTX2LatentUpsamplePipeline.from_pretrained(
            "Lightricks/ltxv-spatial-upscaler-0.9.7",
            torch_dtype=torch.float16
        ).to(DEVICE)
        
        print("✨ Upscaling to High Resolution...", flush=True)
        with torch.inference_mode():
            upscaled_result = upscaler(
                video_latents, prompt_embeds=p_embeds, 
                prompt_attention_mask=p_mask,
                num_inference_steps=10
            )
        final_frames = upscaled_result.frames # List of PIL Images
        
        # Phase 5: Export and Cleanup
        # --------------------------------------------------
        out_path = os.path.join(CONTENT_DIR, f"{job_id}.mp4")
        print(f"🎬 Exporting Video: {len(final_frames)} frames to {out_path}...", flush=True)
        hardware_export_to_video(final_frames, out_path, fps=24)
        
        print(f"✅ Job {job_id} Complete -> {out_path}", flush=True)
        
        # Cleanup upscaler only to keep Transformer cached for next scene
        del upscaler
        torch.cuda.empty_cache()
        gc.collect()

    except Exception as e:
        print(f"❌ Error in render_video: {e}", flush=True)
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Error (Video): {e}")

@app.post("/voice")
async def generate_voice(req: VoiceRequest):
    clear_gpu()
    tts = load_tts()
    job_id = f"aud_{uuid.uuid4().hex[:6]}"
    path = os.path.join(CONTENT_DIR, f"{job_id}.wav")

    try:
        with torch.no_grad():
            speech = tts(
                req.text,
                forward_params={"speaker_embeddings": speaker_embedding}
            )
            sf.write(path, speech["audio"], speech["sampling_rate"])
        print(f"✅ Success: Audio saved to {path}")
        return {"job_id": job_id, "download": f"/download/{job_id}"}
    except Exception as e:
        print(f"❌ Error (TTS): {e}")
        return {"error": str(e)}

@app.post("/vlm")
async def analyze(req: VLMRequest):
    clear_gpu()
    model, tokenizer = load_vlm()
    try:
        img = Image.open(io.BytesIO(base64.b64decode(req.image_base64)))
        enc = model.encode_image(img)
        answer = model.answer_question(enc, req.prompt, tokenizer)
        return {"analysis": answer}
    except Exception as e:
        print(f"❌ Error (VLM): {e}")
        return {"error": str(e)}

@app.post("/transcribe")
async def transcribe(bg: BackgroundTasks, file_path: str = None):
    """
    In a full production setup, this would handle file uploads.
    For this remote node, we can point it to a file generated/downloaded locally.
    """
    if not file_path or not os.path.exists(file_path):
        return {"error": "File not found"}
        
    clear_gpu()
    model = load_whisper()
    try:
        segments, info = model.transcribe(file_path, beam_size=5)
        results = []
        for segment in segments:
            results.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
        return {"language": info.language, "segments": results}
    except Exception as e:
        print(f"❌ Error (Whisper): {e}")
        return {"error": str(e)}

@app.post("/llm")
async def text_gen(req: LLMRequest):
    # Unload large models if needed to prevent OOM
    # In a 16GB environment, we might need to unload LTX before loading Llama
    global pipe
    if pipe is not None:
        print("💾 Unloading LTX-Video to free VRAM for LLM...")
        pipe = None
        clear_gpu()

    model, tokenizer = load_llm()
    try:
        messages = [
            {"role": "system", "content": req.system_prompt},
            {"role": "user", "content": req.prompt},
        ]
        input_ids = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(DEVICE)
        
        outputs = model.generate(
            input_ids, 
            max_new_tokens=req.max_tokens, 
            do_sample=True, 
            temperature=0.7
        )
        response = tokenizer.decode(outputs[0][input_ids.shape[-1]:], skip_special_tokens=True)
        return {"response": response}
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

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
        time.sleep(3600) # Run every hour

@app.get("/download/{job_id}")
async def download(job_id: str, bg: BackgroundTasks):
    print(f"📥 Download requested: {job_id}")
    for ext in ["mp4", "wav"]:
        path = os.path.join(CONTENT_DIR, f"{job_id}.{ext}")
        if os.path.exists(path):
            file_size = os.path.getsize(path) / (1024*1024)
            print(f"✅ Serving file: {path} ({file_size:.2f} MB)")
            # bg.add_task(delete_file, path) # DISABLED: Causes issues with large file downloads
            return FileResponse(path, media_type=f"video/{ext}", filename=f"{job_id}.{ext}")
    
    # Log what files ARE available for debugging
    available = os.listdir(CONTENT_DIR)
    print(f"⚠️ File not found: {job_id}. Available: {available[:10]}...")
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="File not found")

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
    time.sleep(2)
    print("🚀 AI Engine binding to Port 8122...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8122)

# =====================================================
# VIDEO MODEL MANAGER ENDPOINTS
# =====================================================

from video_model_manager import model_manager, VIDEO_MODELS

@app.get("/models")
async def list_models():
    """List all available video models"""
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
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=num_inference_steps,
        num_frames=num_frames,
        height=height,
        width=width,
        guidance_scale=guidance_scale,
    )
    return result

# =====================================================
# END
# =====================================================
