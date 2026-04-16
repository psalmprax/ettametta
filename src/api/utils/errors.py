"""
Error Handling Schema
=====================
Centralized error response schemas for consistent API error handling
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for the API."""
    # Authentication errors
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_USER_NOT_FOUND = "AUTH_USER_NOT_FOUND"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    VALIDATION_MISSING_FIELD = "VALIDATION_MISSING_FIELD"
    VALIDATION_INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    
    # External service errors
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Internal errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


class FieldError(BaseModel):
    """Detailed field-level error information."""
    field: str
    message: str
    type: str


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error_code: ErrorCode
    message: str
    timestamp: datetime = datetime.utcnow()
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-level details."""
    field_errors: List[FieldError] = []
    
    def __init__(self, **data):
        super().__init__(**data)
        self.error_code = ErrorCode.VALIDATION_ERROR


class ErrorHandler:
    """Helper class for creating standardized error responses."""
    
    @staticmethod
    def not_found(resource: str, identifier: str = None) -> ErrorResponse:
        """Create a not found error."""
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with identifier '{identifier}' not found"
        
        return ErrorResponse(
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message
        )
    
    @staticmethod
    def already_exists(resource: str, identifier: str = None) -> ErrorResponse:
        """Create an already exists error."""
        message = f"{resource} already exists"
        if identifier:
            message = f"{resource} with identifier '{identifier}' already exists"
        
        return ErrorResponse(
            error_code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            message=message
        )
    
    @staticmethod
    def validation_error(message: str, field_errors: List[FieldError] = None) -> ValidationErrorResponse:
        """Create a validation error."""
        return ValidationErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            field_errors=field_errors or []
        )
    
    @staticmethod
    def authentication_error(message: str = "Invalid credentials") -> ErrorResponse:
        """Create an authentication error."""
        return ErrorResponse(
            error_code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            message=message
        )
    
    @staticmethod
    def unauthorized_error(message: str = "Unauthorized") -> ErrorResponse:
        """Create an unauthorized error."""
        return ErrorResponse(
            error_code=ErrorCode.AUTH_TOKEN_INVALID,
            message=message
        )
    
    @staticmethod
    def forbidden_error(message: str = "Insufficient permissions") -> ErrorResponse:
        """Create a forbidden error."""
        return ErrorResponse(
            error_code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            message=message
        )
    
    @staticmethod
    def rate_limit_error(message: str = "Rate limit exceeded") -> ErrorResponse:
        """Create a rate limit error."""
        return ErrorResponse(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            details={"retry_after": 60}
        )
    
    @staticmethod
    def internal_error(message: str = "Internal server error", details: dict = None) -> ErrorResponse:
        """Create an internal error."""
        return ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=message,
            details=details
        )
    
    @staticmethod
    def external_service_error(service: str, message: str = None) -> ErrorResponse:
        """Create an external service error."""
        msg = f"Error communicating with {service}"
        if message:
            msg = f"{msg}: {message}"
        
        return ErrorResponse(
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=msg
        )


# Convenience function for creating HTTPException with standardized errors
def create_http_exception(status_code: int, error_code: ErrorCode, message: str):
    """Create an HTTPException with standardized error code."""
    from fastapi import HTTPException
    return HTTPException(
        status_code=status_code,
        detail={
            "error_code": error_code.value,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Common HTTP exception factories
def not_found_exception(resource: str = "Resource"):
    """Create a 404 HTTPException."""
    return create_http_exception(404, ErrorCode.RESOURCE_NOT_FOUND, f"{resource} not found")

def unauthorized_exception(message: str = "Unauthorized"):
    """Create a 401 HTTPException."""
    return create_http_exception(401, ErrorCode.AUTH_TOKEN_INVALID, message)

def forbidden_exception(message: str = "Forbidden"):
    """Create a 403 HTTPException."""
    return create_http_exception(403, ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS, message)

def conflict_exception(resource: str = "Resource"):
    """Create a 409 HTTPException."""
    return create_http_exception(409, ErrorCode.RESOURCE_CONFLICT, f"{resource} conflict")

def validation_exception(message: str = "Validation error"):
    """Create a 422 HTTPException."""
    return create_http_exception(422, ErrorCode.VALIDATION_ERROR, message)

def rate_limit_exception(message: str = "Rate limit exceeded"):
    """Create a 429 HTTPException."""
    return create_http_exception(429, ErrorCode.RATE_LIMIT_EXCEEDED, message)

def internal_exception(message: str = "Internal server error"):
    """Create a 500 HTTPException."""
    return create_http_exception(500, ErrorCode.INTERNAL_ERROR, message)
