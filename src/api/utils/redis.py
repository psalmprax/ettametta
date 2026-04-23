import redis.asyncio as redis
from src.api.config import settings

_redis_instance = None


async def get_redis():
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = redis.from_url(
            settings.REDIS_URL, encoding="utf8", decode_responses=True
        )
    return _redis_instance
