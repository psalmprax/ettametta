"""
Circuit Breaker for External APIs.

Generic CircuitBreaker with CLOSED/OPEN/HALF_OPEN states, decorator pattern,
Prometheus metrics, and state-transition logging. Drop-in compatible with the
existing resilience.CircuitBreaker but adds decorator usage and metrics.
"""

import time
import functools
import logging
import threading
from enum import Enum
from typing import Callable

from src.services.infrastructure.resilience_metrics import (
    safe_counter,
    safe_gauge,
)

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(Exception):
    """Raised when a circuit breaker is OPEN and rejects the call."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Circuit breaker '{name}' is OPEN — call rejected")


class CircuitBreaker:
    """
    Thread-safe circuit breaker with configurable thresholds and recovery.

    States:
        CLOSED   — normal operation, calls pass through
        OPEN     — failures exceeded threshold, calls rejected
        HALF_OPEN — recovery timeout elapsed, limited probe calls allowed

    Usage:
        cb = CircuitBreaker(name='stripe', failure_threshold=5, recovery_timeout=30)
        if cb.allow():
            try:
                result = call_stripe()
                cb.record_success()
            except Exception:
                cb.record_failure()
                raise

    Decorator:
        @circuit_breaker(name='stripe', failure_threshold=5)
        def call_stripe(): ...
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time: float = 0
        self._last_state_change: float = time.time()
        self._lock = threading.Lock()

        # Prometheus metrics
        self._metric_failures = safe_counter(
            "ettametta_circuit_breaker_failures_total",
            "Total circuit breaker failures",
            ["name"],
        )
        self._metric_successes = safe_counter(
            "ettametta_circuit_breaker_successes_total",
            "Total circuit breaker successes",
            ["name"],
        )
        self._metric_state = safe_gauge(
            "ettametta_circuit_breaker_state",
            "Circuit breaker state (0=Closed, 1=HalfOpen, 2=Open)",
            ["name"],
        )
        self._metric_rejects = safe_counter(
            "ettametta_circuit_breaker_rejects_total",
            "Total calls rejected by circuit breaker",
            ["name"],
        )

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._check_recovery()
            return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def _state_value(self) -> int:
        return {
            CircuitState.CLOSED: 0,
            CircuitState.HALF_OPEN: 1,
            CircuitState.OPEN: 2,
        }[self._state]

    def _transition(self, new_state: CircuitState):
        old = self._state
        self._state = new_state
        self._last_state_change = time.time()
        self._metric_state.labels(name=self.name).set(self._state_value())
        logger.warning(
            f"Circuit breaker '{self.name}' transitioned: {old.value} -> {new_state.value}"
        )

    def _check_recovery(self):
        if self._state == CircuitState.OPEN and self._last_failure_time > 0:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._transition(CircuitState.HALF_OPEN)
                self._half_open_calls = 0

    def allow(self) -> bool:
        """Return True if the call should be allowed through."""
        with self._lock:
            self._check_recovery()

            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                self._metric_rejects.labels(name=self.name).inc()
                return False

            # OPEN
            self._metric_rejects.labels(name=self.name).inc()
            return False

    def record_success(self):
        with self._lock:
            self._success_count += 1
            self._metric_successes.labels(name=self.name).inc()

            if self._state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit breaker '{self.name}' probe succeeded — closing")
                self._failure_count = 0
                self._transition(CircuitState.CLOSED)
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            self._metric_failures.labels(name=self.name).inc()

            if self._state == CircuitState.HALF_OPEN:
                logger.warning(
                    f"Circuit breaker '{self.name}' probe failed — re-opening"
                )
                self._transition(CircuitState.OPEN)
            elif self._failure_count >= self.failure_threshold:
                self._transition(CircuitState.OPEN)

    def reset(self):
        """Manually reset to CLOSED."""
        with self._lock:
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._last_failure_time = 0
            self._transition(CircuitState.CLOSED)
            logger.info(f"Circuit breaker '{self.name}' manually reset")

    def is_open(self) -> bool:
        """Backward-compatible check: True if calls should be rejected."""
        return not self.allow()

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "half_open_max_calls": self.half_open_max_calls,
            "last_failure_time": self._last_failure_time,
        }


# ── Global registry ──────────────────────────────────────────────────

_registry: dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    half_open_max_calls: int = 1,
) -> CircuitBreaker:
    """Get or create a named circuit breaker (singleton per name)."""
    with _registry_lock:
        if name not in _registry:
            _registry[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                half_open_max_calls=half_open_max_calls,
            )
        return _registry[name]


def circuit_breaker(
    name: str = "default",
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    half_open_max_calls: int = 1,
):
    """
    Decorator that wraps a function with circuit breaker protection.

    Usage:
        @circuit_breaker(name='stripe', failure_threshold=5)
        def charge_customer(amount):
            return stripe.Charge.create(amount=amount)
    """

    def decorator(func: Callable) -> Callable:
        cb = get_circuit_breaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=half_open_max_calls,
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not cb.allow():
                raise CircuitBreakerOpenError(name)
            try:
                result = func(*args, **kwargs)
                cb.record_success()
                return result
            except CircuitBreakerOpenError:
                raise
            except Exception:
                cb.record_failure()
                raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not cb.allow():
                raise CircuitBreakerOpenError(name)
            try:
                result = await func(*args, **kwargs)
                cb.record_success()
                return result
            except CircuitBreakerOpenError:
                raise
            except Exception:
                cb.record_failure()
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator
