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

    # Check for video generation intent first
    video_trigger = await trigger_video_generation(body.message, body.context)
    if video_trigger:
        return video_trigger

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


# Video generation trigger - detects intent and calls OpenCLAW skills
async def trigger_video_generation(message: str, context: dict) -> dict:
    """Detect video generation intent and trigger OpenCLAW skill"""
    import re

    message_lower = message.lower()

    # Detect video generation keywords
    video_keywords = [
        "generate video",
        "create video",
        "make video",
        "video of",
        "generate using",
        "create using",
        "make using",
    ]
    provider_keywords = [
        "pixverse",
        "kling",
        "haiper",
        "luma",
        "leiapix",
        "pika",
        "runway",
        "leonardo",
        "heygen",
        "genmo",
        "perchance",
    ]

    # Check if it's a video generation request
    is_video_request = any(kw in message_lower for kw in video_keywords)
    provider = None

    # Detect which provider
    for kw in provider_keywords:
        if kw in message_lower:
            provider = kw
            break

    if is_video_request and provider:
        # Extract prompt from message
        prompt_match = re.search(
            r"video (?:of |about )?(.+?)(?:using|$)", message, re.IGNORECASE
        )
        prompt = prompt_match.group(1).strip() if prompt_match else message

        # Auto-detect use case from message
        use_case = None
        if (
            "short" in message_lower
            or "tiktok" in message_lower
            or "reels" in message_lower
        ):
            use_case = "short_form"
        elif "cinematic" in message_lower or "film" in message_lower:
            use_case = "cinematic"
        elif "product" in message_lower:
            use_case = "product"
        elif "portrait" in message_lower:
            use_case = "portrait"

        # Get model settings for auto-recommendation
        try:
            from services.openclaw.skills.model_settings import (
                get_model_settings,
                get_recommended_settings,
                get_image_recommended_settings,
            )

            model_info = get_model_settings(provider)
        except ImportError:
            model_info = None

        # Get aspect ratio from context or auto-recommend
        if context is None:
            context = {}

        use_case_from_ctx = context.get("use_case", use_case)

        if provider == "perchance":
            # Image generation - use image recommended settings
            if not context.get("generator"):
                img_recs = get_image_recommended_settings(provider)
                context.setdefault("generator", img_recs.get("generator", "default"))
            if not context.get("resolution"):
                img_recs = get_image_recommended_settings(provider)
                context.setdefault("resolution", img_recs.get("resolution", "hd"))
            if not context.get("aspect_ratio"):
                img_recs = get_image_recommended_settings(provider)
                context.setdefault("aspect_ratio", img_recs.get("aspect_ratio", "1:1"))
            aspect_ratio = context.get("aspect_ratio", "1:1")
        else:
            # Video generation - use video recommended settings
            aspect_ratio = context.get("aspect_ratio")
            if not aspect_ratio and model_info:
                video_recs = get_recommended_settings(provider, use_case_from_ctx)
                aspect_ratio = video_recs.get("aspect_ratio", "16:9")
            elif not aspect_ratio:
                aspect_ratio = "16:9"

        # Import and run the skill
        try:
            skill_map = {
                "pixverse": ("services.openclaw.skills.pixverse", "PixVerseSkill"),
                "kling": ("services.openclaw.skills.kling", "KlingSkill"),
                "haiper": ("services.openclaw.skills.haiper", "HaiperSkill"),
                "luma": ("services.openclaw.skills.luma", "LumaSkill"),
                "leiapix": ("services.openclaw.skills.leiapix", "LeiaPixSkill"),
                "pika": ("services.openclaw.skills.pika", "PikaSkill"),
                "runway": ("services.openclaw.skills.runway", "RunwaySkill"),
                "perchance": ("services.openclaw.skills.perchance", "PerchanceSkill"),
            }

            if provider in skill_map:
                module_path, class_name = skill_map[provider]
                module = __import__(module_path, fromlist=[class_name])
                skill_class = getattr(module, class_name)

                skill = skill_class()
                await skill.initialize()
                try:
                    # Perchance = image generation (different params)
                    if provider == "perchance":
                        result = await asyncio.wait_for(
                            skill.generate(
                                prompt=prompt,
                                generator=context.get("generator", "default"),
                                resolution=context.get("resolution", "hd"),
                                aspect_ratio=context.get("aspect_ratio", "1:1"),
                                negative_prompt=context.get("negative_prompt", ""),
                                seed=context.get("seed", -1),
                                batch_size=context.get("batch_size", 1),
                            ),
                            timeout=180.0,
                        )
                        await skill.cleanup()
                        if result.get("status") == "success":
                            return {
                                "response": f"✅ Image generated successfully! URLs: {result.get('image_urls', [])}",
                                "status": "success",
                                "provider": provider,
                                "image_urls": result.get("image_urls"),
                            }
                        else:
                            return {
                                "response": f"⚠️ Image generation failed: {result.get('error', 'Unknown error')}",
                                "status": "error",
                                "provider": provider,
                            }
                    else:
                        # Video providers
                        result = await asyncio.wait_for(
                            skill.generate(prompt=prompt, aspect_ratio=aspect_ratio),
                            timeout=180.0,  # 3 minutes
                        )
                        await skill.cleanup()

                        if result.get("status") == "success":
                            return {
                                "response": f"✅ Video generated successfully! URL: {result.get('video_url', 'N/A')}",
                                "status": "success",
                                "provider": provider,
                                "video_url": result.get("video_url"),
                            }
                        else:
                            return {
                                "response": f"⚠️ Video generation failed: {result.get('error', 'Unknown error')}",
                                "status": "error",
                                "provider": provider,
                            }
                except asyncio.TimeoutError:
                    await skill.cleanup()
                    return {
                        "response": f"⏱️ Generation timed out after 3 minutes. Platform {provider} may be slow or require manual verification.",
                        "status": "error",
                    }
        except Exception as e:
            return {
                "response": f"Video generation failed: {str(e)}",
                "status": "error",
            }

    return None  # Not a video generation request


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

            # Check if service is enabled
            if not crewai_service.is_enabled():
                raise HTTPException(
                    status_code=503,
                    detail="CrewAI service not enabled. Set ENABLE_CREWAI=true and provide valid GROQ_API_KEY.",
                )

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
        except HTTPException:
            raise
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
    from services.openclaw.agent import openclaw_agent

    report = openclaw_agent.get_dependency_report()
    cb_status = openclaw_agent.circuit_breaker.state  # "closed", "open", "half-open"

    capabilities = {
        "workforce": {
            "enabled": True,
            "status": "healthy" if cb_status == "closed" else "degraded",
            "report": report,
            "circuit_breaker": cb_status,
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

    return capabilities
