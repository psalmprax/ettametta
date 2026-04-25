"""
LLM Routes - Unified Multi-Provider LLM API
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any
from src.api.routes.auth import get_current_user
from src.services.llm.intelligence_hub import base_intelligence_hub

router = APIRouter(prefix="/llm", tags=["LLM Services"])


class EmbedRequest(BaseModel):
    input: str
    model: str = "text-embedding-3-small"


class CircuitResetRequest(BaseModel):
    providers: list[str] | None = None


@router.post("/reset-circuits")
async def reset_circuits(
    request: CircuitResetRequest,
    current_user=Depends(get_current_user),
):
    """
    Reset circuit breakers for LLM providers.
    Use to force retry previously failing providers.
    """
    if request.providers:
        for provider in request.providers:
            base_intelligence_hub.reset_circuit(provider)
        return {
            "success": True,
            "reset_providers": request.providers,
            "msg": f"Circuit breakers reset for {len(request.providers)} provider(s)",
        }
    else:
        base_intelligence_hub.reset_all_circuits()
        return {
            "success": True,
            "reset_providers": list(base_intelligence_hub.breakers.keys()),
            "msg": "All circuit breakers reset",
        }


@router.post("/embed")
async def embed(
    request: EmbedRequest, current_user=Depends(get_current_user)
):
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
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"LLM embed failed: {e}")
        raise HTTPException(status_code=503, detail="LLM service unavailable")


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

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"LLM chat failed: {e}")
        raise HTTPException(status_code=503, detail="LLM service unavailable")


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
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"LLM embed failed: {e}")
        raise HTTPException(status_code=503, detail="LLM service unavailable")
