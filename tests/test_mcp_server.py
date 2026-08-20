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
    assert "ettametta_generate_free_broll" in tool_names


@pytest.mark.asyncio
async def test_mcp_execute_free_broll_tool():
    result = await base_mcp_server_service.execute_tool(
        tool_name="ettametta_generate_free_broll",
        arguments={
            "prompt": "futuristic smartphone preview",
            "style": "tech",
            "count": 1,
        },
    )

    assert result["success"] is True
    assert result["result"]["total_cost_usd"] == 0.0
    assert len(result["result"]["assets"]) > 0
