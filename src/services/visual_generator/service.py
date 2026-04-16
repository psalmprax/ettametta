import httpx
import logging
import os
from typing import Optional
from api.config import settings

class VisualGenerator:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/images/generations"

    async def generate_image(self, prompt: str) -> Optional[str]:
        """
        Generates a high-impact image. Attempts OpenAI DALL-E 3 first, fallbacks to Pollinations.ai.
        """
        os.makedirs("outputs/images", exist_ok=True)
        file_name = f"gen_{hash(prompt) % 1000000}.png"
        file_path = os.path.join("outputs/images", file_name)

        if self.api_key:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "dall-e-3",
                "prompt": f"Professional cinematic high-impact visual for a viral social media video topic: {prompt}. Dynamic lighting, 9:16 aspect ratio style, hyper-realistic.",
                "n": 1,
                "size": "1024x1792",
                "quality": "hd"
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(self.base_url, headers=headers, json=data, timeout=60.0)
                    if response.status_code == 200:
                        image_url = response.json().get("data", [{}])[0].get("url")
                        if image_url:
                            img_res = await client.get(image_url)
                            if img_res.status_code == 200:
                                with open(file_path, "wb") as f:
                                    f.write(img_res.content)
                                return f"images/{file_name}"
            except Exception as e:
                logging.error(f"[VisualGenerator] OpenAI Exception: {e}. Falling back to Pollinations.")

        # Fallback to Pollinations.ai (Free / No Key)
        try:
            # Pollinations expects a URL-encoded prompt
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt)
            # Use portrait orientation for short-form content
            pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1792&nologo=true&seed={hash(prompt) % 1000}"
            
            async with httpx.AsyncClient() as client:
                img_res = await client.get(pollinations_url, timeout=30.0)
                if img_res.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(img_res.content)
                    return f"images/{file_name}"
        except Exception as e:
            logging.error(f"[VisualGenerator] Pollinations Fallback Failed: {e}")
            return None

base_visual_generator = VisualGenerator()
