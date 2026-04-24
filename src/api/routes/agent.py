from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any
import asyncio
import logging
import uuid
from src.api.routes.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.limiter import limiter
from src.api.utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from src.api.utils.api_responses import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI Agents"])

from src.services.llm.intelligence_hub import IntelligenceHub


class ChatMessage(BaseModel):
    message: str
    context: dict[str, Any] | None = None


class AgentRequest(BaseModel):
    task: str
    agents: list[str] | None = None
    context: dict[str, Any] | None = None


class CodeRequest(BaseModel):
    code: str
    language: str | None = "python"


@router.post("/chat")
async def chat_with_agent(
    request: Request,
    body: ChatMessage,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Chat with AI agent using IntelligenceHub (Standard 3.25)
    """
    # Add correlation ID for tracing
    correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))

    try:
        hub = IntelligenceHub()
        system_prompt = "You are a helpful AI assistant for a viral content creation platform. Be concise and actionable."
        if body.context:
            system_prompt += f"\n\nContext: {body.context}"

        ai_data = await hub.chat(
            prompt=body.message, system_prompt=system_prompt, session_id=correlation_id
        )

        return success_response(
            data={
                "response": ai_data.get("response", ai_data.get("content", "")),
                "status": "success",
                "agent": ai_data.get("provider", "intelligence-hub"),
                "correlation_id": correlation_id,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Agent] Chat failed: {e}")
        raise HTTPException(status_code=503, detail="AI service unavailable")


@router.post("/analyze-code")
async def analyze_code(
    body: CodeRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """
    IntelligenceHub code analysis
    """
    try:
        hub = IntelligenceHub()
        ai_data = await hub.chat(
            prompt=body.code,
            system_prompt=(
                f"You are a {body.language} code assistant. "
                "Analyze, explain, and improve code. "
                "Provide corrected/enhanced code with explanations. "
                "NEVER execute code. Only analyze and generate."
            ),
            complexity="high",
        )

        return success_response(
            data={
                "result": {
                    "analysis": ai_data.get("response", ai_data.get("content", "")),
                    "language": body.language,
                    "note": "Code Interpreter not enabled. Using AI analysis instead of execution.",
                },
                "status": "success",
                "agent": "intelligence-hub-code-analysis",
            }
        )
    except Exception as e:
        logger.error(f"[Agent] Code analysis failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))


class TrademarkRequest(BaseModel):
    niche: str
    account_id: str | None = None


@router.post("/generate-trademark")
async def generate_trademark(
    body: TrademarkRequest,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Autonomous Brand Factory: Generates a brand identity (Logo, Name, Color) for a niche.
    """
    from src.services.branding.service import base_branding_service

    try:
        result = await base_branding_service.generate_brand_identity(
            user_id=current_user.id,
            niche=body.niche,
            account_id=body.account_id,
            db=db,
        )
        return success_response(data=result)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/capabilities")
async def get_agent_capabilities(current_user: UserDB = Depends(get_current_user)):
    """
    Get available agent capabilities with real status.
    """
    from src.api.config import settings
    from src.services.openclaw.agent import openclaw_agent

    report = openclaw_agent.get_dependency_report()
    cb_status = (
        openclaw_agent.circuit_breaker.state
    )  # Returns "CLOSED", "OPEN", or "HALF_OPEN"

    capabilities = {
        "workforce": {
            "enabled": True,
            "status": "healthy" if cb_status.upper() == "CLOSED" else "degraded",
            "report": report,
            "circuit_breaker": cb_status.lower(),  # Return lowercase for API consistency
            "description": "Alpha Workforce (OpenClaw) Agentic Engine",
        },
        "discovery": {
            "enabled": True,
            "actions": ["search", "trends", "scan", "predict", "ideas", "analyze"],
            "description": "Advanced trend discovery, competitor analysis, and content ideation",
            "fallback": "groq-discovery" if settings.GROQ_API_KEY else None,
            "available": True,
        },
        "competitor": {
            "enabled": True,
            "description": "Competitor strategy analysis and market intelligence",
            "fallback": "groq-analysis" if settings.GROQ_API_KEY else None,
            "available": True,
        },
        "account_audit": {
            "enabled": True,
            "actions": ["audit", "compare"],
            "description": "Audit YOUR account on any platform for growth and monetization readiness with 2-week sprint plan",
            "platforms": [
                "youtube",
                "tiktok",
                "instagram",
                "facebook",
                "x",
                "linkedin",
                "snapchat",
                "twitch",
            ],
            "available": bool(settings.GROQ_API_KEY),
        },
        "langchain": {
            "enabled": settings.ENABLE_LANGCHAIN,
            "model": settings.LANGCHAIN_MODEL,
            "description": "LLM-powered conversational agent",
            "fallback": "groq-direct" if settings.GROQ_API_KEY else None,
            "available": settings.ENABLE_LANGCHAIN or bool(settings.GROQ_API_KEY),
        },
        "crewai": {
            "enabled": settings.ENABLE_CREWAI,
            "agents": settings.CREWAI_AGENTS.split(","),
            "description": "Multi-agent crew for complex tasks",
            "fallback": "groq-multi" if settings.GROQ_API_KEY else None,
            "available": settings.ENABLE_CREWAI or bool(settings.GROQ_API_KEY),
        },
        "interpreter": {
            "enabled": settings.ENABLE_INTERPRETER,
            "description": "Code execution agent",
            "fallback": "groq-code-analysis" if settings.GROQ_API_KEY else None,
            "available": settings.ENABLE_INTERPRETER or bool(settings.GROQ_API_KEY),
        },
        "groq": {
            "available": bool(settings.GROQ_API_KEY),
            "model": "llama-3.3-70b-versatile",
            "description": "Direct Groq LLM access (used as fallback)",
        },
    }

    return success_response(data=capabilities)
