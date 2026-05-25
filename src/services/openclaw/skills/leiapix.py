import asyncio
import logging
import os

from .playwright_video_skill import PlaywrightVideoSkill

logger = logging.getLogger(__name__)


class LeiaPixSkill(PlaywrightVideoSkill):
    """
    LeiaPix browser automation skill - Image to video conversion
    VERY easy automation, perfect for image -> video pipeline
    """

    engine_name = "leiapix"
    base_url = "https://convert.leiapix.com"
    wait_timeout_ms = 90000
    create_path = ""
    button_names = ["Animate"]

    async def generate(self, image_uri: str, motion_intensity: int = 5) -> dict:
        """Convert image to motion video using LeiaPix."""
        try:
            await self.initialize()
            logger.info(f"[LeiaPix] Converting image to video: {image_uri[:50]}...")

            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(1.5 + (1.5 * os.urandom(1)[0] / 255))

            # Upload image
            await self.page.get_by_role("button", name="Upload Image").click()
            await asyncio.sleep(0.8)
            file_input = await self.page.query_selector('input[type="file"]')
            await file_input.set_input_files(image_uri)
            await asyncio.sleep(2 + (1 * os.urandom(1)[0] / 255))

            # Set motion intensity
            await self.page.get_by_role("slider").fill(str(motion_intensity))
            await asyncio.sleep(0.5)

            # Click animate
            await self._click_generate()
            logger.info("[LeiaPix] Animation submitted, waiting for render...")

            await self.page.wait_for_selector("video[src]", timeout=90000)
            video_element = await self.page.query_selector("video[src]")
            video_uri = await video_element.get_attribute("src") if video_element else None

            logger.info(f"[LeiaPix] Video generated: {video_uri[:80] if video_uri else 'N/A'}...")
            await self.cleanup()

            return {
                "status": "success" if video_uri else "processing",
                "video_uri": video_uri or "",
                "engine": self.engine_name,
                "input_image": image_uri,
            }
        except Exception as e:
            logger.exception(f"[LeiaPix] Generation failed: {str(e)}")
            await self.cleanup()
            return {"status": "failed", "error": str(e), "engine": self.engine_name}


leiapix_skill = LeiaPixSkill()
