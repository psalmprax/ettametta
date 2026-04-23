import os
import json
import subprocess
import logging
import uuid
import shutil
from typing import Any
from pathlib import Path
from src.api.config import settings

class RemotionService:
    """
    Bridges Python logic to the Remotion React studio for programmatic video rendering.
    """

    def __init__(self, studio_path: str | None = None):
        self.studio_path = os.path.abspath(studio_path or settings.REMOTION_STUDIO_PATH)
        self.output_dir = os.path.join(self.studio_path, "out")
        os.makedirs(self.output_dir, exist_ok=True)
        # Dynamic browser discovery
        self.browser_path = os.getenv("CHROMIUM_PATH") or \
                           shutil.which("chromium") or \
                           shutil.which("chromium-browser") or \
                           "/usr/bin/chromium"
        logging.info(f"[RemotionService] Using browser at: {self.browser_path}")

    async def render_video(self, composition_id: str, props: dict[str, Any], output_name: str = None) -> str | None:
        """
        Renders a video using Remotion CLI.
        """
        job_id = str(uuid.uuid4())[:8]
        if not output_name:
            output_name = f"render_{job_id}.mp4"
        
        output_path = os.path.join(self.output_dir, output_name)
        input_props_path = os.path.join(self.studio_path, f"props_{job_id}.json")

        try:
            # --- HARDENING: Path Mapping for Remotion Browser Security ---
            # Remotion cannot access arbitrary absolute paths. We use the public/assets symlink.
            hardened_props = json.loads(json.dumps(props))
            
            def harden_path(val):
                if isinstance(val, str) and (os.path.isabs(val) or "/" in val):
                    return f"./assets/{os.path.basename(val)}"
                return val

            # Top level hardening
            for key in ["video_url", "audio_url", "trademark_url"]:
                if key in hardened_props and hardened_props[key]:
                    hardened_props[key] = harden_path(hardened_props[key])

            # Nested list hardening (timeline/sections)
            for list_key in ["timeline", "sections", "clips"]:
                if list_key in hardened_props and isinstance(hardened_props[list_key], list):
                    for item in hardened_props[list_key]:
                        for path_key in ["videoPath", "url"]:
                            if path_key in item and item[path_key]:
                                item[path_key] = harden_path(item[path_key])

            # 1. Write props to temporary JSON file
            with open(input_props_path, "w") as f:
                json.dump(hardened_props, f)

            logging.info(f"[RemotionService] Starting render for {composition_id}...")

            # 2. Invoke Remotion CLI
            cmd = [
                "npx", "remotion", "render",
                "src/index.ts",
                composition_id,
                output_path,
                "--props", input_props_path,
                "--browser-executable", self.browser_path,
            ]

            process = subprocess.Popen(
                cmd,
                cwd=self.studio_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                logging.info(f"[RemotionService] Render complete: {output_path}")
                return output_path
            else:
                logging.error(f"[RemotionService] Render failed: {stderr}")
                return None

        except Exception as e:
            logging.error(f"[RemotionService] Error during render: {e}")
            return None
        finally:
            # Cleanup props file
            if os.path.exists(input_props_path):
                os.remove(input_props_path)

# Singleton instance
base_remotion_service = RemotionService()
