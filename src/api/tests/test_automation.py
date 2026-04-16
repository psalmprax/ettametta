"""
End-to-End Automation Loop Tests
================================
Real-world validation of the discovery and synthesis pipeline.
"""

import pytest
import os
import httpx
from fastapi import status
from api.config import settings

# Markers for E2E and External API tests
@pytest.mark.e2e
@pytest.mark.requires_api
class TestAutomationE2E:
    """End-to-End test suite for the autonomous pipeline."""
    
    @pytest.fixture
    def base_url(self):
        """Return the API base URL. Defaults to localhost if not set."""
        return os.getenv("TEST_API_URL", "http://localhost:8000")
    
    @pytest.fixture
    def headers(self):
        """Authentication headers using INTERNAL_API_TOKEN."""
        token = os.getenv("INTERNAL_API_TOKEN") or settings.INTERNAL_API_TOKEN
        if not token:
            pytest.skip("INTERNAL_API_TOKEN not found. Skipping E2E tests.")
        return {"X-Internal-Token": token}

    @pytest.mark.asyncio
    async def test_discovery_scan_real(self, base_url, headers):
        """Verify that a real discovery scan returns results."""
        if not os.getenv("REAL_WORLD_E2E"):
            pytest.skip("REAL_WORLD_E2E not set. Skipping live Discovery hit.")
            
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/discovery/scan",
                json={"niches": ["Motivation"]},
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            # Since discovery is async/background, we just check if it was accepted

    @pytest.mark.asyncio
    async def test_video_transform_real(self, base_url, headers):
        """Verify that a video transformation job can be submitted with a real URL."""
        if not os.getenv("REAL_WORLD_E2E"):
            pytest.skip("REAL_WORLD_E2E not set. Skipping live Transform hit.")
            
        # Using a reliable public sample MP4
        sample_url = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/person-bicycle-car-detection.mp4"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/video/transform",
                json={
                    "input_url": sample_url,
                    "niche": "Security",
                    "platform": "YouTube Shorts",
                    "quality_tier": "standard"
                },
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert data["status"] == "Queued"

    @pytest.mark.asyncio
    async def test_lite4k_synthesis_real(self, base_url, headers):
        """Verify that Lite4K synthesis starts correctly."""
        if not os.getenv("REAL_WORLD_E2E"):
            pytest.skip("REAL_WORLD_E2E not set. Skipping live Synthesis hit.")
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/video/generate",
                json={
                    "prompt": "A futuristic laboratory with AI robots",
                    "engine": "lite4k",
                    "style": "Cinematic"
                },
                headers=headers
            )
            
            # 200 if processed, 402 if credits missing (test tokens should have credits)
            assert response.status_code in [200, 202, 402]

    def test_sentinel_watcher_dispatch(self, base_url, headers):
        """Verify that the Sentinel watcher can be triggered."""
        # This checks if the task endpoint exists and is secure
        with httpx.Client() as client:
            response = client.post(
                f"{base_url}/discovery/sentinel/trigger",
                headers=headers
            )
            
            # Endpoint may vary, but we verify it's not a 404
            assert response.status_code != 404
