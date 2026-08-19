import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_agent_gateway_health():
    response = client.get("/api/v1/agents/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["available_mcp_tools"] >= 4


def test_agent_gateway_list_mcp_tools():
    response = client.get("/api/v1/agents/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "ettametta_discover_trends" in tool_names


def test_agent_gateway_execute_mcp_tool():
    payload = {
        "tool_name": "ettametta_optimize_aeo",
        "arguments": {
            "title": "Agentic Workflows in 2026",
            "script": "Here is how autonomous AI agents cut company operational costs by 90%. First, they manage scheduling automatically.",
            "niche": "Technology",
        },
    }
    response = client.post("/api/v1/agents/mcp/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "scores" in data["result"]


def test_agent_gateway_autonomous_cycle():
    payload = {
        "niche": "saas_marketing",
        "platforms": ["youtube"],
        "autonomy_mode": "SIMULATION",
    }
    response = client.post("/api/v1/agents/autonomous-cycle", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "cycle_id" in data
