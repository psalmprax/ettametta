"""
Shared fixtures for Nexus Engine tests.

Provides robust event loop management for pytest-asyncio v1.3.0
compatibility, preventing "Event loop is closed" errors that occur
when async resources (imported lazily during test execution) hold
references to the previous test's now-closed event loop.
"""
import asyncio
from unittest.mock import patch, AsyncMock
import pytest


@pytest.fixture(scope="function")
def event_loop():
    """Provide a properly managed event loop per test function.

    pytest-asyncio v1.3.0 can close the event loop prematurely when
    async resources (e.g., ``redis.asyncio`` clients created during
    lazy imports like ``ws.py``) outlive the loop's scope.  This
    fixture ensures the loop stays open for all fixture setup/teardown
    and test execution, then closes it cleanly.

    Overrides the default ``event_loop`` fixture provided by the plugin.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Give pending callbacks a chance to drain before closing
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


@pytest.fixture(autouse=True, scope="function")
def _prevent_redis_connections():
    """Prevent any real Redis connections during tests.

    When ``src.api.routes.ws`` is imported (inside ``assemble_video``,
    via ``from src.api.routes.ws import notify_nexus_job_update_sync``),
    the module-level ``manager = ConnectionManager()`` calls
    ``redis.asyncio.from_url(...)``.  Even though this is a lazy
    connection, its internal ``ConnectionPool`` can interact with the
    asyncio event loop in ways that cause ``Event loop is closed``
    errors when the loop from a previous test is referenced.

    This fixture patches both ``redis.Redis`` (sync) and
    ``redis.asyncio.Redis`` (async) so that ``from_url`` returns
    a lightweight mock instead of a real client.
    """
    # Patch both CLASS-level and MODULE-level entry points.
    # In redis-py, ``redis.asyncio.from_url`` is a module-level name
    # (``from_url = Redis.from_url``) — a separate name from the class.
    # Patching ``redis.asyncio.Redis`` alone does NOT intercept calls
    # to ``redis.asyncio.from_url()``, which would create a real client.
    #
    # ``redis.asyncio.from_url`` returns an ``AsyncMock`` so that
    # async methods called on the returned client (e.g.
    # ``await client.xgroup_create(...)``) work correctly.
    # ``AsyncMock`` isawaitable in Python 3.12; ``MagicMock`` is not.
    async_redis_client = AsyncMock()

    patches = [
        patch("redis.Redis"),
        patch("redis.from_url"),
        patch("redis.asyncio.Redis"),
        patch("redis.asyncio.from_url", return_value=async_redis_client),
    ]
    for p in patches:
        p.start()
    yield
    for p in patches:
        p.stop()
