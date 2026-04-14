"""
E2E Flow Tests
Tests complete user workflows: Login → Discovery → Create → Publish
"""

import pytest
import requests

BASE_URL = "http://149.104.110.122:7201"
DASHBOARD_URL = "http://149.104.110.122:7202"

# Test credentials
TEST_USER = "samuelolle"
TEST_PASS = "Single123."


def get_auth_token():
    """Login and get auth token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": TEST_USER, "password": TEST_PASS},
    )
    return response.json()["access_token"]


class TestAuthFlow:
    """Test authentication flow"""

    def test_login_success(self):
        """Test successful login"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": TEST_USER, "password": TEST_PASS},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_invalid_password(self):
        """Test invalid password"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": TEST_USER, "password": "wrong"},
        )
        assert response.status_code in [401, 400]


class TestDiscoveryToCreationFlow:
    """Test: Discover trends → Select → Create video"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_discover_trends(self, token):
        """Get trending content"""
        response = requests.get(
            f"{BASE_URL}/api/v1/discovery/trends",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        trends = response.json()
        assert len(trends) > 0
        return trends[0] if trends else None

    def test_select_niche(self, token):
        """Select a niche to monitor"""
        niche = "Motivation"
        # Find or create monitored niche
        response = requests.get(
            f"{BASE_URL}/api/v1/discovery/niches",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_viral_analysis(self, token, test_discover_trends):
        """Analyze a trending video"""
        if not test_discover_trends:
            pytest.skip("No trends to analyze")

        trend_url = test_discover_trends.get("url")
        response = requests.post(
            f"{BASE_URL}/api/v1/discovery/analyze",
            headers={"Authorization": f"Bearer {token}"},
            json={"url": trend_url, "niche": "Motivation"},
        )
        # May return 200 or 422 depending on endpoint
        assert response.status_code in [200, 201, 422]


class TestContentCreationFlow:
    """Test: Create content from discovery"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_content_editor_providers(self, token):
        """Get available providers"""
        response = requests.get(
            f"{BASE_URL}/api/v1/content-editor/providers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "generation" in data

    def test_video_transform(self, token):
        """Start video transformation"""
        response = requests.post(
            f"{BASE_URL}/api/v1/video/transform",
            headers={"Authorization": f"Bearer {token}"},
            json={"input_url": "https://example.com/test.mp4", "niche": "Motivation"},
        )
        assert response.status_code in [200, 201]
        assert "task_id" in response.json() or "message" in response.json()


class TestNexusFlow:
    """Test: Nexus composition flow"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_nexus_jobs(self, token):
        """Get nexus jobs"""
        response = requests.get(
            f"{BASE_URL}/api/v1/nexus/jobs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_nexus_blueprints(self, token):
        """Get blueprints"""
        response = requests.get(
            f"{BASE_URL}/api/v1/nexus/blueprints",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestPublishingFlow:
    """Test: Publish to social platforms"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_get_platforms(self, token):
        """Get available platforms"""
        response = requests.get(
            f"{BASE_URL}/api/v1/publish/platforms",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        platforms = response.json()
        assert "youtube" in platforms.get("platforms", {})

    def test_get_accounts(self, token):
        """Get connected accounts"""
        response = requests.get(
            f"{BASE_URL}/api/v1/publish/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestAnalyticsFlow:
    """Test: Analytics and reporting"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_dashboard_stats(self, token):
        """Get dashboard summary"""
        response = requests.get(
            f"{BASE_URL}/api/v1/analytics/stats/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_analytics_report(self, token):
        """Get analytics report"""
        response = requests.get(
            f"{BASE_URL}/api/v1/analytics/report",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestAutonomousFlow:
    """Test: Autonomous agent flows"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_zero_status(self, token):
        """Check zero inference status"""
        response = requests.get(
            f"{BASE_URL}/api/v1/zero/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_agent_chat(self, token):
        """Test agent chat"""
        response = requests.post(
            f"{BASE_URL}/api/v1/agent/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "Hello"},
        )
        assert response.status_code == 200


class TestMonetizationFlow:
    """Test: Monetization and empire"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_empire_metrics(self, token):
        """Get empire metrics"""
        response = requests.get(
            f"{BASE_URL}/api/v1/monetization/empire/metrics",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_empire_activity(self, token):
        """Get empire activity"""
        response = requests.get(
            f"{BASE_URL}/api/v1/monetization/empire/activity",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestCreditsFlow:
    """Test: Credits and billing"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_credits_balance(self, token):
        """Get credit balance"""
        response = requests.get(
            f"{BASE_URL}/api/v1/credits/balance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_credits_packages(self, token):
        """Get credit packages"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/packages")
        assert response.status_code == 200


class TestUISmokeTest:
    """Smoke test for all UI pages"""

    def test_all_dashboard_pages(self):
        """Test all dashboard pages load"""
        pages = [
            "/",
            "/discovery",
            "/creation",
            "/nexus",
            "/autonomous",
            "/transformation",
            "/publishing",
            "/analytics",
            "/empire",
            "/credits",
            "/trading",
            "/settings",
        ]
        for page in pages:
            response = requests.get(f"{DASHBOARD_URL}{page}")
            assert response.status_code == 200, f"Failed: {page}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
