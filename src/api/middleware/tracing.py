import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from src.api.utils.tracing import set_request_id, get_request_id
from src.api.config import settings

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.scope["type"] == "websocket":
            return await call_next(request)
        # Extract or generate Request-ID
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(rid)

        response = await call_next(request)

        # Propagate back to client
        response.headers["X-Request-ID"] = rid
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.scope["type"] == "websocket":
            return await call_next(request)

        start_time = time.time()
        rid = get_request_id()
        response = await call_next(request)
        process_time = time.time() - start_time
        if settings.ENV == "production" or settings.DEBUG:
            logger.info(
                f"[{rid}] {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s"
            )
        response.headers["X-Process-Time"] = str(process_time)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.scope["type"] == "websocket":
            return await call_next(request)
        response = await call_next(request)
        if settings.ENV == "production":
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
