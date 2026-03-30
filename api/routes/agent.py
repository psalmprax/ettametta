from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB

router = APIRouter(prefix="/agent", tags=["AI Agents"])


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
    request: ChatMessage, current_user: UserDB = Depends(get_current_user)
):
    """
    Chat with AI agent. Uses LangChain if enabled, otherwise falls back to Groq LLM directly.
    """
    from api.config import settings

    if settings.ENABLE_LANGCHAIN:
        try:
            from services.langchain.service import langchain_service

            response = await langchain_service.chat(
                request.message, request.context or {}
            )
            return {"response": response, "status": "success", "agent": "langchain"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Fallback: Direct Groq API
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="No AI backend configured. Set GROQ_API_KEY or enable LangChain.",
        )

    try:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=settings.GROQ_API_KEY)

        system_prompt = "You are a helpful AI assistant for a viral content creation platform. Be concise and actionable."
        if request.context:
            system_prompt += f"\n\nContext: {request.context}"

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return {
            "response": response.choices[0].message.content,
            "status": "success",
            "agent": "groq-direct",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crew")
async def crew_task(
    request: AgentRequest, current_user: UserDB = Depends(get_current_user)
):
    """
    Execute a task using CrewAI if enabled, otherwise falls back to Groq multi-step execution.
    """
    from api.config import settings

    if settings.ENABLE_CREWAI:
        try:
            from services.crewai.service import crewai_service

            result = await crewai_service.execute_task(
                task=request.task,
                agents=request.agents or ["researcher", "writer"],
                context=request.context or {},
            )
            return {"result": result, "status": "success", "agent": "crewai"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Fallback: Simulate multi-agent workflow with Groq
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="No AI backend configured. Set GROQ_API_KEY or enable CrewAI.",
        )

    try:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=settings.GROQ_API_KEY)

        agents = request.agents or ["researcher", "writer"]
        results = {}
        context = request.context or {}

        agent_prompts = {
            "researcher": "You are a research analyst. Gather key facts and insights about the topic.",
            "writer": "You are a professional content writer. Create engaging, viral-ready content.",
            "analyst": "You are a data analyst. Identify patterns, metrics, and optimization opportunities.",
            "strategist": "You are a content strategist. Plan content distribution and growth tactics.",
            "editor": "You are a senior editor. Refine and polish content for maximum impact.",
        }

        accumulated_context = f"Task: {request.task}\nContext: {context}"
        for agent_name in agents:
            agent_prompt = agent_prompts.get(
                agent_name,
                f"You are a {agent_name} agent. Complete your part of the task.",
            )
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": agent_prompt},
                    {"role": "user", "content": accumulated_context},
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            agent_result = response.choices[0].message.content
            results[agent_name] = agent_result
            accumulated_context += f"\n\n{agent_name.upper()} output: {agent_result}"

        # Final synthesis
        synthesis_response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a synthesizer. Combine all agent outputs into a cohesive final result.",
                },
                {"role": "user", "content": accumulated_context},
            ],
            temperature=0.5,
            max_tokens=2048,
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
