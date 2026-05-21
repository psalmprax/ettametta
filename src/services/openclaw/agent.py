import logging
import json
import requests
import asyncio
import time
from groq import Groq
from src.api.config import settings
from typing import Any
import httpx
import yaml
from pathlib import Path

from .utils import is_package_available

logger = logging.getLogger(__name__)


try:
    from src.api.utils.llm_vault import get_llm_api_key

    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

from src.services.openclaw.skills import (
    discovery_skill,
    system_skill,
    analytics_skill,
    content_skill,
    publishing_skill,
    niche_skill,
    security_skill,
    noface_skill,
    outreach_skill,
    social_metrics_skill,
    paperclip_skill,
    claw4science_skill,
    remotion_skill,
    memory_skill,
    self_improve_skill,
    repurpose_skill,
    trend_prediction_skill,
    competitor_skill,
    audit_skill,
    notification_skill,
    workflow_skill,
    self_healing_skill,
    ettametta_skill,
    pixverse_skill,
    luma_skill,
    branding_skill,
    seo_auditor_skill,
    reputation_manager_skill,
    chat_sales_skill,
    landing_page_skill,
    data_scraping_skill,
    research_skill,
    data_ingestion_skill,
    render_skill,
    agent_zero_skill,
    intelligent_workflow_skill,
    browser_skill,
    document_skill,
    persona_skill,
    perchance_skill,
    kaiber_skill,
    pika_skill,
    runway_skill,
    kling_skill,
    hailuo_skill,
    haiper_skill,
    genmo_skill,
    morph_skill,
    vidu_skill,
    wavespeed_skill,
    seedance_skill,
    frameloop_skill,
    leiapix_skill,
    videoany_skill,
    heygen_skill,
    ltx_skill,
    leonardo_skill,
    invideo_skill,
    fliki_skill,
    content_editor_skill,
    production_assistant_skill,
    video_lead_skill,
    scene_based_video_skill,
)


from src.api.utils.resilience import CircuitBreaker


from src.services.base_agent import BaseEttamettaAgent


