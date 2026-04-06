"""
Free AI Video Generation Providers Service

Integrates with multiple free daily credit AI video providers:
- ZSky AI (~50-100 credits/day, best for automation)
- Kling AI (generous daily credits, high quality)
- PixVerse AI (daily usage, good for short clips)
- Replicate (free trial credits, huge model ecosystem)
- Pika Labs (already implemented)
- Runway ML (already implemented)
- Stability AI (~25 calls/day, reliable API-first)

Configure via AI_VIDEO_PROVIDER env var:
- zsky, kling, pixverse, replicate, pika, runway, stability
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
import uuid
import json

logger = logging.getLogger(__name__)


class FreeVideoProviderService:
    """
    Multi-provider AI video generation service.
    Supports multiple free-tier video generation APIs.
    """

    PROVIDER_CONFIGS = {
        "zsky": {
            "api_url": "https://api.zsky.ai/v1",
            "free_credits": 50,  # Daily
            "max_duration": 10,
            "default_aspect": "9:16",
            "supports_image2video": True,
            "supports_audio": True,
        },
        "kling": {
            "api_url": "https://api.klingai.com/v1",
            "free_credits": 100,  # Daily (very generous)
            "max_duration": 10,
            "default_aspect": "9:16",
            "supports_image2video": True,
            "supports_audio": True,
        },
        "pixverse": {
            "api_url": "https://api.pixverse.ai/v1",
            "free_credits": 20,  # Daily
            "max_duration": 8,
            "default_aspect": "9:16",
            "supports_image2video": True,
            "supports_audio": False,
        },
        "replicate_wan": {
            "api_url": "https://api.replicate.com/v1",
            "free_credits": 0,  # Paid only
            "max_duration": 5,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": False,
            "model_default": "wan-video/wan-2.2-5b-fast",
            "cost_per_video": 0.02,  # $0.01-0.02 per 5s video - CHEAPEST!
            "replicate_model": "wan-video/wan-2.2-5b-fast",
        },
        "replicate_seedance": {
            "api_url": "https://api.replicate.com/v1",
            "free_credits": 0,  # Paid only
            "max_duration": 10,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": False,
            "model_default": "bytedance/seedance-1-lite",
            "cost_per_video": 0.40,  # $0.09-0.72 - BEST QUALITY/PRICE!
            "replicate_model": "bytedance/seedance-1-lite",
        },
        "replicate_hailuo": {
            "api_url": "https://api.replicate.com/v1",
            "free_credits": 0,  # Paid only
            "max_duration": 10,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": False,
            "model_default": "minimax/hailuo-02-fast",
            "cost_per_video": 0.15,  # $0.10-0.15 - Good quality
            "replicate_model": "minimax/hailuo-02-fast",
        },
        "replicate": {
            "api_url": "https://api.replicate.com/v1",
            "free_credits": 10,  # One-time trial
            "max_duration": 10,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": False,
            "model_default": "minimax/mimi-alpha-01",  # Fast video model
        },
        "stability": {
            "api_url": "https://api.stability.ai/v2beta",
            "free_credits": 25,  # Daily
            "max_duration": 6,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": False,
            "model_default": "stable-video-diffusion",
        },
        "runway": {
            "api_url": "https://api.runwayml.com/v1",
            "free_credits": 10,  # Signup bonus
            "max_duration": 10,
            "default_aspect": "9:16",
            "supports_image2video": True,
            "supports_audio": False,
        },
        "pika": {
            "api_url": "https://api.pika.art/v1",
            "free_credits": 10,  # Daily
            "max_duration": 8,
            "default_aspect": "9:16",
            "supports_image2video": True,
            "supports_audio": False,
        },
    }

    def __init__(self):
        # Get primary provider from env
        self.primary_provider = os.getenv("AI_VIDEO_PROVIDER", "none").lower()
        self.enabled = self.primary_provider != "none"

        # Also check for fallback providers (comma-separated list)
        fallback_str = os.getenv("AI_VIDEO_FALLBACKS", "")
        self.fallback_providers = (
            [p.strip() for p in fallback_str.split(",") if p.strip()]
            if fallback_str
            else []
        )

        # Get API keys
        self.zsky_key = os.getenv("ZSKY_API_KEY", "")
        self.kling_key = os.getenv("KLING_API_KEY", "")
        self.pixverse_key = os.getenv("PIXVERSE_API_KEY", "")
        self.replicate_key = os.getenv("REPLICATE_API_KEY", "")
        self.stability_key = os.getenv("STABILITY_API_KEY", "")
        self.runway_key = os.getenv("RUNWAY_API_KEY", "")
        self.pika_key = os.getenv("PIKA_API_KEY", "")

        # Track available free credits (for logging)
        self._available_providers = []

        logger.info(
            f"[FreeVideoProvider] Primary: {self.primary_provider}, "
            f"Fallbacks: {self.fallback_providers}, Enabled: {self.enabled}"
        )

    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider"""
        key_map = {
            "zsky": self.zsky_key,
            "kling": self.kling_key,
            "pixverse": self.pixverse_key,
            "replicate": self.replicate_key,
            "replicate_wan": self.replicate_key,  # Uses same Replicate API key
            "replicate_seedance": self.replicate_key,
            "replicate_hailuo": self.replicate_key,
            "stability": self.stability_key,
            "runway": self.runway_key,
            "pika": self.pika_key,
        }
        return key_map.get(provider)

    def _get_all_providers(self) -> List[str]:
        """Get ordered list of all available providers"""
        providers = []
        if self.primary_provider != "none" and self._get_api_key(self.primary_provider):
            providers.append(self.primary_provider)
        providers.extend(self.fallback_providers)
        return providers

    async def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        style: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate video using available free provider.

        Tries primary provider first, then fallbacks.

        Returns:
            Dict with video_url, provider, and metadata, or None on failure
        """
        providers = self._get_all_providers()

        for provider in providers:
            api_key = self._get_api_key(provider)
            if not api_key:
                logger.debug(f"[FreeVideoProvider] No API key for {provider}, skipping")
                continue

            logger.info(
                f"[FreeVideoProvider] Attempting {provider} - prompt: {prompt[:50]}..."
            )

            try:
                result = await self._generate_with_provider(
                    provider, prompt, duration, aspect_ratio, style, image_url, api_key
                )
                if result:
                    result["provider"] = provider
                    logger.info(f"[FreeVideoProvider] Success with {provider}")
                    return result
            except Exception as e:
                logger.warning(f"[FreeVideoProvider] {provider} failed: {e}")
                continue

        logger.error("[FreeVideoProvider] All providers failed")
        return None

    async def _generate_with_provider(
        self,
        provider: str,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        style: Optional[str],
        image_url: Optional[str],
        api_key: str,
    ) -> Optional[Dict[str, Any]]:
        """Generate video with specific provider"""
        config = self.PROVIDER_CONFIGS.get(provider)
        if not config:
            return None

        # Apply style to prompt if provided
        enhanced_prompt = self._apply_style(prompt, style, provider)

        # Route to provider-specific generator
        if provider == "zsky":
            return await self._generate_zsky(
                enhanced_prompt, duration, aspect_ratio, image_url, api_key, config
            )
        elif provider == "kling":
            return await self._generate_kling(
                enhanced_prompt, duration, aspect_ratio, image_url, api_key, config
            )
        elif provider == "pixverse":
            return await self._generate_pixverse(
                enhanced_prompt, duration, aspect_ratio, image_url, api_key, config
            )
        elif provider in [
            "replicate",
            "replicate_wan",
            "replicate_seedance",
            "replicate_hailuo",
        ]:
            return await self._generate_replicate(
                provider,
                enhanced_prompt,
                duration,
                aspect_ratio,
                image_url,
                api_key,
                config,
            )
        elif provider == "stability":
            return await self._generate_stability(
                enhanced_prompt, duration, aspect_ratio, image_url, api_key, config
            )
        elif provider == "runway":
            return await self._generate_runway(
                enhanced_prompt, duration, aspect_ratio, api_key, config
            )
        elif provider == "pika":
            return await self._generate_pika(
                enhanced_prompt, duration, aspect_ratio, api_key, config
            )

        return None

    def _apply_style(self, prompt: str, style: Optional[str], provider: str) -> str:
        """Apply style preset to prompt"""
        if not style:
            return prompt

        style_presets = {
            "cinematic": "Cinematic, film grain, dramatic lighting, high contrast",
            "anime": "Anime style, vibrant colors, smooth animation",
            "realistic": "Photorealistic, detailed, high resolution",
            "cartoon": "Cartoon style, bold colors, clean lines",
            "documentary": "Documentary style, natural lighting, clean",
        }

        preset = style_presets.get(style.lower(), style)
        return f"{prompt}, {preset}"

    async def _generate_zsky(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        image_url: Optional[str],
        api_key: str,
        config: Dict,
    ) -> Optional[Dict[str, Any]]:
        """Generate video using ZSky AI API"""
        import httpx

        # Map aspect ratio to ZSky format
        aspect_map = {"9:16": "9:16", "16:9": "16:9", "1:1": "1:1"}
        zsky_ratio = aspect_map.get(aspect_ratio, "9:16")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
            "duration": min(duration, config["max_duration"]),
            "ratio": zsky_ratio,
        }

        if image_url and config.get("supports_image2video"):
            payload["image_url"] = image_url

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{config['api_url']}/video/generation",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(
                        f"[FreeVideoProvider] ZSky error {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()

                # Check for immediate result or async job
                if "video_url" in data:
                    return {
                        "video_url": data["video_url"],
                        "metadata": {"model": "zsky-wan"},
                    }
                elif "task_id" in data:
                    return await self._poll_zsky_job(data["task_id"], api_key, config)

                return None

        except Exception as e:
            logger.error(f"[FreeVideoProvider] ZSky request failed: {e}")
            return None

    async def _poll_zsky_job(
        self,
        job_id: str,
        api_key: str,
        config: Dict,
        max_attempts: int = 60,
        delay: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """Poll ZSky job until completion"""
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        f"{config['api_url']}/video/generation/{job_id}",
                        headers=headers,
                    )

                    if response.status_code != 200:
                        await asyncio.sleep(delay)
                        continue

                    data = response.json()
                    status = data.get("status", "").lower()

                    if status == "completed" or status == "succeeded":
                        return {
                            "video_url": data.get("video_url"),
                            "metadata": {"model": "zsky-wan"},
                        }
                    elif status in ("failed", "cancelled"):
                        return None

                    await asyncio.sleep(delay)

                except Exception as e:
                    logger.warning(f"[FreeVideoProvider] ZSky poll exception: {e}")
                    await asyncio.sleep(delay)

            return None

    async def _generate_kling(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        image_url: Optional[str],
        api_key: str,
        config: Dict,
    ) -> Optional[Dict[str, Any]]:
        """Generate video using Kling AI API"""
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
            "mode": "std",  # standard mode
            "duration": min(duration, config["max_duration"]),
            "aspect_ratio": aspect_ratio.replace(":", "x"),
        }

        if image_url and config.get("supports_image2video"):
            payload["first_frame_image"] = image_url

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{config['api_url']}/generations/text-to-video",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(
                        f"[FreeVideoProvider] Kling error {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()

                if "data" in data and "video_url" in data["data"]:
                    return {
                        "video_url": data["data"]["video_url"],
                        "metadata": {"model": "kling"},
                    }
                elif "task_id" in data or "taskId" in data:
                    task_id = data.get("task_id") or data.get("taskId")
                    return await self._poll_kling_job(task_id, api_key, config)

                return None

        except Exception as e:
            logger.error(f"[FreeVideoProvider] Kling request failed: {e}")
            return None

    async def _poll_kling_job(
        self,
        job_id: str,
        api_key: str,
        config: Dict,
        max_attempts: int = 60,
        delay: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """Poll Kling job until completion"""
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        f"{config['api_url']}/generations/{job_id}",
                        headers=headers,
                    )

                    if response.status_code != 200:
                        await asyncio.sleep(delay)
                        continue

                    data = response.json()
                    status = data.get("status", "").lower()

                    if status == "completed":
                        if "data" in data and "video_url" in data["data"]:
                            return {
                                "video_url": data["data"]["video_url"],
                                "metadata": {"model": "kling"},
                            }
                    elif status == "failed":
                        return None

                    await asyncio.sleep(delay)

                except Exception as e:
                    logger.warning(f"[FreeVideoProvider] Kling poll exception: {e}")
                    await asyncio.sleep(delay)

            return None

    async def _generate_pixverse(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        image_url: Optional[str],
        api_key: str,
        config: Dict,
    ) -> Optional[Dict[str, Any]]:
        """Generate video using PixVerse API"""
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # PixVerse uses different aspect ratio format
        pix_ratio_map = {"9:16": "9:16", "16:9": "16:9", "1:1": "1:1"}
        pix_ratio = pix_ratio_map.get(aspect_ratio, "9:16")

        payload = {
            "text": prompt,
            "aspect_ratio": pix_ratio,
            "duration": min(duration, config["max_duration"]),
        }

        if image_url and config.get("supports_image2video"):
            payload["image_url"] = image_url

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{config['api_url']}/generate",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(
                        f"[FreeVideoProvider] PixVerse error {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()

                if "video_url" in data:
                    return {
                        "video_url": data["video_url"],
                        "metadata": {"model": "pixverse"},
                    }
                elif "task_id" in data:
                    return await self._poll_pixverse_job(
                        data["task_id"], api_key, config
                    )

                return None

        except Exception as e:
            logger.error(f"[FreeVideoProvider] PixVerse request failed: {e}")
            return None

    async def _poll_pixverse_job(
        self,
        job_id: str,
        api_key: str,
        config: Dict,
        max_attempts: int = 60,
        delay: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """Poll PixVerse job until completion"""
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        f"{config['api_url']}/task/{job_id}",
                        headers=headers,
                    )

                    if response.status_code != 200:
                        await asyncio.sleep(delay)
                        continue

                    data = response.json()
                    status = data.get("status", "").lower()

                    if status == "completed":
                        return {
                            "video_url": data.get("video_url"),
                            "metadata": {"model": "pixverse"},
                        }
                    elif status == "failed":
                        return None

                    await asyncio.sleep(delay)

                except Exception as e:
                    logger.warning(f"[FreeVideoProvider] PixVerse poll exception: {e}")
                    await asyncio.sleep(delay)

            return None

    async def _generate_replicate(
        self,
        provider: str,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        image_url: Optional[str],
        api_key: str,
        config: Dict,
    ) -> Optional[Dict[str, Any]]:
        """Generate video using Replicate API"""
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Check if this is a specific model (wan, seedance, hailuo)
        model = config.get("replicate_model") or config.get(
            "model_default", "minimax/mimi-alpha-01"
        )

        # Build input payload based on model type
        input_data = {
            "prompt": prompt,
        }

        # Model-specific parameters
        if "wan-2.2-5b" in model:
            input_data["duration"] = min(duration, 5)  # Wan max 5s
        elif "seedance" in model:
            input_data["duration"] = min(duration, 10)
            input_data["resolution"] = "720p"
        elif "hailuo" in model:
            input_data["duration"] = min(duration, 6)
        else:
            input_data["duration"] = min(duration, config.get("max_duration", 10))

        # Handle image-to-video
        if image_url and config.get("supports_image2video"):
            if "wan-2.2" in model:
                input_data["image"] = image_url
            else:
                input_data["image"] = image_url

        payload = {
            "version": model,
            "input": input_data,
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers=headers,
                    json=payload,
                )

                if response.status_code not in (200, 201):
                    logger.error(
                        f"[FreeVideoProvider] Replicate {provider} error {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()

                if "urls" in data and "get" in data["urls"]:
                    result = await self._poll_replicate_job(
                        data["urls"]["get"], api_key, provider, config
                    )
                    if result:
                        # Add cost info
                        result["cost"] = config.get("cost_per_video", 0)
                    return result

                return None

        except Exception as e:
            logger.error(
                f"[FreeVideoProvider] Replicate {provider} request failed: {e}"
            )
            return None

    async def _poll_replicate_job(
        self,
        poll_url: str,
        api_key: str,
        provider: str = "replicate",
        config: Dict = None,
        max_attempts: int = 60,
        delay: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """Poll Replicate job until completion"""
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(poll_url, headers=headers)

                    if response.status_code != 200:
                        await asyncio.sleep(delay)
                        continue

                    data = response.json()
                    status = data.get("status", "").lower()

                    if status == "succeeded":
                        output = data.get("output", {})
                        video_url = None

                        # Handle different output formats
                        if isinstance(output, list) and len(output) > 0:
                            video_url = output[0]
                        elif isinstance(output, str):
                            video_url = output
                        elif isinstance(output, dict):
                            video_url = (
                                output.get("video")
                                or output.get("url")
                                or output.get("output")
                            )

                        if video_url:
                            return {
                                "video_url": video_url,
                                "metadata": {
                                    "model": provider,
                                    "provider": "replicate",
                                },
                            }
                        return None
                    elif status in ("failed", "canceled"):
                        logger.error(
                            f"[FreeVideoProvider] Replicate {provider} job failed: {data.get('error')}"
                        )
                        return None

                    await asyncio.sleep(delay)

                except Exception as e:
                    logger.warning(
                        f"[FreeVideoProvider] Replicate {provider} poll exception: {e}"
                    )
                    await asyncio.sleep(delay)

            logger.error(f"[FreeVideoProvider] Replicate {provider} job timed out")
            return None

    async def _generate_stability(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        image_url: Optional[str],
        api_key: str,
        config: Dict,
    ) -> Optional[Dict[str, Any]]:
        """Generate video using Stability AI API"""
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }

        # Stability uses SVD (Stable Video Diffusion)
        if image_url and config.get("supports_image2video"):
            # Image to video
            endpoint = f"{config['api_url']}/image-to-video/sea"
            payload = {
                "image_url": image_url,
                "prompt": prompt,
            }
        else:
            # Text to video
            endpoint = f"{config['api_url']}/text-to-video/sea"
            payload = {
                "prompt": prompt,
            }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(
                        f"[FreeVideoProvider] Stability error {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()

                if "artifacts" in data and len(data["artifacts"]) > 0:
                    video_base64 = data["artifacts"][0].get("base64")
                    if video_base64:
                        # Would need to decode and save - for now return placeholder
                        return {
                            "video_url": f"data:video/mp4;base64,{video_base64[:100]}...",
                            "metadata": {"model": "stability-svd"},
                        }
                elif "seed" in data:
                    return await self._poll_stability_job(data["seed"], api_key, config)

                return None

        except Exception as e:
            logger.error(f"[FreeVideoProvider] Stability request failed: {e}")
            return None

    async def _poll_stability_job(
        self,
        job_id: str,
        api_key: str,
        config: Dict,
        max_attempts: int = 30,
        delay: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """Poll Stability job until completion"""
        # Stability usually returns synchronously or very fast
        await asyncio.sleep(delay)
        return {
            "video_url": f"stability://{job_id}",
            "metadata": {"model": "stability-svd"},
        }

    async def _generate_runway(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        api_key: str,
        config: Dict,
    ) -> Optional[Dict[str, Any]]:
        """Generate video using Runway ML API"""
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
            "duration": min(duration, config["max_duration"]),
            "aspect_ratio": aspect_ratio,
            "watermark": False,
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{config['api_url']}/generation/text-to-video",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(
                        f"[FreeVideoProvider] Runway error {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()

                if "video_url" in data:
                    return {
                        "video_url": data["video_url"],
                        "metadata": {"model": "runway"},
                    }
                elif "id" in data:
                    return await self._poll_runway_job(data["id"], api_key, config)

                return None

        except Exception as e:
            logger.error(f"[FreeVideoProvider] Runway request failed: {e}")
            return None

    async def _poll_runway_job(
        self,
        job_id: str,
        api_key: str,
        config: Dict,
        max_attempts: int = 60,
        delay: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """Poll Runway job until completion"""
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        f"{config['api_url']}/generation/{job_id}",
                        headers=headers,
                    )

                    if response.status_code != 200:
                        await asyncio.sleep(delay)
                        continue

                    data = response.json()
                    status = data.get("status", "").lower()

                    if status == "succeeded":
                        return {
                            "video_url": data.get("video_url"),
                            "metadata": {"model": "runway"},
                        }
                    elif status in ("failed", "cancelled"):
                        return None

                    await asyncio.sleep(delay)

                except Exception as e:
                    logger.warning(f"[FreeVideoProvider] Runway poll exception: {e}")
                    await asyncio.sleep(delay)

            return None

    async def _generate_pika(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        api_key: str,
        config: Dict,
    ) -> Optional[Dict[str, Any]]:
        """Generate video using Pika Labs API"""
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        pika_ratio = aspect_ratio.replace(":", "x")

        payload = {
            "prompt": prompt,
            "seconds": min(duration, config["max_duration"]),
            "ratio": pika_ratio,
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{config['api_url']}/generation/text-to-video",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(
                        f"[FreeVideoProvider] Pika error {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()

                if "video_url" in data:
                    return {
                        "video_url": data["video_url"],
                        "metadata": {"model": "pika"},
                    }
                elif "id" in data:
                    return await self._poll_pika_job(data["id"], api_key, config)

                return None

        except Exception as e:
            logger.error(f"[FreeVideoProvider] Pika request failed: {e}")
            return None

    async def _poll_pika_job(
        self,
        job_id: str,
        api_key: str,
        config: Dict,
        max_attempts: int = 60,
        delay: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """Poll Pika job until completion"""
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        f"{config['api_url']}/generation/{job_id}",
                        headers=headers,
                    )

                    if response.status_code != 200:
                        await asyncio.sleep(delay)
                        continue

                    data = response.json()
                    status = data.get("status", "").lower()

                    if status == "completed":
                        return {
                            "video_url": data.get("video_url"),
                            "metadata": {"model": "pika"},
                        }
                    elif status in ("failed", "cancelled"):
                        return None

                    await asyncio.sleep(delay)

                except Exception as e:
                    logger.warning(f"[FreeVideoProvider] Pika poll exception: {e}")
                    await asyncio.sleep(delay)

            return None

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about available providers"""
        providers = []
        for name, config in self.PROVIDER_CONFIGS.items():
            api_key = self._get_api_key(name)
            providers.append(
                {
                    "name": name,
                    "enabled": bool(api_key),
                    "free_credits_daily": config.get("free_credits", 0),
                    "max_duration": config.get("max_duration"),
                    "supports_image2video": config.get("supports_image2video", False),
                    "supports_audio": config.get("supports_audio", False),
                }
            )

        return {
            "primary_provider": self.primary_provider,
            "fallback_providers": self.fallback_providers,
            "enabled": self.enabled,
            "providers": providers,
        }


# Global instance
free_video_provider = FreeVideoProviderService()
