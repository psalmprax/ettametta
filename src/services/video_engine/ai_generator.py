from typing import Any
"""
AI Video Generation Service - Any Tier 3 Enhancement

Integrates with AI video generation APIs (Runway, Pika) for creating clips.
Disabled by default - enable via AI_VIDEO_PROVIDER=runway or AI_VIDEO_PROVIDER=pika
"""

import os
import logging
import asyncio
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class AIVideoGeneratorService:
    """
    Any AI video generation service.
    Integrates with Runway ML and Pika Labs APIs.
    """

    PROVIDER_CONFIGS = {
        "runway": {
            "api_url": "https://api.runwayml.com/v1",
            "max_duration": 10,  # seconds
            "default_aspect": "9:16",
        },
        "pika": {
            "api_url": "https://api.pika.art/v1",
            "max_duration": 8,
            "default_aspect": "9:16",
        },
    }

    def __init__(self):
        self.provider = os.getenv("AI_VIDEO_PROVIDER", "none").lower()
        self.enabled = self.provider != "none"

        # API keys from config
        self.runway_key = os.getenv("RUNWAY_API_KEY", "")
        self.pika_key = os.getenv("PIKA_API_KEY", "")

        logger.info(
            f"[AIGenerator] Initialized - Provider: {self.provider}, Enabled: {self.enabled}"
        )

    def _get_api_key(self) -> str | None:
        """Get API key for current provider"""
        if self.provider == "runway":
            return self.runway_key
        elif self.provider == "pika":
            return self.pika_key
        return None

    async def generate_clip(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        style: str | None = None,
    ) -> str | None:
        """
        Generate AI video clip from text prompt.

        Args:
            prompt: Text description of desired video
            duration: Video length in seconds
            aspect_ratio: Video aspect ratio (9:16, 16:9, 1:1)
            style: Any style preset

        Returns:
            URL to generated video, or None if disabled/error
        """
        if not self.enabled:
            logger.debug("[AIGenerator] Disabled, skipping generation")
            return None

        api_key = self._get_api_key()
        if not api_key:
            logger.warning(f"[AIGenerator] No API key for {self.provider}")
            return None

        config = self.PROVIDER_CONFIGS.get(self.provider)
        if not config:
            logger.warning(f"[AIGenerator] Unknown provider: {self.provider}")
            return None

        logger.info(
            f"[AIGenerator] Generating clip - prompt: {prompt[:50]}..., provider: {self.provider}"
        )

        try:
            if self.provider == "runway":
                return await self._generate_runway(
                    prompt, duration, aspect_ratio, api_key
                )
            elif self.provider == "pika":
                return await self._generate_pika(
                    prompt, duration, aspect_ratio, api_key
                )

        except Exception as e:
            logger.error(f"[AIGenerator] Generation failed: {e}")
            return None

    async def _generate_runway(
        self, prompt: str, duration: int, aspect_ratio: str, api_key: str
    ) -> str | None:
        """Generate video using Runway ML API"""
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
            "duration": min(duration, 10),
            "aspect_ratio": aspect_ratio,
            "watermark": False,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.PROVIDER_CONFIGS['runway']['api_url']}/generation/text-to-video",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(
                        f"[AIGenerator] Runway API error {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()

                # Check if immediate result or async job
                if "video_uri" in data:
                    return data["video_uri"]
                elif "id" in data:
                    # Poll for completion
                    job_id = data["id"]
                    return await self._poll_runway_job(job_id, api_key)
                else:
                    logger.error(f"[AIGenerator] Unexpected Runway response: {data}")
                    return None

        except Exception as e:
            logger.error(f"[AIGenerator] Runway request failed: {e}")
            return None

    async def _poll_runway_job(
        self, job_id: str, api_key: str, max_attempts: int = 60, delay: int = 5
    ) -> str | None:
        """Poll Runway generation job until completion"""
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        f"{self.PROVIDER_CONFIGS['runway']['api_url']}/generation/{job_id}",
                        headers=headers,
                    )

                    if response.status_code != 200:
                        logger.warning(
                            f"[AIGenerator] Poll error {response.status_code}"
                        )
                        await asyncio.sleep(delay)
                        continue

                    data = response.json()
                    status = data.get("status", "").lower()

                    if status == "succeeded":
                        return data.get("video_uri")
                    elif status in ("failed", "cancelled"):
                        logger.error(f"[AIGenerator] Runway job {job_id} {status}")
                        return None

                    # Still processing
                    await asyncio.sleep(delay)

                except Exception as e:
                    logger.warning(f"[AIGenerator] Poll exception: {e}")
                    await asyncio.sleep(delay)

            logger.error(
                f"[AIGenerator] Runway job {job_id} timed out after {max_attempts} attempts"
            )
            return None

    async def _generate_pika(
        self, prompt: str, duration: int, aspect_ratio: str, api_key: str
    ) -> str | None:
        """Generate video using Pika Labs API"""
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Pika expects ratio as "9x16" format
        pika_ratio = aspect_ratio.replace(":", "x")

        payload = {"prompt": prompt, "seconds": min(duration, 8), "ratio": pika_ratio}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.PROVIDER_CONFIGS['pika']['api_url']}/generation/text-to-video",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(
                        f"[AIGenerator] Pika API error {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()

                # Check if immediate result or async job
                if "video_uri" in data:
                    return data["video_uri"]
                elif "id" in data:
                    # Poll for completion
                    job_id = data["id"]
                    return await self._poll_pika_job(job_id, api_key)
                else:
                    logger.error(f"[AIGenerator] Unexpected Pika response: {data}")
                    return None

        except Exception as e:
            logger.error(f"[AIGenerator] Pika request failed: {e}")
            return None

    async def _poll_pika_job(
        self, job_id: str, api_key: str, max_attempts: int = 60, delay: int = 5
    ) -> str | None:
        """Poll Pika generation job until completion"""
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        f"{self.PROVIDER_CONFIGS['pika']['api_url']}/generation/{job_id}",
                        headers=headers,
                    )

                    if response.status_code != 200:
                        logger.warning(
                            f"[AIGenerator] Pika poll error {response.status_code}"
                        )
                        await asyncio.sleep(delay)
                        continue

                    data = response.json()
                    status = data.get("status", "").lower()

                    if status == "completed":
                        return data.get("video_uri")
                    elif status in ("failed", "cancelled"):
                        logger.error(f"[AIGenerator] Pika job {job_id} {status}")
                        return None

                    # Still processing
                    await asyncio.sleep(delay)

                except Exception as e:
                    logger.warning(f"[AIGenerator] Pika poll exception: {e}")
                    await asyncio.sleep(delay)

            logger.error(
                f"[AIGenerator] Pika job {job_id} timed out after {max_attempts} attempts"
            )
            return None

    async def generate_intro(self, niche: str, duration: int = 3) -> str | None:
        """Generate intro clip for a niche"""
        prompt = f"Professional intro for {niche} video, cinematic, high quality"
        return await self.generate_clip(prompt, duration)

    async def generate_Outro(
        self, call_to_action: str = "Subscribe for more"
    ) -> str | None:
        """Generate outro clip with CTA"""
        prompt = (
            f"Professional outro with text '{call_to_action}', cinematic, high quality"
        )
        return await self.generate_clip(prompt, duration=3)

    def get_provider_info(self) -> dict:
        """Get information about current provider"""
        return {
            "provider": self.provider,
            "enabled": self.enabled,
            "config": self.PROVIDER_CONFIGS.get(self.provider, {}),
            "has_api_key": bool(self._get_api_key()),
        }


# Global instance
base_ai_generator_service = AIVideoGeneratorService()
