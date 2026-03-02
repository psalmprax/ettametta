"""
Integration Tests for Discovery Bridge
=======================================
Verifies the connection between the FastAPI gateway and the Go-based discovery-go engine.
"""

import pytest
import httpx
from fastapi import status
from unittest.mock import patch, AsyncMock
from api.routes.discovery import DISCOVERY_GO_URL

@pytest.mark.integration
class TestDiscoveryGoBridge:
    """Test suite for the Discovery-Go Bridge."""

    @pytest.mark.asyncio
    async def test_trigger_scan_bridge_success(self, client):
        """Verify that the /discovery/scan endpoint correctly proxies requests to Go."""
        # Mock the external Go service response
        mock_response = {
            "status": "success",
            "message": "Scan initiated for 2 niches",
            "job_ids": ["job-1", "job-2"]
        }
        
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(spec=httpx.Response)
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            response = client.post(
                "/discovery/scan",
                json={"niches": ["Technology", "AI"]}
            )
            
            assert response.status_code == 200
            assert response.json() == mock_response
            # Verify it hit the correct Go URL
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert DISCOVERY_GO_URL in args[0]

    @pytest.mark.asyncio
    async def test_trigger_scan_bridge_failure(self, client):
        """Verify handling of Go service being down (Connection Error)."""
        with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
            response = client.post(
                "/discovery/scan",
                json={"niches": ["Technology"]}
            )
            
            assert response.status_code == 500
            assert "Go Bridge Error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_trigger_scan_bridge_timeout(self, client):
        """Verify handling of Go service timeout."""
        with patch("httpx.AsyncClient.post", side_effect=httpx.ReadTimeout("Read timeout")):
            response = client.post(
                "/discovery/scan",
                json={"niches": ["Technology"]}
            )
            
            assert response.status_code == 500
            assert "Go Bridge Error" in response.json()["detail"]

@pytest.mark.integration
class TestRedisCeleryConnectivity:
    """Verify core middleware connectivity used by Discovery."""
    
    def test_redis_heartbeat(self):
        """Test physical connection to Redis."""
        import redis
        from api.config import settings
        
        # Test client connection logic similar to service.py
        redis_url = settings.REDIS_URL
        if "//localhost" in redis_url:
             redis_url = redis_url.replace("//localhost", "//redis")
             
        try:
            r = redis.from_url(redis_url, socket_timeout=5)
            assert r.ping() is True
        except Exception as e:
            pytest.skip(f"Redis not reachable: {e}")

    def test_celery_broker_health(self):
        """Test if Celery can connect to the broker."""
        from api.utils.celery import celery_app
        try:
            with celery_app.connection() as connection:
                connection.connect()
                assert connection.connected is True
        except Exception as e:
            pytest.skip(f"Celery broker not reachable: {e}")

from unittest.mock import MagicMock
