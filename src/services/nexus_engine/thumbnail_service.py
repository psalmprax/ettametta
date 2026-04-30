import httpx
import logging
import os
import uuid
from pathlib import Path
from src.services.storage.service import base_storage_service
from src.api.config import settings

class ThumbnailGenerator:
    def __init__(self, output_dir: str = "outputs/thumbnails"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    async def generate_thumbnail(self, script_summary: str) -> str:
        """
        Generates a viral thumbnail using Pollinations.ai (free/open).
        Downloads the asset and stores it in the configured storage provider.
        """
        logging.info(f"[Thumbnail] Generating for script: {script_summary[:50]}...")
        
        # Craft a high-conversion prompt
        prompt = f"YouTube Thumbnail, high contrast, viral style, expressive features, {script_summary}, cinematic lighting, 4k"
        encoded_prompt = prompt.replace(" ", "%20")
        
        # Pollinations.ai simple GET endpoint
        image_uri = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed=42"
        
        try:
            # 1. Download the generated asset
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_uri)
                if response.status_code != 200:
                    raise RuntimeError(f"Pollinations returned status {response.status_code}")
                
                # 2. Save to local temporary file
                filename = f"thumb_{uuid.uuid4().hex[:8]}.jpg"
                temp_path = os.path.join(self.output_dir, filename)
                
                with open(temp_path, "wb") as f:
                    f.write(response.content)
                
                # 3. Upload to official storage
                storage_path = base_storage_service.upload_file(temp_path)
                public_url = base_storage_service.get_file_url(storage_path)

                
                logging.info(f"[Thumbnail] Successfully stored at: {public_url}")
                return public_url
                
        except Exception as e:
            logging.error(f"[Thumbnail] Generation Failed: {e}")
            # Return original Pollinations URL as a non-breaking fallback
            return image_uri

base_thumbnail_service = ThumbnailGenerator()
