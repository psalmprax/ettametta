"""
100% Free ($0 Cost) Video & B-Roll Generation Service
=====================================================
Combines Pollinations.ai free open generative API ($0 cost, zero API keys required)
with Coverr & Mixkit free video stock APIs to generate high-definition studio B-roll
and visual assets locally without any subscription fees.
"""

import os
import json
import logging
import random
import urllib.parse
import httpx
import aiofiles
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("FreeVideoService")


class FreeVideoAsset(BaseModel):
    asset_id: str
    prompt: str
    media_url: str
    local_path: Optional[str] = None
    provider: str  # "pollinations", "coverr", "mixkit", "local"
    cost_usd: float = 0.0  # Always $0.00


class FreeVideoService:
    """
    Zero-cost video synthesis and studio B-roll engine.
    """

    def __init__(self):
        self.pollinations_base_url = "https://image.pollinations.ai/prompt"
        self.coverr_base_url = "https://coverr.co/api/videos"
        self.mixkit_base_url = "https://api.mixkit.co/videos/preview"
        self.output_dir = "data/storage/outputs/free_broll"
        os.makedirs(self.output_dir, exist_ok=True)

    def enhance_prompt_free(self, prompt: str, style: str = "cinematic") -> str:
        """
        Local prompt enhancer converting raw text into 4K studio cinematography prompts at $0 cost.
        """
        raw = str(prompt or "").strip()
        if not raw:
            return "cinematic studio product shot 4k portrait volumetric lighting bokeh 60fps"

        cinematic_tags = [
            "4k resolution",
            "cinematic studio lighting",
            "macro camera movement",
            "60fps smooth motion",
            "shallow depth of field",
            "bokeh effect",
        ]

        if style == "tech":
            cinematic_tags.extend(["dark glass reflection", "neon cyan accents"])
        elif style == "product":
            cinematic_tags.extend(["turn table rotation", "studio backdrop"])
        elif style == "luxury":
            cinematic_tags.extend(["golden hour warm glow", "high contrast elegance"])

        enhanced = f"{raw}, {', '.join(cinematic_tags)}"
        return enhanced

    def get_pollinations_free_url(
        self,
        prompt: str,
        width: int = 1080,
        height: int = 1920,
        seed: Optional[int] = None,
    ) -> str:
        """
        Generates a 100% free AI visual URL using Pollinations.ai open API (no API key required).
        """
        enhanced = self.enhance_prompt_free(prompt)
        encoded_prompt = urllib.parse.quote(enhanced)
        chosen_seed = seed or random.randint(1000, 999999)
        url = f"{self.pollinations_base_url}/{encoded_prompt}?width={width}&height={height}&seed={chosen_seed}&nologo=true"
        return url

    async def fetch_free_broll_clip(self, keyword: str, count: int = 1) -> list[FreeVideoAsset]:
        """
        Retrieves 100% free stock or AI B-roll assets ($0 cost).
        Priority: Pollinations AI Visual ($0) -> Coverr Free 1080p ($0) -> Local Fallback ($0)
        """
        assets: list[FreeVideoAsset] = []
        kw_clean = str(keyword or "abstract").strip()

        try:
            # 1. Try Coverr Free API ($0 cost)
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.coverr_base_url, params={"query": kw_clean})
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    for item in results[:count]:
                        videos = item.get("videos", [])
                        if videos:
                            best_v = next((v for v in videos if v.get("width") == 1920), videos[0])
                            video_url = best_v.get("url")
                            if video_url:
                                assets.append(
                                    FreeVideoAsset(
                                        asset_id=f"coverr_{os.urandom(4).hex()}",
                                        prompt=kw_clean,
                                        media_url=video_url,
                                        provider="coverr",
                                        cost_usd=0.0,
                                    )
                                )
        except Exception as e:
            logger.warning(f"[FreeVideoService] Coverr free search skipped: {e}")

        # 2. If no stock video found, generate Pollinations.ai free visual ($0 cost)
        if not assets:
            for i in range(count):
                pollinations_url = self.get_pollinations_free_url(kw_clean)
                assets.append(
                    FreeVideoAsset(
                        asset_id=f"pollinations_{os.urandom(4).hex()}",
                        prompt=kw_clean,
                        media_url=pollinations_url,
                        provider="pollinations",
                        cost_usd=0.0,
                    )
                )

        return assets

    async def download_asset_locally(self, asset: FreeVideoAsset) -> Optional[str]:
        """
        Downloads a free media asset locally for Remotion rendering or MoviePy processing.
        """
        ext = ".jpg" if asset.provider == "pollinations" else ".mp4"
        filename = f"{asset.asset_id}{ext}"
        filepath = os.path.abspath(os.path.join(self.output_dir, filename))

        if os.path.exists(filepath):
            asset.local_path = filepath
            return filepath

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(asset.media_url, follow_redirects=True)
                if resp.status_code == 200:
                    async with aiofiles.open(filepath, "wb") as f:
                        await f.write(resp.content)
                    asset.local_path = filepath
                    return filepath
        except Exception as e:
            logger.error(f"[FreeVideoService] Error downloading free asset: {e}")

        return None


base_free_video_service = FreeVideoService()
