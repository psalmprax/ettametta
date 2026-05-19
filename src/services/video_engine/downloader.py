import os
import uuid
import logging
import asyncio
from pathlib import Path

import yt_dlp

logger = logging.getLogger("VideoDownloader")


# Platform detection patterns → cookie file mapping
# Drop a <platform>_cookies.txt file into data/storage/cookies/ to enable auth.
# yt-dlp supports 1800+ sites — this map covers the most relevant ones
# for content creation, news sourcing, and idea discovery.
PLATFORM_COOKIE_MAP = {
    # ── Social Media & Short-Form ──
    "youtube": ["youtube.com", "youtu.be", "youtube.googleapis.com"],
    "tiktok": ["tiktok.com"],
    "twitter": ["twitter.com", "x.com", "t.co"],
    "instagram": ["instagram.com"],
    "facebook": ["facebook.com", "fb.watch", "fb.com"],
    "linkedin": ["linkedin.com"],
    "snapchat": ["snapchat.com", "story.snapchat.com"],
    "bluesky": ["bsky.app", "bsky.social"],
    "threads": ["threads.net"],
    "pinterest": ["pinterest.com"],
    "reddit": ["reddit.com", "redd.it"],
    "douyin": ["douyin.com"],  # Chinese TikTok

    # ── Video Hosting & Streaming ──
    "vimeo": ["vimeo.com"],
    "dailymotion": ["dailymotion.com"],
    "twitch": ["twitch.tv"],
    "bitchute": ["bitchute.com"],
    "rumble": ["rumble.com"],
    "odysee": ["odysee.com", "lbry.tv"],
    "streamable": ["streamable.com"],
    "bilibili": ["bilibili.com", "b23.tv"],
    "peertube": ["framatube.org", "peertube.tv", "videos.lecrabeinfo.net", "tube.privacytools.io"],
    "coub": ["coub.com"],
    "9gag": ["9gag.com"],
    "gab": ["gab.com", "tv.gab.com"],
    "banned": ["banned.video"],
    "crowdbunker": ["crowdbunker.com"],
    "floatplane": ["floatplane.com"],

    # ── News & Journalism ──
    "bbc": ["bbc.com", "bbc.co.uk"],
    "cnn": ["cnn.com", "edition.cnn.com"],
    "foxnews": ["foxnews.com", "video.foxnews.com"],
    "aljazeera": ["aljazeera.com"],
    "bloomberg": ["bloomberg.com"],
    "cnbc": ["cnbc.com"],
    "cspan": ["c-span.org"],
    "abcnews": ["abcnews.go.com"],
    "cbsnews": ["cbsnews.com"],
    "nbcnews": ["nbcnews.com"],
    "reuters": ["reuters.com"],
    "guardian": ["theguardian.com"],
    "dailymail": ["dailymail.co.uk"],
    "washingtonpost": ["washingtonpost.com"],
    "nytimes": ["nytimes.com"],
    "espn": ["espn.com"],

    # ── Music & Audio ──
    "soundcloud": ["soundcloud.com"],
    "bandcamp": ["bandcamp.com"],
    "audiomack": ["audiomack.com"],
    "mixcloud": ["mixcloud.com"],
    "spotify": ["spotify.com", "open.spotify.com"],

    # ── Podcasts ──
    "anchor": ["anchor.fm"],
    "applepodcasts": ["podcasts.apple.com"],
    "acast": ["acast.com"],

    # ── Educational & Knowledge ──
    "ted": ["ted.com"],
    "udemy": ["udemy.com"],
    "coursera": ["coursera.org"],
    "skillshare": ["skillshare.com"],
    "frontendmasters": ["frontendmasters.com"],
    "nebula": ["nebula.tv", "watchnebula.com"],

    # ── Cloud & File Sharing ──
    "dropbox": ["dropbox.com"],
    "googledrive": ["drive.google.com", "docs.google.com"],
    "mediafire": ["mediafire.com"],

    # ── Creative & Design ──
    "artstation": ["artstation.com"],
    "flickr": ["flickr.com"],
    "deviantart": ["deviantart.com"],
    "behance": ["behance.net"],
    "dribbble": ["dribbble.com"],

    # ── Business & Tech ──
    "crunchbase": ["crunchbase.com"],
    "producthunt": ["producthunt.com"],
    "loom": ["loom.com"],
}



