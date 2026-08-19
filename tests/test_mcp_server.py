import pytest
from src.services.opencli.mcp_server import base_mcp_server_service, EttamettaMCPServer


@pytest.mark.asyncio
async def test_mcp_list_tools():
    tools = base_mcp_server_service.list_tools()
    tool_names = [t["name"] for t in tools]

    assert "ettametta_discover_trends" in tool_names
    assert "ettametta_optimize_aeo" in tool_names
    assert "ettametta_publish_social" in tool_names
    assert "ettametta_run_autonomous_cycle" in tool_names


@pytest.mark.asyncio
async def test_mcp_execute_aeo_tool():
    result = await base_mcp_server_service.execute_tool(
        tool_name="ettametta_optimize_aeo",
        arguments={
            "title": "Why Agents Are The New Customers",
            "script": "Here is why AI agents will generate over $100M in software revenue by 2027. First, they operate 24/7. Second, they have zero human churn.",
            "niche": "AI Economics",
        },
    )

    assert result["success"] is True
    assert "scores" in result["result"]
    assert result["result"]["scores"]["overall_aeo_score"] > 0


@pytest.mark.asyncio
async def test_mcp_execute_autonomous_cycle():
    result = await base_mcp_server_service.execute_tool(
        tool_name="ettametta_run_autonomous_cycle",
        arguments={
            "niche": "crypto_trading",
            "platforms": ["youtube"],
            "autonomy_mode": "SIMULATION",
        },
    )

    assert result["success"] is True
    assert result["result"]["status"] == "completed"
    assert "cycle_id" in result["result"]
