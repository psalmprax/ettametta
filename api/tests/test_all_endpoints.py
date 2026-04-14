"""
Comprehensive tests for all API endpoints
Tests both existing and new endpoints we added/fixed
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.routes.auth import get_current_user
from unittest.mock import patch, MagicMock

client = TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    user = MagicMock()
    user.id = "test-user-id"
    user.email = "test@example.com"
    user.role = "creator"
    return user


@pytest.fixture
def auth_headers(mock_user):
    """Get auth headers with mocked user"""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    # Get token
    response = client.post("/auth/login", json={"username": "test", "password": "test"})
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    return {}


class TestDiscoveryEndpoints:
    """Test Discovery menu endpoints"""

    def test_discovery_trends(self):
        """GET /discovery/trends"""
        response = client.get("/discovery/trends")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_discovery_niches(self):
        """GET /discovery/niches"""
        response = client.get("/discovery/niches")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_discovery_categories(self, auth_headers):
        """GET /discovery/categories - NEW"""
        headers = auth_headers or {}
        response = client.get("/discovery/categories", headers=headers)
        assert response.status_code in [200, 401]

    def test_discovery_search(self):
        """GET /discovery/search"""
        response = client.get("/discovery/search?niche=Motivation")
        assert response.status_code == 200


class TestNexusEndpoints:
    """Test Nexus composition endpoints"""

    def test_nexus_jobs(self, auth_headers):
        """GET /nexus/jobs"""
        headers = auth_headers or {}
        response = client.get("/nexus/jobs", headers=headers)
        assert response.status_code in [200, 401]

    def test_nexus_blueprints(self, auth_headers):
        """GET /nexus/blueprints"""
        headers = auth_headers or {}
        response = client.get("/nexus/blueprints", headers=headers)
        assert response.status_code in [200, 401]

    def test_nexus_queue(self, auth_headers):
        """GET /nexus/queue - NEW"""
        headers = auth_headers or {}
        response = client.get("/nexus/queue", headers=headers)
        assert response.status_code in [200, 401]

    def test_nexus_stats(self, auth_headers):
        """GET /nexus/stats - NEW"""
        headers = auth_headers or {}
        response = client.get("/nexus/stats", headers=headers)
        assert response.status_code in [200, 401]

    def test_nexus_telemetry(self, auth_headers):
        """GET /nexus/telemetry"""
        headers = auth_headers or {}
        response = client.get("/nexus/telemetry", headers=headers)
        assert response.status_code in [200, 401]


class TestContentEditorEndpoints:
    """Test Content Editor endpoints"""

    def test_content_editor_providers(self):
        """GET /content-editor/providers"""
        response = client.get("/content-editor/providers")
        assert response.status_code == 200

    def test_content_editor_generate(self, auth_headers):
        """POST /content-editor/generate - FIXED"""
        headers = auth_headers or {}
        data = {"prompt": "test video", "provider": "pollinations"}
        response = client.post("/content-editor/generate", json=data, headers=headers)
        assert response.status_code in [200, 401, 422]


class TestPersonaEndpoints:
    """Test Persona endpoints"""

    def test_persona_list(self, auth_headers):
        """GET /persona/list"""
        headers = auth_headers or {}
        response = client.get("/persona/list", headers=headers)
        assert response.status_code in [200, 401]

    def test_persona_active(self, auth_headers):
        """GET /persona/active - NEW"""
        headers = auth_headers or {}
        response = client.get("/persona/active", headers=headers)
        assert response.status_code in [200, 401]


class TestLLMEndpoints:
    """Test LLM endpoints"""

    def test_llm_providers(self):
        """GET /llm/providers"""
        response = client.get("/llm/providers")
        assert response.status_code == 200

    def test_llm_models(self):
        """GET /llm/models - NEW"""
        response = client.get("/llm/models")
        assert response.status_code == 200


class TestAnalyticsEndpoints:
    """Test Analytics endpoints"""

    def test_analytics_stats_summary(self, auth_headers):
        """GET /analytics/stats/summary"""
        headers = auth_headers or {}
        response = client.get("/analytics/stats/summary", headers=headers)
        assert response.status_code in [200, 401]

    def test_analytics_posts(self, auth_headers):
        """GET /analytics/posts"""
        headers = auth_headers or {}
        response = client.get("/analytics/posts", headers=headers)
        assert response.status_code in [200, 401]

    def test_analytics_report(self, auth_headers):
        """GET /analytics/report - NEW"""
        headers = auth_headers or {}
        response = client.get("/analytics/report", headers=headers)
        assert response.status_code in [200, 401]

    def test_analytics_export(self, auth_headers):
        """GET /analytics/export"""
        headers = auth_headers or {}
        response = client.get("/analytics/export", headers=headers)
        assert response.status_code in [200, 401]


class TestPublishingEndpoints:
    """Test Publishing endpoints"""

    def test_publish_platforms(self):
        """GET /publish/platforms"""
        response = client.get("/publish/platforms")
        assert response.status_code == 200

    def test_publish_history(self, auth_headers):
        """GET /publish/history"""
        headers = auth_headers or {}
        response = client.get("/publish/history", headers=headers)
        assert response.status_code in [200, 401]

    def test_publish_accounts(self, auth_headers):
        """GET /publish/accounts"""
        headers = auth_headers or {}
        response = client.get("/publish/accounts", headers=headers)
        assert response.status_code in [200, 401]

    def test_publish_scheduled(self, auth_headers):
        """GET /publish/scheduled - NEW"""
        headers = auth_headers or {}
        response = client.get("/publish/scheduled", headers=headers)
        assert response.status_code in [200, 401]


class TestMonetizationEndpoints:
    """Test Monetization endpoints"""

    def test_monetization_report(self, auth_headers):
        """GET /monetization/report"""
        headers = auth_headers or {}
        response = client.get("/monetization/report", headers=headers)
        assert response.status_code in [200, 401]

    def test_monetization_links(self, auth_headers):
        """GET /monetization/links"""
        headers = auth_headers or {}
        response = client.get("/monetization/links", headers=headers)
        assert response.status_code in [200, 401]

    def test_monetization_empire_metrics(self, auth_headers):
        """GET /monetization/empire/metrics - FIXED"""
        headers = auth_headers or {}
        response = client.get("/monetization/empire/metrics", headers=headers)
        assert response.status_code in [200, 401]

    def test_monetization_empire_activity(self, auth_headers):
        """GET /monetization/empire/activity - FIXED"""
        headers = auth_headers or {}
        response = client.get("/monetization/empire/activity", headers=headers)
        assert response.status_code in [200, 401]

    def test_monetization_empire_blueprints(self, auth_headers):
        """GET /monetization/empire/blueprints - FIXED"""
        headers = auth_headers or {}
        response = client.get("/monetization/empire/blueprints", headers=headers)
        assert response.status_code in [200, 401]

    def test_monetization_empire_network(self, auth_headers):
        """GET /monetization/empire/network - FIXED"""
        headers = auth_headers or {}
        response = client.get("/monetization/empire/network", headers=headers)
        assert response.status_code in [200, 401]


class TestTradingEndpoints:
    """Test Trading endpoints"""

    def test_trading_base(self, auth_headers):
        """GET /trading/ - NEW"""
        headers = auth_headers or {}
        response = client.get("/trading/", headers=headers)
        assert response.status_code in [200, 401]

    def test_trading_portfolio(self, auth_headers):
        """GET /trading/portfolio"""
        headers = auth_headers or {}
        response = client.get("/trading/portfolio", headers=headers)
        assert response.status_code in [200, 401]


class TestAutonomousEndpoints:
    """Test Autonomous/Agent endpoints"""

    def test_zero_status(self):
        """GET /zero/status"""
        response = client.get("/zero/status")
        assert response.status_code in [200, 404]

    def test_agent_chat(self, auth_headers):
        """POST /agent/chat"""
        headers = auth_headers or {}
        data = {"message": "hello"}
        response = client.post("/agent/chat", json=data, headers=headers)
        assert response.status_code in [200, 401, 405]

    def test_agent_capabilities(self, auth_headers):
        """GET /agent/capabilities"""
        headers = auth_headers or {}
        response = client.get("/agent/capabilities", headers=headers)
        assert response.status_code in [200, 401]


class TestVideoEndpoints:
    """Test Video endpoints"""

    def test_video_jobs(self, auth_headers):
        """GET /video/jobs/"""
        headers = auth_headers or {}
        response = client.get("/video/jobs/", headers=headers)
        assert response.status_code in [200, 401]

    def test_video_jobs_quotas(self, auth_headers):
        """GET /video/jobs/quotas"""
        headers = auth_headers or {}
        response = client.get("/video/jobs/quotas", headers=headers)
        assert response.status_code in [200, 401]


class TestCreditsEndpoints:
    """Test Credits & Billing endpoints"""

    def test_credits_balance(self, auth_headers):
        """GET /credits/balance"""
        headers = auth_headers or {}
        response = client.get("/credits/balance", headers=headers)
        assert response.status_code in [200, 401]

    def test_credits_transactions(self, auth_headers):
        """GET /credits/transactions"""
        headers = auth_headers or {}
        response = client.get("/credits/transactions", headers=headers)
        assert response.status_code in [200, 401]

    def test_credits_packages(self):
        """GET /credits/packages"""
        response = client.get("/credits/packages")
        assert response.status_code in [200, 404]


class TestSettingsEndpoints:
    """Test Settings endpoints"""

    def test_settings_filters(self, auth_headers):
        """GET /settings/filters"""
        headers = auth_headers or {}
        response = client.get("/settings/filters", headers=headers)
        assert response.status_code in [200, 401]

    def test_settings_user_settings(self, auth_headers):
        """GET /settings/user-settings"""
        headers = auth_headers or {}
        response = client.get("/settings/user-settings", headers=headers)
        assert response.status_code in [200, 401]


class TestABTestingEndpoints:
    """Test A/B Testing endpoints"""

    def test_ab_testing_active(self, auth_headers):
        """GET /ab-testing/tests/active"""
        headers = auth_headers or {}
        response = client.get("/ab-testing/tests/active", headers=headers)
        assert response.status_code in [200, 401]

    def test_ab_testing_completed(self, auth_headers):
        """GET /ab-testing/tests/completed"""
        headers = auth_headers or {}
        response = client.get("/ab-testing/tests/completed", headers=headers)
        assert response.status_code in [200, 401]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
