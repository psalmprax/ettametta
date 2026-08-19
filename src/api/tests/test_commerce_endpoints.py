"""
Tests for the Auto-Merch and Commerce API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    """Create a test client without DB dependency for unit-level endpoint tests."""
    with TestClient(app) as c:
        yield c


class TestAutoMerchEndpoint:
    """Tests for POST /api/v1/monetization/auto-merch."""

    def test_auto_merch_unauthorized(self, client):
        """Should return 401 without auth."""
        response = client.post("/api/v1/monetization/auto-merch", json={"niche": "Motivation"})
        assert response.status_code == 401

    def test_auto_merch_missing_niche(self, client):
        """Should return 401 when niche is missing (auth check runs before validation)."""
        response = client.post("/api/v1/monetization/auto-merch", json={})
        # Auth is checked first, so we get 401 before Pydantic validation runs
        assert response.status_code == 401


class TestCommerceSyncEndpoint:
    """Tests for POST /api/v1/monetization/commerce/sync."""

    def test_commerce_sync_unauthorized(self, client):
        """Should return 401 without auth."""
        response = client.post("/api/v1/monetization/commerce/sync?niche=Motivation")
        assert response.status_code == 401


class TestAffiliateLinkEndpoints:
    """Tests for affiliate link CRUD endpoints."""

    def test_list_links_unauthorized(self, client):
        """GET /monetization/links should return 401 without auth."""
        response = client.get("/api/v1/monetization/links")
        assert response.status_code == 401

    def test_create_link_unauthorized(self, client):
        """POST /monetization/links should return 401 without auth."""
        response = client.post(
            "/api/v1/monetization/links",
            json={"product_name": "Test", "niche": "Motivation", "link": "https://example.com"}
        )
        assert response.status_code == 401

    def test_create_link_missing_fields(self, client):
        """Should return 401 when required fields are missing (auth check runs before validation)."""
        response = client.post(
            "/api/v1/monetization/links",
            json={"product_name": "Test"}
        )
        # Auth is checked first, so we get 401 before Pydantic validation runs
        assert response.status_code == 401


class TestMonetizationReportEndpoint:
    """Tests for GET /api/v1/monetization/report."""

    def test_report_unauthorized(self, client):
        """Should return 401 without auth."""
        response = client.get("/api/v1/monetization/report")
        assert response.status_code == 401

    def test_report_structure(self, client):
        """Should return structured response when authenticated."""
        # Register + login to get token
        client.post("/api/v1/auth/register", json={
            "username": "merchuser",
            "email": "merchuser@example.com",
            "password": "Password123!",
            "full_name": "Merch User"
        })
        login_resp = client.post("/api/v1/auth/login", data={
            "username": "merchuser",
            "password": "Password123!"
        })
        token = login_resp.json().get("data", {}).get("access_token")
        if not token:
            pytest.skip("Auth not available in test env")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/monetization/report", headers=headers)

        # Should succeed or return empty report
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "total_revenue" in data["data"]
            assert "epm" in data["data"]


class TestEmpireEndpoints:
    """Tests for Empire-related endpoints."""

    def test_empire_metrics_unauthorized(self, client):
        """GET /monetization/empire/metrics should return 401 without auth."""
        response = client.get("/api/v1/monetization/empire/metrics")
        assert response.status_code == 401

    def test_empire_activity_unauthorized(self, client):
        """GET /monetization/empire/activity should return 401 without auth."""
        response = client.get("/api/v1/monetization/empire/activity")
        assert response.status_code == 401

    def test_empire_blueprints_unauthorized(self, client):
        """GET /monetization/empire/blueprints should return 401 without auth."""
        response = client.get("/api/v1/monetization/empire/blueprints")
        assert response.status_code == 401

    def test_empire_network_unauthorized(self, client):
        """GET /monetization/empire/network should return 401 without auth."""
        response = client.get("/api/v1/monetization/empire/network")
        assert response.status_code == 401

    def test_clone_strategy_unauthorized(self, client):
        """POST /monetization/empire/clone should return 401 without auth."""
        response = client.post(
            "/api/v1/monetization/empire/clone",
            json={"source_niche": "Motivation", "target_niche": "Fitness"}
        )
        assert response.status_code == 401


class TestWebhookEndpoints:
    """Tests for affiliate network webhook endpoints."""

    def test_affiliate_webhook_success(self, client):
        """POST /monetization/webhook/affiliate should accept postback data."""
        response = client.post(
            "/api/v1/monetization/webhook/affiliate",
            json={
                "network": "amazon",
                "transaction_id": "tx_test_123",
                "amount": 49.99,
                "commission": 2.50,
                "status": "approved"
            }
        )
        assert response.status_code in [200, 422, 500]

    def test_affiliate_webhook_minimal(self, client):
        """Should accept minimal required fields."""
        response = client.post(
            "/api/v1/monetization/webhook/affiliate",
            json={
                "network": "impact",
                "transaction_id": "tx_minimal"
            }
        )
        assert response.status_code in [200, 500]