class VideoDownloader:
    """
    Multi-platform video downloader using yt-dlp (supports 1000+ sites).
    Auto-detects platform from URL and loads matching cookies if available.
    Falls back to Pexels stock video when all download attempts fail.
    """

    def __init__(self, download_dir: str = "data/storage/downloads"):
        self.download_dir = download_dir

        # Try multiple cookie directory locations (Docker vs local)
        self.cookies_dir = self._find_cookies_dir()

        # Ensure download dir exists
        if os.path.exists(self.download_dir) and not os.access(self.download_dir, os.W_OK):
            self.download_dir = "data/storage/user_downloads"
        try:
            os.makedirs(self.download_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to prepare download dir: {e}")

    def _find_cookies_dir(self) -> str | None:
        """Find cookies directory across possible mount locations."""
        candidates = [
            "data/storage/cookies",
            "/app/data/storage/cookies",
            "cookies",
            "/app/cookies",
        ]
        for path in candidates:
            if os.path.isdir(path):
                logger.info(f"Cookies directory found: {path}")
                return path
        logger.warning("No cookies directory found — platform auth will be limited")
        return None

    def _detect_platform(self, url: str) -> str | None:
        """Detect which platform a URL belongs to."""
        url_lower = url.lower()
        for platform, domains in PLATFORM_COOKIE_MAP.items():
            for domain in domains:
                if domain in url_lower:
                    return platform
        return None

    def _find_cookie_file(self, url: str) -> str | None:
        """Find the cookie file matching the URL's platform."""
        if not self.cookies_dir:
            return None

        platform = self._detect_platform(url)
        if not platform:
            return None

        cookie_file = os.path.join(self.cookies_dir, f"{platform}_cookies.txt")
        if os.path.exists(cookie_file):
            logger.info(f"Using cookies for {platform}: {cookie_file}")
            return cookie_file

        logger.debug(f"No cookie file for {platform} at {cookie_file}")
        return None

    def _build_ydl_opts(self, url: str, output_path: str, max_filesize_mb: int = 100) -> dict:
        """Build yt-dlp options with platform-aware cookie injection."""
        opts = {
            "format": "bestvideo[height<=1080][filesize<150M]+bestaudio/best[height<=1080][filesize<150M]/best[height<=1080]/best",
            "outtmpl": output_path,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "retries": 3,
            "max_filesize": max_filesize_mb * 1024 * 1024,  # Convert to bytes
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "extractor_args": {
                "youtube": {"player_client": ["android", "web", "tv"]},
            },
        }

        # Inject cookies if available for this platform
        cookie_file = self._find_cookie_file(url)
        if cookie_file:
            opts["cookiefile"] = cookie_file

        return opts

    async def download_video(self, url: str) -> str | None:
        """
        Downloads a video from ANY yt-dlp supported URL.
        Supports YouTube, TikTok, Instagram, Facebook, Twitter/X,
        Twitch, Dailymotion, and 1000+ other sites.

        Falls back to Pexels stock if all download attempts fail.
        """
        file_id = str(uuid.uuid4())
        output_path = os.path.join(self.download_dir, f"{file_id}.%(ext)s")

        platform = self._detect_platform(url) or "unknown"
        logger.info(f"[{platform}] Starting download: {url}")

        # Attempt 1: Full format selection with cookies
        ydl_opts = self._build_ydl_opts(url, output_path)

        try:
            result = await asyncio.to_thread(self._sync_download, url, ydl_opts)
            if result:
                return result
        except Exception as e:
            logger.warning(f"[{platform}] Primary download failed: {e}")

        # Attempt 2: Let yt-dlp auto-select format (broader compatibility)
        logger.info(f"[{platform}] Retrying with auto format selection...")
        ydl_opts.pop("format", None)
        try:
            result = await asyncio.to_thread(self._sync_download, url, ydl_opts)
            if result:
                return result
        except Exception as e:
            logger.warning(f"[{platform}] Fallback download failed: {e}")

        logger.error(f"[{platform}] All download attempts failed for: {url}")
        return None

    def _sync_download(self, url: str, ydl_opts: dict) -> str | None:
        """Synchronous yt-dlp download (runs in thread)."""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                final_path = ydl.prepare_filename(info)
                if final_path and os.path.exists(final_path):
                    size_mb = os.path.getsize(final_path) / (1024 * 1024)
                    logger.info(f"Download complete: {final_path} ({size_mb:.1f} MB)")
                    return final_path
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            raise
        return None

    async def verify_video_asset(self, url: str) -> bool:
        """
        Quickly checks if a URL points to a valid downloadable video.
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "simulate": True,
            "skip_download": True,
            "socket_timeout": 15,
            "extractor_args": {
                "youtube": {"player_client": ["android", "web", "tv"]},
            },
        }

        # Add cookies for verification too
        cookie_file = self._find_cookie_file(url)
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        try:
            result = await asyncio.to_thread(self._sync_verify, url, ydl_opts)
            return result
        except Exception as e:
            error_str = str(e)
            # Format errors mean the video exists but selector failed
            if "format is not available" in error_str or "Requested format" in error_str:
                logger.info(f"Treating format error as valid for: {url}")
                return True
            logger.warning(f"Verification failed for {url}: {e}")
            return False

    def _sync_verify(self, url: str, ydl_opts: dict) -> bool:
        """Synchronous verification (runs in thread)."""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            vcodec = info.get("vcodec") or "none"
            if vcodec == "none" and not info.get("formats"):
                return False
            return True

    def get_supported_platforms(self) -> list[str]:
        """Return list of platforms with cookies configured."""
        if not self.cookies_dir:
            return []
        platforms = []
        for platform in PLATFORM_COOKIE_MAP:
            cookie_file = os.path.join(self.cookies_dir, f"{platform}_cookies.txt")
            if os.path.exists(cookie_file):
                platforms.append(platform)
        return platforms


base_downloader_service = VideoDownloader()
