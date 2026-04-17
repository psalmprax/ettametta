import asyncio
import logging
import os
import urllib.parse
from playwright.async_api import async_playwright, Browser, Page
from typing import Any

logger = logging.getLogger(__name__)


class PerchanceSkill:
    """
    Perchance AI image generator browser automation skill.
    Supports multiple generator variants with full parameter control.
    Free, no sign-up, unlimited generation.
    """

    GENERATORS = {
        "default": "https://perchance.org/ai-text-to-image-generator",
        "cursed": "https://perchance.org/cursed-ai",
        "photo": "https://perchance.org/photo-realistic-generator",
        "anime": "https://perchance.org/anime-generator",
        "product": "https://perchance.org/product-photography-generator",
    }

    RESOLUTIONS = {
        "square": "512x512",
        "portrait": "512x768",
        "landscape": "768x512",
        "hd": "1024x1024",
        "portrait_hd": "1024x1792",
    }

    ASPECT_RATIOS = {
        "1:1": "square",
        "9:16": "portrait",
        "16:9": "landscape",
        "4:3": "landscape",
        "3:4": "portrait",
    }

    def __init__(
        self,
        generator: str = "default",
        resolution: str = "1024x1024",
        aspect_ratio: str = "1:1",
        negative_prompt: str = "",
        seed: int = -1,
        batch_size: int = 1,
    ):
        self.generator = generator
        self.resolution = resolution
        self.aspect_ratio = aspect_ratio
        self.negative_prompt = negative_prompt
        self.seed = seed
        self.batch_size = batch_size
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

    async def generate(
        self,
        prompt: str,
        generator: str | None = None,
        resolution: str | None = None,
        aspect_ratio: str | None = None,
        negative_prompt: str | None = None,
        seed: int | None = None,
        batch_size: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate image(s) using Perchance.

        Args:
            prompt: Text prompt for image generation
            generator: Generator variant ('default', 'cursed', 'photo', 'anime', 'product')
            resolution: Resolution ('square', 'portrait', 'landscape', 'hd', 'portrait_hd')
            aspect_ratio: Aspect ratio ('1:1', '9:16', '16:9', '4:3', '3:4')
            negative_prompt: Things to avoid in the image
            seed: Seed for reproducibility (-1 for random)
            batch_size: Number of variations to generate

        Returns:
            dict with status, image_urls, error
        """
        generator = generator or self.generator
        resolution = resolution or self.resolution
        aspect_ratio = aspect_ratio or self.aspect_ratio
        negative_prompt = negative_prompt or self.negative_prompt
        seed = seed if seed is not None else self.seed
        batch_size = batch_size or self.batch_size

        try:
            await self.initialize()

            generator_url = self.GENERATORS.get(generator, self.GENERATORS["default"])
            logger.info(f"[Perchance] Generating: {prompt[:50]}... with {generator}")

            await self.page.goto(generator_url)
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2 + (3 * os.urandom(1)[0] / 255))

            await self._set_resolution(resolution)
            await asyncio.sleep(0.5 + os.urandom(1)[0] / 255)

            await self._set_aspect_ratio(aspect_ratio)
            await asyncio.sleep(0.5 + os.urandom(1)[0] / 255)

            await self._set_negative_prompt(negative_prompt)
            await asyncio.sleep(0.5 + os.urandom(1)[0] / 255)

            if seed != -1:
                await self._set_seed(seed)
                await asyncio.sleep(0.5 + os.urandom(1)[0] / 255)

            if batch_size > 1:
                await self._set_batch_size(batch_size)
                await asyncio.sleep(0.5 + os.urandom(1)[0] / 255)

            await self._set_prompt(prompt)
            await asyncio.sleep(1 + (2 * os.urandom(1)[0] / 255))

            await self._click_generate()
            logger.info("[Perchance] Generation submitted, waiting for render...")

            await self.page.wait_for_timeout(60000)

            image_urls = await self._extract_images()

            logger.info(f"[Perchance] Generated {len(image_urls)} image(s)")

            await self.cleanup()

            return {
                "status": "success" if image_urls else "processing",
                "image_urls": image_urls,
                "generator": generator,
                "prompt": prompt,
                "settings": {
                    "resolution": resolution,
                    "aspect_ratio": aspect_ratio,
                    "negative_prompt": negative_prompt,
                    "seed": seed,
                    "batch_size": batch_size,
                },
            }

        except Exception as e:
            logger.error(f"[Perchance] Generation failed: {str(e)}")
            await self.cleanup()
            return {"status": "failed", "error": str(e), "generator": "perchance"}

    async def _set_prompt(self, prompt: str):
        """Enter the main prompt"""
        prompt_area = self.page.get_by_role("textbox").first
        if await prompt_area.count() > 0:
            await prompt_area.click()
            await prompt_area.fill(prompt)

    async def _set_resolution(self, resolution: str):
        """Set image resolution"""
        res_value = self.RESOLUTIONS.get(resolution, resolution)
        res_select = self.page.get_by_role(
            "combobox", name=lambda x: "resolution" in x.lower() or "size" in x.lower()
        )
        if await res_select.count() > 0:
            await res_select.select_option(res_value)

    async def _set_aspect_ratio(self, aspect_ratio: str):
        """Set aspect ratio"""
        ratio_key = self.ASPECT_RATIOS.get(aspect_ratio, aspect_ratio)
        ratio_select = self.page.get_by_role(
            "combobox", name=lambda x: "aspect" in x.lower()
        )
        if await ratio_select.count() > 0:
            await ratio_select.select_option(ratio_key)

    async def _set_negative_prompt(self, negative_prompt: str):
        """Set negative prompt"""
        if negative_prompt:
            neg_area = self.page.get_by_role(
                "textbox", name=lambda x: "negative" in x.lower()
            )
            if await neg_area.count() > 0:
                await neg_area.fill(negative_prompt)

    async def _set_seed(self, seed: int):
        """Set seed for reproducibility"""
        seed_input = self.page.get_by_role(
            "spinbutton", name=lambda x: "seed" in x.lower()
        )
        if await seed_input.count() > 0:
            await seed_input.fill(str(seed))

    async def _set_batch_size(self, batch_size: int):
        """Set number of variations"""
        batch_input = self.page.get_by_role(
            "spinbutton",
            name=lambda x: "batch" in x.lower() or "variations" in x.lower(),
        )
        if await batch_input.count() > 0:
            await batch_input.fill(str(batch_size))

    async def _click_generate(self):
        """Click generate button"""
        generate_btn = self.page.get_by_role(
            "button", name=lambda x: "generate" in x.lower() or "create" in x.lower()
        )
        if await generate_btn.count() > 0:
            await generate_btn.click()

    async def _extract_images(self) -> list[str]:
        """Extract generated image URLs"""
        image_urls = []

        img_elements = await self.page.query_selector_all("img")
        for img in img_elements:
            src = await img.get_attribute("src")
            if src and src.startswith("http"):
                image_urls.append(src)

        anchor_elements = await self.page.query_selector_all("a[href*='image']")
        for anchor in anchor_elements:
            href = await anchor.get_attribute("href")
            if href and href.startswith("http"):
                image_urls.append(href)

        figure_elements = await self.page.query_selector_all("figure img")
        for fig in figure_elements:
            src = await fig.get_attribute("src")
            if src and src.startswith("http"):
                image_urls.append(src)

        return list(set(image_urls))

    async def generate_simple(self, prompt: str) -> dict[str, Any]:
        """Simple generation with defaults"""
        return await self.generate(prompt)

    async def generate_with_settings(
        self,
        prompt: str,
        style: str = "photo",
        resolution: str = "hd",
        aspect_ratio: str = "9:16",
    ) -> dict[str, Any]:
        """Generate with specific style settings"""
        style_map = {
            "photo": "photo",
            "anime": "anime",
            "cursed": "cursed",
            "product": "product",
        }
        generator = style_map.get(style, "default")
        return await self.generate(
            prompt,
            generator=generator,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
        )

    async def cleanup(self):
        """Clean up browser resources"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()


perchance_skill = PerchanceSkill()
