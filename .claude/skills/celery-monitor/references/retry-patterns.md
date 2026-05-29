# Celery Retry Patterns in ettametta

## Pattern A: autoretry_for with Exponential Backoff

Used by: video_engine tasks, optimization.check_and_post_scheduled

```python
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def my_task(self, ...):
    ...
```

**Pros:** Simple, handles transient failures automatically.
**Cons:** Retries ALL exceptions including non-retryable ones.

## Pattern B: Manual Non-Retryable Classification

Used by: video_engine tasks (within their except blocks)

```python
non_retryable_errors = [
    "Asset validation failed", "invalid input", "permission denied",
    "authentication failed", "quota exceeded",
]
is_retryable = not any(nr_error.lower() in error_msg.lower() for ...)
if not is_retryable:
    self.request.retries = self.max_retries  # Fragile!
```

**Problem:** `self.request.retries` is an internal Celery attribute. This can break on upgrades.

**Better approach:**
```python
class NonRetryableError(Exception):
    pass

@celery_app.task(autoretry_for=(Exception,), max_retries=3)
def my_task(self, ...):
    try:
        ...
    except SomeError as e:
        if is_non_retryable(e):
            raise NonRetryableError(str(e)) from e
        raise

# Exclude from autoretry
my_task.autoretry_for = (Exception,)
my_task.dont_autoretry_for = (NonRetryableError,)
```

## Pattern C: Application-Level Retry (DB)

Used by: scheduler_tasks (retry_missed_schedules, retry_failed_posts)

```python
post.retry_count += 1
if post.retry_count >= post.max_retries:
    post.status = ContentPublishStatus.FAILED
else:
    post.status = ContentPublishStatus.PENDING
    # Re-enqueue
    check_and_post_scheduled.delay()
```

**Use case:** When retry state needs to survive worker restarts (persisted in DB).

## Pattern D: CircuitBreaker

Used by: discovery/scanner_service.py, video_engine/remotion_service.py

```python
from src.api.utils.resilience import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=2,
    recovery_timeout=300,
)
```

**Use case:** External service calls where repeated failures should stop attempts temporarily.

## Choosing a Pattern

| Scenario | Pattern |
|----------|---------|
| Transient network errors | A (autoretry) |
| Mixed retryable/non-retryable errors | A + custom exception exclusion |
| State must persist across restarts | C (DB-level) |
| External API with cascading failures | D (CircuitBreaker) |
| Need fine-grained control | B (manual, but use custom exceptions) |
