import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class CookieManager:
    """
    Handles loading and parsing Netscape-formatted cookies from the ./cookies directory.
    """
    def __init__(self, cookies_dir: str = "cookies"):
        self.cookies_dir = cookies_dir

    def parse_netscape_cookies(self, file_path: str) -> Dict[str, str]:
        """
        Parses standard Netscape/Curl cookie file format.
        Format: domain  flag  path  secure  expiration  name  value
        """
        cookies = {}
        if not os.path.exists(file_path):
            logger.warning(f"[CookieManager] File not found: {file_path}")
            return cookies

        try:
            with open(file_path, "r") as f:
                for line in f:
                    if line.startswith("#") or not line.strip():
                        continue
                    
                    parts = line.strip().split("\t")
                    if len(parts) >= 7:
                        name = parts[5]
                        value = parts[6]
                        cookies[name] = value
            
            logger.info(f"[CookieManager] Successfully parsed {len(cookies)} cookies from {file_path}")
        except Exception as e:
            logger.error(f"[CookieManager] Failed to parse {file_path}: {e}")
            
        return cookies

    def get_cookies_for_platform(self, platform: str) -> Dict[str, str]:
        """
        Returns a dictionary of cookies for a specific platform.
        Expects files like cookies/tiktok_cookies.txt
        """
        # Mapping platform keys to filenames
        mapping = {
            "tiktok": "tiktok_cookies.txt",
            "youtube": "youtube_cookies.txt",
            "x": "twitter_cookies.txt",
            "twitter": "twitter_cookies.txt",
            "linkedin": "linkedin_cookies.txt"
        }
        
        filename = mapping.get(platform.lower())
        if not filename:
            return {}
            
        file_path = os.path.join(self.cookies_dir, filename)
        return self.parse_netscape_cookies(file_path)

    def has_cookies(self, platform: str) -> bool:
        """Checks if a cookie file exists for the platform."""
        mapping = {
            "tiktok": "tiktok_cookies.txt",
            "youtube": "youtube_cookies.txt",
            "x": "twitter_cookies.txt",
            "twitter": "twitter_cookies.txt",
            "linkedin": "linkedin_cookies.txt"
        }
        filename = mapping.get(platform.lower())
        if not filename:
            return False
        return os.path.exists(os.path.join(self.cookies_dir, filename))

cookie_manager = CookieManager()
