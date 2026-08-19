import os
import logging
from typing import Any, Dict
from src.api.config import settings

logger = logging.getLogger(__name__)

class DiscoveryResearcherService:
    """
    Discovery Researcher Service
    Uses GPT Researcher to perform autonomous, deep-dive research on trends.
    Configured to use local Ollama and free DuckDuckGo search.
    """

    def __init__(self):
        self.enabled = os.getenv("ENABLE_RESEARCHER", "true").lower() == "true"
        # Configure environment for GPT Researcher to use our internal proxy (sanitizer)
        os.environ["RETRIEVER"] = "duckduckgo"
        proxy_url = "http://127.0.0.1:8000/api/v1/proxy/ollama" # Point to proxy root
        os.environ["OLLAMA_BASE_URL"] = proxy_url
        os.environ["FAST_LLM"] = f"ollama:{settings.OLLAMA_MODEL}"
        os.environ["SMART_LLM"] = f"ollama:{settings.OLLAMA_MODEL}"
        os.environ["STRATEGIC_LLM"] = f"ollama:{settings.OLLAMA_MODEL}"
        os.environ["LLM_PROVIDER"] = "ollama"

        # Fallback for libraries that ignore LLM_PROVIDER
        os.environ["OPENAI_API_BASE"] = f"{proxy_url}/v1"
        os.environ["OPENAI_API_KEY"] = "sk-placeholder"

        # Client-side validation hardening (prevent LangChain None errors)
        os.environ["TEMPERATURE"] = "0.7"
        os.environ["MAX_TOKENS"] = "4000"

        logger.info(f"🔧 [DiscoveryResearcher] Configured via OpenAI-Proxy with placeholder models (remapped to {settings.OLLAMA_MODEL})")

    async def perform_research(self, query: str, report_type: str = "research_report") -> Dict[str, Any]:
        """
        Runs an autonomous research task on a given query.
        """
        if not self.enabled:
            return {"error": "Researcher service is disabled"}

        try:
            # Monkeypatch ChatOpenAI to prevent Pydantic validation errors for temperature=None
            try:
                from langchain_openai import ChatOpenAI
                original_init = ChatOpenAI.__init__
                def patched_init(self, *args, **kwargs):
                    if "temperature" in kwargs and kwargs["temperature"] is None:
                        kwargs["temperature"] = 0.7
                    if "max_tokens" in kwargs and kwargs["max_tokens"] is None:
                        kwargs["max_tokens"] = 4000
                    original_init(self, *args, **kwargs)
                ChatOpenAI.__init__ = patched_init
                logger.info("🐵 [DiscoveryResearcher] Monkeypatched ChatOpenAI for parameter safety.")
            except Exception as patch_e:
                logger.warning(f"⚠️ [DiscoveryResearcher] Could not monkeypatch ChatOpenAI: {patch_e}")

            from gpt_researcher import GPTResearcher

            logger.info(f"🕵️ [DiscoveryResearcher] Starting research for: {query}")

            # Initialize researcher
            researcher = GPTResearcher(query=query, report_type=report_type)

            # Conduct research
            await researcher.conduct_research()

            # Write report
            report = await researcher.write_report()

            logger.info(f"✅ [DiscoveryResearcher] Research completed for: {query}")

            return {
                "query": query,
                "report": report,
                "sources": researcher.get_source_urls(),
                "status": "success"
            }

        except Exception as e:
            logger.exception(f"❌ [DiscoveryResearcher] Research failed: {e}")
            return {"error": str(e), "status": "failed"}

# Singleton instance
base_researcher_service = DiscoveryResearcherService()
