import httpx
import logging
import os
from api.config import settings

class ThumbnailGenerator:
    def __init__(self, output_dir: str = "outputs/thumbnails"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    async def generate_thumbnail(self, script_summary: str) -> str:
        """
        Generates a viral thumbnail using Pollinations.ai (free/open).
        """
        logging.info(f"[Thumbnail] Generating for script: {script_summary[:50]}...")
        
        # Craft a high-conversion prompt
        prompt = f"YouTube Thumbnail, high contrast, viral style, expressive features, {script_summary}, cinematic lighting, 4k"
        encoded_prompt = prompt.replace(" ", "%20")
        
        # Pollinations.ai simple GET endpoint
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed=42"
        
        try:
            # We just return the URL for now as it's a direct generator
            return image_url
        except Exception as e:
            logging.error(f"[Thumbnail] Generation Failed: {e}")
            return "https://via.placeholder.com/1280x720?text=Thumbnail+Generation+Failed"

base_thumbnail_generator = ThumbnailGenerator()
