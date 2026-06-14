"""
Remote LLM Provider Key Check
Uses IntelligenceHub's own validation logic to determine which keys are set and valid.
"""
import sys
sys.path.insert(0, "/app")

from src.services.llm.intelligence_hub import base_intelligence_service as hub
from src.api.config import settings

print("=" * 60)
print("LLM Provider API Key Status")
print("=" * 60)

# Check provider health
print(f"\n{'Provider':12s} {'Key Valid':12s} {'Health':12s} {'Circuit':10s} {'Errors'}")
print("-" * 60)

for p in sorted(hub.provider_health.keys()):
    health = hub.provider_health[p]
    breaker_open = hub.breakers[p].is_open()
    circuit = "OPEN" if breaker_open else "CLOSED"
    print(f"{p:12s} {'—':12s} {health['status']:12s} {circuit:10s} {health['errors']}")

# Check API keys directly
print(f"\n{'Key':30s} {'Status':20s}")
print("-" * 50)

keys_to_check = [
    ("OPENAI_API_KEY", settings.OPENAI_API_KEY),
    ("GROQ_API_KEY", settings.GROQ_API_KEY),
    ("GOOGLE_API_KEY", settings.GOOGLE_API_KEY),
    ("DIFY_API_KEY", settings.DIFY_API_KEY),
    ("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY),
    ("XAI_API_KEY", settings.XAI_API_KEY),
    ("DEEPSEEK_API_KEY", settings.DEEPSEEK_API_KEY),
    ("COHERE_API_KEY", settings.COHERE_API_KEY),
    ("MISTRAL_API_KEY", settings.MISTRAL_API_KEY),
    ("CEREBRAS_API_KEY", settings.CEREBRAS_API_KEY),
    ("HUGGING_FACE_API_KEY", settings.HUGGING_FACE_API_KEY),
    ("OPENROUTER_API_KEY", settings.OPENROUTER_API_KEY),
    ("NVIDIA_API_KEY", settings.NVIDIA_API_KEY),
]

for name, value in keys_to_check:
    is_valid = hub._is_valid_key(value)
    masked = (value[:8] + "..." + value[-4:]) if value and len(value) > 12 else "—"
    status = "✅ Valid" if is_valid else ("❌ Placeholder/Empty" if value else "⬜ Not set")
    print(f"{name:30s} {status:20s}  {masked}")

print(f"\n{'DIFY_API_URL':30s} {settings.DIFY_API_URL}")
print(f"{'DIFY_TIMEOUT':30s} {settings.DIFY_TIMEOUT}s")
print(f"{'OLLAMA_URL':30s} {settings.OLLAMA_URL}")
print(f"{'OLLAMA_MODEL':30s} {settings.OLLAMA_MODEL}")
print(f"{'DEFAULT_LLM_PROVIDER':30s} {settings.DEFAULT_LLM_PROVIDER}")
print(f"{'FALLBACK_LLM_PROVIDER':30s} {settings.FALLBACK_LLM_PROVIDER}")
print()
print("=" * 60)
