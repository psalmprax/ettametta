import subprocess
import json
import logging
from src.api.config import settings

logger = logging.getLogger(__name__)

class RemotionTool:
    """
    Agent Zero tool for programmatic video generation via Remotion.
    """
    
    def __init__(self):
        self.remotion_path = str(settings.REMOTION_APP_DIR)
        
    def render(self, composition: str, text: str, theme: str = "dark") -> str:
        """
        Render a specific composition with text and theme props.
        """
        output_file = str(settings.REMOTION_OUTPUT_DIR / f"agent_zero_{composition}.mp4")
        props = {
            "title": text,
            "theme": theme,
            "brand": "Ettametta"
        }
        
        cmd = [
            "npx", "remotion", "render",
            composition,
            output_file,
            f"--props={json.dumps(props)}"
        ]
        
        try:
            logger.info(f"Agent Zero executing Remotion: {' '.join(cmd)}")
            subprocess.run(cmd, cwd=self.remotion_path, check=True, capture_output=True)
            return f"🎨 Remotion Render Complete for '{composition}'. Path: {output_file}"
        except Exception as e:
            return f"❌ Remotion execution failed: {str(e)}"

remotion_tool = RemotionTool()

def run(action: str, **kwargs) -> str:
    """
    Entry point for Agent Zero tool execution.
    """
    if action == "render":
        return remotion_tool.render(
            kwargs.get("composition", "MainText"),
            kwargs.get("text", "Default Text"),
            kwargs.get("theme", "dark")
        )
    return "Unknown action for Remotion tool."
