import httpx
import logging
from typing import List, Dict, Any
from api.config import settings

class StockMediaService:
    def __init__(self):
        self.api_key = settings.PEXELS_API_KEY
        self.base_url = "https://api.pexels.com/videos"

    async def search_videos(self, query: str, per_page: int = 5) -> List[Dict[str, Any]]:
        """
        Searches for vertical stock videos on Pexels.
        """
        if not self.api_key:
            logging.error("[StockMediaService] No Pexels API Key found.")
            return []

        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": "portrait"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/search", headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for video in data.get("videos", []):
                        # Get the best vertical file
                        best_file = None
                        for file in video.get("video_files", []):
                            if file.get("width") < file.get("height"):
                                best_file = file.get("link")
                                break
                        
                        if best_file:
                            results.append({
                                "id": video.get("id"),
                                "url": best_file,
                                "preview": video.get("image"),
                                "duration": video.get("duration")
                            })
                    return results
                else:
                    logging.error(f"[StockMediaService] API Error: {response.text}")
                    return []
        except Exception as e:
            logging.error(f"[StockMediaService] Exception: {e}")
            return []

base_stock_service = StockMediaService()
