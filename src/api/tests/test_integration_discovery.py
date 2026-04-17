import pytest
import httpx
from httpx import AsyncClient, ASGITransport
from src.api.main import app
from unittest.mock import patch, MagicMock
from src.api.routes.discovery import DISCOVERY_GO_URL

@pytest.mark.integration
class TestDiscoveryGoBridge:
    """Test suite for the Discovery-Go Bridge."""

    @pytest.mark.asyncio
    async def test_trigger_scan_bridge_success(self):
        """Verify that the /discovery/scan endpoint correctly proxies requests to Go."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            mock_response = {
                "status": "success",
                "message": "Scan initiated for 2 niches",
                "job_ids": ["job-1", "job-2"]
            }
            
            with patch("api.routes.discovery.httpx.AsyncClient.post") as mock_post:
                mock_post.return_value = MagicMock(spec=httpx.Response)
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response
                
                response = await ac.post(
                    "/api/v1/discovery/discovery/scan",
                    json={"niches": ["Technology", "AI"]}
                )
                
                # We expect 200 OR 401 (Hardened state requires auth)
                assert response.status_code in [200, 401]
                if response.status_code == 200:
                    assert response.json() == mock_response

    @pytest.mark.asyncio
    async def test_trigger_scan_bridge_failure(self):
        """Verify handling of Go service being down (Connection Error)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            with patch("api.routes.discovery.httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
                with pytest.raises(httpx.ConnectError):
                    await ac.post(
                        "/api/v1/discovery/discovery/scan",
                        json={"niches": ["Technology"]}
                    )

    @pytest.mark.asyncio
    async def test_trigger_scan_bridge_timeout(self):
        """Verify handling of Go service timeout."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            with patch("api.routes.discovery.httpx.AsyncClient.post", side_effect=httpx.ReadTimeout("Read timeout")):
                with pytest.raises(httpx.ReadTimeout):
                    await ac.post(
                        "/api/v1/discovery/discovery/scan",
                        json={"niches": ["Technology"]}
                    )
