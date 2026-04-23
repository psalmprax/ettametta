import asyncio
import logging
import os
from playwright.async_api import async_playwright, Browser, Page
from typing import Any
import uuid
from src.api.config import settings

from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class PixVerseSkill(OpenClawBaseSkill):
    """
    PixVerse browser automation skill - Tier 1 easiest platform
    Clean UI, predictable selectors, no login required for demo generation
    """

    def __init__(self):
        super().__init__()
        self.base_url = "https://pixverse.ai"
        self.browser: Browser | None = None
        self.page: Page | None = None

    async def execute(self, action: str = "generate", prompt: str = "", aspect_ratio: str = "9:16", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        p = prompt or kwargs.get("prompt") or kwargs.get("topic", "")
        if not p:
            return "⚠️ PixVerse failed: Missing prompt"
            
        res = await self.generate(p, aspect_ratio or kwargs.get("aspect_ratio", "9:16"))
        if res.get("status") == "success":
            return f"🎬 **PixVerse Video Generated!**\nURL: {res['video_url']}"
        return f"⚠️ PixVerse failed: {res.get('error')}"

    async def initialize(self):
        """Initialize stealth browser session"""
        playwright = await async_playwright().start()

        # Launch browser with stealth settings
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--window-size=1920,1080",
            ],
        )

        # Create context with fingerprint randomization
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        self.page = await self.context.new_page()
        self.page.set_default_timeout(60000)

        # Auto-login if credentials are available
        if settings.PIXVERSE_EMAIL and settings.PIXVERSE_PASSWORD:
            await self.login()

    async def login(self):
        """Login to PixVerse if credentials available"""
        try:
            await self.page.goto(f"{self.base_url}/login")
            await self.page.wait_for_load_state("networkidle")

            # Fill login form
            await self.page.fill('input[type="email"]', settings.PIXVERSE_EMAIL)
            await self.page.fill('input[type="password"]', settings.PIXVERSE_PASSWORD)
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_load_state("networkidle")

            logger.info("[PixVerse] Logged in successfully")
        except Exception as e:
            logger.warning(f"[PixVerse] Login failed (proceeding without login): {e}")

        self.page = await self.context.new_page()

        # Add stealth delays
        self.page.set_default_timeout(120000)

    async def generate(self, prompt: str, aspect_ratio: str = "9:16") -> dict[str, Any]:
        """
        Generate video from prompt using PixVerse
        Returns: { status: success/failed, video_url: str, error: str }
        """

        try:
            await self.initialize()

            logger.info(f"[PixVerse] Generating video: {prompt[:50]}...")

            # Navigate to homepage
            await self.page.goto(f"{self.base_url}/create")
            await self.page.wait_for_load_state("networkidle")

            # Random human delay
            await asyncio.sleep(2 + (3 * os.urandom(1)[0] / 255))

            # Fill prompt
            prompt_area = self.page.get_by_role("textbox", name="Describe your video")
            await prompt_area.click()
            await prompt_area.type(prompt, delay=50 + (50 * os.urandom(1)[0] / 255))

            await asyncio.sleep(1 + (2 * os.urandom(1)[0] / 255))

            # Select aspect ratio
            if aspect_ratio == "9:16":
                await self.page.get_by_role("button", name="Vertical (9:16)").click()
            else:
                await self.page.get_by_role("button", name="Horizontal (16:9)").click()

            await asyncio.sleep(1)

            # Click generate
            generate_btn = self.page.get_by_role("button", name="Generate")
            await generate_btn.click()

            logger.info("[PixVerse] Generation submitted, waiting for render...")

            # Wait for video to render (60-120s typical)
            await self.page.wait_for_selector("video[src]", timeout=120000)

            # Get video source
            video_element = await self.page.query_selector("video[src]")
            video_url = await video_element.get_attribute("src")

            logger.info(f"[PixVerse] Video generated successfully: {video_url[:80]}...")

            await self.cleanup()

            return {
                "status": "success",
                "video_url": video_url,
                "engine": "pixverse",
                "prompt": prompt,
            }

        except Exception as e:
            logger.error(f"[PixVerse] Generation failed: {str(e)}")
            await self.cleanup()
            return {"status": "failed", "error": str(e), "engine": "pixverse"}

    async def cleanup(self):
        """Clean up browser resources"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()


# Singleton instance
pixverse_skill = PixVerseSkill()
