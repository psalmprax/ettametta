from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from src.services.llm.mythos_agent import MythosReasoningAgent
from src.api.utils.api_responses import success_response
from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB

router = APIRouter(prefix="/reason", tags=["Reasoning"])

class ReasoningRequest(BaseModel):
    prompt: str = Field(..., description="The problem or task to reason about")
    depth: int = Field(3, ge=1, le=10, description="The number of recurrent reasoning loops")
    provider: str | None = Field(None, description="Explicit LLM provider (e.g. 'ollama', 'openai')")

@router.post("")
async def mythos_reasoning(
    body: ReasoningRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """
    OpenMythos-inspired Reasoning Endpoint.
    Uses recurrent-depth logic to 'think' through complex problems.
    """
    try:
        agent = MythosReasoningAgent(provider=body.provider)
        result = await agent.reason(prompt=body.prompt, depth=body.depth, provider=body.provider)

        return success_response(
            data={
                "answer": result["answer"],
                "trace": result["trace"],
                "depth": result["depth"],
                "user": current_user.email
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
