import asyncio
import logging
import os
from playwright.async_api import async_playwright, Browser, Page
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class HaiperSkill:
    """
    Haiper AI browser automation skill - Tier 1 easiest target
    Clean UI, no login required for demo generation, very predictable selectors
    """

    def __init__(self):
        self.base_url = "https://haiper.ai"

    async def generate(self, prompt: str, aspect_ratio: str = "9:16") -> dict[str, Any]:
        """
        Generate video from prompt using Haiper AI
        """

        try:
            playwright = await async_playwright().start()

            # Launch stealth browser
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

            logger.info(f"[Haiper] Generating video: {prompt[:50]}...")

            await page.goto(f"{self.base_url}/create")
            await page.wait_for_load_state("networkidle")

            # Random human delay
            await asyncio.sleep(1.5 + (2 * os.urandom(1)[0] / 255))

            # Fill prompt
            prompt_area = page.get_by_role("textbox", name="Describe your video")
            await prompt_area.click()
            await prompt_area.type(prompt, delay=40 + (30 * os.urandom(1)[0] / 255))

            await asyncio.sleep(1)

            # Select aspect ratio
            if aspect_ratio == "9:16":
                await page.get_by_role("button", name="Vertical").click()
            else:
                await page.get_by_role("button", name="Horizontal").click()

            await asyncio.sleep(0.8)

            # Click generate
            await page.get_by_role("button", name="Generate").click()

            logger.info("[Haiper] Generation submitted, waiting for render...")

            # Wait for video element
            await page.wait_for_selector("video[src]", timeout=120000)

            video_element = await page.query_selector("video[src]")
            video_url = await video_element.get_attribute("src")

            logger.info(f"[Haiper] Video generated successfully")

            await browser.close()
            await playwright.stop()

            return {
                "status": "success",
                "video_url": video_url,
                "engine": "haiper",
                "prompt": prompt,
            }

        except Exception as e:
            logger.error(f"[Haiper] Generation failed: {str(e)}")
            return {"status": "failed", "error": str(e), "engine": "haiper"}


haiper_skill = HaiperSkill()
