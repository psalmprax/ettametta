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
        self.engine_failures = {}  # Engine/Service specific tracking

    def is_open(self, engine: str = None) -> bool:
        if self.state == "OPEN":
            if self.last_failure_time > 0 and (time.time() - self.last_failure_time > self.recovery_timeout):
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                self.state = "HALF_OPEN"
                return False
            return True

        if engine and self.engine_failures.get(engine, 0) >= self.failure_threshold:
            logger.warning(
                f"Circuit breaker '{self.name}' - Engine '{engine}' temporarily disabled due to failures"
            )
            return True

        return False

    def record_success(self, engine: str = None):
        if self.state != "CLOSED":
            logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED")
        self.failure_count = 0
        self.state = "CLOSED"
        if engine:
            self.engine_failures[engine] = 0

    def record_failure(self, engine: str = None):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == "HALF_OPEN" or self.failure_count >= self.failure_threshold:
            if self.state != "OPEN":
                logger.warning(f"Circuit breaker '{self.name}' transitioning to OPEN")
            self.state = "OPEN"
            self.failure_count = max(self.failure_count, self.failure_threshold)
        if engine:
            self.engine_failures[engine] = self.engine_failures.get(engine, 0) + 1
            if self.engine_failures[engine] >= self.failure_threshold:
                logger.warning(
                    f"Circuit breaker '{self.name}' - Engine '{engine}' disabled due to repeated failures"
                )

    def reset(self):
        """Manually reset the circuit breaker to closed state."""
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"
        self.engine_failures = {}
        logger.info(f"Circuit breaker '{self.name}' manually reset")
