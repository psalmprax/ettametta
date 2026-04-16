import requests
import logging
from typing import Dict, Any
from services.openclaw.config import settings

logger = logging.getLogger(__name__)

class RenderTool:
    """
    Standardized Tool for Agent Zero to trigger Remotion video renders.
    """
    def __init__(self):
        self.api_url = f"{settings.API_URL}/remotion/render"

    def run(self, title: str, subtitle: str, video_url: str = "", audio_url: str = "") -> Dict[str, Any]:
        """
        Triggers a headless Remotion render with the specified props.
        """
        try:
            payload = {
                "title": title,
                "subtitle": subtitle,
                "video_url": video_url,
                "audio_url": audio_url
            }
            response = requests.post(self.api_url, json=payload, timeout=30)
            
            if response.status_code in [200, 202]:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}", "detail": response.text}
                
        except Exception as e:
            logger.error(f"RenderTool Error: {e}")
            return {"error": str(e)}

render_tool = RenderTool()
