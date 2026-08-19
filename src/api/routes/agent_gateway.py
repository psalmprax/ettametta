"""
Agent-to-Agent (A2A) Headless Gateway
====================================
Fast, programmatic REST & MCP execution endpoints designed for autonomous AI agents.
"""

import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.opencli.mcp_server import base_mcp_server_service
from src.services.hermes.service import base_hermes_service, HermesCycleConfig

logger = logging.getLogger("AgentGatewayAPI")

router = APIRouter(prefix="/agents", tags=["Agent-to-Agent (A2A) Gateway"])


class MCPExecuteRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class AutonomousCycleRequest(BaseModel):
    niche: str = "ai_technology"
    platforms: list[str] = Field(default_factory=lambda: ["youtube", "tiktok"])
    autonomy_mode: str = "AUTOPILOT"  # AUTOPILOT, SIMULATION, APPROVAL_REQUIRED


@router.get("/health", summary="Check A2A Gateway Health")
async def agent_health():
    """Returns status and tool capabilities for AI agents."""
    return {
        "status": "online",
        "service": "ettametta-agent-gateway",
        "available_mcp_tools": len(base_mcp_server_service.list_tools()),
    }


@router.get("/mcp/tools", summary="List Available MCP Tools")
async def list_mcp_tools():
    """Returns the Model Context Protocol tools manifest."""
    return {
        "tools": base_mcp_server_service.list_tools(),
    }


@router.post("/mcp/execute", summary="Execute MCP Tool")
async def execute_mcp_tool(payload: MCPExecuteRequest):
    """Executes a tool call requested by an external AI Agent."""
    result = await base_mcp_server_service.execute_tool(
        tool_name=payload.tool_name,
        arguments=payload.arguments,
    )
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Execution failed"),
        )
    return result


@router.post("/autonomous-cycle", summary="Trigger Full Hermes Autonomous Cycle")
async def trigger_autonomous_cycle(payload: AutonomousCycleRequest):
    """Triggers an end-to-end trend discovery -> AEO optimization -> render -> publish cycle."""
    config = HermesCycleConfig(
        niche=payload.niche,
        target_platforms=payload.platforms,
        autonomy_mode=payload.autonomy_mode,
    )
    result = await base_hermes_service.run_autonomous_cycle(config)
    return result.model_dump()
