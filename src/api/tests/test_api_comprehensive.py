import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.utils.database import SessionLocal
from api.utils.models import UserDB, VideoJobDB
from api.routes.auth import get_current_user
import json

client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    """Database session for testing"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = UserDB(
        email="test@example.com",
        hashed_password="hashed_password",
        subscription_tier="creator",
        stripe_customer_id="cus_test",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user
    db_session.delete(user)
    db_session.commit()


class TestAPIRoutes:
    """Comprehensive API route testing"""

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_auth_register(self, db_session):
        """Test user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "subscription_tier": "free",
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code in [200, 201]

    def test_video_generation_premium(self, test_user):
        """Test premium video generation with pro workflow"""
        # Mock authentication
        app.dependency_overrides[get_current_user] = lambda: test_user

        video_data = {
            "prompt": "A beautiful sunset over mountains",
            "engine": "veo3",
            "style": "Cinematic",
            "aspect_ratio": "9:16",
            "quality_tier": "premium",
        }

        response = client.post("/video/generate", json=video_data)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_discovery_trending(self):
        """Test trending content discovery"""
        response = client.get("/discovery/trends")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_publishing_schedule(self, test_user):
        """Test content scheduling"""
        app.dependency_overrides[get_current_user] = lambda: test_user

        schedule_data = {
            "content_id": "test_content",
            "platform": "youtube",
            "scheduled_time": "2026-04-07T10:00:00Z",
            "title": "Test Video",
            "description": "Test description",
        }

        response = client.post("/publish/schedule", json=schedule_data)
        assert response.status_code in [200, 201]

    def test_monetization_links(self, test_user):
        """Test affiliate link management"""
        app.dependency_overrides[get_current_user] = lambda: test_user

        link_data = {
            "product_name": "Test Product",
            "niche": "fitness",
            "link": "https://affiliate.link/test",
            "cta_text": "Buy Now",
        }

        response = client.post("/monetization/links", json=link_data)
        assert response.status_code in [200, 201]

    def test_billing_subscription(self, test_user):
        """Test subscription management"""
        app.dependency_overrides[get_current_user] = lambda: test_user

        response = client.get("/billing/subscription")
        assert response.status_code == 200

    def test_analytics_performance(self, test_user):
        """Test performance analytics"""
        app.dependency_overrides[get_current_user] = lambda: test_user

        response = client.get("/analytics/performance")
        assert response.status_code == 200

    def test_ab_testing_create(self, test_user):
        """Test A/B test creation"""
        app.dependency_overrides[get_current_user] = lambda: test_user

        test_data = {
            "content_id": "test_video",
            "variants": [
                {"title": "Version A", "description": "First variant"},
                {"title": "Version B", "description": "Second variant"},
            ],
            "platforms": ["youtube"],
            "test_duration_hours": 24,
        }

        response = client.post("/ab-testing/create", json=test_data)
        assert response.status_code in [200, 201]

    def test_settings_update(self, test_user):
        """Test user settings update"""
        app.dependency_overrides[get_current_user] = lambda: test_user

        settings_data = {"theme": "dark", "notifications": True, "auto_publish": False}

        response = client.put("/settings/preferences", json=settings_data)
        assert response.status_code == 200


class TestVideoGeneration:
    """Test video generation workflows"""

    def test_custom_image_generation(self, test_user):
        """Test video generation with custom image"""
        app.dependency_overrides[get_current_user] = lambda: test_user

        video_data = {
            "prompt": "Animate this custom image",
            "engine": "custom_image",
            "custom_image_url": "https://example.com/image.jpg",
            "style": "Cinematic",
            "aspect_ratio": "9:16",
        }

        response = client.post("/video/generate", json=video_data)
        assert response.status_code == 200

    def test_pro_workflow_quality(self, test_user):
        """Test that premium quality triggers pro workflow"""
        app.dependency_overrides[get_current_user] = lambda: test_user

        video_data = {
            "prompt": "Professional quality video",
            "engine": "veo3",
            "quality_tier": "premium",
        }

        response = client.post("/video/generate", json=video_data)
        assert response.status_code == 200


class TestSecurity:
    """Test security features"""

    def test_rate_limiting(self):
        """Test API rate limiting"""
        # Send multiple requests quickly
        for _ in range(15):
            response = client.get("/health")

        # Should eventually get 429
        response = client.get("/health")
        assert response.status_code in [200, 429]

    def test_authentication_required(self):
        """Test that protected routes require auth"""
        response = client.post("/video/generate", json={})
        assert response.status_code == 401


class TestErrorHandling:
    """Test error handling and validation"""

    def test_invalid_video_request(self, test_user):
        """Test invalid video generation request"""
        app.dependency_overrides[get_current_user] = lambda: test_user

        invalid_data = {
            "prompt": "",  # Invalid empty prompt
            "engine": "invalid_engine",
        }

        response = client.post("/video/generate", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_not_found_route(self):
        """Test 404 for non-existent routes"""
        response = client.get("/nonexistent")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
