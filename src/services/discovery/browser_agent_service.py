import os
import logging
from typing import Any, Dict
from src.api.config import settings

logger = logging.getLogger(__name__)

class BrowserAgentService:
    """
    Ettametta Browser Agent Service
    Uses browser-use + playwright for autonomous discovery and research.
    """

    def __init__(self):
        self.enabled = os.getenv("ENABLE_BROWSER_AGENTS", "true").lower() == "true"
        # Browser agents usually need a powerful model
        self.model_provider = os.getenv("BROWSER_AGENT_PROVIDER", "ollama")
        self.model_name = os.getenv("BROWSER_AGENT_MODEL", settings.OLLAMA_MODEL)

    async def research_trend(self, topic: str, target_platform: str = "tiktok") -> Dict[str, Any]:
        """
        Uses an autonomous agent to research a specific trend or topic.
        """
        if not self.enabled:
            logger.warning("[BrowserAgentService] Browser agents are disabled.")
            return {"error": "Service disabled"}

        try:
            from browser_use import Agent
            from langchain_openai import ChatOpenAI # browser-use often uses LangChain wrappers

            # 1. Setup the LLM for the agent
            # Note: browser-use works best with models that support tool calling.
            # If using Ollama, we ensure it's a model like llama3 or similar.

            # For this implementation, we'll assume the user has configured
            # a compatible LangChain-compatible LLM endpoint.
            llm = self._get_agent_llm()

            task = f"Go to {target_platform}.com and find the top 3 trending videos about '{topic}'. " \
                   "Extract the video titles, view counts, and a brief description of the 'hook' used."

            agent = Agent(
                task=task,
                llm=llm,
            )

            logger.info(f"🕵️ [BrowserAgentService] Starting research task: {task}")
            history = await agent.run()

            # Process history to extract the final result
            result = history.final_result()

            return {
                "topic": topic,
                "platform": target_platform,
                "research_data": result,
                "status": "completed"
            }

        except ImportError:
            logger.exception("[BrowserAgentService] browser-use or langchain-openai not installed.")
            return {"error": "Dependencies missing"}
        except Exception as e:
            logger.exception(f"[BrowserAgentService] Research task failed: {e}")
            return {"error": str(e)}

    def _get_agent_llm(self):
        """Returns a LangChain-compatible LLM instance for the browser agent."""
        from langchain_openai import ChatOpenAI

        if self.model_provider == "ollama":
            # Using the Ollama endpoint via ChatOpenAI (OpenAI-compatible)
            return ChatOpenAI(
                model=self.model_name,
                base_url=f"{settings.OLLAMA_URL.rstrip('/')}/v1",
                api_key="ollama",  # Ollama doesn't require auth; non-empty string required by OpenAI client
            )
        elif self.model_provider == "openai":
            return ChatOpenAI(
                model="gpt-4o",
                api_key=settings.OPENAI_API_KEY
            )
        else:
            # Fallback or other providers
            return ChatOpenAI(
                model=self.model_name,
                base_url=f"{settings.OLLAMA_URL.rstrip('/')}/v1",
                api_key="ollama"
            )

# Singleton instance
base_browser_agent_service = BrowserAgentService()
