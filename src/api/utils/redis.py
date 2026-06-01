"""
Shared Redis connection pool module.

All services MUST import their Redis client from here instead of calling
redis.from_url() directly. This ensures the entire process reuses a single
connection pool instead of opening 20+ independent connections.

Usage:
    from src.api.utils.redis import get_async_redis, get_sync_redis

    async def some_handler():
        r = await get_async_redis()
        await r.get("key")

    def some_sync_func():
        r = get_sync_redis()
        r.get("key")
"""

import asyncio
import logging
import redis
import redis.asyncio as aioredis
from src.api.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pool configuration
# ---------------------------------------------------------------------------
ASYNC_MAX_CONNECTIONS = 20
SYNC_MAX_CONNECTIONS = 10

# ---------------------------------------------------------------------------
# Async pool / client (redis.asyncio)
# ---------------------------------------------------------------------------
_async_pool = None
_async_client = None
_async_loop = None


def _build_async_url() -> str:
    """Resolve the Redis URL, swapping localhost for the Docker service name."""
    url = settings.REDIS_URL
    if "//localhost" in url:
        url = url.replace("//localhost", "//redis")
    return url


async def get_async_redis():
    """Return a shared async Redis client backed by a connection pool.

    The pool is (re)created when:
    - called for the first time, or
    - the running event loop has changed (e.g. uvicorn reload).
    """
    global _async_pool, _async_client, _async_loop

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _async_client is None or (current_loop is not None and _async_loop is not current_loop):
        url = _build_async_url()
        _async_pool = aioredis.ConnectionPool.from_url(
            url,
            max_connections=ASYNC_MAX_CONNECTIONS,
            decode_responses=True,
            encoding="utf8",
        )
        _async_client = aioredis.Redis(connection_pool=_async_pool)
        _async_loop = current_loop
        logger.info("[Redis] Async connection pool created (max=%d)", ASYNC_MAX_CONNECTIONS)

    return _async_client


# ---------------------------------------------------------------------------
# Sync pool / client (redis)
# ---------------------------------------------------------------------------
_sync_pool = None
_sync_client = None


def _build_sync_url() -> str:
    """Resolve the Redis URL, swapping localhost for the Docker service name."""
    url = settings.REDIS_URL
    if "//localhost" in url:
        url = url.replace("//localhost", "//redis")
    return url


def get_sync_redis():
    """Return a shared sync Redis client backed by a connection pool."""
    global _sync_pool, _sync_client

    if _sync_client is None:
        url = _build_sync_url()
        _sync_pool = redis.ConnectionPool.from_url(
            url,
            max_connections=SYNC_MAX_CONNECTIONS,
            decode_responses=True,
            encoding="utf8",
        )
        _sync_client = redis.Redis(connection_pool=_sync_pool)
        logger.info("[Redis] Sync connection pool created (max=%d)", SYNC_MAX_CONNECTIONS)

    return _sync_client


# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------
async def get_redis():
    """Drop-in replacement for the old get_redis() in this module."""
    return await get_async_redis()
