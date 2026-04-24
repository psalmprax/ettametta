import contextvars
import uuid
from typing import Optional
import logging

# Request ID ContextVar
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)

def get_request_id() -> str:
    """
    Get current request ID or generate a new one if none exists.
    Used in both API requests and background tasks.
    """
    rid = request_id_var.get()
    if not rid:
        rid = str(uuid.uuid4())
        request_id_var.set(rid)
    return rid

def set_request_id(rid: str):
    """
    Explicitly set the current request ID.
    Used by middleware and task entry points to propagate IDs.
    """
    if rid:
        request_id_var.set(rid)

class TracingFilter(logging.Filter):
    """Logging filter that adds request_id to every log record."""
    def filter(self, record):
        record.request_id = get_request_id()
        return True

def setup_tracing_logger(name: str):
    """Utility to setup a logger with tracing capabilities."""
    logger = logging.getLogger(name)
    # Avoid adding the filter multiple times
    if not any(isinstance(f, TracingFilter) for f in logger.filters):
        logger.addFilter(TracingFilter())
    return logger
