import asyncio
import redis.asyncio as redis
from src.api.config import settings

_redis_instance = None
_redis_loop = None


async def get_redis():
    global _redis_instance, _redis_loop
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _redis_instance is None or (current_loop is not None and _redis_loop is not current_loop):
        _redis_instance = redis.from_url(
            settings.REDIS_URL, encoding="utf8", decode_responses=True
        )
        _redis_loop = current_loop
    return _redis_instance
