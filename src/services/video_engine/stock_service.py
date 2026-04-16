import httpx
import os
import logging
import random
from typing import List, Optional
from api.utils.vault import get_secret

class StockService:
    def __init__(self):
        self.api_key = get_secret("pexels_api_key")
        self.base_url = "https://api.pexels.com/videos"
        self.headers = {"Authorization": self.api_key} if self.api_key else {}

    async def fetch_b_roll(self, keyword: str, count: int = 1) -> List[str]:
        """
        Searches Pexels for a video matching the keyword and returns the download URL.
        """
        if not self.api_key or self.api_key == "your_key_here":
            logging.warning("[StockService] Pexels API key missing. Skipping B-roll.")
            return []

        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "query": keyword,
                    "per_page": 5,
                    "orientation": "portrait" # Prioritize vertical for Shorts/TikTok
                }
                response = await client.get(f"{self.base_url}/search", params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                videos = data.get("videos", [])
                if not videos:
                    # Fallback to horizontal if no portrait found
                    params["orientation"] = "landscape"
                    response = await client.get(f"{self.base_url}/search", params=params, headers=self.headers)
                    videos = response.json().get("videos", [])

                if not videos:
                    return []

                # Randomly pick from top results
                results = []
                for _ in range(min(count, len(videos))):
                    video = random.choice(videos)
                    # Find best file (HD or SD)
                    video_files = video.get("video_files", [])
                    # Prefer HD mp4
                    best_file = next((f for f in video_files if f.get("quality") == "hd" and f.get("file_type") == "video/mp4"), None)
                    if not best_file:
                        best_file = video_files[0] if video_files else None
                    
                    if best_file:
                        results.append(best_file["link"])
                
                return results
        except Exception as e:
            logging.error(f"[StockService] Error fetching B-roll for '{keyword}': {e}")
            return []

    async def download_stock_video(self, url: str, output_dir: str = "temp") -> Optional[str]:
        """
        Downloads a stock video file to a local path.
        """
        os.makedirs(output_dir, exist_ok=True)
        filename = f"stock_{os.path.basename(url.split('?')[0])}.mp4"
        if not filename.endswith(".mp4"):
            filename += ".mp4"
            
        filepath = os.path.join(output_dir, filename)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return filepath
        except Exception as e:
            logging.error(f"[StockService] Error downloading {url}: {e}")
            return None

stock_service = StockService()
