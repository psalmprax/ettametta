import asyncio
import logging
import os

from .playwright_video_skill import PlaywrightVideoSkill

logger = logging.getLogger(__name__)


class HaiperSkill(PlaywrightVideoSkill):
    """
    Haiper AI browser automation skill - Tier 1 easiest target
    Clean UI, no login required for demo generation, very predictable selectors
    """

    engine_name = "haiper"
    base_url = "https://haiper.ai"
    wait_timeout_ms = 120000
    button_names = ["Generate"]

    async def _enter_prompt(self, prompt: str):
        prompt_area = self.page.get_by_role("textbox", name="Describe your video")
        await prompt_area.click()
        await prompt_area.type(prompt, delay=40 + (30 * os.urandom(1)[0] / 255))

    async def generate(self, prompt: str, aspect_ratio: str = "9:16") -> dict:
        try:
            await self.initialize()
            logger.info(f"[Haiper] Generating video: {prompt[:50]}...")

            await self.page.goto(f"{self.base_url}/create")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(1.5 + (2 * os.urandom(1)[0] / 255))

            await self._enter_prompt(prompt)
            await asyncio.sleep(1)

            # Select aspect ratio
            if aspect_ratio == "9:16":
                await self.page.get_by_role("button", name="Vertical").click()
            else:
                await self.page.get_by_role("button", name="Horizontal").click()
            await asyncio.sleep(0.8)

            await self._click_generate()
            logger.info("[Haiper] Generation submitted, waiting for render...")

            await self.page.wait_for_selector("video[src]", timeout=120000)
            video_element = await self.page.query_selector("video[src]")
            video_uri = await video_element.get_attribute("src") if video_element else None

            logger.info(f"[Haiper] Video generated: {video_uri[:80] if video_uri else 'N/A'}...")
            await self.cleanup()

            return {
                "status": "success" if video_uri else "processing",
                "video_uri": video_uri or "",
                "engine": self.engine_name,
                "prompt": prompt,
            }
        except Exception as e:
            logger.exception(f"[Haiper] Generation failed: {str(e)}")
            await self.cleanup()
            return {"status": "failed", "error": str(e), "engine": self.engine_name}


haiper_skill = HaiperSkill()
