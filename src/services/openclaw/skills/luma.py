import asyncio
import logging
import os
from typing import Optional, Dict, Any
import uuid

logger = logging.getLogger(__name__)

# Optional dependency
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("[Luma] Playwright not installed. Browser automation disabled.")


class LumaSkill:
    """
    Luma Dream Machine browser automation skill - Tier 1 easiest target
    Very clean UI, predictable flow, no login required
    """

    def __init__(self):
        self.base_url = "https://lumalabs.ai/dream-machine"

    async def generate(self, prompt: str, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        """
        Generate video from prompt using Luma Dream Machine
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {
                "status": "failed",
                "error": "Playwright is not installed. Run 'pip install playwright && playwright install chromium' to enable browser-based AI skills.",
                "engine": "luma",
            }

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

            logger.info(f"[Luma] Generating video: {prompt[:50]}...")

            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")

            # Random human delay
            await asyncio.sleep(2 + (1.5 * os.urandom(1)[0] / 255))

            # Fill prompt
            prompt_area = page.get_by_role("textbox", name="Describe your video")
            await prompt_area.click()
            await prompt_area.type(prompt, delay=50 + (40 * os.urandom(1)[0] / 255))

            await asyncio.sleep(1.2)

            # Select aspect ratio
            if aspect_ratio == "9:16":
                await page.get_by_role("button", name="Portrait 9:16").click()
            else:
                await page.get_by_role("button", name="Landscape 16:9").click()

            await asyncio.sleep(0.7)

            # Click generate
            await page.get_by_role("button", name="Generate").click()

            logger.info("[Luma] Generation submitted, waiting for render...")

            # Wait for video element
            await page.wait_for_selector("video[src]", timeout=120000)

            video_element = await page.query_selector("video[src]")
            video_url = await video_element.get_attribute("src")

            logger.info(f"[Luma] Video generated successfully")

            await browser.close()
            await playwright.stop()

            return {
                "status": "success",
                "video_url": video_url,
                "engine": "luma",
                "prompt": prompt,
            }

        except Exception as e:
            logger.error(f"[Luma] Generation failed: {str(e)}")
            return {"status": "failed", "error": str(e), "engine": "luma"}


luma_skill = LumaSkill()
