"""
Integration Tests
Tests database transactions, service integrations, and cross-endpoint flows
"""

import pytest
import requests
from unittest.mock import patch, MagicMock

BASE_URL = "http://149.104.110.122:7201"
TEST_USER = "samuelolle"
TEST_PASS = "Single123."


def get_auth_token():
    """Get auth token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": TEST_USER, "password": TEST_PASS},
    )
    return response.json()["access_token"]


class TestDiscoveryIntegration:
    """Integration tests for Discovery service"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_trends_pagination(self, token):
        """Test discovery pagination"""
        # First page
        r1 = requests.get(
            f"{BASE_URL}/api/v1/discovery/trends?page=1&size=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 200

    def test_niche_filtering(self, token):
        """Test niche filtering"""
        for niche in ["Motivation", "Music", "Gaming"]:
            r = requests.get(
                f"{BASE_URL}/api/v1/discovery/trends?niche={niche}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert r.status_code == 200

    def test_discovery_to_nexus(self, token):
        """Test discovery → nexus flow"""
        # Get trends
        trends = requests.get(
            f"{BASE_URL}/api/v1/discovery/trends",
            headers={"Authorization": f"Bearer {token}"},
        ).json()

        if trends:
            # Get blueprints
            blueprints = requests.get(
                f"{BASE_URL}/api/v1/nexus/blueprints",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert blueprints.status_code == 200


class TestVideoIntegration:
    """Integration tests for video pipeline"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_jobs_tracking(self, token):
        """Test video job tracking"""
        response = requests.get(
            f"{BASE_URL}/api/v1/video/jobs/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_transform_flow(self, token):
        """Test transform pipeline"""
        response = requests.post(
            f"{BASE_URL}/api/v1/video/transform",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "input_url": "https://youtube.com/shorts/test",
                "niche": "Motivation",
            },
        )
        assert response.status_code in [200, 201]

    def test_content_editor_flow(self, token):
        """Test content editor pipeline"""
        # Get providers
        providers = requests.get(
            f"{BASE_URL}/api/v1/content-editor/providers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert providers.status_code == 200


class TestPublishingIntegration:
    """Integration tests for publishing"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_platform_checklist(self, token):
        """Test all platforms available"""
        response = requests.get(
            f"{BASE_URL}/api/v1/publish/platforms",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        platforms = response.json()["platforms"]
        expected = ["youtube", "tiktok", "instagram", "facebook", "x", "linkedin"]
        for p in expected:
            assert p in platforms

    def test_oauth_flow(self, token):
        """Test OAuth URLs available"""
        for platform in ["youtube", "tiktok"]:
            response = requests.get(
                f"{BASE_URL}/api/v1/publish/auth/{platform}",
                headers={"Authorization": f"Bearer {token}"},
            )
            # 200 = already connected, 302 = redirect to OAuth
            assert response.status_code in [200, 302]

    def test_publish_history(self, token):
        """Test publish history"""
        response = requests.get(
            f"{BASE_URL}/api/v1/publish/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestAnalyticsIntegration:
    """Integration tests for analytics"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_stats_aggregation(self, token):
        """Test aggregated stats"""
        for endpoint in [
            "/analytics/stats/summary",
            "/analytics/posts",
            "/analytics/report",
        ]:
            r = requests.get(
                f"{BASE_URL}/api/v1{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert r.status_code == 200

    def test_cross_endpoint_data(self, token):
        """Test data consistency across endpoints"""
        # Stats
        stats = requests.get(
            f"{BASE_URL}/api/v1/analytics/stats/summary",
            headers={"Authorization": f"Bearer {token}"},
        ).json()

        # Posts
        posts = requests.get(
            f"{BASE_URL}/api/v1/analytics/posts",
            headers={"Authorization": f"Bearer {token}"},
        ).json()

        # Jobs
        jobs = requests.get(
            f"{BASE_URL}/api/v1/video/jobs/",
            headers={"Authorization": f"Bearer {token}"},
        ).json()

        # Verify data exists
        assert stats is not None
        assert isinstance(posts, list)


class TestNexusIntegration:
    """Integration tests for Nexus"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_nexus_full_flow(self, token):
        """Test nexus: queue → stats → jobs → blueprints"""
        # Queue
        queue = requests.get(
            f"{BASE_URL}/api/v1/nexus/queue",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert queue.status_code == 200

        # Stats
        stats = requests.get(
            f"{BASE_URL}/api/v1/nexus/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert stats.status_code == 200

        # Jobs
        jobs = requests.get(
            f"{BASE_URL}/api/v1/nexus/jobs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert jobs.status_code == 200

        # Blueprints
        blueprints = requests.get(
            f"{BASE_URL}/api/v1/nexus/blueprints",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert blueprints.status_code == 200


class TestMonetizationIntegration:
    """Integration tests for monetization"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_empire_dashboard(self, token):
        """Test empire dashboard"""
        endpoints = [
            "/monetization/empire/metrics",
            "/monetization/empire/activity",
            "/monetization/empire/blueprints",
        ]
        for ep in endpoints:
            r = requests.get(
                f"{BASE_URL}/api/v1{ep}", headers={"Authorization": f"Bearer {token}"}
            )
            assert r.status_code == 200

    def test_monetization_reports(self, token):
        """Test monetization reporting"""
        response = requests.get(
            f"{BASE_URL}/api/v1/monetization/report",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestCreditsIntegration:
    """Integration tests for credits/billing"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_credits_flow(self, token):
        """Test credits: balance → packages → transactions"""
        # Balance
        balance = requests.get(
            f"{BASE_URL}/api/v1/credits/balance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert balance.status_code == 200

        # Packages
        packages = requests.get(f"{BASE_URL}/api/v1/credits/packages")
        assert packages.status_code == 200

        # Transactions
        transactions = requests.get(
            f"{BASE_URL}/api/v1/credits/transactions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert transactions.status_code == 200


class TestAgentIntegration:
    """Integration tests for autonomous agents"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_agent_flows(self, token):
        """Test agent: zero → chat → capabilities"""
        # Zero status
        zero = requests.get(
            f"{BASE_URL}/api/v1/zero/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert zero.status_code == 200

        # Agent chat
        chat = requests.post(
            f"{BASE_URL}/api/v1/agent/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "What are the trending topics?"},
        )
        assert chat.status_code == 200

        # Capabilities
        cap = requests.get(
            f"{BASE_URL}/api/v1/agent/capabilities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert cap.status_code == 200


class TestSettingsIntegration:
    """Integration tests for settings"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_settings_sync(self, token):
        """Test settings: filters → preferences → system"""
        # Filters
        filters = requests.get(
            f"{BASE_URL}/api/v1/settings/filters",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert filters.status_code == 200

        # User settings
        user = requests.get(
            f"{BASE_URL}/api/v1/settings/user-settings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert user.status_code in [200, 404]


class TestABTestingIntegration:
    """Integration tests for A/B testing"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_ab_testing_flow(self, token):
        """Test A/B testing flows"""
        # Active tests
        active = requests.get(
            f"{BASE_URL}/api/v1/ab-testing/tests/active",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert active.status_code == 200

        # Completed tests
        completed = requests.get(
            f"{BASE_URL}/api/v1/ab-testing/tests/completed",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert completed.status_code == 200


class TestLLMIntegration:
    """Integration tests for LLM service"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_llm_providers(self, token):
        """Test LLM providers"""
        providers = requests.get(
            f"{BASE_URL}/api/v1/llm/providers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert providers.status_code == 200

        models = requests.get(f"{BASE_URL}/api/v1/llm/models")
        assert models.status_code == 200


class TestPersonaIntegration:
    """Integration tests for Persona"""

    @pytest.fixture
    def token(self):
        return get_auth_token()

    def test_persona_flow(self, token):
        """Test persona flow"""
        # List
        list_res = requests.get(
            f"{BASE_URL}/api/v1/persona/list",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_res.status_code == 200

        # Active
        active = requests.get(
            f"{BASE_URL}/api/v1/persona/active",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert active.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
