import redis.asyncio as redis
import json
import logging
import time
from typing import Any
from api.config import settings

logger = logging.getLogger("GlobalFeatureStore")

class GlobalFeatureStore:
    """
    10/10 Distributed Memory: Shared Feature Store for Cluster-Wide Intelligence.
    Replaces local SQLite SignalVault with a high-availability Redis backend.
    """
    def __init__(self):
        self._redis = None
        self.prefix = "VF_FEATURES:"

    async def connect(self):
        if not self._redis:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def set_features(self, topic: str, features: dict[str, Any], ttl: int = 86400):
        """Stores signal features with a 24h default TTL."""
        await self.connect()
        key = f"{self.prefix}{topic}"
        payload = {
            "data": json.dumps(features),
            "updated_at": time.time()
        }
        await self._redis.hmset(key, payload)
        await self._redis.expire(key, ttl)
        logger.info(f"[Features] Shared features for '{topic}' across the cluster.")

    async def get_features(self, topic: str) -> dict[str, Any] | None:
        """Retrieves raw features for a topic from the cluster memory."""
        await self.connect()
        key = f"{self.prefix}{topic}"
        payload = await self._redis.hgetall(key)
        
        if not payload:
            return None
            
        return json.loads(payload.get("data", "{}"))

    async def get_velocity_vitals(self, topic: str) -> dict[str, float]:
        """Specific helper for high-velocity signal monitoring."""
        features = await self.get_features(topic)
        if not features:
            return {"velocity": 0.0, "acceleration": 0.0}
            
        return {
            "velocity": features.get("velocity", 0.0),
            "acceleration": features.get("acceleration", 0.0),
            "score": features.get("score", 0.0)
        }

base_global_feature_store = GlobalFeatureStore()
