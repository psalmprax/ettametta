import logging
import traceback
from typing import Any
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import HTTPException as FastAPIHTTPException
from sqlalchemy.exc import SQLAlchemyError
from slowapi.errors import RateLimitExceeded
from src.api.config import settings
from src.api.utils.database import AsyncSessionLocal
from src.api.utils.models import SelfHealingAuditDB
from src.api.utils.api_responses import error_response, api_error_response, APIError

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: Any):
    """Normalize HTTPException to standard nested error format."""
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", "An error occurred")

    if status_code == 404:
        return error_response(
            code="NOT_FOUND",
            message=f"Endpoint '{request.url.path}' not found.",
            status_code=404,
        )

    return error_response(
        code="HTTP_ERROR",
        message=detail if isinstance(detail, str) else "An error occurred",
        status_code=status_code,
        details=detail if isinstance(detail, dict) else {"detail": detail},
    )


async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return error_response(
        code="RATE_LIMIT_EXCEEDED",
        message="Too many requests. Please slow down.",
        status_code=429,
        details={"retry_after": exc.detail if hasattr(exc, "detail") else "60s"},
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {str(exc)}")
    message = "An internal database error occurred."
    if settings.DEBUG:
        message = f"Database Error: {str(exc)}"

    return error_response(
        code="DB_ERROR",
        message=message,
        status_code=500,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    details = []
    for err in exc.errors():
        cleaned = {}
        for k, v in err.items():
            if isinstance(v, Exception):
                cleaned[k] = str(v)
            elif isinstance(v, dict):
                cleaned[k] = {
                    sk: str(sv) if isinstance(sv, Exception) else sv
                    for sk, sv in v.items()
                }
            else:
                cleaned[k] = v
        details.append(cleaned)

    return error_response(
        code="VALIDATION_ERROR",
        message="Invalid data provided.",
        status_code=422,
        details={"errors": details},
    )


async def value_error_exception_handler(request: Request, exc: ValueError):
    logger.warning(f"Value error: {exc}")
    return error_response(
        code="VALUE_ERROR",
        message=str(exc),
        status_code=400,
    )


async def api_error_exception_handler(request: Request, exc: APIError):
    """Handler for custom APIError types."""
    return api_error_response(exc, request.url.path, request.method)


async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Standard: Hardening Observability - Fault Persistence
    try:
        async with AsyncSessionLocal() as db:
            audit = SelfHealingAuditDB(
                path=request.url.path,
                method=request.method,
                exception_type=type(exc).__name__,
                message=str(exc),
                traceback=traceback.format_exc(),
            )
            db.add(audit)
            await db.commit()

            # Standard 3.12: Compliance Hardening (EU AI Act Article 71)
            # Notify external surveillance authorities of serious incidents
            from src.services.infrastructure.incident_reporting import base_incident_service
            await base_incident_service.report_incident(
                incident_type="SYSTEM_CRASH",
                details={
                    "path": request.url.path,
                    "method": request.method,
                    "exception": type(exc).__name__,
                    "message": str(exc),
                    "audit_id": audit.id
                },
                severity="CRITICAL"
            )
    except Exception as db_exc:
        logger.error(f"Failed to persist fault audit or report incident: {db_exc}")

    return error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Our engineers have been notified.",
        status_code=500,
    )


def register_exception_handlers(app):
    """Register all exception handlers on the FastAPI app."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValueError, value_error_exception_handler)
    app.add_exception_handler(APIError, api_error_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
