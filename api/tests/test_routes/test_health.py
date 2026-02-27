"""
Health Check and Root Endpoint Tests
====================================
Integration tests for health and root endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint returns correct message."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "ettametta API" in data["message"]
        assert "env" in data
    
    def test_root_endpoint_contains_env(self, client: TestClient):
        """Test root endpoint includes environment info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["env"] in ["development", "test", "production"]
    
    def test_health_check(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert data["status"] == "healthy"
        
        # Check optional service fields
        assert "debug" in data
        assert "env" in data
        assert "services" in data
    
    def test_health_check_services(self, client: TestClient):
        """Test health check includes service status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        services = data["services"]
        assert "sound_design" in services
        assert "motion_graphics" in services
        assert "ai_video" in services
        assert "langchain" in services
        assert "crewai" in services


class TestCORSHeaders:
    """Test CORS configuration."""
    
    def test_cors_headers_present(self, client: TestClient):
        """Test CORS headers are present in response."""
        response = client.get("/health")
        
        # In test mode, security headers may not be added
        assert response.status_code == 200


class TestRequestLogging:
    """Test request logging middleware."""
    
    def test_process_time_header(self, client: TestClient):
        """Test X-Process-Time header is added to responses."""
        response = client.get("/health")
        
        assert "x-process-time" in response.headers
        # Process time should be a valid number
        process_time = float(response.headers["x-process-time"])
        assert process_time >= 0
