# Async Bridge Patterns in ettametta Celery Tasks

Celery tasks are synchronous by default, but ettametta's services are largely async. Three different bridge patterns exist — this documents them and recommends the best approach.

## Pattern 1: Fresh Event Loop (video_engine) — RECOMMENDED

File: `src/services/video_engine/tasks.py`

```python
import asyncio

def run_async(coro):
    """Run async coroutine from sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
```

**Why this is best:**
- Creates a fresh loop per call (no loop reuse contamination)
- Handles the case where a loop already exists
- Handles the case where no loop exists (RuntimeError)
- Used by the most critical tasks (video rendering)

**Usage in tasks:**
```python
@celery_app.task(bind=True)
def download_and_process(self, ...):
    set_request_id(self.request.id)
    result = run_async(_async_download_and_process(...))
    return result
```

## Pattern 2: Simple asyncio.run() (nexus_engine, discovery)

File: `src/services/nexus_engine/tasks.py`, `src/services/discovery/tasks.py`

```python
@celery_app.task(bind=True)
def create_cinema_video(self, ...):
    result = asyncio.run(_async_create_cinema_video(...))
    return result
```

**Problem:** `asyncio.run()` creates AND destroys the event loop. Libraries that cache loop references (aiohttp, asyncpg) may break on subsequent calls.

## Pattern 3: Manual Loop Management (storage) — AVOID

File: `src/services/storage/tasks.py`

```python
loop = asyncio.get_event_loop()
if loop.is_closed():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
result = loop.run_until_complete(coro)
```

**Problem:** Doesn't handle the `RuntimeError` case where no loop exists in the current thread.

## Cross-Module Coupling Issue

`scheduler_tasks.py` imports `run_async` from `video_engine/tasks.py`:

```python
from src.services.video_engine.tasks import run_async
```

This creates an artificial dependency between optimization and video_engine services. If you need `run_async` in a new task module, copy the function rather than importing it across service boundaries.

## Recommendation

For all new Celery tasks that need async code, use Pattern 1 (fresh event loop). Place the `run_async` helper locally in the task module — do not import it from another service.
