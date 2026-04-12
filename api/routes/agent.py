from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import logging
import uuid
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from api.utils.limiter import limiter
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI Agents"])

# Global Groq client to avoid duplicate initialization
_groq_client = None


def get_groq_client():
    """Get or create Groq client singleton"""
    global _groq_client
    if _groq_client is None:
        from api.config import settings

        if settings.GROQ_API_KEY:
            from groq import AsyncGroq

            _groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _groq_client


class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class AgentRequest(BaseModel):
    task: str
    agents: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


class CodeRequest(BaseModel):
    code: str
    language: Optional[str] = "python"


@router.post("/chat")
async def chat_with_agent(
    request: Request,
    body: ChatMessage,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Chat with AI agent. Supports both Groq and OpenAI.
    """
    from api.config import settings

    # Add correlation ID for tracing
    correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    # Try OpenAI first (default), fallback to Groq
    provider = body.context.get("provider", "openai") if body.context else "openai"

    try:
        system_prompt = "You are a helpful AI assistant for a viral content creation platform. Be concise and actionable."
        if body.context:
            system_prompt += f"\n\nContext: {body.context}"

        if provider == "openai" and settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": body.message},
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            return {
                "response": response.choices[0].message.content,
                "status": "success",
                "agent": "openai",
                "correlation_id": correlation_id,
            }
        elif settings.GROQ_API_KEY:
            client = get_groq_client()
            if not client:
                raise HTTPException(status_code=503, detail="GROQ API not configured")
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": body.message},
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            return {
                "response": response.choices[0].message.content,
                "status": "success",
                "agent": "groq",
                "correlation_id": correlation_id,
            }
        else:
            raise HTTPException(status_code=503, detail="No LLM API keys configured")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crew")
@limiter.limit("5/minute")  # Rate limit crew executions
async def crew_task(
    request: Request,
    body: AgentRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Execute a task using CrewAI if enabled, otherwise falls back to Groq multi-step execution.
    """
    from api.config import settings

    # Add correlation ID for tracing
    correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    if settings.ENABLE_CREWAI:
        try:
            from services.crewai.service import crewai_service

            result = await crewai_service.execute_task(
                task=body.task,
                agents=body.agents or ["researcher", "writer"],
                context=body.context or {},
            )
            return {
                "result": result,
                "status": "success",
                "agent": "crewai",
                "correlation_id": correlation_id,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Fallback: Simulate multi-agent workflow with Groq
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="No AI backend configured. Set GROQ_API_KEY or enable CrewAI.",
        )

    try:
        client = get_groq_client()
        if not client:
            raise HTTPException(status_code=503, detail="GROQ API not configured")

        agents = body.agents or ["researcher", "writer"]
        context = body.context or {}

        agent_prompts = {
            "researcher": "You are a research analyst. Gather key facts and insights about the topic.",
            "writer": "You are a professional content writer. Create engaging, viral-ready content.",
            "analyst": "You are a data analyst. Identify patterns, metrics, and optimization opportunities.",
            "strategist": "You are a content strategy. Plan content distribution and growth tactics.",
            "editor": "You are a senior editor. Refine and polish content for maximum impact.",
        }

        accumulated_context = f"Task: {body.task}\nContext: {context}"

        # Run agents in parallel using asyncio.gather
        async def run_agent(agent_name: str) -> tuple[str, str]:
            agent_prompt = agent_prompts.get(
                agent_name,
                f"You are a {agent_name} agent. Complete your part of the task.",
            )
            try:
                response = await client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": agent_prompt},
                        {"role": "user", "content": accumulated_context},
                    ],
                    temperature=0.7,
                    max_tokens=1024,
                    timeout=30.0,
                )
                return agent_name, response.choices[0].message.content
            except Exception as e:
                logger.warning(f"[Agent] Agent {agent_name} failed: {e}")
                return agent_name, f"Agent failed: {str(e)}"

        # Execute all agents concurrently
        agent_tasks = [run_agent(agent) for agent in agents]
        agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)

        results = {}
        for result in agent_results:
            if isinstance(result, Exception):
                logger.error(f"[Agent] Task exception: {result}")
                continue
            agent_name, agent_output = result
            results[agent_name] = agent_output

        if not results:
            raise HTTPException(status_code=500, detail="All agents failed")

        # Build context for synthesis from all outputs
        synthesis_context = accumulated_context
        for agent_name, agent_output in results.items():
            synthesis_context += f"\n\n{agent_name.upper()} output: {agent_output}"

        # Final synthesis
        synthesis_response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a synthesizer. Combine all agent outputs into a cohesive final result.",
                },
                {"role": "user", "content": synthesis_context},
            ],
            temperature=0.5,
            max_tokens=2048,
            timeout=30.0,
        )

        return {
            "result": {
                "agent_outputs": results,
                "synthesis": synthesis_response.choices[0].message.content,
            },
            "status": "success",
            "agent": "groq-multi",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AccountAuditRequest(BaseModel):
    action: str = "audit"
    platform: str = "youtube"
    competitor_url: Optional[str] = None


@router.post("/account-audit")
@limiter.limit("10/minute")
async def account_audit(
    request: Request,
    body: AccountAuditRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Audit YOUR account on any platform for growth and monetization readiness.
    Generates a 2-week sprint plan to reach monetization eligibility.
    Supported platforms: youtube, tiktok, instagram, facebook, x, linkedin, snapchat, twitch
    """
    from api.config import settings
    from services.openclaw.skills.audit import audit_skill

    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="AI backend not configured")

    # Validate platform
    supported_platforms = [
        "youtube",
        "tiktok",
        "instagram",
        "facebook",
        "x",
        "linkedin",
        "snapchat",
        "twitch",
    ]
    if body.platform.lower() not in supported_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported platform. Supported: {', '.join(supported_platforms)}",
        )

    try:
        if body.action == "audit":
            result = audit_skill.audit_account(current_user.id, body.platform.lower())
        elif body.action == "compare":
            if not body.competitor_url:
                raise HTTPException(
                    status_code=400, detail="competitor_url required for compare action"
                )
            result = audit_skill.compare_with_competitor(
                current_user.id, body.competitor_url, body.platform.lower()
            )
        else:
            raise HTTPException(
                status_code=400, detail="Invalid action. Use 'audit' or 'compare'"
            )

        return {
            "result": result,
            "status": "success",
            "action": body.action,
            "platform": body.platform,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code-executor")
async def execute_code(
    request: CodeRequest, current_user: UserDB = Depends(get_current_user)
):
    """
    Execute code using Code Interpreter if enabled, otherwise uses Groq for code analysis/generation.
    Does NOT execute arbitrary code server-side — returns AI-generated code and explanation.
    """
    from api.config import settings

    if settings.ENABLE_INTERPRETER:
        try:
            from services.interpreter.service import interpreter_service

            result = await interpreter_service.execute(request.code)
            return {"result": result, "status": "success", "agent": "interpreter"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Fallback: Groq code analysis/generation
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="No AI backend configured. Set GROQ_API_KEY or enable Code Interpreter.",
        )

    try:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=settings.GROQ_API_KEY)

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a {request.language} code assistant. "
                        "Analyze, explain, and improve code. "
                        "Provide corrected/enhanced code with explanations. "
                        "NEVER execute code. Only analyze and generate."
                    ),
                },
                {"role": "user", "content": request.code},
            ],
            temperature=0.3,
            max_tokens=2048,
        )

        return {
            "result": {
                "analysis": response.choices[0].message.content,
                "language": request.language,
                "note": "Code Interpreter not enabled. Using AI analysis instead of execution.",
            },
            "status": "success",
            "agent": "groq-code-analysis",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_agent_capabilities(current_user: UserDB = Depends(get_current_user)):
    """
    Get available agent capabilities with real status.
    """
    from api.config import settings

    capabilities = {
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

    return capabilities
