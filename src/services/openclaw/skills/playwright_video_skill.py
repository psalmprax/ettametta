"""
PlaywrightVideoSkill - Base class for browser-automated video generation skills.

Eliminates ~2000 lines of duplicated code across runway, pika, kling, hailuo,
haiper, genmo, morph, vidu, wavespeed, seedance, frameloop, leiapix, videoany,
heygen, ltx, leonardo, invideo, fliki skills.

Subclasses only need to set class attributes for platform-specific behavior.
"""

import asyncio
import logging
import os
from typing import Any

from playwright.async_api import async_playwright, Browser, Page

from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class PlaywrightVideoSkill(OpenClawBaseSkill):
    """
    Base class for Playwright-based video generation skills.

    Subclasses set these class attributes:
        engine_name: str - engine identifier for return dicts
        base_url: str - platform URL
        wait_timeout_ms: int - how long to wait for video render (default: 60000)
        create_path: str - path to append to base_url for creation page (default: "/create")
        button_names: list[str] - button text patterns to match (default: ["Generate", "Create"])
    """

    engine_name: str = "unknown"
    base_url: str = ""
    wait_timeout_ms: int = 60000
    create_path: str = "/create"
    button_names: list[str] = ["Generate", "Create"]

    def __init__(self):
        super().__init__()
        self.browser: Browser | None = None
        self.page: Page | None = None

    async def execute(self, action: str = "generate", prompt: str = "", aspect_ratio: str = "9:16", **kwargs) -> str:
        """Polymorphic entry point for OpenClaw agent."""
        p = prompt or kwargs.get("prompt") or kwargs.get("topic", "")
        if not p:
            return f"Warning: {self.__class__.__name__} failed: Missing prompt"

        res = await self.generate(p, aspect_ratio or kwargs.get("aspect_ratio", "9:16"))
        if res.get("status") == "success":
            return f"Video Generated ({self.__class__.__name__})! URL: {res.get('video_uri')}"
        return f"Warning: {self.__class__.__name__} failed: {res.get('error')}"

    async def initialize(self):
        """Initialize stealth browser session."""
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
        Generate video from prompt using browser automation.
        Returns: {status: success/failed, video_uri: str, error: str, engine: str}
        """
        try:
            await self.initialize()
            logger.info(f"[{self.engine_name}] Generating video: {prompt[:50]}...")

            await self.page.goto(f"{self.base_url}{self.create_path}")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2 + (3 * os.urandom(1)[0] / 255))

            # Type prompt into text field
            await self._enter_prompt(prompt)
            await asyncio.sleep(1 + (2 * os.urandom(1)[0] / 255))

            # Click generate button
            await self._click_generate()

            logger.info(f"[{self.engine_name}] Generation submitted, waiting for render...")
            await self.page.wait_for_timeout(self.wait_timeout_ms)

            # Extract video URL
            video_uri = await self._extract_video_uri()

            logger.info(f"[{self.engine_name}] Video generated: {video_uri[:80] if video_uri else 'N/A'}...")
            await self.cleanup()

            return {
                "status": "success" if video_uri else "processing",
                "video_uri": video_uri or "",
                "engine": self.engine_name,
                "prompt": prompt,
            }

        except Exception as e:
            logger.exception(f"[{self.engine_name}] Generation failed: {str(e)}")
            await self.cleanup()
            return {"status": "failed", "error": str(e), "engine": self.engine_name}

    async def _enter_prompt(self, prompt: str):
        """Enter prompt text into the platform's input field. Override for custom selectors."""
        prompt_area = self.page.get_by_role("textbox")
        if await prompt_area.count() > 0:
            await prompt_area.first.click()
            await prompt_area.first.type(prompt, delay=50 + (50 * os.urandom(1)[0] / 255))
        else:
            # Fallback to textarea
            textareas = self.page.locator("textarea")
            if await textareas.count() > 0:
                await textareas.first.click()
                await textareas.first.type(prompt, delay=50 + (50 * os.urandom(1)[0] / 255))

    async def _click_generate(self):
        """Click the generate/create button. Override for custom selectors."""
        btn = self.page.get_by_role(
            "button",
            name=lambda x: x and any(name in x for name in self.button_names),
        )
        await btn.click()

    async def _extract_video_uri(self) -> str | None:
        """Extract video URL from the page. Override for custom extraction logic."""
        video_element = await self.page.query_selector("video")
        if not video_element:
            video_element = await self.page.query_selector("[class*='video'] video")
        if video_element:
            return await video_element.get_attribute("src")
        return None

    async def cleanup(self):
        """Clean up browser resources."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
