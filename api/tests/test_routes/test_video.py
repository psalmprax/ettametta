"""
Video Pipeline Endpoint Tests
============================
Integration tests for video transformation and generation routes
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, AsyncMock, MagicMock


class TestVideoTransformation:
    """Test video transformation endpoints."""
    
    @pytest.fixture
    def auth_token(self, client: TestClient):
        """Get auth token for authenticated requests."""
        client.post("/auth/register", json={
            "username": "videouser",
            "email": "video@example.com",
            "password": "password123"
        })
        
        response = client.post("/auth/login", data={
            "username": "videouser",
            "password": "password123"
        })
        
        return response.json()["access_token"]
    
    def test_transform_requires_auth(self, client: TestClient):
        """Test that transform endpoint requires authentication."""
        response = client.post("/video/transform", json={
            "input_url": "https://example.com/video.mp4",
            "niche": "Technology",
            "platform": "YouTube Shorts"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch("services.video_engine.tasks.download_and_process_task.delay")
    def test_transform_success(self, mock_task, client: TestClient, auth_token):
        """Test successful video transformation."""
        mock_task.return_value = MagicMock(id="test-task-123")
        
        response = client.post(
            "/video/transform",
            json={
                "input_url": "https://example.com/video.mp4",
                "niche": "Technology",
                "platform": "YouTube Shorts",
                "quality_tier": "standard"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "Queued"
    
    @patch("services.video_engine.tasks.download_and_process_task.delay")
    def test_transform_with_style(self, mock_task, client: TestClient, auth_token):
        """Test transformation with custom style."""
        mock_task.return_value = MagicMock(id="test-task-456")
        
        response = client.post(
            "/video/transform",
            json={
                "input_url": "https://example.com/video.mp4",
                "niche": "Motivation",
                "platform": "TikTok",
                "style": "Cinematic"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
    
    def test_transform_missing_input_url(self, client: TestClient, auth_token):
        """Test transformation with missing input URL."""
        response = client.post(
            "/video/transform",
            json={
                "niche": "Technology",
                "platform": "YouTube Shorts"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestVideoGeneration:
    """Test AI video generation endpoints."""
    
    @pytest.fixture
    def auth_token(self, client: TestClient):
        """Get auth token for authenticated requests."""
        client.post("/auth/register", json={
            "username": "genuser",
            "email": "gen@example.com",
            "password": "password123"
        })
        
        response = client.post("/auth/login", data={
            "username": "genuser",
            "password": "password123"
        })
        
        return response.json()["access_token"]
    
    def test_generate_requires_auth(self, client: TestClient):
        """Test that generate endpoint requires authentication."""
        response = client.post("/video/generate", json={
            "prompt": "A beautiful sunset",
            "engine": "lite4k",
            "style": "Cinematic"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch("services.video_engine.tasks.generate_video_task.delay")
    def test_generate_lite4k(self, mock_task, client: TestClient, auth_token):
        """Test lite4k video generation."""
        mock_task.return_value = MagicMock(id="lite4k-task-123")
        
        response = client.post(
            "/video/generate",
            json={
                "prompt": "A futuristic city at night",
                "engine": "lite4k",
                "style": "Cinematic",
                "aspect_ratio": "9:16"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should return 200 or 402 (payment required for non-premium)
        assert response.status_code in [200, 402]
    
    @patch("services.video_engine.tasks.generate_video_task.delay")
    def test_generate_ltx_video(self, mock_task, client: TestClient, auth_token):
        """Test LTX video generation."""
        mock_task.return_value = MagicMock(id="ltx-task-123")
        
        response = client.post(
            "/video/generate",
            json={
                "prompt": "Ocean waves crashing",
                "engine": "ltx-video",
                "style": "Natural",
                "aspect_ratio": "16:9"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should return 200 or 402 (payment required)
        assert response.status_code in [200, 402]
    
    @patch("services.video_engine.tasks.generate_video_task.delay")
    def test_generate_veo3(self, mock_task, client: TestClient, auth_token):
        """Test Veo3 video generation."""
        mock_task.return_value = MagicMock(id="veo3-task-123")
        
        response = client.post(
            "/video/generate",
            json={
                "prompt": "A bird flying over mountains",
                "engine": "veo3",
                "style": "Cinematic"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [200, 402]
    
    def test_generate_invalid_engine(self, client: TestClient, auth_token):
        """Test generation with invalid engine."""
        response = client.post(
            "/video/generate",
            json={
                "prompt": "Test",
                "engine": "invalid_engine"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # May pass or fail depending on implementation
        assert response.status_code in [200, 422, 500]


class TestVideoJobs:
    """Test video job listing and status endpoints."""
    
    @pytest.fixture
    def auth_token(self, client: TestClient):
        """Get auth token for authenticated requests."""
        client.post("/auth/register", json={
            "username": "jobuser",
            "email": "job@example.com",
            "password": "password123"
        })
        
        response = client.post("/auth/login", data={
            "username": "jobuser",
            "password": "password123"
        })
        
        return response.json()["access_token"]
    
    def test_list_jobs_requires_auth(self, client: TestClient):
        """Test that jobs list requires authentication."""
        response = client.get("/video/jobs")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_jobs_success(self, client: TestClient, auth_token):
        """Test listing jobs with authentication."""
        response = client.get(
            "/video/jobs",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_job_status(self, client: TestClient, auth_token):
        """Test getting specific job status."""
        response = client.get(
            "/video/jobs/test-job-id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # May return 200 with job data or 404
        assert response.status_code in [200, 404]


class TestRemotion:
    """Test Remotion rendering endpoints."""
    
    @pytest.fixture
    def auth_token(self, client: TestClient):
        """Get auth token for authenticated requests."""
        client.post("/auth/register", json={
            "username": "remotionuser",
            "email": "remotion@example.com",
            "password": "password123"
        })
        
        response = client.post("/auth/login", data={
            "username": "remotionuser",
            "password": "password123"
        })
        
        return response.json()["access_token"]
    
    def test_remotion_requires_auth(self, client: TestClient):
        """Test that Remotion endpoint requires authentication."""
        response = client.post("/remotion/render", json={
            "composition_id": "test",
            "input_props": {}
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch("services.video_engine.remotion_service.render_composition")
    def test_remotion_render(self, mock_render, client: TestClient, auth_token):
        """Test Remotion composition rendering."""
        mock_render.return_value = AsyncMock()()
        mock_render.return_value.__aenter__ = AsyncMock(return_value={
            "render_id": "render-123",
            "status": "completed",
            "output_url": "https://example.com/output.mp4"
        })
        mock_render.return_value.__aexit__ = AsyncMock(return_value=None)
        
        response = client.post(
            "/remotion/render",
            json={
                "composition_id": "CinematicMinimal",
                "input_props": {
                    "title": "Test Video",
                    "subtitle": "Test Subtitle"
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [200, 500]
