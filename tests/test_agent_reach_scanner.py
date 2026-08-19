import pytest
from src.services.discovery.agent_reach_scanner import base_agent_reach_service, AgentReachScanner, AgentReachPlatformStatus
from src.services.discovery.models import ContentCandidate


@pytest.mark.asyncio
async def test_agent_reach_doctor_check():
    statuses = await base_agent_reach_service.doctor_check()
    assert isinstance(statuses, list)
    assert len(statuses) >= 4
    platform_names = [s.platform for s in statuses]
    assert "youtube" in platform_names
    assert "reddit" in platform_names
    assert "bilibili" in platform_names


@pytest.mark.asyncio
async def test_agent_reach_stealth_youtube_search():
    candidates = await base_agent_reach_service.search_platform_trends(
        query="AI Automation",
        platform="youtube",
        max_results=3,
    )

    assert len(candidates) > 0
    assert isinstance(candidates[0], ContentCandidate)
    assert candidates[0].platform == "youtube"
    assert candidates[0].viral_score > 80


@pytest.mark.asyncio
async def test_agent_reach_stealth_bilibili_search():
    candidates = await base_agent_reach_service.search_platform_trends(
        query="Tech Gadgets",
        platform="bilibili",
        max_results=2,
    )

    assert len(candidates) > 0
    assert candidates[0].platform == "bilibili"
    assert candidates[0].viral_score > 90
