import requests
import logging
from config import settings

logger = logging.getLogger(__name__)

class RenderSkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}/remotion"

    def render_clip(self, title: str, subtitle: str, video_url: str = None) -> str:
        """
        Triggers a programmatic video render using Remotion.
        """
        try:
            payload = {
                "title": title,
                "subtitle": subtitle,
                "video_url": video_url or "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
            }
            
            # This calls the upcoming /remotion/render endpoint on the main API
            response = requests.post(f"{self.api_url}/render", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id", "Unknown")
                return f"🎨 **Render Initiated!**\nTitle: {title}\nJob ID: `{job_id}`\n\nI will notify you once the cinematic clip is ready."
            else:
                return f"⚠️ **Render Failed**: server returned {response.status_code}"
                
        except Exception as e:
            logger.error(f"Render Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

render_skill = RenderSkill()
