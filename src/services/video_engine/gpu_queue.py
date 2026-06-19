import logging
from contextlib import asynccontextmanager

from src.api.config import settings


class GpuQueueManager:
    def __init__(self):
        from src.api.utils.redis import get_sync_redis
        self.redis = get_sync_redis()
        self.semaphore_key = "ettametta:gpu:slots"
        self.total_slots = settings.GPU_QUEUE_SLOTS or 1
        self.timeout = settings.GPU_QUEUE_TIMEOUT or 300

    def _initialize_queue(self):
        """Initializes the GPU slot queue with tokens if empty."""
        try:
            if not self.redis.exists(self.semaphore_key):
                logging.info(
                    f"[GpuQueue] Initializing {self.total_slots} slots in Redis list..."
                )
                tokens = [str(i) for i in range(self.total_slots)]
                self.redis.rpush(self.semaphore_key, *tokens)
                self.redis.expire(self.semaphore_key, 604800)  # 7 days persistence
        except Exception as e:
            logging.exception(f"[GpuQueue] Initialization failed: {e}")

    @asynccontextmanager
    async def acquire_slot(self):
        """
        Async context manager to acquire a GPU slot using blocking BLPOP.
        """
        logging.info("[GpuQueue] Requesting GPU slot (BRPOP)...")
        self._initialize_queue()

        token = None
        try:
            # blpop returns (key, value) or None on timeout
            result = self.redis.blpop(self.semaphore_key, timeout=int(self.timeout))
            if result:
                _, token = result
                logging.info(f"[GpuQueue] Slot acquired (Token: {token})")
                yield True
            else:
                logging.error("[GpuQueue] Timeout waiting for GPU slot.")
                raise TimeoutError(
                    "System busy: All GPU generation slots are currently occupied."
                )
        finally:
            if token:
                self.redis.rpush(self.semaphore_key, token)
                logging.info(f"[GpuQueue] Slot released (Token: {token}).")
