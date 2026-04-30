import requests
import logging
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class AgentZeroSkill(OpenClawBaseSkill):
    """
    OpenClaw skill to control the autonomous Agent Zero Director.
    """

    def __init__(self):
        super().__init__()
        # Note: In a production setup, AgentZero might have its own API port.

    def execute(self, action: str = "status", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        return self.control_agent(action)

    def control_agent(self, action: str) -> str:
        """
        Sends control commands (start/stop/status) to Agent Zero.
        Uses API calls instead of direct imports for distributed compatibility.
        """
        try:
            if action == "start":
                try:
                    from src.services.agent_zero.agent import base_agent_zero_service_service
                    import threading

                    def _start_async():
                        import asyncio

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(base_agent_zero_service_service.start())

                    thread = threading.Thread(target=_start_async, daemon=True)
                    thread.start()
                    return "🚀 **Agent Zero Loop Started!** The autonomous director is now active."
                except Exception as e:
                    return f"⚠️ Failed to start Agent Zero: {e}"
            elif action == "stop":
                try:
                    from src.services.agent_zero.agent import base_agent_zero_service_service

                    base_agent_zero_service_service.stop()
                    return "🛑 **Agent Zero Loop Stopped.** Autonomy suspended."
                except Exception as e:
                    return f"⚠️ Failed to stop Agent Zero: {e}"
            elif action == "status":
                try:
                    from src.services.agent_zero.agent import base_agent_zero_service_service

                    status = "RUNNING" if base_agent_zero_service_service.is_running else "STOPPED"
                    step = (
                        base_agent_zero_service_service.current_step
                        if base_agent_zero_service_service.is_running
                        else "N/A"
                    )
                    last_run = (
                        str(base_agent_zero_service_service.last_run_at)
                        if base_agent_zero_service_service.last_run_at
                        else "Never"
                    )
                    return (
                        f"🤖 **Agent Zero Status**\n"
                        f"• State: `{status}`\n"
                        f"• Current Step: `{step}`\n"
                        f"• Last Run: `{last_run}`"
                    )
                except Exception as e:
                    return f"⚠️ Failed to get status: {e}"
            else:
                return "⚠️ Invalid action. Use: start, stop, status."
        except Exception as e:
            logger.error(f"AgentZeroSkill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"


agent_zero_skill = AgentZeroSkill()
