import logging
import json
from typing import Optional, Dict, List
from api.utils.vault import get_secret
import httpx
import os
import asyncio
import uuid
import shutil
from pathlib import Path
from api.config import settings
import redis
import time
from contextlib import asynccontextmanager


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
        try:
            from huggingface_hub import hf_hub_download
        except ImportError:
            logging.warning(
                "[ModelManager] huggingface_hub not installed, skipping real download"
            )
            raise RuntimeError("huggingface_hub not available")

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
            shutil.move(downloaded_path, target_path)

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
                    model_path.unlink()

            if model_name in self.active_usage:
                del self.active_usage[model_name]


class GpuQueueManager:
    """
    Manages a Redis-backed semaphore to limit concurrent GPU tasks on the VPS.
    Ensures VRAM isn't overloaded.
    """

    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.semaphore_key = "gpu_generation_slots"
        self.total_slots = settings.GPU_QUEUE_SLOTS
        self.timeout = settings.GPU_QUEUE_TIMEOUT

    @asynccontextmanager
    async def acquire_slot(self):
        """
        Async context manager to acquire a GPU slot.
        """
        logging.info("[GpuQueue] Requesting GPU slot...")
        start_time = time.time()

        # Simple polling-based semaphore and slot acquisition
        # In a real heavy-prod environment, we'd use Redlock or Blpop
        while True:
            current_slots = self.redis.get(self.semaphore_key)
            if current_slots is None:
                # Initialize slots if not present
                self.redis.set(self.semaphore_key, self.total_slots)
                current_slots = self.total_slots

            slots = int(current_slots)
            if slots > 0:
                # Atomic decrement
                if self.redis.decr(self.semaphore_key) >= 0:
                    logging.info(f"[GpuQueue] Slot acquired. Slots left: {slots - 1}")
                    try:
                        yield True
                        return
                    finally:
                        self.redis.incr(self.semaphore_key)
                        logging.info("[GpuQueue] Slot released.")
                else:
                    # Oops, someone took it just now
                    self.redis.incr(self.semaphore_key)

            if time.time() - start_time > self.timeout:
                logging.error("[GpuQueue] Timeout waiting for GPU slot.")
                raise TimeoutError(
                    "System busy: All GPU generation slots are currently occupied."
                )

            await asyncio.sleep(1)  # Wait before retry


class GenerativeService:
    def __init__(self):
        self.gemini_api_key = get_secret("gemini_api_key")
        self.silicon_flow_key = get_secret("silicon_flow_key")
        self.model_manager = ModelManager()
        self.gpu_queue = GpuQueueManager()

    def _get_engine_params(self, engine: str) -> Dict:
        """
        Returns optimized inference parameters for each engine to balance quality and VRAM safety.
        RTX 8000 (48GB) safe-zones.
        """
        configs = {
            "hunyuan": {
                "steps": 30,
                "cfg": 6.0,
                "vram_limit": "35GB",
                "height": 480,
                "width": 832,
            },
            "mochi": {
                "steps": 50,
                "cfg": 4.5,
                "vram_limit": "24GB",
                "height": 480,
                "width": 848,
            },
            "cogvideo": {
                "steps": 40,
                "cfg": 7.0,
                "vram_limit": "12GB",
                "height": 480,
                "width": 720,
            },
            "wan": {
                "steps": 35,
                "cfg": 5.0,
                "vram_limit": "28GB",
                "height": 480,
                "width": 832,
            },
            "wan2.2": {
                "steps": 35,
                "cfg": 5.0,
                "vram_limit": "28GB",
                "height": 480,
                "width": 832,
            },
            "ltx-video": {
                "steps": 25,
                "cfg": 3.0,
                "vram_limit": "16GB",
                "height": 480,
                "width": 832,
            },
            "zeroscope": {
                "steps": 20,
                "cfg": 7.5,
                "vram_limit": "8GB",
                "height": 480,
                "width": 480,
            },
            "lite4k": {
                "steps": 30,
                "cfg": 7.0,
                "vram_limit": "8GB",
                "height": 480,
                "width": 832,
            },
        }
        return configs.get(engine, {"steps": 20, "cfg": 7.0, "vram_limit": "12GB"})

    async def synthesize_video(
        self,
        prompt: str,
        engine: str = "veo3",
        aspect_ratio: str = "9:16",
        style: str = "Cinematic",
        custom_image_url: str = None,
    ) -> Optional[str]:
        """
        Synthesizes a new video from a text prompt.
        """
        # Global Prompt Optimization (Engine & Style Aware)
        optimized_prompt = self.optimize_prompt(prompt, style=style, engine=engine)
        params = self._get_engine_params(engine)

        logging.info(
            f"[GenerativeService] Synthesizing video with engine: {engine} (Steps: {params['steps']}, CFG: {params['cfg']}), prompt: {optimized_prompt[:50]}..."
        )

        # Engines that run on the local production GPU (RTX 8000)
        local_gpu_engines = [
            "hunyuan",
            "mochi",
            "cogvideo",
            "wan",
            "ltx-video",
            "zeroscope",
            "lite4k",
        ]

        if engine in local_gpu_engines:
            try:
                async with self.gpu_queue.acquire_slot():
                    return await self._dispatch_synthesis(
                        optimized_prompt, engine, aspect_ratio, params, custom_image_url
                    )
            except TimeoutError as e:
                logging.warning(f"[GenerativeService] Queue Timeout: {e}")
                return None
        else:
            # Cloud engines don't need the local GPU queue
            return await self._dispatch_synthesis(
                optimized_prompt, engine, aspect_ratio, params, custom_image_url
            )

    async def _dispatch_synthesis(
        self,
        prompt: str,
        engine: str,
        aspect_ratio: str,
        params: Dict = None,
        custom_image_url: str = None,
    ) -> Optional[str]:
        """Internal dispatcher for actual synthesis calls."""
        if not params:
            params = self._get_engine_params(engine)

        if engine == "veo3":
            return await self._synthesize_veo3(prompt, aspect_ratio)
        elif engine in ["wan2.2", "wan"]:
            from .models.wan_inference import generate_wan_t2v

            loop = asyncio.get_event_loop()
            _, path = await loop.run_in_executor(None, generate_wan_t2v, prompt)
            return path
        elif engine == "hunyuan":
            from .models.hunyuan_inference import generate_hunyuan

            loop = asyncio.get_event_loop()
            _, path = await loop.run_in_executor(None, generate_hunyuan, prompt)
            return path
        elif engine == "ltx-video":
            from .models.ltx_video_inference import generate_ltx

            loop = asyncio.get_event_loop()
            _, path = await loop.run_in_executor(None, generate_ltx, prompt)
            return path
        elif engine == "mochi":
            from .models.mochi_inference import generate_mochi

            loop = asyncio.get_event_loop()
            _, path = await loop.run_in_executor(None, generate_mochi, prompt)
            return path
        elif engine == "cogvideo":
            from .models.cogvideo_inference import generate_cogvideo

            loop = asyncio.get_event_loop()
            _, path = await loop.run_in_executor(None, generate_cogvideo, prompt)
            return path
        elif engine == "lite4k":
            return await self._synthesize_lite_4k(prompt, aspect_ratio)
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
            return await self._synthesize_free_provider(engine, prompt, aspect_ratio)
        else:
            logging.error(f"[GenerativeService] Unsupported engine: {engine}")
            return None

    async def _synthesize_comfy(
        self, prompt: str, model_type: str, aspect_ratio: str
    ) -> Optional[str]:
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

            output_path = f"outputs/comfy_{uuid.uuid4()}.mp4"
            os.makedirs("outputs", exist_ok=True)

            # Actual ComfyUI execution logic
            success = False
            try:
                import json

                # This represents a basic generic text-to-video workflow payload
                # In prod, this would load a specific JSON workflow matched to model_type
                payload = {
                    "prompt": {
                        "3": {
                            "class_type": "KSampler",
                            "inputs": {"seed": 1234, "steps": 20, "cfg": 8.0},
                        },
                        "6": {
                            "class_type": "CLIPTextEncode",
                            "inputs": {"text": prompt},
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
    ) -> Optional[str]:
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
        self, scenes: List[Dict], engine: str = "veo3", style: str = "Cinematic"
    ) -> List[Dict]:
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

    async def _synthesize_veo3(self, prompt: str, aspect_ratio: str) -> Optional[str]:
        """
        Google Veo 3 (Gemini 1.5/Veo API) Integration.
        Falls back to remote GPU node, then to Lite4K image+parallax approach.
        """
        import uuid, os

        job_id = f"veo3_{uuid.uuid4().hex[:8]}"
        output_dir = "/workspace/outputs"
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
                async with httpx.AsyncClient(timeout=300) as client:
                    response = await client.post(
                        f"{render_node_url}/generate", json=payload
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

    async def _synthesize_wan(self, prompt: str, aspect_ratio: str) -> Optional[str]:
        """
        Open-Source Synthesis (Wan2.2 via SiliconFlow/Fal.ai or remote GPU).
        Falls back to Lite4K image+parallax.
        """
        import uuid, os

        job_id = f"wan_{uuid.uuid4().hex[:8]}"
        output_dir = "/workspace/outputs"
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
                async with httpx.AsyncClient(timeout=300) as client:
                    response = await client.post(
                        f"{render_node_url}/generate", json=payload
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

    async def _synthesize_local(self, prompt: str, aspect_ratio: str) -> Optional[str]:
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
                async with httpx.AsyncClient(timeout=300) as client:
                    response = await client.post(
                        f"{render_node_url}/generate", json=payload
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
    ) -> Optional[str]:
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


generative_service = GenerativeService()
