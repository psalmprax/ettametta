import requests
import logging
from typing import Dict, Any
from services.openclaw.config import settings

logger = logging.getLogger(__name__)

class PublishTool:
    """
    Standardized Tool for Agent Zero to publish content to social platforms.
    """
    def __init__(self):
        self.api_url = f"{settings.API_URL}/publish"

    def run(self, video_path: str, platform: str, title: str, description: str = "") -> Dict[str, Any]:
        """
        Publishes a video file to the specified platform (YouTube, TikTok, Instagram).
        """
        try:
            payload = {
                "video_path": video_path,
                "platform": platform,
                "title": title,
                "description": description
            }
            # Note: Assuming POST /publish/video or similar based on publish.py
            response = requests.post(f"{self.api_url}/video", json=payload, timeout=60)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}", "detail": response.text}
                
        except Exception as e:
            logger.error(f"PublishTool Error: {e}")
            return {"error": str(e)}

publish_tool = PublishTool()
