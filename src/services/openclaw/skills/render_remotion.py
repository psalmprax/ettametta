import json
import subprocess
import logging
from typing import Any

from src.api.config import settings

from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class RemotionRenderSkill(OpenClawBaseSkill):
    """
    Skill for programmatic React-based video rendering via @remotion/cli.
    Provides pixel-perfect control over typography and animations.
    """

    def __init__(
        self,
        remotion_project_path: str | None = None,
    ):
        super().__init__()
        self.project_path = str(remotion_project_path or settings.REMOTION_APP_DIR)

    def execute(self, action: str = "render", composition: str = "main", props: dict = None, **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        comp = composition or kwargs.get("composition", "main")
        p = props or kwargs.get("props") or kwargs

        # Extract specific remotion flags from kwargs
        use_gpu = kwargs.get("use_gpu", False)
        frames = kwargs.get("frames")

        return self.render_remotion_clip(
            composition=comp,
            props=p,
            output_name=kwargs.get("output_name", "remotion_output.mp4"),
            use_gpu=use_gpu,
            frames=frames
        )

    def render_remotion_clip(
        self,
        composition: str,
        props: dict[str, Any],
        output_name: str = "remotion_output.mp4",
        use_gpu: bool = False,
        frames: str | None = None,
    ) -> str:
        """
        Executes a remotion render command.
        Example: npx remotion render <comp-id> out.mp4 --props='{"text": "Hello"}'
        """
        output_path = str(settings.REMOTION_OUTPUT_DIR / output_name)
        props_json = json.dumps(props)

        # Command construction
        cmd = [
            "npx",
            "remotion",
            "render",
            composition,
            output_path,
            f"--props={props_json}",
        ]

        if not use_gpu:
            cmd.append("--disable-gpu")
            # Force software rendering for maximum compatibility on CPU
            cmd.append("--gl=swiftshader")

        if frames:
            cmd.append(f"--frames={frames}")

        logger.info(f"Executing Remotion Render (GPU={'ON' if use_gpu else 'OFF'}): {' '.join(cmd)}")

        try:
            # Check if Node.js/NPX is installed
            subprocess.run(["npx", "--version"], check=True, capture_output=True)

            # Run the render in the project directory
            subprocess.run(
                cmd, cwd=self.project_path, check=True, capture_output=True, text=True
            )
            return f"🎬 **Remotion Render Success**\nComposition: `{composition}`\nOutput: {output_path}\nHardware: {'GPU' if use_gpu else 'CPU (Software)'}"
        except subprocess.CalledProcessError as e:
            logger.exception(f"Remotion Render Failed: {e.stderr}")
            return f"⚠️ Remotion Render Failed: {e.stderr}"
        except FileNotFoundError:
            return "⚠️ Remotion CLI not found. Please ensure Node.js and @remotion/cli are installed."
        except Exception as e:
            return f"⚠️ System Error during Remotion render: {str(e)}"


remotion_skill = RemotionRenderSkill()
