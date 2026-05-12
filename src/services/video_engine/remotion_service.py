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
                           shutil.which("chromium-browser")
        
        if self.browser_path:
            logging.info(f"[RemotionService] Using browser at: {self.browser_path}")
        else:
            logging.warning("[RemotionService] No browser found in PATH. Remotion will attempt auto-download.")

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
            # Create a clean assets directory in public
            public_assets_dir = os.path.join(self.studio_path, "public", "assets")
            os.makedirs(public_assets_dir, exist_ok=True)
            
            # Helper to copy and return relative path
            def prepare_asset(src_path: str) -> str:
                if not src_path or src_path.startswith("http"):
                    return src_path
                
                filename = os.path.basename(src_path)
                dest_path = os.path.join(public_assets_dir, filename)
                
                try:
                    if os.path.exists(src_path) and os.path.abspath(src_path) != os.path.abspath(dest_path):
                        shutil.copy2(src_path, dest_path)
                        logging.info(f"[RemotionService] Prepared physical asset: {filename}")
                except Exception as e:
                    logging.warning(f"[RemotionService] Asset prep failed for {src_path}: {e}")
                
                return f"assets/{filename}"

            # Prepare props by replacing absolute paths with public/assets relative paths
            def recursive_prep(obj):
                if isinstance(obj, dict):
                    return {k: recursive_prep(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [recursive_prep(i) for i in obj]
                elif isinstance(obj, str) and (os.path.isabs(obj) or "/outputs/" in obj):
                    return prepare_asset(obj)
                return obj

            remotion_ready_props = recursive_prep(props)

            with open(input_props_path, "w") as f:
                json.dump(remotion_ready_props, f)

            logging.info(f"[RemotionService] Starting render for {composition_id}...")

            # 2. Invoke Remotion CLI
            local_bin = os.path.join(self.studio_path, "node_modules", ".bin", "remotion")
            if os.path.exists(local_bin):
                cmd_base = [local_bin]
            else:
                cmd_base = ["npx", "remotion"]
                
            cmd = cmd_base + [
                "render",
                "src/index.ts",
                composition_id,
                output_path,
                "--props", input_props_path,
            ]
            
            if self.browser_path:
                cmd.extend(["--browser-executable", self.browser_path])
                
            # Add security bypass for Docker
            cmd.extend([
                "--chromium-flags", "--no-sandbox --disable-setuid-sandbox --disable-web-security",
                "--public-dir=public",
                "--port", "3005",
                "--force"
            ])

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
                error_msg = stderr or stdout
                logging.error(f"[RemotionService] Render failed: {error_msg}")
                print(f"REMOTION_ERROR_STDOUT: {stdout}")
                print(f"REMOTION_ERROR_STDERR: {stderr}")
                return None

        except Exception as e:
            logging.error(f"[RemotionService] Error during render: {e}")
            return None
        finally:
            # Cleanup props file
            if os.path.exists(input_props_path):
                # os.remove(input_props_path)
                logging.info(f"[RemotionService] Debug: Props kept at {input_props_path}")

# Singleton instance
base_remotion_service = RemotionService()
