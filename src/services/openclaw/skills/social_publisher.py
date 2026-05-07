"""
Playwright Social Publisher Skill
=================================
Automates posting to TikTok and Instagram using headless browser automation.
Bypasses official API restrictions by simulating human interaction.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)


class PlaywrightPublisher:
    """Handles automated posting via Playwright."""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.sessions_dir = Path("data/storage/sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    async def _start_browser(self) -> Browser:
        """Start a stealthy browser instance."""
        if not self.browser:
            playwright = await async_playwright().start()
            # Use Chromium with stealth options
            self.browser = await playwright.chromium.launch(
                headless=False,  # Headed mode is less detectable
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
        return self.browser

    async def _load_session(self, platform: str, user_id: str) -> Optional[dict]:
        """Load saved cookies for a user."""
        session_file = self.sessions_dir / f"{platform}_{user_id}.json"
        if session_file.exists():
            import json
            with open(session_file, 'r') as f:
                return json.load(f)
        return None

    async def _save_session(self, platform: str, user_id: str, cookies: list):
        """Save cookies for future sessions."""
        import json
        session_file = self.sessions_dir / f"{platform}_{user_id}.json"
        with open(session_file, 'w') as f:
            json.dump(cookies, f)

    async def post_to_tiktok(
        self, 
        user_id: str,
        video_path: str, 
        description: str, 
        tags: list[str]
    ) -> dict[str, Any]:
        """
        Post a video to TikTok using browser automation.
        """
        try:
            browser = await self._start_browser()
            context = await browser.new_context(
                viewport={'width': 1080, 'height': 1920},
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1'
            )
            
            # Load session if available
            cookies = await self._load_session("tiktok", user_id)
            if cookies:
                await context.add_cookies(cookies)
            
            page = await context.new_page()
            await page.goto('https://www.tiktok.com/upload?lang=en')
            
            # Check if logged in
            await page.wait_for_timeout(5000)
            if "login" in page.url.lower():
                raise Exception("Not logged in to TikTok. Please log in manually first.")
            
            # Upload Video
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(video_path)
            else:
                # Fallback selector
                await page.click('div[data-e2e="upload-btn"]')
                await page.wait_for_timeout(2000)
                await page.setInputFiles('input[type="file"]', video_path)
            
            # Wait for upload to process
            await page.wait_for_timeout(10000)
            
            # Fill Caption
            caption_box = await page.query_selector('div[data-e2e="caption-container"]')
            if caption_box:
                await caption_box.fill(description + " " + " ".join(tags))
            
            # Click Post
            post_btn = await page.query_selector('button[data-e2e="post-button"]')
            if post_btn:
                await post_btn.click()
                await page.wait_for_timeout(5000)
                
                # Save new session cookies
                new_cookies = await context.cookies()
                await self._save_session("tiktok", user_id, new_cookies)
                
                return {
                    "platform": "tiktok",
                    "status": "posted",
                    "message": "Video posted successfully via automation."
                }
            else:
                raise Exception("Post button not found. UI may have changed.")
                
        except Exception as e:
            logger.error(f"TikTok automation failed: {str(e)}")
            raise Exception(f"TikTok automation failed: {str(e)}")

    async def post_to_instagram(
        self, 
        user_id: str,
        video_path: str, 
        description: str, 
        tags: list[str]
    ) -> dict[str, Any]:
        """
        Post a Reel to Instagram using browser automation.
        """
        try:
            browser = await self._start_browser()
            context = await browser.new_context(
                viewport={'width': 1080, 'height': 1920},
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1'
            )
            
            # Load session
            cookies = await self._load_session("instagram", user_id)
            if cookies:
                await context.add_cookies(cookies)
            
            page = await context.new_page()
            await page.goto('https://www.instagram.com/reels/')
            
            # Check login
            await page.wait_for_timeout(5000)
            if "login" in page.url.lower():
                raise Exception("Not logged in to Instagram. Please log in manually first.")
            
            # Click Create
            create_btn = await page.query_selector('svg[aria-label="New Reel"]')
            if not create_btn:
                create_btn = await page.query_selector('svg[aria-label="New Post"]')
            
            if create_btn:
                await create_btn.click()
                await page.wait_for_timeout(2000)
                
                # Upload
                file_input = await page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(video_path)
                
                await page.wait_for_timeout(10000)
                
                # Next/Share
                next_btn = await page.query_selector('button:has-text("Next")')
                if next_btn:
                    await next_btn.click()
                    await page.wait_for_timeout(2000)
                    
                    # Caption
                    caption_area = await page.query_selector('textarea[placeholder="Write a caption..."]')
                    if caption_area:
                        await caption_area.fill(description + " " + " ".join(tags))
                    
                    share_btn = await page.query_selector('button:has-text("Share")')
                    if share_btn:
                        await share_btn.click()
                        
                        # Save session
                        new_cookies = await context.cookies()
                        await self._save_session("instagram", user_id, new_cookies)
                        
                        return {
                            "platform": "instagram",
                            "status": "posted",
                            "message": "Reel posted successfully via automation."
                        }
            raise Exception("Could not find upload interface.")
                
        except Exception as e:
            logger.error(f"Instagram automation failed: {str(e)}")
            raise Exception(f"Instagram automation failed: {str(e)}")


# Singleton instance
base_playwright_publisher = PlaywrightPublisher()
