import os
import json
import asyncio
import logging
import uuid
import shutil
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Any
from pathlib import Path
from src.api.config import settings
from src.api.utils.resilience import CircuitBreaker

logger = logging.getLogger(__name__)

class RemotionService:
    """
    Bridges Python logic to the Remotion React studio for programmatic video rendering.
    Hardened with Circuit Breaker and automated failure recovery.
    Uses non-blocking asyncio subprocess for production scale.
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
            logger.info(f"[RemotionService] Using browser at: {self.browser_path}")
        else:
            logger.warning("[RemotionService] No browser found in PATH. Remotion will attempt auto-download.")
        
        self.breaker = CircuitBreaker(name="RemotionRender", failure_threshold=2, recovery_timeout=300)

    @retry(
        stop=stop_after_attempt(2), 
        wait=wait_exponential(multiplier=2, min=10, max=60),
        retry=retry_if_exception_type(RuntimeError),
        reraise=True
    )
    async def render_video(self, composition_id: str, props: dict[str, Any], output_name: str = None) -> str | None:
        """
        Renders a video using Remotion CLI with non-blocking async monitoring.
        """
        if self.breaker.is_open():
            logger.error("[RemotionService] Circuit breaker is OPEN. Rendering denied.")
            raise RuntimeError("Remotion rendering service is temporarily unavailable (Circuit OPEN)")

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
                        logger.info(f"[RemotionService] Prepared physical asset: {filename}")
                except Exception as e:
                    logger.warning(f"[RemotionService] Asset prep failed for {src_path}: {e}")
                
                return f"assets/{filename}"

            # Prepare props by replacing absolute paths with public/assets relative paths
            def recursive_prep(obj):
                if isinstance(obj, dict):
                    return {k: recursive_prep(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [recursive_prep(i) for i in obj]
                elif isinstance(obj, str) and (os.path.isabs(obj) or "/outputs/" in obj or "temp/" in obj):
                    return prepare_asset(obj)
                return obj

            remotion_ready_props = recursive_prep(props)

            # Use non-blocking write for props
            with open(input_props_path, "w") as f:
                json.dump(remotion_ready_props, f)

            logger.info(f"[RemotionService] Starting non-blocking render for {composition_id}...")

            # 2. Invoke Remotion CLI
            local_bin = os.path.join(self.studio_path, "node_modules", ".bin", "remotion")
            if os.path.exists(local_bin):
                program = local_bin
                args = []
            else:
                program = "npx"
                args = ["remotion"]
                
            args.extend([
                "render",
                "src/index.ts",
                composition_id,
                output_path,
                "--props", input_props_path,
            ])
            
            if self.browser_path:
                args.extend(["--browser-executable", self.browser_path])

            args.extend(["--concurrency", "1"])

            if "duration_in_frames" in props:
                args.extend(["--frames", f"0-{props['duration_in_frames']}"])
                
            args.extend([
                "--chromium-flags", "--no-sandbox --disable-setuid-sandbox --disable-web-security --disable-gpu --disable-dev-shm-usage --single-process --js-flags='--max-old-space-size=1024'",
                "--public-dir=public",
                "--scale", "0.5" if "test" in (output_name or "") else "1",
                "--force"
            ])

            # Use settings for rendering timeout
            timeout = settings.LLM_TIMEOUT * 10 

            # Non-blocking subprocess execution
            process = await asyncio.create_subprocess_exec(
                program,
                *args,
                cwd=self.studio_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                
                if process.returncode == 0:
                    logger.info(f"[RemotionService] Render complete: {output_path}")
                    self.breaker.record_success()
                    return output_path
                else:
                    error_msg = stderr.decode()[-2000:] if stderr else "Unknown error"
                    logger.error(f"[RemotionService] Render failed (code {process.returncode}): {error_msg}")
                    self.breaker.record_failure()
                    raise RuntimeError(f"Remotion render failed with code {process.returncode}")
                    
            except asyncio.TimeoutExpired:
                process.kill()
                logger.error(f"[RemotionService] Render TIMEOUT after {timeout}s")
                self.breaker.record_failure()
                raise RuntimeError("Remotion render timed out")

        except Exception as e:
            logger.error(f"[RemotionService] Error during render: {e}")
            self.breaker.record_failure()
            raise
        finally:
            if os.path.exists(input_props_path):
                try:
                    os.remove(input_props_path)
                except:
                    pass

base_remotion_service = RemotionService()
