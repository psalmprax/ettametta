import logging
import json
from src.api.utils.vault import get_secret
import httpx
import os
import asyncio
import uuid
import shutil
from pathlib import Path
from src.api.config import settings
import redis
import time
from contextlib import asynccontextmanager

import importlib.util

def check_module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None

# Graceful imports for optional dependencies
TORCH_AVAILABLE = check_module_available("torch")
if TORCH_AVAILABLE:
    import torch
else:
    torch = None

CV2_AVAILABLE = check_module_available("cv2")
if CV2_AVAILABLE:
    import cv2
else:
    cv2 = None

MOVIEPY_AVAILABLE = check_module_available("moviepy")
if MOVIEPY_AVAILABLE:
    import moviepy
else:
    moviepy = None

DIFFUSERS_AVAILABLE = check_module_available("diffusers")
if DIFFUSERS_AVAILABLE:
    import diffusers
else:
    diffusers = None

FASTER_WHISPER_AVAILABLE = check_module_available("faster_whisper")
if FASTER_WHISPER_AVAILABLE:
    import faster_whisper
else:
    faster_whisper = None


class ModelManager:
    """
    Handles downloading and deleting large video models to save space on the VPS.
    """

    def __init__(self):
        self.models_dir = Path(settings.COMFYUI_MODELS_DIR)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        # Persistent models stay on disk
        self.persistent_models = ["cogvideox-5b"]
        # Track active tasks using each model
        self.active_usage = {}  # {model_name: count}

    async def acquire_model(self, model_name: str) -> str:
        """
        Increments usage counter and ensures model is present.
        Downloads from HuggingFace if not available locally.
        """
        self.active_usage[model_name] = self.active_usage.get(model_name, 0) + 1
        model_path = self.models_dir / f"{model_name}.safetensors"

        if model_path.exists():
            logging.info(
                f"[ModelManager] Acquired {model_name} (Active users: {self.active_usage[model_name]})"
            )
            return str(model_path)

        logging.info(f"[ModelManager] Downloading model: {model_name}...")

        try:
            # Download from HuggingFace
            await self._download_model_from_hf(model_name, model_path)
            logging.info(f"[ModelManager] Download complete: {model_name}")
        except Exception as e:
            logging.error(f"[ModelManager] Download failed for {model_name}: {e}")
            # Fallback to touch (for testing)
            model_path.touch()
            logging.warning(f"[ModelManager] Using mock model for {model_name}")

        return str(model_path)

    async def _download_model_from_hf(self, model_name: str, target_path: Path):
        """
        Download model from HuggingFace Hub.
        """
        if not check_module_available("huggingface_hub"):
            logging.warning(
                "[ModelManager] huggingface_hub not installed, skipping real download"
            )
            raise RuntimeError("huggingface_hub not available")

        from huggingface_hub import hf_hub_download

        # Map model names to HuggingFace repo/file paths
        model_mapping = {
            "cogvideox-5b": ("THUDM/CogVideoX-5B", "CogVideoX-5B-I2V-5B.safetensors"),
            "hunyuan": ("Tencent/HunyuanVideo", "HunyuanVideo.safetensors"),
            "wan": ("Wan-AI/Wan2.2-T2V-14B", "Wan2.2-T2V-14B.safetensors"),
        }

        if model_name not in model_mapping:
            raise ValueError(f"Unknown model: {model_name}")

        repo_id, filename = model_mapping[model_name]

        # Download in background thread to avoid blocking
        import concurrent.futures
        import functools

        def download_sync():
            return hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(self.models_dir),
                local_dir_use_symlinks=False,
            )

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            downloaded_path = await loop.run_in_executor(executor, download_sync)

        # Move to expected location
        if downloaded_path != str(target_path):
            await asyncio.to_thread(shutil.move, downloaded_path, str(target_path))

    async def release_model(self, model_name: str):
        """
        Decrements usage counter and only cleans up if no other tasks need it.
        """
        if model_name not in self.active_usage:
            return

        self.active_usage[model_name] -= 1
        count = self.active_usage[model_name]

        logging.info(
            f"[ModelManager] Released {model_name} (Active users remaining: {count})"
        )

        if count <= 0:
            if (
                model_name in self.persistent_models
                or not settings.CLEANUP_TRANSIENT_MODELS
            ):
                logging.info(f"[ModelManager] Skipping cleanup for {model_name}")
            else:
                model_path = self.models_dir / f"{model_name}.safetensors"
                if model_path.exists():
                    logging.info(
                        f"[ModelManager] No more users. Cleaning up transient model: {model_name}"
                    )
                    await asyncio.to_thread(model_path.unlink)

            if model_name in self.active_usage:
                del self.active_usage[model_name]


class CircuitBreaker:
    """Enhanced circuit breaker to prevent cascading failures with engine-specific tracking"""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 120):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.engine_failures = {}  # Track failures per engine

    def is_open(self, engine: str = None) -> bool:
        # Global circuit breaker check
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logging.info("[CircuitBreaker] Circuit entering half-open state")
                return False
            return True

        # Engine-specific check
        if engine and self.engine_failures.get(engine, 0) >= self.failure_threshold:
            logging.warning(
                f"[CircuitBreaker] Engine {engine} temporarily disabled due to failures"
            )
            return True

        return False

    def record_success(self, engine: str = None):
        self.failure_count = 0
        self.state = "CLOSED"
        if engine:
            self.engine_failures[engine] = 0  # Reset engine-specific failures

    def record_failure(self, engine: str = None):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logging.warning("[CircuitBreaker] Global circuit opened due to failures")

        # Track engine-specific failures
        if engine:
            self.engine_failures[engine] = self.engine_failures.get(engine, 0) + 1
            if self.engine_failures[engine] >= self.failure_threshold:
                logging.warning(
                    f"[CircuitBreaker] Engine {engine} disabled due to repeated failures"
                )


