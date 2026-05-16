from src.api.utils.vault import get_secret
import logging

logger = logging.getLogger(__name__)

LLM_API_KEYS = {
    "groq": "groq_api_key",
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
    "xai": "xai_api_key",
    "deepseek": "deepseek_api_key",
    "gemini": "google_api_key",
    "google": "google_api_key",
    "cohere": "cohere_api_key",
    "mistral": "mistral_api_key",
    "cerebras": "cerebras_api_key",
    "cloudflare": "cloudflare_api_key",
    "cloudflare_account_id": "cloudflare_account_id",
    "huggingface": "hugging_face_api_key",
    "openrouter": "openrouter_api_key",
    "nvidia": "nvidia_api_key",
    "ollama_cloud": "ollama_cloud_api_key",
    "siliconflow": "siliconflow_api_key",
    "ollama_url": "ollama_url",
    "lm_studio_url": "lm_studio_url",
}


def get_llm_api_key(provider: str, user_id: str = None) -> str:
    """
    Get LLM API key from vault with priority:
    1. User-specific override (UserSetting)
    2. System-wide setting (SystemSettings)
    3. Environment-based settings (api.config)
    """
    key = LLM_API_KEYS.get(provider.lower())
    if not key:
        logger.warning(f"Unknown LLM provider: {provider}")
        return None
    value = get_secret(key, user_id=user_id)
    if value:
        return str(value)
    return None


def get_llm_setting(key: str, user_id: str = None, default=None):
    """Get LLM setting from vault"""
    return get_secret(key, user_id=user_id) or default


def get_all_llm_providers() -> list[str]:
    """Get list of available LLM providers that have valid API keys"""
    available = []
    for provider in LLM_API_KEYS.keys():
        if provider in ["ollama_url", "lm_studio_url", "cloudflare_account_id"]:
            continue
        if get_llm_api_key(provider):
            available.append(provider)
    return available
