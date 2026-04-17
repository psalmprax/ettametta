import asyncio
import logging
import os
from playwright.async_api import async_playwright, Browser, Page
from typing import Any

logger = logging.getLogger(__name__)


class GenmoSkill:
    """
    Genmo browser automation skill - Tier 2 moderate
    Creative AI video generation platform
    """

    def __init__(self):
        self.base_url = "https://genmo.ai"
        self.browser: Browser | None = None
        self.page: Page | None = None

    async def initialize(self):
        """Initialize stealth browser session"""
        playwright = await async_playwright().start()

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

        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        )

        self.page = await self.context.new_page()
        self.page.set_default_timeout(120000)

    async def generate(self, prompt: str, aspect_ratio: str = "16:9") -> dict[str, Any]:
        """
        Generate video from prompt using Genmo
        Returns: { status: success/failed, video_url: str, error: str }
        """

        try:
            await self.initialize()

            logger.info(f"[Genmo] Generating video: {prompt[:50]}...")

            await self.page.goto(f"{self.base_url}/create")
            await self.page.wait_for_load_state("networkidle")

            await asyncio.sleep(2 + (3 * os.urandom(1)[0] / 255))

            prompt_area = self.page.get_by_role("textbox")
            if await prompt_area.count() > 0:
                await prompt_area.first.click()
                await prompt_area.first.type(
                    prompt, delay=50 + (50 * os.urandom(1)[0] / 255)
                )
            else:
                textareas = self.page.locator("textarea")
                await textareas.first.click()
                await textareas.first.type(
                    prompt, delay=50 + (50 * os.urandom(1)[0] / 255)
                )

            await asyncio.sleep(1 + (2 * os.urandom(1)[0] / 255))

            generate_btn = self.page.get_by_role(
                "button",
                name=lambda x: "Generate" in x or "Create" in x or "Video" in x,
            )
            await generate_btn.click()

            logger.info("[Genmo] Generation submitted, waiting for render...")

            await self.page.wait_for_timeout(45000)

            video_element = await self.page.query_selector("video")
            if not video_element:
                video_element = await self.page.query_selector(
                    "[class*='video'] video, [class*='player'] video"
                )

            video_url = None
            if video_element:
                video_url = await video_element.get_attribute("src")

            logger.info(
                f"[Genmo] Video generated: {video_url[:80] if video_url else 'N/A'}..."
            )

            await self.cleanup()

            return {
                "status": "success" if video_url else "processing",
                "video_url": video_url or "",
                "engine": "genmo",
                "prompt": prompt,
            }

        except Exception as e:
            logger.error(f"[Genmo] Generation failed: {str(e)}")
            await self.cleanup()
            return {"status": "failed", "error": str(e), "engine": "genmo"}

    async def cleanup(self):
        """Clean up browser resources"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()


genmo_skill = GenmoSkill()
