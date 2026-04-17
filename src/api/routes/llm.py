"""
LLM Routes - Unified Multi-Provider LLM API
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any
from src.api.routes.auth import get_current_user
from src.api.utils.user_models import UserDB

router = APIRouter(prefix="/llm", tags=["LLM - Multi-Provider"])


class CompletionRequest(BaseModel):
    prompt: str
    system_message: str | None = None
    provider: str | None = None  # groq, openai, xai, deepseek, anthropic, gemini
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1024
    response_format: dict | None = None


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    provider: str | None = None
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1024


@router.get("/providers")
async def list_providers(current_user: UserDB = Depends(get_current_user)):
    """Get available LLM providers and their status."""
    from src.services.llm.service import unified_llm_service

    return {
        "default_provider": unified_llm_service.default_provider.value,
        "providers": unified_llm_service.get_available_providers(),
    }


@router.get("/models")
async def list_models():
    """
    Get available models across all LLM providers.
    """
    return {
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"],
        "groq": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma-7b"],
        "mistral": ["mistral-large", "mistral-small", "mixtral"],
        "perplexity": ["llama-3.1-sonar-small", "llama-3.1-sonar-large"],
    }


@router.post("/complete")
async def complete(
    request: CompletionRequest, current_user: UserDB = Depends(get_current_user)
):
    """
    Generate a completion using any available LLM provider.
    Falls back to alternate providers if primary fails.
    """
    from src.services.llm.service import unified_llm_service, LLMProvider

    provider = None
    if request.provider:
        try:
            provider = LLMProvider(request.provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider. Choose from: groq, openai, xai, deepseek, anthropic, gemini",
            )

    try:
        result = await unified_llm_service.complete(
            prompt=request.prompt,
            system_message=request.system_message,
            provider=provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=request.response_format,
        )

        if "error" in result and "content" not in result:
            raise HTTPException(status_code=503, detail=result["error"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(request: ChatRequest, current_user: UserDB = Depends(get_current_user)):
    """
    Chat completion using message history with any LLM provider.
    """
    from src.services.llm.service import unified_llm_service, LLMProvider

    provider = None
    if request.provider:
        try:
            provider = LLMProvider(request.provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider. Choose from: groq, openai, xai, deepseek, anthropic, gemini",
            )

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        result = await unified_llm_service.chat(
            messages=messages,
            provider=provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        if "error" in result and "content" not in result:
            raise HTTPException(status_code=503, detail=result["error"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class EmbedRequest(BaseModel):
    input: str
    model: str = "text-embedding-3-small"


@router.post("/embed")
async def create_embedding(
    request: EmbedRequest, current_user: UserDB = Depends(get_current_user)
):
    """
    Create embeddings using available provider.
    """
    from src.services.llm.service import LLMProvider, unified_llm_service

    # Use OpenAI for embeddings (most compatible)
    if not unified_llm_service.is_available(LLMProvider.OPENAI):
        raise HTTPException(
            status_code=503, detail="OpenAI API key required for embeddings"
        )

    import httpx
    from src.api.config import settings

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"input": request.input, "model": request.model},
            )
            response.raise_for_status()
            data = response.json()

            return {
                "embedding": data["data"][0]["embedding"],
                "model": data["model"],
                "provider": "openai",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
