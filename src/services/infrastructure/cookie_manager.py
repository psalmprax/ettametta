import os
import logging
import time
from pathlib import Path

logger = logging.getLogger("CookieManager")

class CookieManager:
    """
    10/10 Production: Automated Cookie Guardian.
    Ensures that yt-dlp has valid session cookies for YouTube/TikTok downloads.
    """
    def __init__(self, cookie_dir: str = "data/storage/cookies"):
        self.cookie_dir = Path(cookie_dir)
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        self.youtube_path = self.cookie_dir / "youtube_cookies.txt"

    def get_youtube_cookies(self) -> str | None:
        """Returns the path to the YouTube cookies file if it is valid."""
        if self.youtube_path.exists() and self.youtube_path.stat().st_size > 0:
            # Check if cookies are older than 24 hours
            mtime = self.youtube_path.stat().st_mtime
            if time.time() - mtime > 86400:
                logger.warning("🕒 [Cookies] YouTube cookies are older than 24 hours. Refresh recommended.")
            return str(self.youtube_path)
        
        logger.error(f"❌ [Cookies] YouTube cookies missing or empty at {self.youtube_path}")
        return None

    def update_cookies(self, content: str):
        """Updates the cookie file with new content (Netscape format)."""
        try:
            with open(self.youtube_path, "w") as f:
                f.write(content)
            logger.info(f"✅ [Cookies] Successfully updated YouTube cookies ({len(content)} bytes)")
            return True
        except Exception as e:
            logger.error(f"❌ [Cookies] Failed to update cookies: {e}")
            return False

base_cookie_manager = CookieManager()
