import os
import json
import subprocess
import logging
from typing import Any

from src.api.config import settings

logger = logging.getLogger(__name__)


class RemotionRenderSkill:
    """
    Skill for programmatic React-based video rendering via @remotion/cli.
    Provides pixel-perfect control over typography and animations.
    """

    def __init__(
        self,
        remotion_project_path: str | None = None,
    ):
        self.project_path = str(remotion_project_path or settings.REMOTION_APP_DIR)

    def render_remotion_clip(
        self,
        composition: str,
        props: dict[str, Any],
        output_name: str = "remotion_output.mp4",
    ) -> str:
        """
        Executes a remotion render command.
        Example: npx remotion render <comp-id> out.mp4 --props='{"text": "Hello"}'
        """
        output_path = str(settings.OUTPUT_DIR / output_name)
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

        logger.info(f"Executing Remotion Render: {' '.join(cmd)}")

        try:
            # Check if Node.js/NPX is installed
            subprocess.run(["npx", "--version"], check=True, capture_output=True)

            # Run the render in the project directory
            result = subprocess.run(
                cmd, cwd=self.project_path, check=True, capture_output=True, text=True
            )
            return f"🎬 **Remotion Render Success**\nComposition: `{composition}`\nOutput: {output_path}"
        except subprocess.CalledProcessError as e:
            return f"⚠️ Remotion Render Failed: {e.stderr}"
        except FileNotFoundError:
            return "⚠️ Remotion CLI not found. Please ensure Node.js and @remotion/cli are installed."
        except Exception as e:
            return f"⚠️ System Error during Remotion render: {str(e)}"


remotion_skill = RemotionRenderSkill()
