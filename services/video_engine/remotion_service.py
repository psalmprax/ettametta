import os
import json
import subprocess
import logging
import uuid
from typing import Dict, Any, Optional
from pathlib import Path

class RemotionService:
    """
    Bridges Python logic to the Remotion React studio for programmatic video rendering.
    """

    def __init__(self, studio_path: str = "apps/remotion-studio"):
        self.studio_path = os.path.abspath(studio_path)
        self.output_dir = os.path.join(self.studio_path, "out")
        os.makedirs(self.output_dir, exist_ok=True)

    async def render_video(self, composition_id: str, props: Dict[str, Any], output_name: str = None) -> Optional[str]:
        """
        Renders a video using Remotion CLI.
        """
        job_id = str(uuid.uuid4())[:8]
        if not output_name:
            output_name = f"render_{job_id}.mp4"
        
        output_path = os.path.join(self.output_dir, output_name)
        input_props_path = os.path.join(self.studio_path, f"props_{job_id}.json")

        try:
            # 1. Write props to temporary JSON file
            with open(input_props_path, "w") as f:
                json.dump(props, f)

            logging.info(f"[RemotionService] Starting render for {composition_id}...")

            # 2. Invoke Remotion CLI
            # We use npx remotion render <entry> <comp-id> <output> --props <props-file>
            cmd = [
                "npx", "remotion", "render",
                "src/index.ts",
                composition_id,
                output_path,
                "--props", input_props_path,
                "--browser-executable", "/usr/bin/chromium" # Expected path in Docker
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
remotion_service = RemotionService()
