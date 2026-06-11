"""Tests for Phase 12-01 Task 5: GET /engines/availability endpoint."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestEnginesAvailability:
    def test_endpoint_returns_200(self, client):
        resp = client.get("/api/v1/engines/availability")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "data" in body
        assert isinstance(body["data"], list)

    def test_response_includes_runway_and_pika(self, client):
        body = client.get("/api/v1/engines/availability").json()
        ids = {e["id"] for e in body["data"]}
        assert "runway" in ids
        assert "pika" in ids

    def test_each_entry_has_expected_shape(self, client):
        body = client.get("/api/v1/engines/availability").json()
        required = {"id", "name", "provider", "enabled", "key_set", "key_env_var", "circuit_closed", "category"}
        for entry in body["data"]:
            missing = required - entry.keys()
            assert not missing, f"Engine {entry.get('id')} missing fields: {missing}"

    def test_local_engines_have_no_key_required(self, client):
        body = client.get("/api/v1/engines/availability").json()
        local = [e for e in body["data"] if e["category"] == "local"]
        assert local, "Expected at least one local engine"
        for e in local:
            assert e["key_env_var"] is None, f"Local engine {e['id']} should have no key_env_var"
            assert e["key_set"] is True, f"Local engine {e['id']} should report key_set=True"

    def test_runway_key_set_reflects_settings(self, client):
        """With RUNWAY_API_KEY set in settings, runway.key_set is True; without, False."""
        from src.api.config import settings

        with patch.object(settings, "RUNWAY_API_KEY", "test-key-xyz"):
            body = client.get("/api/v1/engines/availability").json()
            runway = next(e for e in body["data"] if e["id"] == "runway")
            assert runway["key_set"] is True
            assert runway["key_env_var"] == "RUNWAY_API_KEY"

        with patch.object(settings, "RUNWAY_API_KEY", None):
            body = client.get("/api/v1/engines/availability").json()
            runway = next(e for e in body["data"] if e["id"] == "runway")
            assert runway["key_set"] is False
            assert runway["enabled"] is False

    def test_pika_key_set_reflects_settings(self, client):
        from src.api.config import settings

        with patch.object(settings, "PIKA_API_KEY", "test-pika-xyz"):
            body = client.get("/api/v1/engines/availability").json()
            pika = next(e for e in body["data"] if e["id"] == "pika")
            assert pika["key_set"] is True
            assert pika["key_env_var"] == "PIKA_API_KEY"

        with patch.object(settings, "PIKA_API_KEY", None):
            body = client.get("/api/v1/engines/availability").json()
            pika = next(e for e in body["data"] if e["id"] == "pika")
            assert pika["key_set"] is False
            assert pika["enabled"] is False

    def test_circuit_closed_is_always_true_today(self, client):
        """Phase 12-02 will wire per-engine circuit breakers; for now all are closed."""
        body = client.get("/api/v1/engines/availability").json()
        for e in body["data"]:
            assert e["circuit_closed"] is True, f"Engine {e['id']} circuit should be closed"

    def test_endpoint_does_not_leak_secret_values(self, client):
        """The endpoint must never return the value of any API key."""
        from src.api.config import settings

        with patch.object(settings, "RUNWAY_API_KEY", "supersecret-do-not-leak-42"):
            body = client.get("/api/v1/engines/availability").json()
            response_text = str(body)
            assert "supersecret-do-not-leak-42" not in response_text
