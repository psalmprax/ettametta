import asyncio
import logging
from .base_skill import OpenClawBaseSkill
import os
from playwright.async_api import async_playwright, Browser, Page
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class LeiaPixSkill(OpenClawBaseSkill):
    """
    LeiaPix browser automation skill - Image to video conversion
    VERY easy automation, perfect for image -> video pipeline
    """

    def __init__(self):
        super().__init__()
        self.base_url = "https://convert.leiapix.com"

    async def execute(self, action: str = "generate", prompt: str = "", aspect_ratio: str = "9:16", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        p = prompt or kwargs.get("prompt") or kwargs.get("topic", "")
        if not p:
            return f"⚠️ {self.__class__.__name__} failed: Missing prompt"
            
        res = await self.generate(p, aspect_ratio or kwargs.get("aspect_ratio", "9:16"))
        if res.get("status") == "success":
            return f"🎬 **{self.__class__.__name__} Video Generated!**\nURL: {res.get('video_uri')}"
        return f"⚠️ {self.__class__.__name__} failed: {res.get('error')}"

    async def generate(
        self, image_uri: str, motion_intensity: int = 5
    ) -> dict[str, Any]:
        """
        Convert image to motion video using LeiaPix
        """

        try:
            playwright = await async_playwright().start()

            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--window-size=1920,1080",
                ],
            )

            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            )

            page = await context.new_page()
            page.set_default_timeout(120000)

            logger.info(f"[LeiaPix] Converting image to video: {image_uri[:50]}...")

            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")

            await asyncio.sleep(1.5 + (1.5 * os.urandom(1)[0] / 255))

            # Upload image
            await page.get_by_role("button", name="Upload Image").click()
            await asyncio.sleep(0.8)

            file_input = await page.query_selector('input[type="file"]')
            await file_input.set_input_files(image_uri)

            await asyncio.sleep(2 + (1 * os.urandom(1)[0] / 255))

            # Set motion intensity
            await page.get_by_role("slider").fill(str(motion_intensity))

            await asyncio.sleep(0.5)

            # Click animate
            await page.get_by_role("button", name="Animate").click()

            logger.info("[LeiaPix] Animation submitted, waiting for render...")

            await page.wait_for_selector("video[src]", timeout=90000)

            video_element = await page.query_selector("video[src]")
            video_uri = await video_element.get_attribute("src")

            logger.info(f"[LeiaPix] Video generated successfully")

            await browser.close()
            await playwright.stop()

            return {
                "status": "success",
                "video_uri": video_uri,
                "engine": "leiapix",
                "input_image": image_uri,
            }

        except Exception as e:
            logger.error(f"[LeiaPix] Generation failed: {str(e)}")
            return {"status": "failed", "error": str(e), "engine": "leiapix"}


leiapix_skill = LeiaPixSkill()
