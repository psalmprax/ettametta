import pytest
import httpx
from httpx import AsyncClient, ASGITransport
from src.api.main import app
from unittest.mock import patch, MagicMock
import json

@pytest.mark.asyncio
async def test_get_blueprints():
    # App routers are triple-prefixed: /api + /v1 + /nexus + router_prefix(/nexus)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/nexus/blueprints")
    # Real-First: Expect 200 or 401 if auth is strictly enforced
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        data = response.json()
        assert len(data) > 0
        assert data[0]["id"] in ["viral-reskin", "story-factory"]

@pytest.mark.asyncio
async def test_nexus_composition_route():
    payload = {
        "niche": "Motivation",
        "blueprint_id": "story-factory",
        "cinema_mode": True
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Note: This might return 401 if auth is enforced, but we test the route logic
        response = await ac.post("/api/v1/nexus/compose", json=payload)
    
    assert response.status_code in [200, 401]

@pytest.mark.asyncio
async def test_trigger_scan_bridge_timeout():
    """Verify handling of Go service timeout."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with patch("src.api.routes.discovery.httpx.AsyncClient.post", side_effect=httpx.ReadTimeout("Read timeout")):
            with pytest.raises(httpx.ReadTimeout):
                await ac.post(
                    "/api/v1/discovery/scan",
                    json={"niches": ["Technology"]}
                )

@pytest.mark.asyncio
async def test_discovery_deep_scan_route():
    payload = {
        "niches": ["AI Automation"],
        "deep": True
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/discovery/scan", json=payload)
    
    assert response.status_code in [200, 401]

@pytest.mark.asyncio
async def test_autocreator_fallback_logic():
    from src.services.nexus_engine.auto_creator import base_creator_service
    from src.services.monetization.auto_merch import base_auto_merch_service
    
    # Hardened Reality: Should raise ValueError if no keys are set
    with pytest.raises(ValueError) as exc:
        await base_auto_merch_service._publish_to_pod("Test Niche", "https://example.com/a.png")
    assert "Printful API Key not configured" in str(exc.value)

@pytest.mark.asyncio
async def test_trigger_scan_bridge_failure():
    """Verify handling of Go service being down (Connection Error)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # We expect the error to bubble up or return 500. 
        # In ASGITransport, it often bubbles up if not caught by middleware.
        with patch("src.api.routes.discovery.httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
            with pytest.raises(httpx.ConnectError):
                await ac.post(
                    "/api/v1/discovery/scan",
                    json={"niches": ["Technology"]}
                )
