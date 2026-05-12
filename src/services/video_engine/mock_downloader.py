import os
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger("MockDownloader")

class MockDownloader:
    """
    Testing Maturity: Fast-Track Mock Downloader.
    Returns local placeholder assets to bypass external API calls during E2E testing.
    """
    def __init__(self, mock_asset_path: str = "tests/assets/mock_video.mp4"):
        self.mock_asset_path = Path(mock_asset_path)
        # Ensure mock asset exists for testing
        if not self.mock_asset_path.exists():
            self.mock_asset_path.parent.mkdir(parents=True, exist_ok=True)
            # Create a 1-second dummy file if missing (requires ffmpeg)
            os.system(f"ffmpeg -f lavfi -i color=c=blue:s=1080x1920:d=5 -c:v libx264 {self.mock_asset_path}")

    async def download_video(self, url: str, **kwargs) -> str:
        """Simulate a download by returning the local mock asset."""
        logger.info(f"🧪 [Mock] Intercepted download for {url}. Returning mock asset.")
        await asyncio.sleep(0.5) # Simulate slight network delay
        return str(self.mock_asset_path.absolute())

base_mock_downloader = MockDownloader()
