import httpx
import os
import logging
import random
from src.api.utils.vault import get_secret

class StockService:
    def __init__(self):
        self.pexels_api_key = get_secret("pexels_api_key")
        self.pexels_base_url = "https://api.pexels.com/videos"
        self.pexels_headers = {"Authorization": self.pexels_api_key} if self.pexels_api_key else {}
        
        # Free fallback APIs (No Key Required)
        self.mixkit_base_url = "https://api.mixkit.co/videos/preview/"
        self.coverr_base_url = "https://coverr.co/api/videos"

    async def fetch_b_roll(self, keyword: str, count: int = 1) -> list[str]:
        """
        Searches for videos matching the keyword.
        Priority: Pexels (High Quality) -> Mixkit/Coverr (Free Fallback)
        """
        # Re-read key each call to pick up late-set env vars
        pexels_key = self.pexels_api_key or get_secret("pexels_api_key")
        pexels_headers = {"Authorization": pexels_key} if pexels_key else {}
        
        urls = []

        # 1. Try Pexels First
        if pexels_key and pexels_key != "your_key_here":
            try:
                async with httpx.AsyncClient() as client:
                    params = {"query": keyword, "per_page": 5, "orientation": "portrait"}
                    response = await client.get(f"{self.pexels_base_url}/search", params=params, headers=pexels_headers)
                    response.raise_for_status()
                    data = response.json()
                    videos = data.get("videos", [])
                    if videos:
                        for video in videos[:count]:
                            video_files = video.get("video_files", [])
                            best_file = next((f for f in video_files if f.get("quality") == "hd"), video_files[0] if video_files else None)
                            if best_file:
                                urls.append(best_file["link"])
                        if len(urls) >= count:
                            return urls
            except Exception as e:
                logging.warning(f"[StockService] Pexels failed: {e}. Falling back to free sources.")

        # 2. Fallback to Mixkit (Curated Free Stock Video)
        # Mixkit doesn't have a public search API, so we use curated categories/keywords mapping
        # Or we can use Coverr which has a simple JSON endpoint
        try:
            async with httpx.AsyncClient() as client:
                # Coverr API Example: https://coverr.co/api/videos?query={keyword}
                response = await client.get(f"{self.coverr_base_url}", params={"query": keyword})
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                
                for item in results[:count]:
                    # Coverr returns direct MP4 links in 'videos' array
                    mp4_links = [v['url'] for v in item.get('videos', []) if v['format'] == 'mp4']
                    if mp4_links:
                        urls.append(mp4_links[0])
                
                if len(urls) >= count:
                    return urls
                    
        except Exception as e:
            logging.warning(f"[StockService] Coverr failed: {e}")

        # 3. Last Resort: High-Quality Public Domain Samples
        # These are real, working URLs from Pexels/Mixkit that are free to use
        fallback_db = {
            "tech": ["https://cdn.coverr.co/videos/coverr-robot-hand-shaking-8766/1080p.mp4"],
            "nature": ["https://cdn.coverr.co/videos/coverr-waterfall-in-forest-2765/1080p.mp4"],
            "city": ["https://cdn.coverr.co/videos/coverr-night-traffic-in-tokyo-1593/1080p.mp4"],
            "abstract": ["https://cdn.coverr.co/videos/coverr-blue-particles-2529/1080p.mp4"]
        }
        
        for key, links in fallback_db.items():
            if key in keyword.lower():
                return random.sample(links, min(count, len(links)))
        
        # Global Fallback
        return ["https://cdn.coverr.co/videos/coverr-blue-particles-2529/1080p.mp4"]

    async def download_stock_video(self, url: str, output_dir: str = "temp") -> str | None:
        """
        Downloads a stock video file to a local path.
        """
        os.makedirs(output_dir, exist_ok=True)
        filename = f"stock_{os.path.basename(url.split('?')[0])}.mp4"
        if not filename.endswith(".mp4"):
            filename += ".mp4"
            
        filepath = os.path.join(output_dir, filename)
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://coverr.co/"
            }
            async with httpx.AsyncClient(headers=headers) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return filepath
        except Exception as e:
            logging.error(f"[StockService] Error downloading {url}: {e}")
            return None

base_stock_service = StockService()
