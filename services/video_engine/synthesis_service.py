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
        self.active_usage = {} # {model_name: count}
        
    async def acquire_model(self, model_name: str) -> str:
        """
        Increments usage counter and ensures model is present.
        """
        self.active_usage[model_name] = self.active_usage.get(model_name, 0) + 1
        model_path = self.models_dir / f"{model_name}.safetensors"
        
        if model_path.exists():
            logging.info(f"[ModelManager] Acquired {model_name} (Active users: {self.active_usage[model_name]})")
            return str(model_path)
            
        logging.info(f"[ModelManager] Downloading model: {model_name}...")
        await asyncio.sleep(2) # Simulate download time
        model_path.touch()
        logging.info(f"[ModelManager] Download complete: {model_name}")
        return str(model_path)

    async def release_model(self, model_name: str):
        """
        Decrements usage counter and only cleans up if no other tasks need it.
        """
        if model_name not in self.active_usage:
            return

        self.active_usage[model_name] -= 1
        count = self.active_usage[model_name]
        
        logging.info(f"[ModelManager] Released {model_name} (Active users remaining: {count})")
        
        if count <= 0:
            if model_name in self.persistent_models or not settings.CLEANUP_TRANSIENT_MODELS:
                logging.info(f"[ModelManager] Skipping cleanup for {model_name}")
            else:
                model_path = self.models_dir / f"{model_name}.safetensors"
                if model_path.exists():
                    logging.info(f"[ModelManager] No more users. Cleaning up transient model: {model_name}")
                    model_path.unlink()
            
            if model_name in self.active_usage:
                del self.active_usage[model_name]

