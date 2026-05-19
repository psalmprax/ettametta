import os
import hashlib
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger("MockDownloader")

class MockDownloader:
    """
    Testing Maturity: Premium Mock Downloader.
    Manages a pool of visually distinct, high-definition (1080x1920) vertical video clips.
    Prevents clip repetition by deterministically rotating assets based on the URL hash.
    """
    def __init__(self, pool_dir: str = "tests/assets/mock_pool"):
        self.pool_dir = Path(pool_dir)
        self.mock_pool = []
        
        # Ensure pool directory exists
        self.pool_dir.mkdir(parents=True, exist_ok=True)
        
        # Define 5 distinct mock asset definitions
        self.asset_definitions = [
            ("mock_1.mp4", "color=c=crimson:s=1080x1920:d=5"),          # Vibrant Crimson Canvas
            ("mock_2.mp4", "testsrc=size=1080x1920:d=5:rate=30"),       # Moving Tech Grid / Calibration Screen
            ("mock_3.mp4", "color=c=gold:s=1080x1920:d=5"),             # Premium Solid Gold Canvas
            ("mock_4.mp4", "color=c=darkslategray:s=1080x1920:d=5"),    # Sleek Charcoal Slate Canvas
            ("mock_5.mp4", "color=c=darkviolet:s=1080x1920:d=5"),       # Vibrant Electric Violet Canvas
        ]

        self._initialize_pool()

    def _initialize_pool(self):
        """Pre-generates high-definition distinct mock assets if they do not exist."""
        for filename, lavfi_filter in self.asset_definitions:
            file_path = self.pool_dir / filename
            if not file_path.exists():
                logger.info(f"Generating high-definition mock stock clip: {filename}")
                # Create the premium mock clip using FFMPEG lavfi sources
                cmd = f'ffmpeg -y -f lavfi -i "{lavfi_filter}" -c:v libx264 -pix_fmt yuv420p "{file_path}" >/dev/null 2>&1'
                os.system(cmd)
            
            if file_path.exists():
                self.mock_pool.append(file_path)

        # Fallback to single test file if pool generation failed or was empty
        if not self.mock_pool:
            fallback_path = Path("tests/assets/mock_video.mp4")
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            if not fallback_path.exists():
                os.system(f"ffmpeg -y -f lavfi -i color=c=blue:s=1080x1920:d=5 -c:v libx264 -pix_fmt yuv420p {fallback_path} >/dev/null 2>&1")
            self.mock_pool.append(fallback_path)

    async def download_video(self, url: str, **kwargs) -> str:
        """
        Simulate a stock video download.
        Deterministically returns one of the 5 distinct mock clips based on URL hashing
        to guarantee visual variety in the final compiled edit.
        """
        logger.info(f"🧪 [Mock] Intercepting download for {url}.")
        await asyncio.sleep(0.3) # Simulate slight network delay
        
        # Calculate a stable hash of the URL to pick a file deterministically
        url_hash = int(hashlib.md5(url.encode('utf-8')).hexdigest(), 16)
        chosen_index = url_hash % len(self.mock_pool)
        chosen_file = self.mock_pool[chosen_index]
        
        logger.info(f"🧪 [Mock] Selected mock stock asset index {chosen_index}: {chosen_file.name}")
        return str(chosen_file.absolute())

base_mock_downloader = MockDownloader()
