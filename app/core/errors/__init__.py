"""Core error handling module."""

from .handlers import register_error_handlers, ErrorResponse
from .exceptions import (
    BaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    BusinessRuleViolationError,
    InvalidTokenError,
    RateLimitError,
    ExternalServiceError,
    InternalError,
)

# Alias for backward compatibility
UnauthorizedError = AuthenticationError

__all__ = [
    "register_error_handlers",
    "ErrorResponse",
    "BaseError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "BusinessRuleViolationError",
    "InvalidTokenError",
    "RateLimitError",
    "ExternalServiceError",
    "InternalError",
    "UnauthorizedError",
]