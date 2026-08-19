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
from typing import Any

logger = logging.getLogger(__name__)

from src.api.utils.resilience import CircuitBreaker

REPLICATE_API_URL = "https://api.replicate.com/v1"
JSON_CONTENT_TYPE = "application/json"


# Lazy check for browser automation
_playwright_available = None

def check_playwright_available():
    global _playwright_available
    if _playwright_available is None:
        try:
            import playwright
            _playwright_available = True
        except ImportError:
            _playwright_available = False
            logger.warning("[FreeVideoProvider] Playwright not installed. Browser automation fallback disabled.")
    return _playwright_available


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
            "api_url": REPLICATE_API_URL,
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
            "api_url": REPLICATE_API_URL,
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
            "api_url": REPLICATE_API_URL,
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
            "api_url": REPLICATE_API_URL,
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
        "haiper": {
            "api_url": "https://api.haiper.ai/v1",
            "free_credits": 25,  # Daily - very generous
            "max_duration": 5,
            "default_aspect": "9:16",
            "supports_image2video": True,
            "supports_audio": True,
        },
        "luma": {
            # Phase 13: migrated from the deprecated Dream Machine endpoint
            # (https://api.lumalabs.ai/dream-machine/v1) to the current
            # Luma Ray API (https://api.lumalabs.ai/v1).
            "api_url": "https://api.lumalabs.ai/v1",
            "free_credits": 15,  # Daily
            "max_duration": 9,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": False,
            "model_default": "ray-2",  # Luma Ray 2
        },
        "kaiber": {
            "api_url": "https://api.kaiber.ai/v1",
            "free_credits": 20,  # Daily
            "max_duration": 10,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": True,
        },
        "fliki": {
            "api_url": "https://api.fliki.ai/v1",
            "free_credits": 15,  # Daily
            "max_duration": 5,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": True,
        },
        "invideo": {
            "api_url": "https://api.invideo.io/v1",
            "free_credits": 20,  # Daily
            "max_duration": 10,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": False,
        },
        "morph": {
            "api_url": "https://api.morphstudio.com/v1",
            "free_credits": 10,  # Daily
            "max_duration": 6,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": False,
        },
        "genmo": {
            "api_url": "https://api.genmo.ai/v1",
            "free_credits": 15,  # Daily
            "max_duration": 8,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": False,
        },
        "leonardo": {
            "api_url": "https://api.leonardo.ai/v1",
            "free_credits": 50,  # Daily
            "max_duration": 5,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": False,
        },
        "frameloop": {
            "api_url": "https://api.frameloop.ai/v1",
            "free_credits": 20,  # Daily
            "max_duration": 8,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": True,
        },
        "wavespeed": {
            "api_url": "https://api.wavespeed.ai/v1",
            "free_credits": 25,  # Daily
            "max_duration": 15,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": True,
        },
        "ltx": {
            "api_url": "https://api.ltx.ai/v1",
            "free_credits": 15,  # Daily
            "max_duration": 20,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": True,
        },
        "videoany": {
            "api_url": "https://api.videoany.io/v1",
            "free_credits": 20,  # Daily
            "max_duration": 8,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": True,
        },
        "vidu": {
            "api_url": "https://api.vidu.ai/v1",
            "free_credits": 10,  # Trial
            "max_duration": 8,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": True,
        },
        "hailuo": {
            "api_url": "https://api.hailuoml.com/v1",
            "free_credits": 15,  # Daily
            "max_duration": 6,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": False,
        },
        "seedance": {
            "api_url": "https://api.seedance.ai/v1",
            "free_credits": 20,  # Daily
            "max_duration": 15,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": True,
        },
        "leiapix": {
            "api_url": "https://convert.leiapix.com",
            "free_credits": 0,  # Browser-automation only, no API credits needed
            "max_duration": 10,
            "default_aspect": "16:9",
            "supports_image2video": True,  # Image-to-video depth animation
            "supports_audio": False,
            "note": "Browser automation (Playwright) — image-to-video depth conversion",
        },
        "heygen": {
            "api_url": "https://api.heygen.com/v1",
            "free_credits": 3,  # Monthly
            "max_duration": 10,
            "default_aspect": "16:9",
            "supports_image2video": True,
            "supports_audio": True,
        },
    }

    def __init__(self):
        # Get primary provider from env
        self.primary_provider = os.getenv("AI_VIDEO_PROVIDER", "none").lower()
        self.enabled = self.primary_provider != "none"
        self.circuit_breaker = CircuitBreaker(recovery_timeout=300, name="FreeVideoProvider")

        # Also check for fallback providers (comma-separated list)
        fallback_str = os.getenv("AI_VIDEO_FALLBACKS", "")
        self.fallback_providers = (
            [p.strip() for p in fallback_str.split(",") if p.strip()]
            if fallback_str
            else []
        )

        # Get API keys — Phase 12 wired Runway/Pika through settings;
        # Phase 13 does the same for Luma. We fall back to os.getenv for
        # backward compatibility with deployments that still pass keys
        # via env-only.
        try:
            from src.api.config.settings import settings as _api_settings
            self.runway_key = _api_settings.RUNWAY_API_KEY or os.getenv("RUNWAY_API_KEY", "")
            self.pika_key = _api_settings.PIKA_API_KEY or os.getenv("PIKA_API_KEY", "")
            self.luma_key = _api_settings.LUMA_API_KEY or os.getenv("LUMA_API_KEY", "")
        except Exception:
            self.runway_key = os.getenv("RUNWAY_API_KEY", "")
            self.pika_key = os.getenv("PIKA_API_KEY", "")
            self.luma_key = os.getenv("LUMA_API_KEY", "")
        self.zsky_key = os.getenv("ZSKY_API_KEY", "")
        self.kling_key = os.getenv("KLING_API_KEY", "")
        self.pixverse_key = os.getenv("PIXVERSE_API_KEY", "")
        self.replicate_key = os.getenv("REPLICATE_API_KEY", "")
        self.stability_key = os.getenv("STABILITY_API_KEY", "")

        # Track available free credits (for logging)
        self._available_providers = []

        logger.info(
            f"[FreeVideoProvider] Primary: {self.primary_provider}, "
            f"Fallbacks: {self.fallback_providers}, Enabled: {self.enabled}"
        )

    def get_dependency_report(self):
        """Returns health of browser automation and API drivers."""
        p_available = check_playwright_available()
        return {
            "name": "Free Video Providers",
            "drivers": [
                {
                    "name": "playwright",
                    "installed": p_available,
                    "impact": "Browser automation fallbacks (Kling, LTX, etc.) will be disabled."
                }
            ],
            "healthy": True # Service can still use Direct APIs if playwright is missing
        }

    def get_health_report(self):
        """Returns real-time health for the dashboard."""
        status = "Healthy"
        if self.circuit_breaker.is_open():
            status = "Degraded"

        return {
            "service": "Free Video Providers",
            "status": status,
            "circuit_breaker": self.circuit_breaker.state,
            "primary": self.primary_provider
        }

    def _get_api_key(self, provider: str) -> str | None:
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
            "luma": self.luma_key,
        }
        return key_map.get(provider, "")

    def _get_all_providers(self) -> list[str]:
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
        style: str | None = None,
        image_uri: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Generate video using available free provider.
        """
        if self.circuit_breaker.is_open():
            logger.error("[FreeVideoProvider] Circuit is open. Skipping generation.")
            return None

        providers = self._get_all_providers()

        try:
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
                        provider, prompt, duration, aspect_ratio, style, image_uri, api_key
                    )
                    if result:
                        result["provider"] = provider
                        logger.info(f"[FreeVideoProvider] Success with {provider}")
                        self.circuit_breaker.record_success()
                        return result
                except Exception as e:
                    logger.warning(f"[FreeVideoProvider] {provider} failed: {e}")
                    continue

            # Fallback: Try browser automation (Playwright) when API keys are not available
            if check_playwright_available():
                logger.info("[FreeVideoProvider] All API providers failed, trying browser automation...")
                result = await self._generate_with_browser(prompt, aspect_ratio)
                if result:
                    self.circuit_breaker.record_success()
                    return result

            self.circuit_breaker.record_failure()
            logger.error("[FreeVideoProvider] All providers failed")
            return None

        except Exception:
            self.circuit_breaker.record_failure()
            logger.exception("[FreeVideoProvider] Generation exploded")
            return None

    async def _generate_with_browser(
        self, prompt: str, aspect_ratio: str
    ) -> dict[str, Any] | None:
        """
        Generate video using Playwright browser automation as fallback.
        Uses OpenCLAW skills to automate free video platform UIs.
        """
        try:
            # Try PixVerse first (easiest UI)
            from src.services.openclaw.skills.pixverse import PixVerseSkill

            skill = PixVerseSkill()
            await skill.initialize()
            result = await skill.generate(prompt, aspect_ratio=aspect_ratio)
            await skill.cleanup()

            if result and result.get("video_uri"):
                return {"video_uri": result["video_uri"], "provider": "pixverse-browser"}
        except Exception as e:
            logger.warning(f"[FreeVideoProvider] Browser fallback failed: {e}")

        return None

    async def _generate_with_provider(
        self,
        provider: str,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        style: str | None,
        image_uri: str | None,
        api_key: str,
    ) -> dict[str, Any] | None:
        """Generate video with specific provider"""
        config = self.PROVIDER_CONFIGS.get(provider)
        if not config:
            return None

        # Apply style to prompt if provided
        enhanced_prompt = self._apply_style(prompt, style)

        # Map standard providers to their respective method names
        standard_generators = {
            "zsky": "_generate_zsky",
            "kling": "_generate_kling",
            "pixverse": "_generate_pixverse",
            "stability": "_generate_stability",
            "runway": "_generate_runway",
            "pika": "_generate_pika",
            "haiper": "_generate_haiper",
            "luma": "_generate_luma",
        }

        if provider in standard_generators:
            method_name = standard_generators[provider]
            generator = getattr(self, method_name)
            if provider in ["runway", "pika"]:
                return await generator(enhanced_prompt, duration, aspect_ratio, api_key, config)
            return await generator(enhanced_prompt, duration, aspect_ratio, image_uri, api_key, config)

        if provider in ["replicate", "replicate_wan", "replicate_seedance", "replicate_hailuo"]:
            return await self._generate_replicate(
                provider,
                enhanced_prompt,
                duration,
                aspect_ratio,
                image_uri,
                api_key,
                config,
            )

        browser_providers = {
            "kaiber", "fliki", "invideo", "morph", "genmo",
            "leonardo", "frameloop", "wavespeed", "ltx", "videoany",
            "vidu", "hailuo", "seedance", "heygen", "leiapix",
        }
        if provider in browser_providers:
            return await self._generate_browser_automation(
                provider, prompt, aspect_ratio
            )

        return None

    def _apply_style(self, prompt: str, style: str | None) -> str:
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
        image_uri: str | None,
        api_key: str,
        config: dict,
    ) -> dict[str, Any] | None:
        """Generate video using ZSky AI API"""
        import httpx

        # Map aspect ratio to ZSky format
        aspect_map = {"9:16": "9:16", "16:9": "16:9", "1:1": "1:1"}
        zsky_ratio = aspect_map.get(aspect_ratio, "9:16")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": JSON_CONTENT_TYPE,
        }

        payload = {
            "prompt": prompt,
            "duration": min(duration, config["max_duration"]),
            "ratio": zsky_ratio,
        }

        if image_uri and config.get("supports_image2video"):
            payload["image_uri"] = image_uri

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
                if "video_uri" in data:
                    return {
                        "video_uri": data["video_uri"],
                        "metadata": {"model": "zsky-wan"},
                    }
                elif "task_id" in data:
                    return await self._poll_zsky_job(data["task_id"], api_key, config)

                return None

        except Exception:
            logger.exception("[FreeVideoProvider] ZSky request failed")
            return None

    async def _poll_zsky_job(
        self,
        job_id: str,
        api_key: str,
        config: dict,
        max_attempts: int = 60,
        delay: int = 5,
    ) -> dict[str, Any] | None:
        """Poll ZSky job until completion"""
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=30) as client:
            for _ in range(max_attempts):
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
                            "video_uri": data.get("video_uri"),
                            "metadata": {"model": "zsky-wan"},
                        }
                    elif status in ("failed", "cancelled"):
                        return None
                except Exception as e:
                    logger.warning(f"[FreeVideoProvider] Poll error for {job_id}: {e}")
                    await asyncio.sleep(delay)
                    continue

                await asyncio.sleep(delay)

        return None

    async def _generate_haiper(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        image_uri: str | None,
        api_key: str,
        config: dict,
    ) -> dict[str, Any] | None:
        """Generate video using Haiper AI"""
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": JSON_CONTENT_TYPE,
        }

        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "duration": min(duration, config["max_duration"]),
        }

        if image_uri and config.get("supports_image2video"):
            payload["image_uri"] = image_uri

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{config['api_url']}/generate",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(
                        f"[FreeVideoProvider] Haiper error {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()

                if "video_uri" in data:
                    return {
                        "video_uri": data["video_uri"],
                        "metadata": {"model": "haiper"},
                    }
                elif "task_id" in data:
                    return await self._poll_haiper_job(
                        data["task_id"], api_key, config
                    )
                else:
                    logger.info("[Haiper] API unavailable, falling back to browser automation")
                    from src.services.openclaw.skills.haiper import haiper_skill
                    return await haiper_skill.generate(prompt, aspect_ratio)

                return None

        except Exception:
            logger.exception("[FreeVideoProvider] Haiper request failed")
            logger.info("[Haiper] Falling back to browser automation")
            try:
                from src.services.openclaw.skills.haiper import haiper_skill
                return await haiper_skill.generate(prompt, aspect_ratio)
            except Exception:
                logger.exception("[FreeVideoProvider] Haiper browser fallback failed")
                return None

    async def _generate_luma(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        image_uri: str | None,
        api_key: str,
        config: dict,
    ) -> dict[str, Any] | None:
        """Generate video using Luma Ray API (Phase 13).

        Endpoint: POST {api_url}/generations
        Auth:     Authorization: Bearer luma-XXXXX
        Schema:   {
            "prompt": str,
            "model": "ray-2",        # Luma Ray 2
            "aspect_ratio": "16:9",  # "1:1" | "16:9" | "9:16" | "4:3" | "3:4" | "21:9" | "9:21"
            "duration": "5s",        # string in seconds with "s" suffix
            "loop": false,
            "keyframes": {            # only for image-to-video
                "frame0": {"type": "image", "url": "..."}
            }
        }
        Response: {"id": str, "state": "queued", ...}
        Poll:     GET {api_url}/generations/{id} → {"id", "state", "assets": {"video": "https://..."}}
        States:   "queued" | "dreaming" | "completed" | "failed"
        """
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": JSON_CONTENT_TYPE,
            "Accept": "application/json",
        }

        # Map our standard aspect ratios to Luma Ray's accepted set.
        # If the caller passes something Luma doesn't accept, fall back to 16:9.
        luma_aspects = {"1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"}
        luma_aspect = aspect_ratio if aspect_ratio in luma_aspects else "16:9"

        # Luma Ray 2 wants duration as a string with "s" suffix, capped to
        # config["max_duration"] seconds.
        luma_duration = f"{min(int(duration), int(config.get('max_duration', 9)))}s"

        payload: dict[str, Any] = {
            "prompt": prompt,
            "model": config.get("model_default", "ray-2"),
            "aspect_ratio": luma_aspect,
            "loop": False,
            "duration": luma_duration,
        }

        # Image-to-video: Luma Ray uses keyframes.frame0.url.
        if image_uri and config.get("supports_image2video"):
            payload["keyframes"] = {
                "frame0": {"type": "image", "url": image_uri}
            }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{config['api_url']}/generations",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200 and response.status_code != 201:
                    logger.error(
                        f"[FreeVideoProvider] Luma Ray error {response.status_code}: "
                        f"{response.text[:300]}"
                    )
                    return None

                data = response.json()

                # Immediate sync result (rare; Luma usually returns a job id).
                if "assets" in data and isinstance(data["assets"], dict):
                    video_url = data["assets"].get("video")
                    if video_url:
                        return {
                            "video_uri": video_url,
                            "metadata": {
                                "model": payload["model"],
                                "aspect_ratio": luma_aspect,
                            },
                        }

                # Standard async path: poll the job.
                if "id" in data:
                    return await self._poll_luma_job(
                        data["id"], api_key, config
                    )

                # Unknown response shape — log and return None (no Playwright
                # fallback for the API code path; user must have a real key).
                logger.warning(
                    f"[Luma Ray] Unexpected response shape (no id, no assets.video): "
                    f"{str(data)[:200]}"
                )
                return None

        except Exception:
            logger.exception("[FreeVideoProvider] Luma Ray request failed")
            return None

    async def _poll_luma_job(
        self,
        job_id: str,
        api_key: str,
        config: dict,
        max_attempts: int = 60,
        delay: int = 5,
    ) -> dict[str, Any] | None:
        """Poll a Luma Ray generation job until completion.

        GET {api_url}/generations/{id}  →  {
            "id": str,
            "state": "queued" | "dreaming" | "completed" | "failed",
            "assets": {"video": "https://...", "thumbnail": "..."},
            "failure_reason": "..."  # when state == "failed"
        }
        """
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            for _ in range(max_attempts):
                try:
                    response = await client.get(
                        f"{config['api_url']}/generations/{job_id}",
                        headers=headers,
                    )

                    if response.status_code != 200:
                        await asyncio.sleep(delay)
                        continue

                    data = response.json()
                    state = (data.get("state") or "").lower()

                    if state == "completed":
                        assets = data.get("assets") or {}
                        video_url = assets.get("video") if isinstance(assets, dict) else None
                        if not video_url:
                            logger.warning(
                                f"[Luma Ray] job {job_id} completed but no assets.video URL"
                            )
                            return None
                        return {
                            "video_uri": video_url,
                            "metadata": {
                                "model": data.get("model") or config.get("model_default", "ray-2"),
                                "aspect_ratio": data.get("aspect_ratio"),
                            },
                        }

                    if state == "failed":
                        logger.error(
                            f"[Luma Ray] job {job_id} failed: "
                            f"{data.get('failure_reason') or 'unknown'}"
                        )
                        return None

                    # queued | dreaming (or anything else) — keep polling.
                except Exception as e:
                    logger.warning(f"[FreeVideoProvider] Luma poll error for {job_id}: {e}")
                    # fall through to sleep + retry

                await asyncio.sleep(delay)

        logger.error(f"[Luma Ray] job {job_id} did not complete within {max_attempts * delay}s")
        return None

    async def _generate_browser_automation(
        self,
        provider: str,
        prompt: str,
        aspect_ratio: str = "16:9",
    ) -> dict[str, Any] | None:
        """
        Generate video using browser automation (no API key required).
        Falls back to Playwright automation for free video providers.
        """

        logger.info(f"[FreeVideoProvider] Using browser automation for {provider}")

        skill_map = {
            "kaiber": "services.openclaw.skills.kaiber",
            "fliki": "services.openclaw.skills.fliki",
            "invideo": "services.openclaw.skills.invideo",
            "morph": "services.openclaw.skills.morph",
            "genmo": "services.openclaw.skills.genmo",
            "kling": "services.openclaw.skills.kling",
            "pika": "services.openclaw.skills.pika",
            "runway": "services.openclaw.skills.runway",
            "leonardo": "services.openclaw.skills.leonardo",
            "frameloop": "services.openclaw.skills.frameloop",
            "wavespeed": "services.openclaw.skills.wavespeed",
            "ltx": "services.openclaw.skills.ltx",
            "videoany": "services.openclaw.skills.videoany",
            "vidu": "services.openclaw.skills.vidu",
            "hailuo": "services.openclaw.skills.hailuo",
            "seedance": "services.openclaw.skills.seedance",
            "heygen": "services.openclaw.skills.heygen",
            "leiapix": "services.openclaw.skills.leiapix",
        }

        try:
            if provider in skill_map:
                module = __import__(skill_map[provider], fromlist=[f"{provider}_skill"])
                skill = getattr(module, f"{provider}_skill")
                result = await skill.generate(prompt, aspect_ratio)
                return result
            return None

        except Exception:
            logger.exception(f"[FreeVideoProvider] Browser automation failed for {provider}")
            return None


# Global instance
base_free_video_provider_service = FreeVideoProviderService()
free_video_provider = base_free_video_provider_service