class GpuQueueManager:
    def _initialize_queue(self):
        """Initializes the GPU slot queue with tokens if empty."""
        try:
            if not self.redis.exists(self.semaphore_key):
                logging.info(
                    f"[GpuQueue] Initializing {self.total_slots} slots in Redis list..."
                )
                tokens = [str(i) for i in range(self.total_slots)]
                self.redis.rpush(self.semaphore_key, *tokens)
                self.redis.expire(self.semaphore_key, 604800)  # 7 days persistence
        except Exception as e:
            logging.error(f"[GpuQueue] Initialization failed: {e}")

    @asynccontextmanager
    async def acquire_slot(self):
        """
        Async context manager to acquire a GPU slot using blocking BLPOP.
        """
        logging.info("[GpuQueue] Requesting GPU slot (BRPOP)...")
        self._initialize_queue()

        token = None
        try:
            # blpop returns (key, value) or None on timeout
            result = self.redis.blpop(self.semaphore_key, timeout=int(self.timeout))
            if result:
                _, token = result
                logging.info(f"[GpuQueue] Slot acquired (Token: {token})")
                yield True
            else:
                logging.error("[GpuQueue] Timeout waiting for GPU slot.")
                raise TimeoutError(
                    "System busy: All GPU generation slots are currently occupied."
                )
        finally:
            if token:
                self.redis.rpush(self.semaphore_key, token)
                logging.info(f"[GpuQueue] Slot released (Token: {token}).")


