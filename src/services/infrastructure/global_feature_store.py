import json
import logging
import time
from typing import Any
from src.api.utils.redis import get_async_redis

logger = logging.getLogger("GlobalFeatureStore")

class GlobalFeatureStore:
    """
    10/10 Distributed Memory: Shared Feature Store for Cluster-Wide Intelligence.
    Replaces local SQLite SignalVault with a high-availability Redis backend.
    """
    def __init__(self):
        self._redis = None
        self.prefix = "EM_FEATURES:"  # Updated to EttaMetta branding

    async def connect(self):
        if not self._redis:
            self._redis = await get_async_redis()

    async def set_features(self, niche: str, features: dict[str, Any], ttl: int = 86400):
        """Stores signal features with a 24h default TTL."""
        await self.connect()
        key = f"{self.prefix}{niche}"
        payload = {
            "data": json.dumps(features),
            "updated_at": time.time()
        }
        await self._redis.hmset(key, payload)
        await self._redis.expire(key, ttl)
        logger.info(f"[Features] Shared features for '{niche}' across the cluster.")

    async def get_features(self, niche: str) -> dict[str, Any] | None:
        """Retrieves raw features for a niche from the cluster memory."""
        await self.connect()
        key = f"{self.prefix}{niche}"
        payload = await self._redis.hgetall(key)
        
        if not payload:
            return None
            
        return json.loads(payload.get("data", "{}"))

    async def get_velocity_vitals(self, niche: str) -> dict[str, float]:
        """Specific helper for high-velocity signal monitoring."""
        features = await self.get_features(niche)
        if not features:
            return {"velocity": 0.0, "acceleration": 0.0}
            
        return {
            "velocity": features.get("velocity", 0.0),
            "acceleration": features.get("acceleration", 0.0),
            "score": features.get("score", 0.0)
        }

base_global_feature_store = GlobalFeatureStore()
