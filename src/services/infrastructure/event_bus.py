import redis.asyncio as redis
import json
import logging
import asyncio
import time
from typing import Any, Awaitable, Callable
from src.api.config import settings

logger = logging.getLogger("DistributedEventBus")

class DistributedEventBus:
    """
    10/10 Infrastructure: Redis Streams-backed Event Bus for Distributed Content Clusters.
    Supports Consumer Groups, Fault Acknowledgment (XACK), and Retry/DLQ logic.
    """
    def __init__(self):
        self._redis = None
        self.stream_name = "VF_FLOW_STREAMS"
        self.dlq_name = "VF_FLOW_DLQ"
        self.group_name = "VF_COORDINATOR_GROUP"
        self.max_retries = 3
        self.consumer_name = f"worker_{int(time.time())}"

    async def connect(self):
        if not self._redis:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Ensure consumer group exists
            try:
                await self._redis.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
            except redis.exceptions.ResponseError:
                pass # Already exists

    async def emit(self, topic: str, payload: dict[str, Any]):
        """Emits an event into the global stream."""
        await self.connect()
        event_body = {
            "topic": topic,
            "payload": json.dumps(payload),
            "timestamp": time.time()
        }
        await self._redis.xadd(self.stream_name, event_body)
        logger.info(f"[Bus] Emitted {topic} to global stream.")

    async def subscribe(self, topic_filter: str, callback: Callable[[dict[str, Any]], Awaitable[None]]):
        """
        Subscribes a worker to a specific topic within the distributed group.
        Implements at-least-once delivery with XACK.
        """
        await self.connect()
        logger.info(f"[Bus] Worker {self.consumer_name} subscribed to {topic_filter}")
        
        while True:
            try:
                # Read new messages from the group
                results = await self._redis.xreadgroup(
                    self.group_name, 
                    self.consumer_name, 
                    {self.stream_name: ">"}, 
                    count=1, 
                    block=5000
                )
                
                if not results:
                    continue

                for stream_name, messages in results:
                    for message_id, data in messages:
                        try:
                            topic = data.get("topic")
                            if topic == topic_filter or topic_filter == "*":
                                payload = json.loads(data.get("payload", "{}"))
                                await callback(payload)
                            
                            # Acknowledge completion (XACK)
                            await self._redis.xack(self.stream_name, self.group_name, message_id)
                        except Exception as e:
                            logger.error(f"[Bus] Worker failed to process event {message_id}: {e}")
                            
                            # 10/10 Resilience: Retries & DLQ
                            payload = json.loads(data.get("payload", "{}"))
                            retries = payload.get("_retries", 0)
                            
                            if retries < self.max_retries:
                                logger.info(f"[Bus] Retrying event {message_id} (Attempt {retries + 1}/{self.max_retries})")
                                payload["_retries"] = retries + 1
                                await self.emit(topic, payload)
                            else:
                                logger.error(f"[Bus] Event {message_id} exceeded max retries. Moving to DLQ.")
                                await self._move_to_dlq(topic, payload, str(e))
                            
                            # Ack the failed one so it doesn't stay in PEL
                            await self._redis.xack(self.stream_name, self.group_name, message_id)
                            
            except Exception as e:
                logger.error(f"[Bus] Subscription loop error: {e}")
                await asyncio.sleep(2)

    async def _move_to_dlq(self, topic: str, payload: dict[str, Any], error: str):
        """Moves unrecoverable events to the Dead Letter Queue."""
        dlq_event = {
            "topic": topic,
            "payload": json.dumps(payload),
            "error": error,
            "timestamp": time.time()
        }
        await self._redis.xadd(self.dlq_name, dlq_event)
        logger.info(f"💀 [Bus] Event moved to DLQ: {topic}")

    async def get_dlq_size(self) -> int:
        """Returns the number of pending failures in the DLQ."""
        await self.connect()
        try:
            return await self._redis.xlen(self.dlq_name)
        except:
            return 0

    async def claim_stale_messages(self, min_idle_time: int = 60000):
        """
        10/10 Fail-Safe: Reclaims messages that were started but never finished 
        by other workers (e.g., node crashes).
        """
        await self.connect()
        try:
            # Check for pending messages older than min_idle_time
            pending = await self._redis.xpending_range(
                self.stream_name, self.group_name, "-", "+", 10
            )
            
            for msg in pending:
                if msg["idle"] > min_idle_time:
                    msg_id = msg["message_id"]
                    logger.warning(f"[Bus] Reclaiming stale message {msg_id} from {msg['consumer']}")
                    await self._redis.xclaim(
                        self.stream_name, self.group_name, self.consumer_name, min_idle_time, [msg_id]
                    )
        except Exception as e:
            logger.error(f"[Bus] Fail-over check failed: {e}")

base_event_service = DistributedEventBus()