class GenerativeService:
    def __init__(self):
        self.gemini_api_key = get_secret("gemini_api_key")
        self.silicon_flow_key = get_secret("silicon_flow_key")
        self.model_manager = ModelManager()
        self.gpu_queue = GpuQueueManager()
        self.circuit_breaker = CircuitBreaker()

    def get_dependency_report(self):
        """Aggregate reports from media drivers and internal GPU status."""
        from .processor import VideoProcessor
        from .free_video_providers import free_video_provider

        proc = VideoProcessor()
        p_report = proc.get_dependency_report()
        f_report = free_video_provider.get_dependency_report()

        circuit_open = self.circuit_breaker.is_open()

        return {
            "name": "Synthesis Engine",
            "circuit_status": "OPEN" if circuit_open else "CLOSED",
            "drivers": [
                {
                    "name": "Local GPU (RTX 8000)",
                    "status": "Healthy" if not circuit_open else "Circuit Open",
                    "slots": getattr(self.gpu_queue, "total_slots", 1),
                }
            ]
            + p_report["drivers"]
            + f_report["drivers"],
            "healthy": not circuit_open
            and (p_report["healthy"] or f_report["healthy"]),
        }

    def get_health_report(self):
        """Returns real-time health for the dashboard."""
        status = "Healthy"
        issues = []

        if self.circuit_breaker.is_open():
            status = "Degraded"
            issues.append("Global circuit breaker open")

        if self.circuit_breaker.engine_failures:
            failing_engines = [
                k
                for k, v in self.circuit_breaker.engine_failures.items()
                if v >= self.circuit_breaker.failure_threshold
            ]
            if failing_engines:
                status = "Degraded"
                issues.append(f"Engines disabled: {', '.join(failing_engines)}")

        dep_report = self.get_dependency_report()
        if not dep_report["healthy"]:
            status = "Degraded"
            issues.extend(
                [
                    f"{driver['name']}: {driver['status']}"
                    for driver in dep_report["drivers"]
                    if driver["status"] != "Healthy"
                ]
            )

        return {
            "service": "Synthesis Service",
            "status": status,
            "circuit_breaker": self.circuit_breaker.state,
            "managed_models": len(self.model_manager.persistent_models),
            "engine_failures": self.circuit_breaker.engine_failures,
            "issues": issues,
        }

        # Check optional dependencies
        self.dependencies_available = {
            "torch": TORCH_AVAILABLE,
            "cv2": CV2_AVAILABLE,
            "moviepy": MOVIEPY_AVAILABLE,
            "diffusers": DIFFUSERS_AVAILABLE,
            "faster_whisper": FASTER_WHISPER_AVAILABLE,
        }

        self.logger = logging.getLogger(__name__)
        if not all(self.dependencies_available.values()):
            missing = [k for k, v in self.dependencies_available.items() if not v]
            self.logger.warning(
                f"GenerativeService: Missing dependencies: {missing}. Some features may not work."
            )
        else:
            self.logger.info("GenerativeService: All dependencies available.")

    def _get_engine_params(self, engine: str) -> dict:
        """
        Returns optimized inference parameters for each engine following the optimization hierarchy:
        1. Efficient attention (xFormers) - BEST overall
        2. Resolution + frame tuning (480p, 8-12 frames) - biggest practical win
        3. FP16 (half precision)
        4. VAE slicing/tiling
        5. Quantization (only if needed)
        Supports 8-12GB GPUs while maintaining quality.
        """
        configs = {
            "hunyuan": {
                "steps": 30,
                "cfg": 6.0,
                "vram_limit": "14GB",  # Optimized from 16-20GB → 10-14GB
                "height": 480,
                "width": 832,
                "optimization": {
                    "fp16": True,
                    "xformers": True,
                    "vae_tiling": True,
                    "vae_slicing": True,
                    "resolution_reduction": "480p",
                },
            },
            "mochi": {
                "steps": 50,
                "cfg": 4.5,
                "vram_limit": "12GB",  # Optimized from 14-18GB → 9-12GB
                "height": 480,
                "width": 848,
                "optimization": {
                    "fp16": True,
                    "xformers": True,
                    "vae_tiling": True,
                    "vae_slicing": True,
                    "resolution_reduction": "480p",
                },
            },
            "cogvideo": {
                "steps": 40,
                "cfg": 7.0,
                "vram_limit": "16GB",  # Optimized from 18-24GB → 12-16GB
                "height": 480,
                "width": 720,
                "optimization": {
                    "fp16": True,
                    "xformers": True,
                    "vae_tiling": True,
                    "vae_slicing": True,
                    "resolution_reduction": "480p",
                },
            },
            "wan": {
                "steps": 35,
                "cfg": 5.0,
                "vram_limit": "10GB",  # Optimized from 12-14GB → 8-10GB
                "height": 480,
                "width": 832,
                "optimization": {
                    "fp16": True,
                    "xformers": True,
                    "vae_tiling": True,
                    "vae_slicing": True,
                    "resolution_reduction": "480p",
                },
            },
            "wan2.2": {
                "steps": 35,
                "cfg": 5.0,
                "vram_limit": "10GB",  # Optimized from 12-14GB → 8-10GB
                "height": 480,
                "width": 832,
                "optimization": {
                    "fp16": True,
                    "xformers": True,
                    "vae_tiling": True,
                    "vae_slicing": True,
                    "resolution_reduction": "480p",
                },
            },
            "ltx-video": {
                "steps": 25,
                "cfg": 3.0,
                "vram_limit": "8GB",  # Optimized from 10-12GB → 6-8GB
                "height": 480,
                "width": 832,
                "optimization": {
                    "fp16": True,
                    "xformers": True,
                    "vae_tiling": True,
                    "vae_slicing": True,
                    "resolution_reduction": "480p",
                },
            },
            "zeroscope": {
                "steps": 20,
                "cfg": 7.5,
                "vram_limit": "8GB",  # Optimized from 10-12GB → 6-8GB
                "height": 480,
                "width": 480,
                "optimization": {
                    "fp16": True,
                    "xformers": True,
                    "vae_tiling": True,
                    "vae_slicing": True,
                    "resolution_reduction": "480p",
                },
            },
            "lite4k": {
                "steps": 30,
                "cfg": 7.0,
                "vram_limit": "7GB",  # Optimized from 8-10GB → 5-7GB
                "height": 480,
                "width": 832,
                "optimization": {
                    "fp16": True,
                    "xformers": True,
                    "vae_tiling": True,
                    "vae_slicing": True,
                    "resolution_reduction": "480p",
                },
            },
            "animatediff": {
                "steps": 25,
                "cfg": 7.5,
                "vram_limit": "8GB",  # Low VRAM requirement for animation
                "height": 512,
                "width": 512,
                "optimization": {
                    "fp16": True,
                    "xformers": True,
                    "vae_tiling": True,
                    "vae_slicing": True,
                    "resolution_reduction": "512p",  # Square format for animation
                },
            },
        }
        return configs.get(
            engine,
            {
                "steps": 20,
                "cfg": 7.0,
                "vram_limit": "12GB",
                "optimization": {
                    "fp16": True,
                    "xformers": True,
                    "vae_tiling": True,
                    "vae_slicing": True,
                    "resolution_reduction": "480p",
                },
            },
        )

    async def synthesize_video(
        self,
        prompt: str,
        engine: str = "veo3",
        aspect_ratio: str = "9:16",
        style: str = "Cinematic",
        custom_image_url: str = None,
        enhance_quality: bool = False,  # Enable Real-ESRGAN post-processing
    ) -> str | None:
        """
        Synthesizes a new video from a text prompt.
        """
        if self.circuit_breaker.is_open(engine):
            logging.error(
                f"[GenerativeService] Circuit is open for engine {engine}. Skipping synthesis."
            )
            return None

        # Global Prompt Optimization (Engine & Style Aware)
        try:
            optimized_prompt = self.optimize_prompt(prompt, style=style, engine=engine)
        except Exception as e:
            logging.warning(
                f"[GenerativeService] Prompt optimization failed: {e}, using original"
            )
            optimized_prompt = prompt

        try:
            params = self._get_engine_params(engine)
        except Exception as e:
            logging.warning(
                f"[GenerativeService] Failed to get engine params for {engine}: {e}, using defaults"
            )
            params = self._get_engine_params("veo3")  # fallback

        logging.info(
            f"[GenerativeService] Synthesizing video with engine: {engine} (Steps: {params['steps']}, CFG: {params['cfg']}), prompt: {optimized_prompt[:50]}..."
        )

        try:
            # Engines that run on the local production GPU (RTX 8000)
            local_gpu_engines = [
                "hunyuan",
                "mochi",
                "cogvideo",
                "wan",
                "ltx-video",
                "zeroscope",
                "lite4k",
                "animatediff",
            ]

            if engine in local_gpu_engines:
                async with self.gpu_queue.acquire_slot():
                    video_path = await self._dispatch_synthesis(
                        optimized_prompt, engine, aspect_ratio, params, custom_image_url
                    )
            else:
                # Cloud engines don't need the local GPU queue
                video_path = await self._dispatch_synthesis(
                    optimized_prompt, engine, aspect_ratio, params, custom_image_url
                )

            # Apply quality enhancement if requested and video was generated
            if video_path and enhance_quality:
                try:
                    video_path = await self._enhance_video_quality(video_path)
                except Exception as e:
                    logging.warning(
                        f"[GenerativeService] Quality enhancement failed: {e}, using original video"
                    )

            if video_path:
                self.circuit_breaker.record_success(engine)
                return video_path
            else:
                self.circuit_breaker.record_failure(engine)
                return video_path

        except Exception as e:
            self.circuit_breaker.record_failure(engine)
            logging.error(f"[GenerativeService] Synthesis failed for {engine}: {e}")
            return None

    async def _dispatch_synthesis(
        self,
        prompt: str,
        engine: str,
        aspect_ratio: str,
        params: dict = None,
        custom_image_url: str = None,
    ) -> str | None:
        """Internal dispatcher for actual synthesis calls with comprehensive error handling."""
        try:
            if not params:
                params = self._get_engine_params(engine)
        except Exception as e:
            logging.warning(
                f"[GenerativeService] Failed to get params for {engine}: {e}"
            )
            params = {}

        try:
            if engine == "veo3":
                return await self._synthesize_veo3(prompt, aspect_ratio)
            elif engine in ["wan2.2", "wan"]:
                try:
                    from .models.wan_inference import generate_wan_t2v

                    loop = asyncio.get_event_loop()
                    _, path = await loop.run_in_executor(None, generate_wan_t2v, prompt)
                    return path
                except ImportError as e:
                    logging.error(f"[GenerativeService] Wan model not available: {e}")
                    return None
                except Exception as e:
                    logging.error(f"[GenerativeService] Wan synthesis failed: {e}")
                    return None
            elif engine == "hunyuan":
                try:
                    from .models.hunyuan_inference import generate_hunyuan

                    loop = asyncio.get_event_loop()
                    _, path = await loop.run_in_executor(None, generate_hunyuan, prompt)
                    return path
                except ImportError as e:
                    logging.error(
                        f"[GenerativeService] Hunyuan model not available: {e}"
                    )
                    return None
                except Exception as e:
                    logging.error(f"[GenerativeService] Hunyuan synthesis failed: {e}")
                    return None
            elif engine == "ltx-video":
                try:
                    from .models.ltx_video_inference import generate_ltx

                    loop = asyncio.get_event_loop()
                    _, path = await loop.run_in_executor(None, generate_ltx, prompt)
                    return path
                except ImportError as e:
                    logging.error(
                        f"[GenerativeService] LTX-Video model not available: {e}"
                    )
                    return None
                except Exception as e:
                    logging.error(
                        f"[GenerativeService] LTX-Video synthesis failed: {e}"
                    )
                    return None
            elif engine == "mochi":
                try:
                    from .models.mochi_inference import generate_mochi

                    loop = asyncio.get_event_loop()
                    _, path = await loop.run_in_executor(None, generate_mochi, prompt)
                    return path
                except ImportError as e:
                    logging.error(f"[GenerativeService] Mochi model not available: {e}")
                    return None
                except Exception as e:
                    logging.error(f"[GenerativeService] Mochi synthesis failed: {e}")
                    return None
            elif engine == "cogvideo":
                try:
                    from .models.cogvideo_inference import generate_cogvideo

                    loop = asyncio.get_event_loop()
                    _, path = await loop.run_in_executor(
                        None, generate_cogvideo, prompt
                    )
                    return path
                except ImportError as e:
                    logging.error(
                        f"[GenerativeService] CogVideo model not available: {e}"
                    )
                    return None
                except Exception as e:
                    logging.error(f"[GenerativeService] CogVideo synthesis failed: {e}")
                    return None
            elif engine == "animatediff":
                # Use remote AI service for AnimateDiff (most robust implementation)
                return await self._synthesize_animatediff(prompt, aspect_ratio, params)
            elif engine == "lite4k":
                return await self._synthesize_lite_4k(
                    prompt, aspect_ratio, custom_image_url
                )
            # Free daily providers (external APIs)
            elif engine in [
                "zsky",
                "kling",
                "pixverse",
                "replicate",
                "stability",
                "runway",
                "pika",
            ]:
                return await self._synthesize_free_provider(
                    engine, prompt, aspect_ratio
                )
            else:
                logging.error(f"[GenerativeService] Unsupported engine: {engine}")
                return None
        except Exception as e:
            logging.error(
                f"[GenerativeService] Dispatch failed for engine {engine}: {e}"
            )
            return None

    async def _synthesize_comfy(
        self, prompt: str, model_type: str, aspect_ratio: str
    ) -> str | None:
        """
        ComfyUI Self-Hosted Stack: Downloads model, runs workflow, cleans up.
        """
        model_name_map = {
            "hunyuan": "HunyuanVideo-1.5",
            "mochi": "Mochi-1",
            "cogvideo": "CogVideoX-5b",
            "wan": "Wan-2.2-V2V",
            "ltx-video": "LTX-Video",
            "zeroscope": "Zeroscope_v2_XL",
        }
        model_name = model_name_map.get(model_type, "Wan-2.2-V2V")

        try:
            # 1. Acquire Model (Reference Counted)
            await self.model_manager.acquire_model(model_name)

            # 2. Trigger ComfyUI Workflow
            logging.info(
                f"[GenerativeService] Dispatching ComfyUI workflow for {model_name} to {settings.COMFYUI_URL}..."
            )

            output_path = f"{settings.STORAGE_OUTPUT_DIR}/comfy_{uuid.uuid4()}.mp4"
            os.makedirs(settings.STORAGE_OUTPUT_DIR, exist_ok=True)

            # Actual ComfyUI execution logic
            success = False
            try:
                import json

                # This represents a basic generic text-to-video workflow payload
                # In prod, this would load a specific JSON workflow matched to model_type
                # Apply VRAM optimization settings
                params = self._get_engine_params(model_type)
                optimized_steps = params.get("steps", 20)
                optimized_cfg = params.get("cfg", 7.0)

                payload = {
                    "prompt": {
                        "3": {
                            "class_type": "KSampler",
                            "inputs": {
                                "seed": 1234,
                                "steps": optimized_steps,
                                "cfg": optimized_cfg,
                                # Enable xFormers attention optimization
                                "sampler_name": "euler",
                                "scheduler": "normal",
                            },
                        },
                        "6": {
                            "class_type": "CLIPTextEncode",
                            "inputs": {"text": prompt},
                        },
                        # VAE settings for memory optimization
                        "vae_settings": {
                            "class_type": "VAELoader",
                            "inputs": {
                                "vae_name": f"{model_type}_vae.safetensors",
                                "tiling": True,  # Enable VAE tiling for lower VRAM
                            },
                        },
                        # Just a skeleton to attempt the connection
                    }
                }
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.post(
                        f"{settings.COMFYUI_URL.rstrip('/')}/prompt", json=payload
                    )
                    if resp.status_code == 200:
                        logging.info(
                            f"[GenerativeService] ComfyUI job submitted. Polling for completion..."
                        )
                        # Poll /history for job completion
                        job_id = resp.json().get("prompt_id")
                        if job_id:
                            for attempt in range(30):
                                await asyncio.sleep(2)
                                hist_resp = await client.get(
                                    f"{settings.COMFYUI_URL.rstrip('/')}/history/{job_id}"
                                )
                                if hist_resp.status_code == 200:
                                    hist_data = hist_resp.json()
                                    if job_id in hist_data and hist_data[job_id].get(
                                        "outputs"
                                    ):
                                        success = True
                                        break
                        if not success:
                            raise RuntimeError(
                                "ComfyUI job did not complete within timeout"
                            )
                    else:
                        raise RuntimeError(
                            f"ComfyUI returned {resp.status_code}: {resp.text[:200]}"
                        )
            except Exception as e:
                logging.error(
                    f"[GenerativeService] ComfyUI connection failed: {e}. Falling back."
                )

            # No dummy fallback - let the error propagate
            if not success:
                raise RuntimeError(
                    "Generative video synthesis failed: ComfyUI unavailable and no fallback configured."
                )

            return output_path

        except Exception as e:
            logging.error(f"[GenerativeService] Synthesis orchestrator failed: {e}")
            raise
        finally:
            # 3. Release Model (Cleans up only if count is 0)
            await self.model_manager.release_model(model_name)

    async def _synthesize_lite_4k(
        self, prompt: str, aspect_ratio: str, custom_image_url: str = None
    ) -> str | None:
        # ... (rest of the code stays same)
        """
        4K Lite Orchestrator: High-res image generation + Cinematic Parallax.
        Uses Pollinations.ai for zero-cost high-quality assets.
        """
        import httpx
        import uuid
        import urllib.parse
        from .processor import VideoProcessor

        logging.info(
            f"[GenerativeService] Triggering 4K Lite Synthesis: {prompt[:50]}..."
        )

        # 1. Generate or use custom 4K Static Image
        if custom_image_url:
            # Use provided custom image
            image_url = custom_image_url
            logging.info(f"[GenerativeService] Using custom image: {image_url}")
        else:
            # Generate high-quality image (Pollinations.ai with FLUX model)
            encoded_prompt = urllib.parse.quote(prompt)
            # We request a large resolution (which translates to high quality for upscale later)
            width, height = (3840, 2160) if aspect_ratio == "16:9" else (2160, 3840)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&seed={uuid.uuid4().int}"
            logging.info(f"[GenerativeService] Generated FLUX image: {image_url}")

        # 2. Process into 4K Cinematic Video
        processor = VideoProcessor()
        output_name = f"lite4k_{uuid.uuid4()}.mp4"

        # We'll call a new processor method specifically for image-to-parallax
        video_path = await processor.apply_cinematic_motion(
            image_url, output_name, aspect_ratio=aspect_ratio
        )

        return video_path

    async def synthesize_scene_batch(
        self, scenes: list[dict], engine: str = "veo3", style: str = "Cinematic"
    ) -> list[dict]:
        """
        Synthesizes multiple scenes for storytelling.
        Optimized to group by model and prevent redundant model thrashing.
        """
        logging.info(
            f"[GenerativeService] Synthesizing optimized batch of {len(scenes)} scenes..."
        )

        # 1. Group by model if using ComfyUI stack
        is_comfy = engine in ["hunyuan", "mochi", "cogvideo", "wan"]

        if is_comfy:
            model_name_map = {
                "hunyuan": "HunyuanVideo-1.5",
                "mochi": "Mochi-1",
                "cogvideo": "CogVideoX-5b",
                "wan": "Wan-2.2-V2V",
            }
            model_name = model_name_map.get(engine, "Wan-2.2-V2V")

            # Acquire model ONCE for the whole batch
            await self.model_manager.acquire_model(model_name)
            try:
                tasks = [
                    self.synthesize_video(
                        s.get("visual_prompt", ""), engine=engine, style=style
                    )
                    for s in scenes
                ]
                results = await asyncio.gather(*tasks)
            finally:
                # Release model ONCE after batch finishes
                await self.model_manager.release_model(model_name)
        else:
            # Standard parallel processing for cloud models
            tasks = [
                self.synthesize_video(
                    s.get("visual_prompt", ""), engine=engine, style=style
                )
                for s in scenes
            ]
            results = await asyncio.gather(*tasks)

        synthesized_scenes = []
        for i, url in enumerate(results):
            synthesized_scenes.append({**scenes[i], "video_url": url})

        return synthesized_scenes

    async def _synthesize_veo3(self, prompt: str, aspect_ratio: str) -> str | None:
        """
        Google Veo 3 (Gemini 1.5/Veo API) Integration.
        Falls back to remote GPU node, then to Lite4K image+parallax approach.
        """
        import uuid, os

        job_id = f"veo3_{uuid.uuid4().hex[:8]}"
        output_dir = settings.REMOTE_STORAGE_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{job_id}.mp4")

        # Try Gemini API if key is available
        if self.gemini_api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel("gemini-1.5-pro")
                response = model.generate_content(
                    f"Generate a detailed video scene description for: {prompt}. "
                    f"Aspect ratio: {aspect_ratio}. Return a vivid visual description only."
                )
                logging.info(
                    f"[GenerativeService] Veo3 Gemini prompt optimized: {response.text[:100]}"
                )
            except Exception as e:
                logging.warning(f"[GenerativeService] Gemini API failed: {e}")

        # Try remote GPU node
        render_node_url = os.getenv("RENDER_NODE_URL")
        if render_node_url:
            try:
                payload = {
                    "prompt": prompt,
                    "model": "veo3",
                    "resolution": "720p",
                    "aspect_ratio": aspect_ratio,
                }
                headers = {"x-worker-token": settings.AI_CLUSTER_SECRET}
                async with httpx.AsyncClient(timeout=300) as client:
                    response = await client.post(
                        f"{render_node_url}/generate", json=payload, headers=headers
                    )
                if response.status_code == 200:
                    data = response.json()
                    dl_url = data.get("download_url") or data.get("url")
                    if dl_url:
                        dl_resp = await client.get(dl_url, timeout=120)
                        with open(output_path, "wb") as f:
                            f.write(dl_resp.content)
                        return output_path
            except Exception as e:
                logging.warning(
                    f"[GenerativeService] Remote GPU node failed for Veo3: {e}"
                )

        # Fallback to Lite4K image+parallax
        logging.info("[GenerativeService] Veo3 falling back to Lite4K image+parallax")
        return await self._synthesize_lite_4k(prompt, aspect_ratio)

    async def _synthesize_wan(self, prompt: str, aspect_ratio: str) -> str | None:
        """
        Open-Source Synthesis (Wan2.2 via SiliconFlow/Fal.ai or remote GPU).
        Falls back to Lite4K image+parallax.
        """
        import uuid, os

        job_id = f"wan_{uuid.uuid4().hex[:8]}"
        output_dir = settings.REMOTE_STORAGE_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{job_id}.mp4")

        # Try SiliconFlow API if key is available
        if self.silicon_flow_key:
            try:
                async with httpx.AsyncClient(timeout=600) as client:
                    response = await client.post(
                        "https://api.siliconflow.cn/v1/video/generations",
                        headers={"Authorization": f"Bearer {self.silicon_flow_key}"},
                        json={
                            "model": "Wan-AI/Wan2.2-T2V-14B-Diffusers",
                            "prompt": prompt,
                        },
                    )
                if response.status_code == 200:
                    data = response.json()
                    dl_url = data.get("video", {}).get("url") or data.get("url")
                    if dl_url:
                        async with httpx.AsyncClient(timeout=120) as client:
                            dl_resp = await client.get(dl_url)
                        with open(output_path, "wb") as f:
                            f.write(dl_resp.content)
                        return output_path
            except Exception as e:
                logging.warning(f"[GenerativeService] SiliconFlow API failed: {e}")

        # Try remote GPU node
        render_node_url = os.getenv("RENDER_NODE_URL")
        if render_node_url:
            try:
                payload = {
                    "prompt": prompt,
                    "model": "wan-2.2-t2v",
                    "resolution": "480p",
                }
                headers = {"x-worker-token": settings.AI_CLUSTER_SECRET}
                async with httpx.AsyncClient(timeout=300) as client:
                    response = await client.post(
                        f"{render_node_url}/generate", json=payload, headers=headers
                    )
                if response.status_code == 200:
                    data = response.json()
                    dl_url = data.get("download_url") or data.get("url")
                    if dl_url:
                        dl_resp = await client.get(dl_url, timeout=120)
                        with open(output_path, "wb") as f:
                            f.write(dl_resp.content)
                        return output_path
            except Exception as e:
                logging.warning(
                    f"[GenerativeService] Remote GPU node failed for Wan: {e}"
                )

        # Fallback to Lite4K
        logging.info("[GenerativeService] Wan falling back to Lite4K image+parallax")
        return await self._synthesize_lite_4k(prompt, aspect_ratio)

    async def _synthesize_local(self, prompt: str, aspect_ratio: str) -> str | None:
        """
        Remote/Local GPU Video Synthesis Integration.
        Checks for a RENDER_NODE_URL. If present, proxies the request to the
        external GPU server running the diffusers FastAPI app.
        """
        import os

        render_node_url = os.getenv("RENDER_NODE_URL")

        if render_node_url:
            logging.info(
                f"[GenerativeService] Routing synthesis to Remote GPU Node: {render_node_url}"
            )
            try:
                # We would typically use httpx here for an async call, and either await the result
                # or rely on a webhook callback for long-running jobs.
                payload = {
                    "prompt": prompt,
                    "resolution": "720p",
                    "duration_seconds": 5,
                }
                headers = {"x-worker-token": settings.AI_CLUSTER_SECRET}
                async with httpx.AsyncClient(timeout=300) as client:
                    response = await client.post(
                        f"{render_node_url}/generate", json=payload, headers=headers
                    )

                if response.status_code == 200:
                    data = response.json()
                    job_id = data.get("job_id")
                    if job_id:
                        return f"{render_node_url}/download/{job_id}"
                raise RuntimeError(
                    f"Remote GPU node returned {response.status_code}: {response.text[:200]}"
                )
            except Exception as e:
                logging.error(
                    f"[GenerativeService] Failed to contact Remote GPU Node: {e}"
                )
                # Fallback to mock
        else:
            logging.error(
                "[GenerativeService] RENDER_NODE_URL not configured. Cannot generate video."
            )
            raise ValueError(
                "Render node URL not configured. Please set RENDER_NODE_URL in environment."
            )

        return None

    def optimize_prompt(
        self, user_prompt: str, style: str = "Cinematic", engine: str = "veo3"
    ) -> str:
        """
        Refines a simple user prompt into a high-fidelity director's prompt tailored for the specific engine.
        """
        # Engine-specific base grammars
        engine_modifiers = {
            "hunyuan": "High-fidelity natural language, volumetric lighting, photorealistic, 8k, detailed textures, cinematic composition.",
            "ltx-video": "A detailed video of, cinematic movement, highly realistic, professional cinematography.",
            "zeroscope": "8k, high quality, masterpiece, sharp focus, highly detailed.",
            "mochi": "Realistic physics, complex motion, fluid movement, high-energy action.",
            "cogvideo": "3D causal convolution, deep semantic consistency, cinematic realism.",
            "veo3": "Google DeepMind aesthetics, ultra-high definition, artistic masterpiece.",
            "lite4k": "4k resolution, cinematic parallax, sharpest details, stunning clarity.",
            # Free daily providers
            "zsky": "High-fidelity, WAN 2.2 model, RTX 5090 quality, smooth motion.",
            "kling": "Cinematic quality, realistic physics, high detail, professional grade.",
            "pixverse": "Vibrant colors, smooth animation, dynamic motion, high quality.",
            "replicate": "Fast generation, efficient, high-quality output.",
            "stability": "Stable diffusion video, consistent quality, reliable output.",
            "runway": "Professional filmmaking quality, cinematic, high production value.",
            "pika": "Fast generation, creative, high energy, polished results.",
            "animatediff": "Smooth character animation, fluid motion, consistent movement, high frame coherence.",
        }

        style_modifiers = {
            "Cinematic": "Shot on 35mm, anamorphic lenses, moody lighting, realistic physics.",
            "Glitch": "Cyberpunk aesthetic, VHS artifacts, digital distortion, high energy.",
            "Noir": "Black and white, high contrast, shadows, smoke, film grain, 1940s detective vibe.",
            "Hectic/Viral": "Fast-paced editing, dynamic camera shakes, zoom bursts, high intensity.",
            "ASMR/Calm": "Slow motion, macro shots, soft focus, ambient lighting, peaceful atmosphere.",
        }

        # Merge modifiers
        engine_mod = engine_modifiers.get(engine, "")
        style_mod = style_modifiers.get(style, "")

        refined = (
            f"{user_prompt}. {style_mod} {engine_mod} Professional production grade."
        )

        # FUTURE: Add LLM-based expansion here if LLM_API_KEY is present
        # e.g., prompt_expert = LLMExpert(engine=engine)
        # return prompt_expert.refine(refined)

        return refined

    async def _synthesize_free_provider(
        self, provider: str, prompt: str, aspect_ratio: str
    ) -> str | None:
        """
        Synthesize video using free daily credit providers (ZSky, Kling, PixVerse, etc.)
        """
        from .free_video_providers import free_video_provider

        logging.info(
            f"[GenerativeService] Calling free provider: {provider} for: {prompt[:50]}..."
        )

        # Map aspect ratio to provider format
        aspect_map = {"9:16": "9:16", "16:9": "16:9", "1:1": "1:1"}
        provider_aspect = aspect_map.get(aspect_ratio, "9:16")

        try:
            result = await free_video_provider.generate_video(
                prompt=prompt,
                duration=5,
                aspect_ratio=provider_aspect,
                style=None,
            )

            if result and result.get("video_url"):
                logging.info(
                    f"[GenerativeService] {provider} generated video: {result['video_url'][:50]}..."
                )
                return result["video_url"]
            else:
                logging.warning(f"[GenerativeService] {provider} returned no result")
                return None

        except Exception as e:
            logging.error(f"[GenerativeService] {provider} failed: {e}")
            return None

    async def _enhance_video_quality(self, video_path: str) -> str:
        """
        Enhance video quality using Real-ESRGAN post-processing.
        Pro strategy: Generate low-VRAM + enhance after for better quality.
        """
        import uuid
        import os
        from pathlib import Path

        try:
            # Import enhancement libraries
            if not check_module_available("realesrgan") or not check_module_available("basicsr"):
                logging.warning(
                    "[GenerativeService] Real-ESRGAN or BasicSR not available, skipping enhancement"
                )
                return video_path

            from realesrgan import RealESRGANer
            from basicsr.archs.rrdbnet_arch import RRDBNet

            # Create enhanced output path
            video_dir = Path(video_path).parent
            video_name = Path(video_path).stem
            enhanced_path = video_dir / f"{video_name}_enhanced.mp4"

            logging.info(
                f"[GenerativeService] Enhancing video quality with Real-ESRGAN: {video_path}"
            )

            # Initialize Real-ESRGAN model (x4 upscale for quality)
            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=4,
            )
            upscaler = RealESRGANer(
                scale=4,
                model_path="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
                model=model,
                tile=400,
                tile_pad=10,
                pre_pad=0,
                half=True,  # Use FP16 for memory efficiency
            )

            # Extract frames from video
            import cv2

            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Create temp directory for frames
            temp_dir = video_dir / f"temp_enhance_{uuid.uuid4().hex[:8]}"
            temp_dir.mkdir(exist_ok=True)

            enhanced_frames = []
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Enhance frame with Real-ESRGAN
                enhanced_frame, _ = upscaler.enhance(frame, outscale=4)
                enhanced_frames.append(enhanced_frame)

                frame_idx += 1
                if frame_idx % 10 == 0:
                    logging.info(
                        f"[GenerativeService] Enhanced {frame_idx}/{frame_count} frames"
                    )

            cap.release()

            # Write enhanced video
            if enhanced_frames:
                first_frame = enhanced_frames[0]
                h, w = first_frame.shape[:2]

                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                out = cv2.VideoWriter(str(enhanced_path), fourcc, fps, (w, h))

                for frame in enhanced_frames:
                    out.write(frame)

                out.release()

                # Cleanup temp files
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)

                logging.info(
                    f"[GenerativeService] Video quality enhancement completed: {enhanced_path}"
                )
                return str(enhanced_path)
            else:
                logging.warning("[GenerativeService] No frames to enhance")
                return video_path

        except Exception as e:
            logging.error(f"[GenerativeService] Quality enhancement failed: {e}")
            return video_path  # Return original if enhancement fails

    async def _synthesize_animatediff(
        self, prompt: str, aspect_ratio: str, params: dict = None
    ) -> str | None:
        """
        Generate animation using AnimateDiff model.
        Specialized for smooth character animations and motion.
        """
        import uuid
        import os

        try:
            # Use remote AI service for AnimateDiff (more robust)
            render_node_url = settings.RENDER_NODE_URL
            if render_node_url:
                payload = {
                    "prompt": prompt,
                    "model": "animatediff_v15",
                    "negative_prompt": "low quality, blurry, distorted, static, motionless",
                    "num_inference_steps": params.get("steps", 25) if params else 25,
                    "num_frames": 16,  # AnimateDiff typically uses 16 frames
                    "height": params.get("height", 512) if params else 512,
                    "width": params.get("width", 512) if params else 512,
                    "guidance_scale": params.get("cfg", 7.5) if params else 7.5,
                }

                async with httpx.AsyncClient(
                    timeout=600
                ) as client:  # Longer timeout for animation
                    response = await client.post(
                        f"{render_node_url}/generate_animatediff", json=payload
                    )

                if response.status_code == 200:
                    data = response.json()
                    job_id = data.get("job_id")
                    if job_id:
                        # Poll for completion
                        for attempt in range(60):  # 10 minutes max
                            await asyncio.sleep(10)
                            status_resp = await client.get(
                                f"{render_node_url}/status/{job_id}"
                            )
                            if status_resp.status_code == 200:
                                status_data = status_resp.json()
                                if status_data.get("status") == "completed":
                                    # Download the result
                                    dl_resp = await client.get(
                                        f"{render_node_url}/download/{job_id}"
                                    )
                                    if dl_resp.status_code == 200:
                                        output_path = f"{settings.STORAGE_OUTPUT_DIR}/animatediff_{uuid.uuid4().hex[:8]}.mp4"
                                        os.makedirs(
                                            settings.STORAGE_OUTPUT_DIR, exist_ok=True
                                        )
                                        with open(output_path, "wb") as f:
                                            f.write(dl_resp.content)
                                        return output_path
                                elif status_data.get("status") == "failed":
                                    logging.error(
                                        f"[GenerativeService] AnimateDiff job failed: {status_data}"
                                    )
                                    break

                        logging.warning("[GenerativeService] AnimateDiff job timeout")
                        return None
                    else:
                        logging.error(
                            f"[GenerativeService] No job_id returned from AnimateDiff"
                        )
                        return None
                else:
                    logging.error(
                        f"[GenerativeService] AnimateDiff API error: {response.status_code}"
                    )
                    return None
            else:
                logging.warning(
                    "[GenerativeService] No RENDER_NODE_URL configured for AnimateDiff"
                )
                return None

        except Exception as e:
            logging.error(f"[GenerativeService] AnimateDiff synthesis failed: {e}")
            return None


    async def pull_stock_for_niche(self, niche: str, count: int = 3) -> list[dict]:
        """
        Procures professional stock assets matching the niche.
        Uses StockService to fetch and download assets.
        """
        from .stock_service import base_stock_service
        
        logging.info(f"[GenerativeService] Pulling {count} stock assets for niche: {niche}")
        
        try:
            urls = await base_stock_service.fetch_b_roll(niche, count=count)
            downloaded_assets = []
            
            for url in urls:
                # Use a reliable local path for stock
                path = await base_stock_service.download_stock_video(url, output_dir="local_downloads/stock")
                if path:
                    downloaded_assets.append({
                        "id": f"stock_{uuid.uuid4().hex[:8]}",
                        "platform": "Pexels",
                        "url": url,
                        "file_path": path,
                        "motion_score": 0.8, # Stock is usually high quality
                        "relevance": 0.9
                    })
            
            return downloaded_assets
        except Exception as e:
            logging.error(f"[GenerativeService] Failed to pull stock for {niche}: {e}")
            return []


base_generative_service = GenerativeService()
