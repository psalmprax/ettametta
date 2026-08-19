import httpx
import aiofiles
import os
import logging
import random
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.api.utils.vault import get_secret
from src.api.config import settings
from src.api.utils.resilience import CircuitBreaker

logger = logging.getLogger(__name__)


class StockService:
    """
    High-Definition Stock & Studio B-Roll Retrieval Service.
    Optimized for product showcases, cinematic macro shots, and 4K portrait videos.
    """

    def __init__(self):
        self.pexels_api_key = get_secret("pexels_api_key") or settings.PEXELS_API_KEY
        self.pexels_base_url = "https://api.pexels.com/videos"

        # Free fallback APIs (No Key Required)
        self.mixkit_base_url = "https://api.mixkit.co/videos/preview/"
        self.coverr_base_url = "https://coverr.co/api/videos"

        self.breakers = {
            "pexels": CircuitBreaker(name="Pexels"),
            "coverr": CircuitBreaker(name="Coverr"),
        }

    def optimize_product_broll_prompt(self, keyword: str) -> str:
        """
        Enhances raw keywords into high-converting studio product cinematography prompts.
        """
        raw = str(keyword or "").strip().lower()
        if not raw:
            return "cinematic studio product shot 4k bokeh portrait"

        modifiers = ["cinematic studio macro product shot", "4k resolution", "portrait", "professional studio lighting"]
        
        # Add niche specific modifiers
        if any(w in raw for w in ["phone", "laptop", "app", "software", "tech", "gadget", "ai"]):
            modifiers.append("sleek dark mode glass reflection 60fps")
        elif any(w in raw for w in ["shoe", "sneaker", "fashion", "apparel", "wear"]):
            modifiers.append("slow motion turn table dynamic lighting")
        elif any(w in raw for w in ["food", "drink", "coffee", "supplement", "beauty"]):
            modifiers.append("macro close up high speed camera depth of field")

        return f"{raw} {' '.join(modifiers)}"

    def _get_search_keywords(self, keyword: str) -> list[str]:
        if isinstance(keyword, list):
            keyword = " ".join(str(k) for k in keyword if k)
        keyword = str(keyword or "").strip()
        if not keyword:
            return ["cinematic studio product portrait"]

        optimized = self.optimize_product_broll_prompt(keyword)
        search_keywords = [optimized, keyword]
        
        if len(keyword.split()) > 2:
            parts = keyword.split()
            search_keywords.append(" ".join(parts[1:]))
            search_keywords.append(parts[-1])

        return search_keywords

    def _find_best_file(self, sorted_files: list) -> dict | None:
        # Prioritize 1080p+ portrait orientation files for maximum vertical quality
        for f in sorted_files:
            width = f.get("width") or 0
            height = f.get("height") or 0
            if width >= 1080 and height > width:
                return f
        # Fallback to highest resolution file available
        return sorted_files[0] if sorted_files else None

    def _parse_pexels_video_link(self, video: dict) -> str | None:
        video_files = video.get("video_files", [])
        if not video_files:
            return None

        sorted_files = sorted(
            video_files,
            key=lambda x: (x.get("width", 0) or 0),
            reverse=True
        )

        best_file = self._find_best_file(sorted_files)
        return best_file.get("link") if best_file else None

    async def _try_pexels(self, kw: str, pexels_key: str, pexels_headers: dict, count: int) -> list[str]:
        if not pexels_key or self.breakers["pexels"].is_open():
            return []
        try:
            async with httpx.AsyncClient(timeout=settings.STOCK_TIMEOUT) as client:
                params = {"query": kw, "per_page": 8, "orientation": "portrait"}
                response = await client.get(f"{self.pexels_base_url}/search", params=params, headers=pexels_headers)
                response.raise_for_status()

                data = response.json()
                videos = data.get("videos", [])
                urls = []
                for video in videos[:count]:
                    link = self._parse_pexels_video_link(video)
                    if link:
                        urls.append(link)
                self.breakers["pexels"].record_success()
                return urls
        except Exception as e:
            logger.warning(f"[StockService] Pexels failed for '{kw}': {e}")
            self.breakers["pexels"].record_failure()
            return []

    def _parse_coverr_video_link(self, item: dict) -> str | None:
        videos = item.get('videos', [])
        if not videos:
            return None

        best_v = next((v for v in videos if v.get('width') == 1920),
                 next((v for v in videos if v.get('width') == 1280), videos[0]))
        return best_v.get('url')

    async def _try_coverr(self, kw: str, count: int) -> list[str]:
        if self.breakers["coverr"].is_open():
            return []
        try:
            async with httpx.AsyncClient(timeout=settings.STOCK_TIMEOUT) as client:
                response = await client.get(f"{self.coverr_base_url}", params={"query": kw})
                response.raise_for_status()

                data = response.json()
                results = data.get("results", [])
                urls = []
                for item in results[:count]:
                    link = self._parse_coverr_video_link(item)
                    if link:
                        urls.append(link)
                self.breakers["coverr"].record_success()
                return urls
        except Exception as e:
            logger.warning(f"[StockService] Coverr failed for '{kw}': {e}")
            self.breakers["coverr"].record_failure()
            return []

    def _get_db_fallback(self, search_keywords: list[str], count: int) -> list[str] | None:
        fallback_db = {
            "tech": ["https://cdn.coverr.co/videos/coverr-robot-hand-shaking-8766/1080p.mp4"],
            "nature": ["https://cdn.coverr.co/videos/coverr-waterfall-in-forest-2765/1080p.mp4"],
            "city": ["https://cdn.coverr.co/videos/coverr-night-traffic-in-tokyo-1593/1080p.mp4"],
            "abstract": ["https://cdn.coverr.co/videos/coverr-blue-particles-2529/1080p.mp4"],
            "business": ["https://cdn.coverr.co/videos/coverr-typing-on-a-keyboard-5178/1080p.mp4"],
            "product": ["https://cdn.coverr.co/videos/coverr-typing-on-a-keyboard-5178/1080p.mp4"],
        }
        for kw_check in search_keywords:
            for key, links in fallback_db.items():
                if key in kw_check.lower():
                    return random.sample(links, min(count, len(links)))
        return None

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
        Searches for high-definition 4K portrait B-roll videos matching the keyword.
        Priority: Optimized Visual Prompt -> Pexels (4K Portrait) -> Coverr (HD Fallback)
        """
        pexels_key = self.pexels_api_key or get_secret("pexels_api_key") or settings.PEXELS_API_KEY
        pexels_headers = {"Authorization": pexels_key} if pexels_key else {}

        urls = []
        search_keywords = self._get_search_keywords(keyword)

        for kw in search_keywords:
            pexels_urls = await self._try_pexels(kw, pexels_key, pexels_headers, count - len(urls))
            urls.extend(pexels_urls)
            if len(urls) >= count:
                return urls[:count]

            coverr_urls = await self._try_coverr(kw, count - len(urls))
            urls.extend(coverr_urls)
            if len(urls) >= count:
                return urls[:count]

        fallback = self._get_db_fallback(search_keywords, count)
        if fallback:
            return fallback

        return ["https://cdn.coverr.co/videos/coverr-blue-particles-2529/1080p.mp4"]

    async def download_stock_video(self, url: str, output_dir: str = "temp") -> str | None:
        """
        Downloads a stock video file to a local path with retries.
        """
        os.makedirs(output_dir, exist_ok=True)
        base = os.path.basename(url.split("?")[0])
        if base.lower().endswith(".mp4"):
            base = base[:-4]
        filename = f"stock_{base}.mp4"
        filepath = os.path.abspath(os.path.join(output_dir, filename))

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
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(response.content)
                return filepath

        try:
            return await _do_download()
        except Exception:
            logger.exception(f"[StockService] Error downloading {url}")
            local_fallback = "/app/templates/safety/generic_space.mp4"
            if not os.path.exists(local_fallback):
                local_fallback = "templates/safety/generic_space.mp4"

            if os.path.exists(local_fallback):
                import shutil
                try:
                    shutil.copy2(local_fallback, filepath)
                    logger.info(f"[StockService] Dynamically recovered download failure using local fallback: {filepath}")
                    return filepath
                except Exception:
                    logger.exception("[StockService] Failed to copy local fallback video")
            return None


base_stock_service = StockService()
