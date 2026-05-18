import httpx
import os
import logging
import random
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.api.utils.vault import get_secret
from src.api.config import settings
from src.api.utils.resilience import CircuitBreaker

logger = logging.getLogger(__name__)

class StockService:
    def __init__(self):
        self.pexels_api_key = get_secret("pexels_api_key") or settings.PEXELS_API_KEY
        self.pexels_base_url = "https://api.pexels.com/videos"
        
        # Free fallback APIs (No Key Required)
        self.mixkit_base_url = "https://api.mixkit.co/videos/preview/"
        self.coverr_base_url = "https://coverr.co/api/videos"
        
        self.breakers = {
            "pexels": CircuitBreaker(name="Pexels"),
            "coverr": CircuitBreaker(name="Coverr")
        }

    @retry(
        stop=stop_after_attempt(settings.DEFAULT_RETRY_COUNT),
        wait=wait_exponential(
            multiplier=settings.RETRY_MULTIPLIER, 
            min=settings.RETRY_MIN_WAIT, 
            max=settings.RETRY_MAX_WAIT
        ),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def fetch_b_roll(self, keyword: str, count: int = 1) -> list[str]:
        """
        Searches for videos matching the keyword.
        Priority: Pexels (High Quality) -> Coverr (Free Fallback)
        Hardened with Circuit Breakers and global settings.
        """
        # Re-read key each call to pick up late-set env vars
        pexels_key = self.pexels_api_key or get_secret("pexels_api_key") or settings.PEXELS_API_KEY
        pexels_headers = {"Authorization": pexels_key} if pexels_key else {}
        
        urls = []
        search_keywords = [keyword]
        if len(keyword.split()) > 2:
            parts = keyword.split()
            search_keywords.append(" ".join(parts[1:]))
            search_keywords.append(parts[-1])

        for kw in search_keywords:
            # 1. Try Pexels
            if pexels_key and not self.breakers["pexels"].is_open():
                try:
                    async with httpx.AsyncClient(timeout=settings.STOCK_TIMEOUT) as client:
                        params = {"query": kw, "per_page": 5, "orientation": "portrait"}
                        response = await client.get(f"{self.pexels_base_url}/search", params=params, headers=pexels_headers)
                        response.raise_for_status()
                        
                        data = response.json()
                        videos = data.get("videos", [])
                        if videos:
                            for video in videos[:count]:
                                video_files = video.get("video_files", [])
                                if not video_files:
                                    continue
                                
                                # Sort by width descending to get highest resolution (preferring 1080p+)
                                sorted_files = sorted(
                                    video_files, 
                                    key=lambda x: (x.get("width", 0) or 0), 
                                    reverse=True
                                )
                                
                                # Prefer HD/UHD but anything > 720p is good
                                best_file = next(
                                    (f for f in sorted_files if (f.get("width") or 0) >= 720), 
                                    sorted_files[0]
                                )
                                
                                if best_file:
                                    urls.append(best_file["link"])
                            
                            if len(urls) >= count:
                                self.breakers["pexels"].record_success()
                                return urls[:count]
                        self.breakers["pexels"].record_success() # Found nothing, but API worked
                except Exception as e:
                    logger.warning(f"[StockService] Pexels failed for '{kw}': {e}")
                    self.breakers["pexels"].record_failure()

            # 2. Try Coverr
            if not self.breakers["coverr"].is_open():
                try:
                    async with httpx.AsyncClient(timeout=settings.STOCK_TIMEOUT) as client:
                        response = await client.get(f"{self.coverr_base_url}", params={"query": kw})
                        response.raise_for_status()
                        
                        data = response.json()
                        results = data.get("results", [])
                        if results:
                            for item in results[:count]:
                                videos = item.get('videos', [])
                                if not videos:
                                    continue
                                
                                # Prefer 1080p, then 720p
                                best_v = next((v for v in videos if v.get('width') == 1920), 
                                         next((v for v in videos if v.get('width') == 1280), videos[0]))
                                
                                urls.append(best_v['url'])
                            
                            if len(urls) >= count:
                                self.breakers["coverr"].record_success()
                                return urls[:count]
                        self.breakers["coverr"].record_success()
                except Exception as e:
                    logger.warning(f"[StockService] Coverr failed for '{kw}': {e}")
                    self.breakers["coverr"].record_failure()

        # 3. Last Resort: High-Quality Public Domain Samples
        fallback_db = {
            "tech": ["https://cdn.coverr.co/videos/coverr-robot-hand-shaking-8766/1080p.mp4"],
            "nature": ["https://cdn.coverr.co/videos/coverr-waterfall-in-forest-2765/1080p.mp4"],
            "city": ["https://cdn.coverr.co/videos/coverr-night-traffic-in-tokyo-1593/1080p.mp4"],
            "abstract": ["https://cdn.coverr.co/videos/coverr-blue-particles-2529/1080p.mp4"],
            "business": ["https://cdn.coverr.co/videos/coverr-typing-on-a-keyboard-5178/1080p.mp4"]
        }
        
        for kw_check in search_keywords:
            for key, links in fallback_db.items():
                if key in kw_check.lower():
                    return random.sample(links, min(count, len(links)))
        
        # Global Fallback
        return ["https://cdn.coverr.co/videos/coverr-blue-particles-2529/1080p.mp4"]

    async def download_stock_video(self, url: str, output_dir: str = "temp") -> str | None:
        """
        Downloads a stock video file to a local path with retries.
        """
        os.makedirs(output_dir, exist_ok=True)
        filename = f"stock_{os.path.basename(url.split('?')[0])}.mp4"
        if not filename.endswith(".mp4"):
            filename += ".mp4"
            
        filepath = os.path.join(output_dir, filename)
        
        @retry(
            stop=stop_after_attempt(settings.DEFAULT_RETRY_COUNT),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            reraise=True
        )
        async def _do_download():
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://coverr.co/"
            }
            async with httpx.AsyncClient(headers=headers, timeout=settings.STOCK_TIMEOUT * 4) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return filepath

        try:
            return await _do_download()
        except Exception as e:
            logger.error(f"[StockService] Error downloading {url}: {e}")
            # Recover failed download dynamically using high-quality local template
            local_fallback = "/app/templates/safety/generic_space.mp4"
            if not os.path.exists(local_fallback):
                local_fallback = "templates/safety/generic_space.mp4"
            
            if os.path.exists(local_fallback):
                import shutil
                try:
                    shutil.copy2(local_fallback, filepath)
                    logger.info(f"[StockService] Dynamically recovered download failure for '{url}' using local fallback: {filepath}")
                    return filepath
                except Exception as copy_err:
                    logger.error(f"[StockService] Failed to copy local fallback video: {copy_err}")
            return None

base_stock_service = StockService()
