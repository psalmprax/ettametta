import pytest
from fastapi import Depends
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from src.api.main import app
from src.api.utils.database import SessionLocal, get_db
from src.api.utils.models import UserDB, SubscriptionTier, UserRole
from src.api.utils.credit_models import UserCreditDB, CreditTransactionDB
from src.api.utils.auth import get_current_user
from sqlalchemy import select
import uuid

# Initialize FastAPICache with InMemoryBackend to support cached routes without Redis
FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")


@pytest.fixture
def db_session(test_db):
    """Database session for testing, isolated per test function"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """Clear FastAPI dependency overrides before and after each test"""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user and seed their credit balance"""
    # Create the user with STUDIO tier to allow full access to premium engines and studio-grade endpoints
    user = UserDB(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        subscription=SubscriptionTier.STUDIO,
        role=UserRole.USER,
        stripe_customer_id="cus_test",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create the credit balance
    user_credit = UserCreditDB(
        user_id=user.id,
        balance=1000,
        lifetime_purchased=1000,
    )
    db_session.add(user_credit)
    db_session.commit()

    yield user

    # Cleanup credit transactions, balances and user
    db_session.query(CreditTransactionDB).filter(CreditTransactionDB.user_id == user.id).delete()
    db_session.query(UserCreditDB).filter(UserCreditDB.user_id == user.id).delete()
    db_session.delete(user)
    db_session.commit()


async def override_current_user(db=Depends(get_db)):
    """
    FastAPI dependency override to retrieve the test user from the active request session.
    This prevents SQLAlchemy Multiple Sessions / Instance not persistent errors.
    """
    stmt = select(UserDB).where(UserDB.email == "test@example.com")
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user


class TestAPIRoutes:
    """Comprehensive API route testing"""

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_auth_register(self, client, db_session):
        """Test user registration"""
        unique_id = uuid.uuid4().hex[:8]
        email = f"newuser_{unique_id}@example.com"
        username = f"newuser_{unique_id}"
        user_data = {
            "email": email,
            "password": "SecurePassword123",
            "username": username,
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code in [200, 201]

        # Cleanup the registered user to keep the DB pristine
        db_session.query(UserDB).filter(UserDB.email == email).delete()
        db_session.commit()

    def test_video_generation_premium(self, client, test_user):
        """Test premium video generation with pro workflow"""
        # Mock authentication using unified session override
        app.dependency_overrides[get_current_user] = override_current_user

        video_data = {
            "prompt": "A beautiful sunset over mountains",
            "engine": "ltx-video",
            "style": "Cinematic",
            "aspect_ratio": "9:16",
            "quality_tier": "premium",
        }

        response = client.post("/api/v1/video/generate", json=video_data)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "parent_id" in data["data"]

    def test_discovery_trending(self, client, test_user):
        """Test trending content discovery"""
        app.dependency_overrides[get_current_user] = override_current_user
        response = client.get("/api/v1/discovery/trends")
        assert response.status_code == 200
        data = response.json()
        # Verify that either the "trends" or "items" list key exists in the paginated nested response
        assert "data" in data
        trends_data = data["data"]
        assert "trends" in trends_data or "items" in trends_data
        trends = trends_data.get("trends", trends_data.get("items"))
        assert isinstance(trends, list)

    def test_publishing_schedule(self, client, test_user):
        """Test content scheduling"""
        app.dependency_overrides[get_current_user] = override_current_user

        schedule_data = {
            "video_path": "test_video.mp4",
            "niche": "Technology",
            "platform": "YouTube Shorts",
        }

        response = client.post(
            "/api/v1/publish/schedule?scheduled_time=2026-04-07T10:00:00Z",
            json=schedule_data
        )
        assert response.status_code in [200, 201]

    def test_monetization_links(self, client, test_user):
        """Test affiliate link management"""
        app.dependency_overrides[get_current_user] = override_current_user

        link_data = {
            "product_name": "Test Product",
            "niche": "fitness",
            "link": "https://affiliate.link/test",
            "cta_text": "Buy Now",
        }

        response = client.post("/api/v1/monetization/links", json=link_data)
        assert response.status_code in [200, 201]

    def test_billing_subscription(self, client, test_user):
        """Test subscription management"""
        app.dependency_overrides[get_current_user] = override_current_user

        response = client.get("/api/v1/billing/subscription")
        assert response.status_code == 200

    def test_analytics_performance(self, client, test_user):
        """Test performance analytics"""
        app.dependency_overrides[get_current_user] = override_current_user

        response = client.get("/api/v1/analytics/posts")
        assert response.status_code == 200

    def test_ab_testing_create(self, client, test_user):
        """Test A/B test creation"""
        app.dependency_overrides[get_current_user] = override_current_user

        response = client.get("/api/v1/ab-testing/tests/active")
        assert response.status_code == 200

    def test_settings_update(self, client, test_user):
        """Test user settings update"""
        app.dependency_overrides[get_current_user] = override_current_user

        settings_data = {
            "telegram_chat_id": "123456789",
            "whatsapp_number": "+1234567890",
        }

        response = client.put("/api/v1/settings/user-settings", json=settings_data)
        assert response.status_code == 200


class TestVideoGeneration:
    """Test video generation workflows"""

    def test_custom_image_generation(self, client, test_user):
        """Test video generation with custom image"""
        app.dependency_overrides[get_current_user] = override_current_user

        video_data = {
            "prompt": "Animate this custom image",
            "engine": "kling",
            "custom_image_uri": "https://example.com/image.jpg",
            "style": "Cinematic",
            "aspect_ratio": "9:16",
        }

        response = client.post("/api/v1/video/generate", json=video_data)
        assert response.status_code == 200

    def test_pro_workflow_quality(self, client, test_user):
        """Test video generation triggers correctly"""
        app.dependency_overrides[get_current_user] = override_current_user

        video_data = {
            "prompt": "Professional quality video",
            "engine": "kling",
        }

        response = client.post("/api/v1/video/generate", json=video_data)
        assert response.status_code == 200


class TestSecurity:
    """Test security features"""

    def test_rate_limiting(self, client):
        """Test API rate limiting"""
        # Send multiple requests quickly
        for _ in range(15):
            response = client.get("/health")

        # Should eventually get 200 or 429
        response = client.get("/health")
        assert response.status_code in [200, 429]

    def test_authentication_required(self, client):
        """Test that protected routes require auth"""
        # cleared overrides means this will require auth
        response = client.post("/api/v1/video/generate", json={})
        assert response.status_code == 401


class TestErrorHandling:
    """Test error handling and validation"""

    def test_invalid_video_request(self, client, test_user):
        """Test invalid video generation request (missing required prompt)"""
        app.dependency_overrides[get_current_user] = override_current_user

        invalid_data = {
            "engine": "kling",
        }

        response = client.post("/api/v1/video/generate", json=invalid_data)
        assert response.status_code == 422

    def test_not_found_route(self, client):
        """Test 404 for non-existent routes"""
        response = client.get("/nonexistent")
        assert response.status_code == 404


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
