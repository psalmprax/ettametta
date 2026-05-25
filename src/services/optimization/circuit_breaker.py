"""
Circuit Breaker Pattern Implementation for External API Resilience

Provides circuit breaker functionality to prevent cascading failures when
external services (YouTube, Stripe, TikTok, etc.) are unavailable.
"""
import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable
from dataclasses import dataclass, field
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"         # Failure threshold exceeded, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Failures before opening circuit
    success_threshold: int = 2          # Successes needed to close from half-open
    timeout: float = 60.0               # Seconds before trying half-open
    excluded_exceptions: tuple = ()      # Exception types that don't count as failures


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for external API calls.
    
    Usage:
        breaker = CircuitBreaker("youtube", failure_threshold=5, timeout=60)
        
        # Use as decorator
        @breaker
        async def call_youtube_api():
            ...
        
        # Or use directly
        if breaker.can_execute():
            try:
                result = await call_youtube_api()
                breaker.record_success()
            except Exception as e:
                breaker.record_failure(e)
    """
    name: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: float | None = field(default=None, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    
    @property
    def state(self) -> CircuitState:
        return self._state
    
    @property
    def is_available(self) -> bool:
        """Check if requests can be made"""
        if self._state == CircuitState.CLOSED:
            return True
        elif self._state == CircuitState.OPEN:
            # Check if timeout has passed
            if self._last_failure_time and (time.time() - self._last_failure_time) >= self.config.timeout:
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        return self.is_available
    
    def record_success(self) -> None:
        """Record a successful call"""
        self._failure_count = 0
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._state = CircuitState.CLOSED
                self._success_count = 0
                logger.info(f"[CircuitBreaker] {self.name}: Circuit CLOSED (recovered)")
    
    def record_failure(self, exception: Exception) -> None:
        """Record a failed call"""
        # Check if exception should be excluded
        if isinstance(exception, self.config.excluded_exceptions):
            return
            
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            self._success_count = 0
            logger.warning(f"[CircuitBreaker] {self.name}: Circuit OPEN (half-open test failed)")
        elif self._failure_count >= self.config.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"[CircuitBreaker] {self.name}: Circuit OPEN (failure threshold: {self._failure_count})")
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with circuit breaker protection"""
        if not self.can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
            )
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise
    
    def reset(self) -> None:
        """Manually reset the circuit breaker"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        logger.info(f"[CircuitBreaker] {self.name}: Circuit manually reset")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, **config) -> CircuitBreaker:
    """Get or create a circuit breaker"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, CircuitBreakerConfig(**config))
    return _circuit_breakers[name]


def circuit_breaker(name: str, **config):
    """Decorator to add circuit breaker to async functions"""
    breaker = get_circuit_breaker(name, **config)
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.execute(func, *args, **kwargs)
        return wrapper
    return decorator


# Pre-configured circuit breakers for common external services
youtube_breaker = get_circuit_breaker(
    "youtube",
    failure_threshold=5,
    timeout=60,
    success_threshold=2
)

stripe_breaker = get_circuit_breaker(
    "stripe",
    failure_threshold=3,
    timeout=30,
    success_threshold=1
)

tiktok_breaker = get_circuit_breaker(
    "tiktok",
    failure_threshold=5,
    timeout=60,
    success_threshold=2
)

instagram_breaker = get_circuit_breaker(
    "instagram",
    failure_threshold=5,
    timeout=60,
    success_threshold=2
)


def get_all_breakers_status() -> dict:
    """Get status of all circuit breakers"""
    return {
        name: {
            "state": breaker.state.value,
            "failure_count": breaker._failure_count,
            "is_available": breaker.is_available
        }
        for name, breaker in _circuit_breakers.items()
    }