class GenerativeService:
    def __init__(self):
        self.gemini_api_key = get_secret("gemini_api_key")
        self.silicon_flow_key = get_secret("silicon_flow_key") # For Wan2.2/LTX-2
        self.model_manager = ModelManager()
        
    async def synthesize_video(self, prompt: str, engine: str = "veo3", aspect_ratio: str = "9:16") -> Optional[str]:
        """
        Synthesizes a new video from a text prompt.
        """
        logging.info(f"[GenerativeService] Synthesizing video with engine: {engine}, prompt: {prompt[:50]}...")
        
        if engine == "veo3":
            return await self._synthesize_veo3(prompt, aspect_ratio)
        elif engine == "wan2.2":
            return await self._synthesize_wan(prompt, aspect_ratio)
        elif engine == "ltx-video":
            return await self._synthesize_local(prompt, aspect_ratio)
        elif engine == "lite4k":
            return await self._synthesize_lite_4k(prompt, aspect_ratio)
        elif engine in ["hunyuan", "mochi", "cogvideo", "wan"]:
            return await self._synthesize_comfy(prompt, engine, aspect_ratio)
        else:
            logging.error(f"[GenerativeService] Unsupported engine: {engine}")
            return None

    async def _synthesize_comfy(self, prompt: str, model_type: str, aspect_ratio: str) -> Optional[str]:
        """
        ComfyUI Self-Hosted Stack: Downloads model, runs workflow, cleans up.
        """
        model_name_map = {
            "hunyuan": "HunyuanVideo-1.5",
            "mochi": "Mochi-1",
            "cogvideo": "CogVideoX-5b",
            "wan": "Wan-2.2-V2V"
        }
        model_name = model_name_map.get(model_type, "Wan-2.2-V2V")
        
        try:
            # 1. Acquire Model (Reference Counted)
            await self.model_manager.acquire_model(model_name)
            
            # 2. Trigger ComfyUI Workflow
            logging.info(f"[GenerativeService] Dispatching ComfyUI workflow for {model_name}...")
            
            # Simulation of ComfyUI API call
            await asyncio.sleep(5) 
            
            output_path = f"outputs/comfy_{uuid.uuid4()}.mp4"
            os.makedirs("outputs", exist_ok=True)
            with open(output_path, "w") as f: f.write("mock video data")
            
            return output_path
            
        except Exception as e:
            logging.error(f"[GenerativeService] ComfyUI synthesis failed: {e}")
            return None
        finally:
            # 3. Release Model (Cleans up only if count is 0)
            await self.model_manager.release_model(model_name)

    async def _synthesize_lite_4k(self, prompt: str, aspect_ratio: str) -> Optional[str]:
        # ... (rest of the code stays same)
        """
        4K Lite Orchestrator: High-res image generation + Cinematic Parallax.
        Uses Pollinations.ai for zero-cost high-quality assets.
        """
        import httpx
        import uuid
        import urllib.parse
        from .processor import VideoProcessor
        
        logging.info(f"[GenerativeService] Triggering 4K Lite Synthesis: {prompt[:50]}...")
        
        # 1. Generate 4K Static Image (Pollinations.ai)
        encoded_prompt = urllib.parse.quote(prompt)
        # We request a large resolution (which translates to high quality for upscale later)
        width, height = (3840, 2160) if aspect_ratio == "16:9" else (2160, 3840)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&seed={uuid.uuid4().int}"
        
        # 2. Process into 4K Cinematic Video
        processor = VideoProcessor()
        output_name = f"lite4k_{uuid.uuid4()}.mp4"
        
        # We'll call a new processor method specifically for image-to-parallax
        video_path = await processor.apply_cinematic_motion(image_url, output_name, aspect_ratio=aspect_ratio)
        
        return video_path

    async def synthesize_scene_batch(self, scenes: List[Dict], engine: str = "veo3") -> List[Dict]:
        """
        Synthesizes multiple scenes for storytelling.
        Optimized to group by model and prevent redundant model thrashing.
        """
        logging.info(f"[GenerativeService] Synthesizing optimized batch of {len(scenes)} scenes...")
        
        # 1. Group by model if using ComfyUI stack
        is_comfy = engine in ["hunyuan", "mochi", "cogvideo", "wan"]
        
        if is_comfy:
            model_name_map = {
                "hunyuan": "HunyuanVideo-1.5",
                "mochi": "Mochi-1",
                "cogvideo": "CogVideoX-5b",
                "wan": "Wan-2.2-V2V"
            }
            model_name = model_name_map.get(engine, "Wan-2.2-V2V")
            
            # Acquire model ONCE for the whole batch
            await self.model_manager.acquire_model(model_name)
            try:
                tasks = [self.synthesize_video(s.get("visual_prompt", ""), engine=engine) for s in scenes]
                results = await asyncio.gather(*tasks)
            finally:
                # Release model ONCE after batch finishes
                await self.model_manager.release_model(model_name)
        else:
            # Standard parallel processing for cloud models
            tasks = [self.synthesize_video(s.get("visual_prompt", ""), engine=engine) for s in scenes]
            results = await asyncio.gather(*tasks)
        
        synthesized_scenes = []
        for i, url in enumerate(results):
            synthesized_scenes.append({
                **scenes[i],
                "video_url": url
            })
            
        return synthesized_scenes

    async def _synthesize_veo3(self, prompt: str, aspect_ratio: str) -> Optional[str]:
        """
        Google Veo 3 (Gemini 1.5/Veo API) Integration.
        """
        if not self.gemini_api_key:
            logging.error("[GenerativeService] Gemini API key missing. Cannot generate video.")
            raise ValueError("Google Gemini API key not configured. Please set GEMINI_API_KEY in environment.")

        # Actual API call logic for Google Veo 3 would go here
        # TODO: Implement actual API call when API is available
        raise NotImplementedError("Veo 3 synthesis not yet implemented. API integration pending.")

    async def _synthesize_wan(self, prompt: str, aspect_ratio: str) -> Optional[str]:
        """
        Open-Source Synthesis (Wan2.2 via SiliconFlow/Fal.ai).
        """
        if not self.silicon_flow_key:
            logging.error("[GenerativeService] SiliconFlow API key missing. Cannot generate video.")
            raise ValueError("SiliconFlow API key not configured. Please set SILICON_FLOW_API_KEY in environment.")

        # Interface with SiliconFlow/Open-Source cloud provider
        # TODO: Implement actual API call when API is available
        raise NotImplementedError("Wan2.2 synthesis not yet implemented. API integration pending.")

    async def _synthesize_local(self, prompt: str, aspect_ratio: str) -> Optional[str]:
        """
        Remote/Local GPU Video Synthesis Integration.
        Checks for a RENDER_NODE_URL. If present, proxies the request to the 
        external GPU server running the diffusers FastAPI app.
        """
        import os
        render_node_url = os.getenv("RENDER_NODE_URL")
        
        if render_node_url:
            logging.info(f"[GenerativeService] Routing synthesis to Remote GPU Node: {render_node_url}")
            try:
                # We would typically use httpx here for an async call, and either await the result
                # or rely on a webhook callback for long-running jobs.
                # Since synthesis takes minutes, we simulate the async request structure.
                payload = {
                    "prompt": prompt,
                    "resolution": "720p",
                    "duration_seconds": 5
                }
                async with httpx.AsyncClient(timeout=300) as client:
                    response = await client.post(f"{render_node_url}/generate", json=payload)
                    
                if response.status_code == 200:
                    data = response.json()
                    job_id = data.get("job_id")
                    
                    # NOTE: A robust implementation would involve Celery polling `download_url`
                    # For demonstration, we return a URL pattern that the system would eventually fetch.
                    return f"{render_node_url}/download/{job_id}"
            except Exception as e:
                logging.error(f"[GenerativeService] Failed to contact Remote GPU Node: {e}")
                # Fallback to mock
        else:
            logging.error("[GenerativeService] RENDER_NODE_URL not configured. Cannot generate video.")
            raise ValueError("Render node URL not configured. Please set RENDER_NODE_URL in environment.")
        
        return None

    def optimize_prompt(self, user_prompt: str, style: str = "Cinematic") -> str:
        """
        Uses an LLM to expand a simple user prompt into a high-fidelity director's prompt.
        """
        style_modifiers = {
            "Cinematic": "Shot on 35mm, anamorphic lenses, moody lighting, 4K, realistic physics.",
            "Glitch": "Cyberpunk aesthetic, VHS artifacts, digital distortion, high energy.",
            "Noir": "Black and white, high contrast, shadows, smoke, film grain, 1940s detective vibe."
        }
        
        refined = f"{user_prompt}. {style_modifiers.get(style, '')} Highly detailed, professional grade."
        return refined

generative_service = GenerativeService()
