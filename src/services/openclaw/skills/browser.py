import asyncio
import logging
from typing import Any
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)

class BrowserSkill(OpenClawBaseSkill):
    """
    Browser Skill for OpenClaw agents.
    Retrieves raw HTML content from target URLs for analysis.
    """

    def __init__(self):
        super().__init__()
        self.browser = None
        self.context = None
        self.page = None

    async def _ensure_browser(self):
        if not self.browser:
            from playwright.async_api import async_playwright
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

    async def execute(self, action: str = "navigate", url: str = None, selector: str = None, **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        try:
            await self._ensure_browser()
            
            if action == "navigate" and url:
                await self.page.goto(url)
                return f"✅ Navigated to {url}"
            elif action == "click" and selector:
                await self.page.click(selector)
                return f"✅ Clicked element: {selector}"
            elif action == "extract":
                content = await self.page.content()
                return f"📄 Content Extracted ({len(content)} chars)\nPreview: {content[:500]}..."
            else:
                return f"⚠️ Unknown action or missing params for Browser: {action}"
        except Exception as e:
            logger.error(f"Browser Skill Error: {e}")
            return f"⚠️ Browser Error: {str(e)}"

browser_skill = BrowserSkill()
