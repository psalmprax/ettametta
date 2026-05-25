from fastapi.responses import JSONResponse
from typing import Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error with standardized format."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
        field: str | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.field = field
        super().__init__(message)


class ValidationError(APIError):
    """Input validation error."""

    def __init__(self, message: str, field: str, details: dict | None = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
            field=field,
        )


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class AuthenticationError(APIError):
    """Authentication failed error."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR", status_code=401)


class AuthorizationError(APIError):
    """Authorization failed error."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR", status_code=403)


class RateLimitError(APIError):
    """Rate limit exceeded error."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after},
        )


class ExternalServiceError(APIError):
    """External service (payment, AI, etc.) error."""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service},
        )


class ConflictError(APIError):
    """Resource conflict error."""

    def __init__(self, message: str, resource_id: str | None = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details={"resource_id": resource_id} if resource_id else {},
        )


def api_error_response(
    error: APIError,
    request_path: str | None = None,
    request_method: str | None = None,
) -> JSONResponse:
    """Convert APIError to JSONResponse."""

    error_body = {
        "error": {
            "code": error.code,
            "message": error.message,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
    }

    if error.details:
        error_body["error"]["details"] = error.details

    if error.field:
        error_body["error"]["field"] = error.field

    if request_path:
        error_body["error"]["request"] = {
            "path": request_path,
            "method": request_method,
        }

    return JSONResponse(status_code=error.status_code, content=error_body)


async def api_exception_handler(request, exc: APIError) -> JSONResponse:
    """FastAPI exception handler for APIError."""
    return api_error_response(exc, request.url.path, request.method)


def handle_exception(exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with logging."""

    if isinstance(exc, APIError):
        return api_error_response(exc)

    # Log unexpected errors
    logger.error(f"Unexpected error: {type(exc).__name__}: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
        },
    )


class Paginator:
    """Standard pagination utility."""

    def __init__(self, page: int = 1, page_size: int = 20, max_page_size: int = 100):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), max_page_size)
        self.max_page_size = max_page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size

    def paginate_response(self, items: list[Any], total: int) -> dict[str, Any]:
        """Create paginated response."""
        total_pages = (total + self.page_size - 1) // self.page_size

        return {
            "items": items,
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": self.page < total_pages,
                "has_prev": self.page > 1,
            },
        }


# Pagination parameters for OpenAPI
PAGINATION_PARAMS = {
    "page": (int, 1, "Page number (starting from 1)"),
    "page_size": (int, 20, "Number of items per page (max 100)"),
}


# Standard paginated response model
from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    data: list[Any]
    pagination: dict[str, Any]


def paginate_list(
    items: list[Any], page: int = 1, page_size: int = 20, max_page_size: int = 100
) -> dict[str, Any]:
    """Standalone pagination helper."""
    paginator = Paginator(page, page_size, max_page_size)
    total = len(items)
    start = paginator.offset
    end = start + paginator.limit
    return paginator.paginate_response(items[start:end], total)


def success_response(
    data: Any = None, message: str | None = None, meta: dict | None = None
) -> dict[str, Any]:
    """Standard success response format."""
    response = {"success": True, "timestamp": datetime.now(timezone.utc).isoformat() + "Z"}

    if message:
        response["message"] = message

    if data is not None:
        response["data"] = data

    if meta:
        response["meta"] = meta

    return response


def error_response(
    code: str, message: str, status_code: int = 400, details: dict | None = None
) -> JSONResponse:
    """Quick error response creation."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "details": details or {},
            }
        },
    )