class OpenClawAgent(BaseEttamettaAgent):
    # Class-level base system prompt for the agent
    BASE_SYSTEM_PROMPT = """You are OpenClaw, the autonomous Master Controller for the ettametta multi-agent empire.
    Your goal is to assist the user by orchestrating a team of specialized agents:
    - SCOUT (Discovery): Advanced trend discovery, competitor analysis, content ideation, and market research.
    - MUSE (Creative): Writes viral scripts and hook strategies.
    - EYE (Visual): Analyzes video vibes and optimizes aesthetic positioning.
    - HERALD (Distribution): Handles publishing and monetization arbitrage.

    DISCOVERY CAPABILITIES:
    - Search trending topics with AI analysis
    - Analyze competitor strategies
    - Predict upcoming trends
    - Generate viral content ideas
    - Scan niches for opportunities
    
    You have access to the following tools:
    {tools_description}
    
    PLANNING MODE:
    When a user gives a complex command, you must first output a brief "Plan" explicitly naming which sub-agents (SCOUT, MUSE, etc.) you are delegating to, followed by the actual tool JSON.
    
    If a tool is needed, output:
    "Plan: [Sub-agent names] - [Action description]"
    {{
        "tool": "TOOL_NAME",
        "params": {{ ... }}
    }}
    """

    def __init__(self, user_id: str = None, reasoning_mode: str = "standard"):
        self.user_id = user_id
        self.reasoning_mode = reasoning_mode
        super().__init__(agent_name="OPENCLAW")
        self.circuit_breaker = CircuitBreaker()
        self.skills_path = Path(__file__).parent / "skills.yaml"
        self.system_prompt = self._build_system_prompt()

        # Polymorphic Skill Registry (deduplicated - removed semantic aliases)
        self.skill_registry = {
            "DISCOVERY": discovery_skill,
            "ETTAMETTA": ettametta_skill,
            "NICHE": niche_skill,
            "SEO_AUDIT": seo_auditor_skill,
            "REPUTATION": reputation_manager_skill,
            "CHAT_SALES": chat_sales_skill,
            "LANDING_PAGE": landing_page_skill,
            "SCRAPE": data_scraping_skill,
            "SECURITY": security_skill,
            "SYSTEM": system_skill,
            "ANALYTICS": analytics_skill,
            "CONTENT": content_skill,
            "PUBLISH": publishing_skill,
            "NOFACE": noface_skill,
            "OUTREACH": outreach_skill,
            "RENDER": render_skill,
            "ZERO": agent_zero_skill,
            "RESEARCH": research_skill,
            "INGESTION": data_ingestion_skill,
            "METRICS": social_metrics_skill,
            "PAPERCLIP": paperclip_skill,
            "SCIENTIFIC": claw4science_skill,
            "REMOTION": remotion_skill,
            "MEMORY": memory_skill,
            "NOTIFICATIONS": notification_skill,
            "WORKFLOW": workflow_skill,
            "ACCOUNT_AUDIT": audit_skill,
            "BRANDING": branding_skill,
            "SELF_IMPROVE": self_improve_skill,
            "REPURPOSE": repurpose_skill,
            "TREND_PRED": trend_prediction_skill,
            "HEALING": self_healing_skill,
            "VIDEO_LEAD": video_lead_skill,
            "SCENE_VIDEO": scene_based_video_skill,
            "BROWSER": browser_skill,
            "DOCUMENT": document_skill,
            "PERSONA": persona_skill,
            "INTELLIGENT_WORKFLOW": intelligent_workflow_skill,
            # Video generation skills
            "PIXVERSE": pixverse_skill,
            "LUMA": luma_skill,
            "PERCHANCE": perchance_skill,
            "KAIBER": kaiber_skill,
            "PIKA": pika_skill,
            "RUNWAY": runway_skill,
            "KLING": kling_skill,
            "HAILUO": hailuo_skill,
            "HAIPER": haiper_skill,
            "GENMO": genmo_skill,
            "MORPH": morph_skill,
            "VIDU": vidu_skill,
            "WAVESPEED": wavespeed_skill,
            "SEEDANCE": seedance_skill,
            "FRAMELOOP": frameloop_skill,
            "LEIAPIX": leiapix_skill,
            "VIDEOANY": videoany_skill,
            "HEYGEN": heygen_skill,
            "LTX": ltx_skill,
            "LEONARDO": leonardo_skill,
            "INVIDEO": invideo_skill,
            "FLIKI": fliki_skill,
            "CONTENT_EDITOR": content_editor_skill,
            "VIDEO_ASSISTANT": production_assistant_skill,
        }

    def _load_dynamic_skills(self) -> list:
        """Load skills from external YAML configuration."""
        if not self.skills_path.exists():
            logger.warning(f"[OpenClaw] Skills file not found at {self.skills_path}")
            return []
        try:
            with open(self.skills_path, "r") as f:
                config = yaml.safe_load(f)
                return config.get("skills", [])
        except Exception as e:
            logger.error(f"[OpenClaw] Failed to load dynamic skills: {e}")
            return []

    def _build_system_prompt(self) -> str:
        """Construct the system prompt by injecting dynamic skills."""
        skills = self._load_dynamic_skills()
        tools_description = ""
        for skill in skills:
            name = skill.get("name", "UNKNOWN")
            desc = skill.get("description", "No description")
            params = json.dumps(skill.get("params", {}))
            tools_description += f"- {name}: {desc} Params: {params}\n    "

        return self.BASE_SYSTEM_PROMPT.format(
            tools_description=tools_description.strip()
        )

    def get_dependency_status(self) -> dict[str, bool]:
        """Check availability of optional heavy dependencies."""
        return {
            "playwright": is_package_available("playwright"),
            "groq": is_package_available("groq"),
            "requests": is_package_available("requests"),
            "openai": is_package_available("openai"),
        }

    def get_dependency_report(self) -> dict[str, Any]:
        """Generate a detailed report of missing dependencies and their impact."""
        status = self.get_dependency_status()
        missing = [pkg for pkg, installed in status.items() if not installed]

        impact = {}
        if not status["playwright"]:
            impact["playwright"] = (
                "24+ Browser AI skills (Luma, Runway, Pika, etc.) are disabled."
            )
        if not status["groq"]:
            impact["groq"] = "Standard reasoning mode is disabled."

        return {
            "all_installed": len(missing) == 0,
            "status": status,
            "missing": missing,
            "impact": impact,
            "fix_command": f"pip install {' '.join(missing)}" if missing else None,
        }

    def _get_api_key(self, key_name: str) -> str:
        """Get API key from vault or fall back to settings"""
        if VAULT_AVAILABLE:
            api_key = get_llm_api_key(key_name, user_id=self.user_id)
            if api_key:
                return api_key
        return getattr(settings, f"{key_name.upper()}_API_KEY", None) or getattr(
            settings, key_name.upper(), None
        )

    def _get_setting(self, key_name: str, default=None):
        """Get setting from vault or fall back to settings"""
        if VAULT_AVAILABLE:
            value = get_llm_api_key(key_name, user_id=self.user_id)
            if value:
                return value
        return getattr(settings, key_name.upper(), default)

    def _init_llm_clients(self):
        """Initialize multiple LLM clients with fallback support"""
        providers = {
            "groq": self._init_groq,
            "openai": self._init_openai,
            "anthropic": self._init_anthropic,
            "xai": self._init_xai,
            "deepseek": self._init_deepseek,
            "gemini": self._init_gemini,
            "cohere": self._init_cohere,
            "mistral": self._init_mistral,
            "cerebras": self._init_cerebras,
            "cloudflare": self._init_cloudflare,
            "huggingface": self._init_huggingface,
            "openrouter": self._init_openrouter,
            "nvidia": self._init_nvidia,
            "ollama_cloud": self._init_ollama_cloud,
            "siliconflow": self._init_siliconflow,
            "ollama": self._init_ollama,
            "lm_studio": self._init_lm_studio,
        }

        # Initialize all available providers
        initialized_count = 0
        for provider_name, init_func in providers.items():
            try:
                init_func()
                if provider_name in self.clients:
                    initialized_count += 1
                    logger.debug(f"[OpenClaw] Initialized {provider_name}")
            except Exception as e:
                logger.debug(f"[OpenClaw] Provider {provider_name} not available: {e}")

        if initialized_count == 0:
            logger.error(
                "[OpenClaw] No LLM providers available - please check environment variables."
            )
            raise RuntimeError(
                "OpenClaw configuration error: No valid LLM providers initialized. Set GROQ_API_KEY or similar."
            )

        logger.info(
            f"[OpenClaw] Initialized {initialized_count} LLM providers (Primary: {self.llm_provider})"
        )

    def _init_groq(self):
        api_key = self._get_api_key("groq")
        if api_key:
            self.clients["groq"] = Groq(api_key=api_key)

    def _init_openai(self):
        api_key = self._get_api_key("openai")
        if api_key:
            try:
                from openai import OpenAI

                self.clients["openai"] = OpenAI(api_key=api_key)
            except ImportError:
                logger.warning("[OpenClaw] OpenAI package not installed")

    def _init_anthropic(self):
        api_key = self._get_api_key("anthropic")
        if api_key:
            try:
                import anthropic

                self.clients["anthropic"] = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                logger.warning("[OpenClaw] Anthropic package not installed")

    def _init_xai(self):
        api_key = self._get_api_key("xai")
        if api_key:
            try:
                from openai import OpenAI

                self.clients["xai"] = OpenAI(
                    api_key=api_key, base_url="https://api.x.ai/v1"
                )
            except ImportError:
                logger.warning("[OpenClaw] OpenAI package not installed for XAI")

    def _init_deepseek(self):
        api_key = self._get_api_key("deepseek")
        if api_key:
            try:
                from openai import OpenAI

                self.clients["deepseek"] = OpenAI(
                    api_key=api_key, base_url="https://api.deepseek.com/v1"
                )
            except ImportError:
                logger.warning("[OpenClaw] OpenAI package not installed for DeepSeek")

    def _init_gemini(self):
        api_key = self._get_api_key("google")
        if api_key:
            try:
                from google import genai

                self.clients["gemini"] = genai.Client(api_key=api_key)
                self._gemini_model_name = "gemini-pro"
            except ImportError:
                logger.warning("[OpenClaw] Google Generative AI package not installed")

    def _init_cohere(self):
        api_key = self._get_api_key("cohere")
        if api_key:
            try:
                import cohere

                self.clients["cohere"] = cohere.Client(api_key=api_key)
                logger.info("[OpenClaw] Cohere initialized")
            except ImportError:
                logger.warning("[OpenClaw] Cohere package not installed")

    def _init_mistral(self):
        api_key = self._get_api_key("mistral")
        if api_key:
            try:
                from openai import OpenAI

                self.clients["mistral"] = OpenAI(
                    api_key=api_key, base_url="https://api.mistral.ai/v1"
                )
                logger.info("[OpenClaw] Mistral AI initialized")
            except ImportError:
                logger.warning("[OpenClaw] OpenAI package not installed for Mistral")

    def _init_cerebras(self):
        api_key = self._get_api_key("cerebras")
        if api_key:
            try:
                from openai import OpenAI

                self.clients["cerebras"] = OpenAI(
                    api_key=api_key, base_url="https://api.cerebras.ai/v1"
                )
                logger.info("[OpenClaw] Cerebras initialized")
            except ImportError:
                logger.warning("[OpenClaw] OpenAI package not installed for Cerebras")

    def _init_cloudflare(self):
        api_key = self._get_api_key("cloudflare")
        account_id = self._get_setting("cloudflare_account_id", "")
        if api_key:
            self.clients["cloudflare"] = {"api_key": api_key, "account_id": account_id}
            logger.info("[OpenClaw] Cloudflare Workers AI initialized")

    def _init_huggingface(self):
        api_key = self._get_api_key("huggingface")
        if api_key:
            self.clients["huggingface"] = {"api_key": api_key}
            logger.info("[OpenClaw] Hugging Face initialized")

    def _init_openrouter(self):
        api_key = self._get_api_key("openrouter")
        if api_key:
            try:
                from openai import OpenAI

                self.clients["openrouter"] = OpenAI(
                    api_key=api_key, base_url="https://openrouter.ai/api/v1"
                )
                logger.info("[OpenClaw] OpenRouter initialized")
            except ImportError:
                logger.warning("[OpenClaw] OpenAI package not installed for OpenRouter")

    def _init_nvidia(self):
        api_key = self._get_api_key("nvidia")
        if api_key:
            try:
                from openai import OpenAI

                self.clients["nvidia"] = OpenAI(
                    api_key=api_key, base_url="https://integrate.api.nvidia.com/v1"
                )
                logger.info("[OpenClaw] NVIDIA NIM initialized")
            except ImportError:
                logger.warning("[OpenClaw] OpenAI package not installed for NVIDIA")

    def _init_ollama_cloud(self):
        api_key = self._get_api_key("ollama_cloud")
        if api_key:
            try:
                from openai import OpenAI, AsyncOpenAI

                self.clients["ollama_cloud"] = OpenAI(
                    api_key=api_key, base_url="https://cloud.ollama.ai/v1"
                )
                self.clients["ollama_cloud_async"] = AsyncOpenAI(
                    api_key=api_key, base_url="https://cloud.ollama.ai/v1"
                )
                logger.info("[OpenClaw] Ollama Cloud initialized")
            except ImportError:
                logger.warning(
                    "[OpenClaw] OpenAI package not installed for Ollama Cloud"
                )

    def _init_siliconflow(self):
        api_key = self._get_api_key("siliconflow")
        if api_key:
            try:
                from openai import OpenAI

                self.clients["siliconflow"] = OpenAI(
                    api_key=api_key, base_url="https://api.siliconflow.cn/v1"
                )
                logger.info("[OpenClaw] SiliconFlow initialized")
            except ImportError:
                logger.warning(
                    "[OpenClaw] OpenAI package not installed for SiliconFlow"
                )

    def _get_model_name(self) -> str:
        """Get the appropriate model name for the current provider"""
        # Comprehensive mapping for all supported providers (updated models)
        model_map = {
            "groq": "llama-3.3-70b-versatile",
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022",
            "xai": "grok-2",
            "deepseek": "deepseek-chat",
            "gemini": "gemini-1.5-pro",
            "cohere": "command-r-plus",
            "mistral": "mistral-large-2411",
            "cerebras": "llama-3.3-70b",
            "cloudflare": "@cf/meta-llama/llama-3.1-70b-instruct",
            "huggingface": "meta-llama/Llama-3.3-70B-Instruct",
            "openrouter": "anthropic/claude-3.5-sonnet",
            "nvidia": "meta/llama-3.3-70b-instruct",
            "ollama_cloud": getattr(settings, "OLLAMA_CLOUD_MODEL", "qwen2.5:72b"),
            "siliconflow": "Qwen/Qwen2.5-72B-Instruct",
            "ollama": getattr(settings, "OLLAMA_MODEL", "llama3"),
            "lm_studio": "local-model",
        }

        default_model = "llama-3.3-70b-versatile"

        # Use mapped model or fall back to settings default
        if self.llm_provider in model_map:
            return model_map[self.llm_provider]

        # Fallback to settings or default
        return getattr(settings, "MODEL", None) or default_model

    def _get_user_from_api(self, identifier: str):
        # 1. Immediate Admin Fallback (Highest Priority)
        # Trust the configured admin ID even if API is unreachable
        if str(identifier) == str(settings.TELEGRAM_ADMIN_ID):
            logger.info(f"Admin access verified for {identifier}")
            return {
                "id": 1,  # Match the DB id found earlier for psalmprax
                "username": "admin",
                "role": "admin",
                "subscription": "premium",
                "telegram_chat_id": str(identifier),
            }

        # 2. Dynamic User Verification via API
        try:
            if str(identifier).startswith("whatsapp:"):
                # Format: whatsapp:+1234567890
                clean_id = str(identifier)
                response = requests.get(
                    f"{settings.API_URL}/auth/verify-whatsapp/{clean_id}", timeout=5
                )
            else:
                response = requests.get(
                    f"{settings.API_URL}/auth/verify-telegram/{identifier}", timeout=5
                )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error calling verification API: {e}")
            return None

    async def process_message(self, identifier: str, message: str) -> str:
        """
        Process a user message and determine the action.
        """
        # Dynamic verification via API
        user = await asyncio.to_thread(self._get_user_from_api, identifier)

        if not user:
            logger.warning(f"Unauthorized access attempt from {identifier}")
            return f"⛔ Unauthorized access. Your ID is: `{identifier}`.\n\nPlease log in to the ettametta dashboard and add this ID to your profile settings to enable agent access."

        try:
            # 5-Star Upgrade: Closed-Loop Learning
            # Before processing, probe analytics for historical viral performance to ground the response.
            recent_metrics = "No recent data"
            try:
                recent_metrics = analytics_skill.get_system_stats()
            except:
                pass

            # 5-Star Upgrade: Hierarchical Negotiation (Workforce Council)
            if self.reasoning_mode == "hierarchical":
                return await self._process_hierarchical(message, recent_metrics)

            # 1. Ask LLM for intent (Standard Mode)
            response_text = await self._call_llm(
                prompt=message,
                system_prompt=f"{self.system_prompt}\n\n[CLOSED-LOOP CONTEXT]: {recent_metrics}",
            )
            logger.info(f"LLM Raw Response: {response_text}")  # Debug log

            # 2. Check if response is a tool call (JSON)
            try:
                # Naive check for JSON
                if "{" in response_text and "}" in response_text:
                    # Extract JSON if mixed with text
                    start = response_text.find("{")
                    end = response_text.rfind("}") + 1
                    json_str = response_text[start:end]

                    tool_call = json.loads(json_str)

                    # Prepend the plan/thought if it exists
                    thought = response_text[:start].strip()
                    result = await self.execute_tool(tool_call)

                    if thought:
                        return f"🧠 **{thought}**\n\n{result}"
                    return result
                else:
                    return response_text

            except json.JSONDecodeError:
                return response_text

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"⚠️ Agent Error: {str(e)}"

    async def execute_tool(self, tool_call: dict[str, Any]) -> str:
        """
        Routes the tool execution to the correct backend service or skill.
        Standardized via Polymorphic Skill Registry.
        """
        tool = tool_call.get("tool")
        params = tool_call.get("params", {})

        logger.info(f"Executing tool: {tool} with params: {params}")

        # Standard Polymorphic Dispatch
        if tool in self.skill_registry:
            skill = self.skill_registry[tool]

            # Inject dependencies into params if not present and skill can accept them
            # Most skills create their own clients, but we provide these for skills that need them
            if "clients" not in params:
                params["clients"] = self.clients

            # Also provide a convenience API key reference
            if "api_key" not in params:
                params["api_key"] = getattr(
                    settings, f"{self.llm_provider.upper()}_API_KEY", None
                )

            try:
                # Check if skill has execute method (OpenClawBaseSkill pattern)
                if hasattr(skill, "execute"):
                    # Use execute method with kwargs from params
                    if asyncio.iscoroutinefunction(skill.execute):
                        return await skill.execute(**params)
                    else:
                        return skill.execute(**params)

                # Fallback for skills not yet refactored to OpenClawBaseSkill
                logger.warning(
                    f"[OpenClaw] Skill {tool} lacks execute() method. Falling back to legacy dispatch."
                )
            except Exception as e:
                logger.error(f"[OpenClaw] Skill execution failed for {tool}: {e}")
                return f"⚠️ Skill {tool} execution error: {str(e)}"

        return f"❓ Unknown or unhandled tool: {tool}"

    async def _process_hierarchical(self, message: str, metrics: str) -> str:
        """
        Works as the 'Director' for the Workforce Council.
        """
        logger.info("[OpenClaw] Council Deliberation initiated.")

        manager_prompt = (
            "You are the OpenClaw Workforce Council Director (GPT-4o). "
            "Analyze the user request and historical performance metrics. "
            "Formulate a multi-step strategy using specialized tools. "
            "If the request is complex, break it down into steps for specialists."
        )

        # Force high-reasoning model for Council Manager
        original_model = self.model
        original_provider = self.llm_provider

        if "openai" in self.clients:
            self.llm_provider = "openai"
            self.model = "gpt-4o"

        try:
            response = await self._call_llm(
                prompt=message,
                system_prompt=f"{manager_prompt}\n\n[ANALYTICS]: {metrics}",
            )
            return f"🏛️ **Workforce Council Strategy**\n\n{response}"
        finally:
            self.llm_provider = original_provider
            self.model = original_model


# Global singleton for unified status and health reporting
# This orchestrator manages discovery and reasoning across all sectors.
base_openclaw_agent_service = OpenClawAgent()
