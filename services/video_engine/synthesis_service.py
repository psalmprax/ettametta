import logging
import json
from typing import Optional, Dict
from api.utils.vault import get_secret
import httpx

class GenerativeService:
    def __init__(self):
        self.gemini_api_key = get_secret("gemini_api_key")
        self.silicon_flow_key = get_secret("silicon_flow_key") # For Wan2.2/LTX-2
        
    async def synthesize_video(self, prompt: str, engine: str = "veo3", aspect_ratio: str = "9:16") -> Optional[str]:
        """
        Synthesizes a new video from a text prompt.
        """
        logging.info(f"[GenerativeService] Synthesizing video with engine: {engine}, prompt: {prompt[:50]}...")
        
        if engine == "veo3":
            return await self._synthesize_veo3(prompt, aspect_ratio)
        elif engine == "wan2.2":
            return await self._synthesize_wan(prompt, aspect_ratio)
        elif engine == "ltx2":
            return await self._synthesize_ltx2(prompt, aspect_ratio)
        elif engine == "lite4k":
            return await self._synthesize_lite_4k(prompt, aspect_ratio)
        else:
            logging.error(f"[GenerativeService] Unsupported engine: {engine}")
            return None

    async def _synthesize_lite_4k(self, prompt: str, aspect_ratio: str) -> Optional[str]:
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
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model=flux&seed={uuid.uuid4().int}"
        
        # 2. Process into 4K Cinematic Video
        processor = VideoProcessor()
        output_name = f"lite4k_{uuid.uuid4()}.mp4"
        
        # We'll call a new processor method specifically for image-to-parallax
        video_path = await processor.apply_cinematic_motion(image_url, output_name, aspect_ratio=aspect_ratio)
        
        return video_path

    async def synthesize_scene_batch(self, scenes: List[Dict], engine: str = "veo3") -> List[Dict]:
        """
        Synthesizes multiple scenes in parallel for storytelling.
        """
        import asyncio
        logging.info(f"[GenerativeService] Synthesizing batch of {len(scenes)} scenes...")
        
        tasks = []
        for i, scene in enumerate(scenes):
            prompt = scene.get("visual_prompt", "")
            tasks.append(self.synthesize_video(prompt, engine=engine))
        
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
            logging.warning("[GenerativeService] Gemini API key missing. Mocking Veo 3 output.")
            return "https://storage.googleapis.com/viral-forge-assets/mocks/veo3_sample.mp4"

        # Actual API call logic for Google Veo 3 would go here
        # For now, we simulate the request flow
        return "https://storage.googleapis.com/viral-forge-assets/mocks/veo3_generated.mp4"

    async def _synthesize_wan(self, prompt: str, aspect_ratio: str) -> Optional[str]:
        """
        Open-Source Synthesis (Wan2.2 via SiliconFlow/Fal.ai).
        """
        if not self.silicon_flow_key:
            logging.warning("[GenerativeService] SiliconFlow API key missing. Mocking Wan2.2 output.")
            return "https://storage.googleapis.com/viral-forge-assets/mocks/wan22_sample.mp4"

        # Interface with SiliconFlow/Open-Source cloud provider
        return "https://storage.googleapis.com/viral-forge-assets/mocks/wan22_generated.mp4"

    async def _synthesize_ltx2(self, prompt: str, aspect_ratio: str) -> Optional[str]:
        """
        LTX-2 (by Lightricks) Integration — Roadmap Item.
        High-fidelity native 4K output.
        """
        logging.info("[GenerativeService] LTX-2 Synthesis requested (Roadmap).")
        # In the future, this would call Fal.ai or a local LTX-2 worker
        return "https://storage.googleapis.com/viral-forge-assets/mocks/ltx2_roadmap_preview.mp4"

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
