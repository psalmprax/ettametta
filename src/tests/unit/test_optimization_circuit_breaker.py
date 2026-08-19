import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.utils.resilience import CircuitBreaker
from src.services.optimization.service import OptimizationService


def test_circuit_breaker_states():
    """Verify state transitions of CircuitBreaker."""
    # Initialize circuit breaker with low threshold and timeout for test
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=2, name="TestCB")

    assert cb.state == "CLOSED"
    assert cb.is_open() is False

    # 1. Record two failures (threshold is 3)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "CLOSED"
    assert cb.is_open() is False

    # 2. Record third failure (threshold reached)
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.is_open() is True

    # 3. Simulate recovery timeout not reached yet
    assert cb.is_open() is True

    # 4. Simulate recovery timeout reached
    cb.last_failure_time = time.time() - 3  # older than 2 seconds recovery_timeout
    assert cb.is_open() is False  # transitions to HALF_OPEN and returns False
    assert cb.state == "HALF_OPEN"

    # 5. Half-open success transitions to CLOSED
    cb.record_success()
    assert cb.state == "CLOSED"
    assert cb.failure_count == 0


def test_circuit_breaker_half_open_failure():
    """Verify that failure in HALF_OPEN state transitions back to OPEN immediately."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=2)

    # Force state to HALF_OPEN
    cb.state = "HALF_OPEN"

    # Record failure
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.failure_count == 3  # Tripped to failure_threshold


def test_circuit_breaker_engine_specific():
    """Verify engine-specific failure tracking."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

    # Trigger 2 failures on "engine_A" and 1 failure on "engine_B"
    cb.record_failure(engine="engine_A")
    cb.record_failure(engine="engine_A")
    cb.record_failure(engine="engine_B")

    # engine_failures dictionary should track counts independently
    assert cb.engine_failures["engine_A"] == 2
    assert cb.engine_failures["engine_B"] == 1

    # Global state is OPEN because total failures = 3
    assert cb.state == "OPEN"
    assert cb.is_open(engine="engine_A") is True


def test_circuit_breaker_reset():
    """Verify manual reset of CircuitBreaker."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
    cb.record_failure()
    cb.record_failure(engine="engine_A")
    cb.state = "OPEN"

    cb.reset()
    assert cb.state == "CLOSED"
    assert cb.failure_count == 0
    assert cb.last_failure_time == 0
    assert cb.engine_failures == {}


@pytest.mark.asyncio
async def test_optimization_service_circuit_breaking():
    """Verify OptimizationService integrates correctly with CircuitBreaker."""
    service = OptimizationService()

    # Mock settings
    with patch("src.services.optimization.service.settings") as mock_settings:
        mock_settings.GROQ_API_KEY = "mock_groq_key"

        # Scenario 1: Circuit breaker is OPEN
        service.groq_circuit_breaker.state = "OPEN"
        service.groq_circuit_breaker.last_failure_time = time.time()

        res = await service._call_groq("Hello")
        assert res is None  # Immediately returned None without calling API

        # Scenario 2: Circuit breaker is CLOSED, Groq succeeds
        service.groq_circuit_breaker.reset()

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Viral SEO Title"
        mock_response.choices = [mock_choice]

        mock_client_instance = AsyncMock()
        mock_client_instance.chat.completions.create.return_value = mock_response

        with patch("groq.AsyncGroq", return_value=mock_client_instance):
            res = await service._call_groq("Generate title")
            assert res == "Viral SEO Title"
            assert service.groq_circuit_breaker.failure_count == 0
            assert service.groq_circuit_breaker.state == "CLOSED"

        # Scenario 3: Circuit breaker is CLOSED, Groq fails
        mock_client_instance.chat.completions.create.side_effect = RuntimeError("API Limit Exceeded")

        with patch("groq.AsyncGroq", return_value=mock_client_instance):
            res = await service._call_groq("Generate title")
            assert res is None
            assert service.groq_circuit_breaker.failure_count == 1
            assert service.groq_circuit_breaker.state == "CLOSED"
