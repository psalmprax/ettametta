import requests
import logging
from config import settings

logger = logging.getLogger(__name__)

class AgentZeroSkill:
    """
    OpenClaw skill to control the autonomous Agent Zero Director.
    """
    def __init__(self):
        # Note: In a production setup, AgentZero might have its own API port.
        # For this integration, we'll assume it's manageable via internal calls 
        # or we'll trigger the base_agent_zero instance directly if in-process.
        # For the prototype, we assume OpenClaw is the management layer.
        pass

    def control_agent(self, action: str) -> str:
        """
        Sends control commands (start/stop/status) to Agent Zero.
        """
        try:
            # For this integrated version, we'll use a direct singleton import
            # In a distributed system, this would be a requests.post call.
            # Try absolute import from the project root (services.agent_zero)
            try:
                from services.agent_zero.agent import base_agent_zero
            except ImportError:
                # Fallback for different environments or legacy paths
                import sys
                import os
                sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
                from services.agent_zero.agent import base_agent_zero
            
            if action == "start":
                import asyncio
                # We trigger the background loop
                asyncio.create_task(base_agent_zero.start())
                return "🚀 **Agent Zero Loop Started!** The autonomous director is now active."
            elif action == "stop":
                base_agent_zero.stop()
                return "🛑 **Agent Zero Loop Stopped.** Autonomy suspended."
            elif action == "status":
                status = "RUNNING" if base_agent_zero.is_running else "STOPPED"
                return f"🤖 **Agent Zero Status:** `{status}`"
            else:
                return "⚠️ Invalid action. Use: start, stop, status."
                
        except Exception as e:
            logger.error(f"AgentZeroSkill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

agent_zero_skill = AgentZeroSkill()
