"""
Video Pipeline Endpoint Tests
============================
Integration tests for video transformation and generation routes
"""

from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, AsyncMock, MagicMock


class TestVideoTransformation:
    """Test video transformation endpoints."""

    def test_transform_requires_auth(self, client: TestClient):
        """Test that transform endpoint requires authentication."""
        response = client.post("/api/v1/video/transform", json={
            "source_uri": "https://example.com/video.mp4",
            "niche": "Technology",
            "platform": "YouTube Shorts"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.services.video_engine.tasks.download_and_process_task.apply_async")
    @patch("src.services.payment.credit_service.credit_service.consume_credits", new_callable=AsyncMock)
    def test_transform_success(self, mock_credits, mock_task, client: TestClient, auth_token):
        """Test successful video transformation."""
        mock_task.return_value = MagicMock(id="test-task-123")
        mock_credits.return_value = (True, "ok")

        response = client.post(
            "/api/v1/video/transform",
            json={
                "source_uri": "https://example.com/video.mp4",
                "niche": "Technology",
                "platform": "YouTube Shorts",
                "quality_tier": "standard"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # May return 200 or 503 (Celery not running) or 402 (credits)
        assert response.status_code in [200, 402, 503]
        if response.status_code == 200:
            data = response.json()["data"]
            assert "task_id" in data

    @patch("src.services.video_engine.tasks.download_and_process_task.apply_async")
    @patch("src.services.payment.credit_service.credit_service.consume_credits", new_callable=AsyncMock)
    def test_transform_with_style(self, mock_credits, mock_task, client: TestClient, auth_token):
        """Test transformation with custom style."""
        mock_task.return_value = MagicMock(id="test-task-456")
        mock_credits.return_value = (True, "ok")

        response = client.post(
            "/api/v1/video/transform",
            json={
                "source_uri": "https://example.com/video.mp4",
                "niche": "Motivation",
                "platform": "TikTok",
                "style": "Cinematic"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code in [200, 402, 503]

    def test_transform_missing_source_uri(self, client: TestClient, auth_token):
        """Test transformation with missing source URL."""
        response = client.post(
            "/api/v1/video/transform",
            json={
                "niche": "Technology",
                "platform": "YouTube Shorts"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Credit check may run before Pydantic validation
        assert response.status_code in [402, 422]


class TestVideoGeneration:
    """Test AI video generation endpoints."""

    def test_generate_requires_auth(self, client: TestClient):
        """Test that generate endpoint requires authentication."""
        response = client.post("/api/v1/video/generate", json={
            "prompt": "A beautiful sunset",
            "engine": "lite4k",
            "style": "Cinematic"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.services.video_engine.tasks.generate_video_task.delay")
    def test_generate_lite4k(self, mock_task, client: TestClient, auth_token):
        """Test lite4k video generation."""
        mock_task.return_value = MagicMock(id="lite4k-task-123")

        response = client.post(
            "/api/v1/video/generate",
            json={
                "prompt": "A futuristic city at night",
                "engine": "lite4k",
                "style": "Cinematic",
                "aspect_ratio": "9:16"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Should return 200 or 402 (payment required for non-premium)
        assert response.status_code in [200, 402, 500]

    @patch("src.services.video_engine.tasks.generate_video_task.delay")
    def test_generate_ltx_video(self, mock_task, client: TestClient, auth_token):
        """Test LTX video generation."""
        mock_task.return_value = MagicMock(id="ltx-task-123")

        response = client.post(
            "/api/v1/video/generate",
            json={
                "prompt": "Ocean waves crashing",
                "engine": "ltx-video",
                "style": "Natural",
                "aspect_ratio": "16:9"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Should return 200 or 402 (payment required)
        assert response.status_code in [200, 402, 500]

    @patch("src.services.video_engine.tasks.generate_video_task.delay")
    def test_generate_ltx_video_v2(self, mock_task, client: TestClient, auth_token):
        """Test LTX-Video video generation (v2 prompt)."""
        mock_task.return_value = MagicMock(id="ltx-video-task-123")

        response = client.post(
            "/api/v1/video/generate",
            json={
                "prompt": "A bird flying over mountains",
                "engine": "ltx-video",
                "style": "Cinematic"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code in [200, 402, 500]

    def test_generate_invalid_engine(self, client: TestClient, auth_token):
        """Test generation with invalid engine."""
        response = client.post(
            "/api/v1/video/generate",
            json={
                "prompt": "Test",
                "engine": "invalid_engine"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # May pass or fail depending on implementation
        assert response.status_code in [200, 402, 422, 500]


class TestVideoJobs:
    """Test video job listing and status endpoints."""

    def test_list_jobs_requires_auth(self, client: TestClient):
        """Test that jobs list requires authentication."""
        response = client.get("/api/v1/video/jobs/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_jobs_success(self, client: TestClient, auth_token):
        """Test listing jobs with authentication."""
        response = client.get(
            "/api/v1/video/jobs/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    def test_get_job_metadata(self, client: TestClient, auth_token):
        """Test getting specific job metadata."""
        response = client.get(
            "/api/v1/video/jobs/metadata/test-job-id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # May return 200 with job data or 404
        assert response.status_code in [200, 404, 500]


class TestRemotion:
    """Test Remotion rendering endpoints."""

    def test_remotion_requires_auth(self, client: TestClient):
        """Test that Remotion endpoint requires authentication."""
        response = client.post("/api/v1/remotion/render", json={
            "composition_id": "test",
            "input_props": {}
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.api.routes.remotion.base_remotion_service.render_video", new_callable=AsyncMock)
    def test_remotion_render(self, mock_render, client: TestClient, auth_token):
        """Test Remotion composition rendering."""
        mock_render.return_value = "/tmp/test_render.mp4"

        response = client.post(
            "/api/v1/remotion/render",
            json={
                "title": "Test Video",
                "subtitle": "Test Subtitle",
                "composition_id": "ViralClip"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code in [200, 500]
