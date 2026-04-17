import time
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Stateful circuit breaker to track strategy health."""
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 600):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "CLOSED"

    def is_open(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"[CircuitBreaker] Circuit opened after {self.failure_count} failures.")

class BaseMonetizationStrategy(ABC):
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()

    @abstractmethod
    async def get_assets(self, niche: str) -> list[dict[str, Any]]:
        """
        Fetches relevant products, links, or lead magnets for the given niche.
        """
        pass

    @abstractmethod
    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generates a conversion-optimized call to action.
        """
        pass
