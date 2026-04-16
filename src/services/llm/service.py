"""
Unified LLM Service - Multi-Provider Support
============================================
Supports: Groq, OpenAI, xAI (Grok), DeepSeek, Anthropic, Google Gemini
"""

import os
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"
    XAI = "xai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class UnifiedLLMService:
    """
    Unified LLM service that supports multiple providers.
    Configure API keys in environment variables.
    """

    PROVIDER_KEYS = {
        LLMProvider.GROQ: "GROQ_API_KEY",
        LLMProvider.OPENAI: "OPENAI_API_KEY",
        LLMProvider.XAI: "XAI_API_KEY",
        LLMProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
        LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
        LLMProvider.GEMINI: "GOOGLE_API_KEY",
    }

    PROVIDER_MODELS = {
        LLMProvider.GROQ: [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768",
        ],
        LLMProvider.OPENAI: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        LLMProvider.XAI: ["grok-beta", "grok-2-1212"],
        LLMProvider.DEEPSEEK: ["deepseek-chat", "deepseek-coder"],
        LLMProvider.ANTHROPIC: ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        LLMProvider.GEMINI: ["gemini-1.5-flash", "gemini-1.5-pro"],
    }

    # Base URLs for API endpoints
    BASE_URLS = {
        LLMProvider.GROQ: "https://api.groq.com/openai/v1",
        LLMProvider.OPENAI: "https://api.openai.com/v1",
        LLMProvider.XAI: "https://api.x.ai/v1",
        LLMProvider.DEEPSEEK: "https://api.deepseek.com/v1",
        LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
    }

    def __init__(self, default_provider: LLMProvider = LLMProvider.GROQ):
        self.default_provider = default_provider
        self._api_keys: Dict[LLMProvider, str] = {}
        self._load_api_keys()
        
        # Framework integration
        self.enable_langchain = os.getenv("ENABLE_LANGCHAIN", "false").lower() == "true"
        self.enable_crewai = os.getenv("ENABLE_CREWAI", "false").lower() == "true"

    def get_intelligence_report(self):
        """Returns status of agentic frameworks including the new Hermes Skill Engine."""
        from services.langchain.service import _check_langchain_available
        from services.crewai.service import _check_crewai_available
        from services.hermes.service import hermes_service
        
        lc_installed = _check_langchain_available()
        ca_installed = _check_crewai_available()
        h_report = hermes_service.get_intelligence_report()
        
        return {
            "name": "Intelligence Suite",
            "frameworks": [
                {
                    "name": "LangChain",
                    "installed": lc_installed,
                    "enabled": self.enable_langchain,
                    "status": "Healthy" if lc_installed and self.enable_langchain else "Inactive"
                },
                {
                    "name": "CrewAI",
                    "installed": ca_installed,
                    "enabled": self.enable_crewai,
                    "status": "Healthy" if ca_installed and self.enable_crewai else "Inactive"
                },
                h_report
            ],
            "healthy": lc_installed or ca_installed or h_report.get("learning_enabled", False)
        }

    def get_dependency_report(self):
        """Audit compatibility for intelligence frameworks."""
        return self.get_intelligence_report()

    def _load_api_keys(self):
        """Load API keys from environment variables."""
        for provider, key_name in self.PROVIDER_KEYS.items():
            api_key = os.getenv(key_name, "")
            if api_key and api_key != "your_key_here":
                self._api_keys[provider] = api_key
                logger.info(f"[LLM] Loaded API key for {provider.value}")

        if not self._api_keys:
            logger.warning(
                "[LLM] No API keys configured - service will use fallback mode"
            )

    def is_available(self, provider: LLMProvider) -> bool:
        """Check if a provider is available."""
        return provider in self._api_keys

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers with their models."""
        available = []
        for provider in LLMProvider:
            is_avail = self.is_available(provider)
            available.append(
                {
                    "provider": provider.value,
                    "available": is_avail,
                    "default_model": self.PROVIDER_MODELS[provider][0]
                    if is_avail
                    else None,
                    "models": self.PROVIDER_MODELS[provider],
                }
            )
        return available

    async def complete(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate completion using specified provider.
        Falls back to available providers if primary fails.
        """
        import httpx

        # Use default if not specified
        if provider is None:
            provider = self.default_provider

        # Determine model
        if model is None:
            model = self.PROVIDER_MODELS[provider][0]

        providers_to_try = [provider]

        # Add fallbacks
        for p in LLMProvider:
            if p not in providers_to_try and self.is_available(p):
                providers_to_try.append(p)

        last_error = None
        for try_provider in providers_to_try:
            if not self.is_available(try_provider):
                continue

            try:
                return await self._call_api(
                    try_provider,
                    model,
                    prompt,
                    system_message,
                    temperature,
                    max_tokens,
                    **kwargs,
                )
            except Exception as e:
                logger.warning(f"[LLM] {try_provider.value} failed: {e}")
                last_error = e
                continue

        return {
            "error": f"All LLM providers failed. Last error: {last_error}",
            "content": "AI service temporarily unavailable. Please try again later.",
        }

    async def _call_api(
        self,
        provider: LLMProvider,
        model: str,
        prompt: str,
        system_message: Optional[str],
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> Dict[str, Any]:
        """Call the appropriate API based on provider."""
        import httpx

        api_key = self._api_keys[provider]
        headers = {"Authorization": f"Bearer {api_key}"}

        # Build messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        # Provider-specific handling
        if provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(
                api_key, model, messages, temperature, max_tokens
            )

        if provider == LLMProvider.GEMINI:
            return await self._call_gemini(
                api_key, model, prompt, system_message, temperature, max_tokens
            )

        # OpenAI-compatible API call
        url = f"{self.BASE_URLS[provider]}/chat/completions"

        # Adjust model name for Groq if needed
        if provider == LLMProvider.GROQ and "/" in model:
            model = model.split("/")[-1]

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if kwargs.get("response_format"):
            payload["response_format"] = kwargs["response_format"]

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            return {
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model", model),
                "provider": provider.value,
                "usage": data.get("usage", {}),
                "raw": data,
            }

    async def _call_anthropic(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Call Anthropic API (different format)."""
        import httpx

        # Convert messages to Anthropic format
        system = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                user_messages.append(msg)

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": user_messages,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            return {
                "content": data["content"][0]["text"],
                "model": data.get("model", model),
                "provider": "anthropic",
                "usage": data.get("usage", {}),
                "raw": data,
            }

    async def _call_gemini(
        self,
        api_key: str,
        model: str,
        prompt: str,
        system_message: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Call Google Gemini API."""
        import httpx

        # Gemini uses different endpoint format
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

        # Build contents
        contents = [{"parts": [{"text": prompt}]}]

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system_message:
            payload["systemInstruction"] = {"parts": [{"text": system_message}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                params={"key": api_key},
            )
            response.raise_for_status()
            data = response.json()

            content = data["candidates"][0]["content"]["parts"][0]["text"]

            return {
                "content": content,
                "model": model,
                "provider": "gemini",
                "raw": data,
            }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Chat completion with message history."""
        if not messages:
            return {"error": "No messages provided"}

        # Extract system message if present
        system_message = None
        if messages[0]["role"] == "system":
            system_message = messages[0]["content"]
            messages = messages[1:]

        # Combine remaining messages into single prompt
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

        return await self.complete(
            prompt=prompt,
            system_message=system_message,
            provider=provider,
            model=model,
            **kwargs,
        )


# Singleton instance
unified_llm_service = UnifiedLLMService()


# Helper functions for easy use
async def generate(
    prompt: str, provider: Optional[str] = None, model: Optional[str] = None, **kwargs
) -> str:
    """Simple generation function."""
    if provider:
        provider_enum = LLMProvider(provider)
    else:
        provider_enum = None

    result = await unified_llm_service.complete(
        prompt=prompt, provider=provider_enum, model=model, **kwargs
    )

    return result.get("content", result.get("error", ""))


async def chat_with_llm(
    messages: List[Dict[str, str]], provider: Optional[str] = None, **kwargs
) -> str:
    """Chat with LLM using message history."""
    if provider:
        provider_enum = LLMProvider(provider)
    else:
        provider_enum = None

    result = await unified_llm_service.chat(
        messages=messages, provider=provider_enum, **kwargs
    )

    return result.get("content", result.get("error", ""))
