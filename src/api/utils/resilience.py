import time
import logging

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, name: str = "Generic"):
        self.name = name
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        if self.state == "OPEN":
            if self.last_failure_time > 0 and (time.time() - self.last_failure_time > self.recovery_timeout):
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self):
        if self.state != "CLOSED":
            logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED")
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            if self.state != "OPEN":
                logger.warning(f"Circuit breaker '{self.name}' transitioning to OPEN")
            self.state = "OPEN"

    def reset(self):
        """Manually reset the circuit breaker to closed state."""
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"
        logger.info(f"Circuit breaker '{self.name}' manually reset")
