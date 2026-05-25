import logging
import os
from src.api.config import settings

logger = logging.getLogger(__name__)


class BaseEttamettaAgent:
    """
    Standard parent class for all primary orchestrators (AgentZero, Hermes, OpenClaw).
    Handles universal LLM client initialization, fallback logic, and WebSocket logging.
    """

    def __init__(self, agent_name: str = "BaseAgent"):
        self.agent_name = agent_name
        self.is_running = False
        self.clients = {}
        self.llm_provider = getattr(settings, "DEFAULT_LLM_PROVIDER", "groq")
        self.model = getattr(settings, "MODEL", "llama-3.3-70b-versatile")

        # Initialize LLM stack
        self._init_llm_clients()

    async def _log(self, message: str, level: str = "INFO"):
        """Broadcasts a log message to the UI console and local logger."""
        try:
            from src.api.routes.ws import notify_system_log_async

            await notify_system_log_async(message, level=level, module=self.agent_name)
        except Exception:
            pass  # Handle cases where event loop isn't running or WS is down

        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{self.agent_name}] {message}")

    def _init_llm_clients(self):
        """Initialize all available LLM providers from settings."""
        self._init_groq()
        self._init_openai()
        self._init_anthropic()
        self._init_gemini()
        self._init_mistral()
        self._init_cohere()
        self._init_openrouter()
        self._init_deepseek()
        self._init_xai()

        # Local Providers
        self._init_ollama()
        self._init_lm_studio()

        # Free/High-Quota Providers
        self._init_cerebras()
        self._init_siliconflow()
        self._init_nvidia()

    def _init_groq(self):
        if hasattr(settings, "GROQ_API_KEY") and settings.GROQ_API_KEY:
            try:
                import httpx
                from groq import Groq, AsyncGroq

                self.clients["groq"] = Groq(api_key=settings.GROQ_API_KEY, http_client=httpx.Client())
                self.clients["groq_async"] = AsyncGroq(api_key=settings.GROQ_API_KEY, http_client=httpx.AsyncClient())
            except ImportError:
                logger.warning(f"[{self.agent_name}] Groq package not installed")

    def _init_openai(self):
        if hasattr(settings, "OPENAI_API_KEY") and settings.OPENAI_API_KEY:
            try:
                import httpx
                from openai import OpenAI, AsyncOpenAI

                self.clients["openai"] = OpenAI(api_key=settings.OPENAI_API_KEY, http_client=httpx.Client())
                self.clients["openai_async"] = AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    http_client=httpx.AsyncClient()
                )
            except ImportError:
                logger.warning(f"[{self.agent_name}] OpenAI package not installed")

    def _init_anthropic(self):
        if hasattr(settings, "ANTHROPIC_API_KEY") and settings.ANTHROPIC_API_KEY:
            try:
                import httpx
                from anthropic import Anthropic, AsyncAnthropic

                self.clients["anthropic"] = Anthropic(
                    api_key=settings.ANTHROPIC_API_KEY,
                    http_client=httpx.Client()
                )
                self.clients["anthropic_async"] = AsyncAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY,
                    http_client=httpx.AsyncClient()
                )
            except ImportError:
                logger.warning(f"[{self.agent_name}] Anthropic package not installed")

    def _init_gemini(self):
        if hasattr(settings, "GOOGLE_API_KEY") and settings.GOOGLE_API_KEY:
            try:
                from google import genai

                self.clients["gemini"] = genai.Client(api_key=settings.GOOGLE_API_KEY)
                self._gemini_model_name = "gemini-1.5-pro"
            except ImportError:
                logger.warning(
                    f"[{self.agent_name}] Google Generative AI package not installed"
                )

    def _init_mistral(self):
        if hasattr(settings, "MISTRAL_API_KEY") and settings.MISTRAL_API_KEY:
            try:
                from openai import OpenAI

                self.clients["mistral"] = OpenAI(
                    api_key=settings.MISTRAL_API_KEY,
                    base_url="https://api.mistral.ai/v1",
                )
            except ImportError:
                pass

    def _init_cohere(self):
        if hasattr(settings, "COHERE_API_KEY") and settings.COHERE_API_KEY:
            try:
                import cohere

                self.clients["cohere"] = cohere.Client(api_key=settings.COHERE_API_KEY)
            except ImportError:
                pass

    def _init_openrouter(self):
        if hasattr(settings, "OPENROUTER_API_KEY") and settings.OPENROUTER_API_KEY:
            try:
                from openai import OpenAI

                self.clients["openrouter"] = OpenAI(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1",
                )
            except ImportError:
                pass

    def _init_deepseek(self):
        if hasattr(settings, "DEEPSEEK_API_KEY") and settings.DEEPSEEK_API_KEY:
            try:
                from openai import OpenAI

                self.clients["deepseek"] = OpenAI(
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url="https://api.deepseek.com/v1",
                )
            except ImportError:
                pass

    def _init_xai(self):
        if hasattr(settings, "XAI_API_KEY") and settings.XAI_API_KEY:
            try:
                from openai import OpenAI

                self.clients["xai"] = OpenAI(
                    api_key=settings.XAI_API_KEY, base_url="https://api.x.ai/v1"
                )
            except ImportError:
                pass

    def _init_ollama(self):
        """Initializes Ollama client. Removal of restrictive ping to allow on-demand recovery."""
        try:
            url = os.getenv("OLLAMA_BASE_URL") or settings.OLLAMA_URL
            from openai import OpenAI, AsyncOpenAI
            base_url = url.rstrip("/") + "/v1"
            self.clients["ollama"] = OpenAI(base_url=base_url, api_key="dummy")
            self.clients["ollama_async"] = AsyncOpenAI(
                base_url=base_url, api_key="dummy"
            )
            logger.info(f"[{self.agent_name}] Ollama client initialized at {base_url}")
        except Exception as e:
            logger.debug(f"[{self.agent_name}] Ollama initialization failed: {e}")

    def _init_lm_studio(self):
        try:
            url = getattr(settings, "LM_STUDIO_URL", "http://localhost:1234")
            self.clients["lm_studio"] = {"base_url": url}
        except Exception:
            pass

    def _init_cerebras(self):
        if hasattr(settings, "CEREBRAS_API_KEY") and settings.CEREBRAS_API_KEY:
            try:
                from openai import OpenAI

                self.clients["cerebras"] = OpenAI(
                    api_key=settings.CEREBRAS_API_KEY,
                    base_url="https://api.cerebras.ai/v1",
                )
            except ImportError:
                pass

    def _init_siliconflow(self):
        if hasattr(settings, "SILICONFLOW_API_KEY") and settings.SILICONFLOW_API_KEY:
            try:
                from openai import OpenAI

                self.clients["siliconflow"] = OpenAI(
                    api_key=settings.SILICONFLOW_API_KEY,
                    base_url="https://api.siliconflow.cn/v1",
                )
            except ImportError:
                pass

    def _init_nvidia(self):
        if hasattr(settings, "NVIDIA_API_KEY") and settings.NVIDIA_API_KEY:
            try:
                from openai import OpenAI

                self.clients["nvidia"] = OpenAI(
                    api_key=settings.NVIDIA_API_KEY,
                    base_url="https://integrate.api.nvidia.com/v1",
                )
            except ImportError:
                pass

    async def _call_llm(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str = None,
        response_format: str = "text",
    ) -> str:
        """Unified LLM call with automatic provider fallback."""
        target_model = model or self.model

        # Try primary provider and fallbacks (priority order)
        providers = [
            self.llm_provider,
            "ollama",
            "xai",
            "deepseek",
            "cerebras",
            "groq",
            "openai",
            "openrouter",
            "mistral",
            "siliconflow",
            "nvidia",
            "gemini",
            "anthropic",
        ]

        for provider in providers:
            # On-demand initialization for Ollama if missing
            if provider == "ollama" and "ollama" not in self.clients:
                logger.info(f"🧬 [{self.agent_name}] Lazy-initializing Ollama client...")
                self._init_ollama()

            client = self.clients.get(provider)
            if not client:
                logger.debug(f"⏩ [{self.agent_name}] Skipping {provider} (client not initialized)")
                continue

            logger.info(f"🚀 [{self.agent_name}] Attempting {provider}... (VERSION_V56)")
            try:
                if provider in [
                    "groq",
                    "openai",
                    "mistral",
                    "openrouter",
                    "deepseek",
                    "xai",
                    "cerebras",
                    "siliconflow",
                    "nvidia",
                    "ollama",
                    "ollama_cloud",
                ]:
                    return await self._execute_openai_compatible(
                        provider, target_model, prompt, system_prompt, response_format
                    )
                elif provider == "gemini":
                    return await self._execute_gemini(client, prompt, system_prompt)
                elif provider == "anthropic":
                    return await self._execute_anthropic(provider, client, prompt, system_prompt)
            except Exception as e:
                logger.warning(
                    f"[{self.agent_name}] LLM provider {provider} failed: {e}"
                )
                continue

        return "⚠️ All LLM providers exhausted. Execution failed."

    async def _execute_openai_compatible(
        self,
        provider: str,
        target_model: str,
        prompt: str,
        system_prompt: str,
        response_format: str,
    ) -> str:
        # map common model names to provider-specific ones
        actual_model = target_model
        if provider == "groq":
            actual_model = "llama-3.3-70b-versatile"
        elif provider == "ollama":
            actual_model = getattr(settings, "OLLAMA_MODEL", "llama3")
        elif provider == "ollama_cloud":
            actual_model = getattr(
                settings, "OLLAMA_CLOUD_MODEL", "qwen2.5:72b"
            )
        elif provider == "cerebras":
            actual_model = "llama3.1-70b"
        elif provider == "openai" and "llama" in target_model.lower():
            actual_model = "gpt-4o"  # Fallback for OpenAI if llama requested

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs = {"model": actual_model, "messages": messages}
        if response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}

        # Use direct httpx for local proxy to avoid library deadlocks/formatting issues
        import httpx
        from types import SimpleNamespace
        
        # Determine the target endpoint
        target_url = f"{self.clients[provider].base_url}/chat/completions"
        
        try:
            async with httpx.AsyncClient() as h_client:
                h_resp = await h_client.post(
                    target_url,
                    json=kwargs,
                    timeout=600.0
                )
                
                if h_resp.status_code != 200:
                    logger.error(f"❌ [{self.agent_name}] Proxy error {h_resp.status_code}: {h_resp.text}")
                    raise ValueError(f"Proxy returned {h_resp.status_code}")
                
                raw_data = h_resp.json()
                resp = SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content=raw_data['choices'][0]['message']['content']
                            )
                        )
                    ]
                )
        except Exception as call_err:
            logger.exception(f"❌ [{self.agent_name}] {provider} call failed")
            raise call_err

        return resp.choices[0].message.content

    async def _execute_gemini(self, client, prompt: str, system_prompt: str) -> str:
        resp = await client.aio.models.generate_content(
            model=self._gemini_model_name,
            contents=f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
        )
        return resp.text

    async def _execute_anthropic(self, provider: str, client, prompt: str, system_prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 1024,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        # Use async client if available
        async_client = self.clients.get(f"{provider}_async")
        if async_client:
            resp = await async_client.messages.create(**kwargs)
        else:
            resp = client.messages.create(**kwargs)
        return resp.content[0].text
