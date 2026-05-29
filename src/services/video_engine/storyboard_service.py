import asyncio
import aiohttp
import base64
import os
import logging
import subprocess
import shutil
from pathlib import Path
from bs4 import BeautifulSoup
import aiofiles

logger = logging.getLogger("StoryboardService")
logging.basicConfig(level=logging.INFO)

class StoryboardService:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.output_dir = Path("downloads/storyboard")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Dynamic FFmpeg discovery for system portability
        self.ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"

    async def fetch_likeness_image(self, character_name: str) -> str:
        """
        Fetches an HD portrait for the requested character.
        Tries: DuckDuckGo HTML scraping → Wikipedia API → fallback placeholder.
        Returns base64 encoded image or empty string.
        """
        logger.info(f"Sourcing HD Reference Image for '{character_name}'...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with aiohttp.ClientSession() as session:
            # Strategy 1: DuckDuckGo HTML image search
            try:
                search_url = f"https://html.duckduckgo.com/html/?q={character_name.replace(' ', '+')}+portrait+high+definition"
                async with session.get(search_url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        # Parse DuckDuckGo result links for image URLs
                        for link in soup.find_all("a", class_="result__a"):
                            href = link.get("href", "")
                            if any(ext in href.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                                if "duckduckgo.com" not in href:
                                    img_url = href
                                    logger.info(f"   => Found DDG image: {img_url[:80]}")
                                    async with session.get(img_url, headers=headers, timeout=10) as img_resp:
                                        if img_resp.status == 200:
                                            img_data = await img_resp.read()
                                            if len(img_data) > 5000:  # Skip tiny placeholders
                                                return base64.b64encode(img_data).decode('utf-8')
            except Exception as e:
                logger.debug(f"DDG search failed: {e}")

            # Strategy 2: Wikipedia API for known characters
            try:
                wiki_api = f"https://en.wikipedia.org/api/rest_v1/page/summary/{character_name.replace(' ', '_')}"
                async with session.get(wiki_api, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        thumb = data.get("thumbnail", {})
                        img_url = thumb.get("source", "")
                        if img_url:
                            logger.info(f"   => Found Wikipedia image: {img_url[:80]}")
                            async with session.get(img_url, headers=headers, timeout=10) as img_resp:
                                if img_resp.status == 200:
                                    img_data = await img_resp.read()
                                    if len(img_data) > 5000:
                                        return base64.b64encode(img_data).decode('utf-8')
            except Exception as e:
                logger.debug(f"Wikipedia API failed: {e}")

            # Strategy 3: Generate a placeholder image with the character's initials
            try:
                initials = "".join(w[0].upper() for w in character_name.split()[:2])
                placeholder_url = f"https://ui-avatars.com/api/?name={initials}&size=512&background=random&color=fff&bold=true&format=png"
                logger.info(f"   => Using generated avatar for '{character_name}'")
                async with session.get(placeholder_url, timeout=10) as img_resp:
                    if img_resp.status == 200:
                        img_data = await img_resp.read()
                        return base64.b64encode(img_data).decode('utf-8')
            except Exception as e:
                logger.debug(f"Avatar generation failed: {e}")

        logger.warning(f"No image found for '{character_name}'")
        return ""

    async def generate_scene(self, prompt: str, character_name: str = None, frames: int = 49, steps: int = 20) -> str | None:
        """
        Requests an Image-to-Video generation using the remote RTX 6000 node.
        """
        b64_image = ""
        if character_name:
            b64_image = await self.fetch_likeness_image(character_name)

        scene_payload = {
            "prompt": prompt,
            "frames": frames,
            "steps": steps,
            "upscale_factor": 1, # Keep at 1 for testing speed, change to 4 for 4K
            "purge_hallucination": True
        }

        if b64_image:
            scene_payload["image_base64"] = b64_image
            logger.info("Injecting Likeness Portrait into AI Diffusion stream (Image-To-Video active).")

        logger.info(f"🎬 Requesting Shot: '{prompt[:60]}...'")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/video", json=scene_payload, timeout=20) as r:
                    if r.status == 200:
                        job = await r.json()
                        job_id = job["job_id"]
                        logger.info(f"   => 🟢 Job Started: {job_id}")
                        return job_id
                    else:
                        logger.error(f"   => ❌ Error starting job: HTTP {r.status} - {await r.text()}")
                        return None
        except Exception as e:
            logger.exception(f"   => ❌ API Request failed: {e}")
            return None

    async def poll_and_download(self, job_id: str, output_path: str):
        logger.info(f"   ⏳ Polling {job_id} until completion...")
        download_url = f"{self.api_url}/download/{job_id}"
        
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(download_url, timeout=10) as r:
                        if r.status == 200:
                            logger.info(f"   📥 Downloading {job_id} to local disk...")
                            content = await r.read()
                            async with aiofiles.open(output_path, 'wb') as f:
                                await f.write(content)
                            logger.info(f"   ✅ Saved clip: {output_path}")
                            return True
                        elif r.status == 404:
                            # Not ready yet
                            await asyncio.sleep(15)
                        else:
                            logger.warning(f"Unexpected status {r.status}")
                            await asyncio.sleep(15)
            except Exception as e:
                logger.warning(f"Connection error: {e}")
                await asyncio.sleep(15)

    def assemble_master(self, video_files: list, final_output: str):
        logger.info(f"🎞️ Assembling {len(video_files)} sequential shots into Master Sequence...")
        list_file = self.output_dir / "concat_list.txt"
        
        with open(list_file, "w") as f:
            for vf in video_files:
                f.write(f"file '{os.path.abspath(vf)}'\n")
        
        cmd = [
            self.ffmpeg_path, "-y", "-", "concat", "-safe", "0", "-i", str(list_file), 
            "-c", "copy", final_output
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            logger.info(f"🌟 Master Sequence Completed Successfully: {final_output}")
        except subprocess.CalledProcessError as e:
            logger.exception(f"❌ Error during multi-shot assembly: {e}")
        finally:
            if list_file.exists():
                os.remove(list_file)

if __name__ == "__main__":
    # Internal Test Routine
    async def main_test():
        composer = StoryboardService()
        
        # We will test an Image-to-Video sequence.
        # Generating 1 minute of video directly (1440 frames) is unsupported by current foundational open-source models (LTX/SVD).
        # Standard cinematography generates a 1 minute video by concatenating 10 to 12 x 5-second scenes.
        print("======== TESTING ETTAMETTA LIKENESS ENGINE ========")
        job_id = await composer.generate_scene(
            prompt="High quality cinematic portrait of Davido on stage performing, neon lighting, highly detailed, expressive face, 4k",
            character_name="Davido",
            frames=25  # ~1 second B-Roll test
        )
        
        if job_id:
            out_file = str(composer.output_dir / f"likeness_test_{job_id}.mp4")
            await composer.poll_and_download(job_id, out_file)
            print(f"TEST COMPLETE. CHECK OUTPUT AT: {out_file}")

    asyncio.run(main_test())
