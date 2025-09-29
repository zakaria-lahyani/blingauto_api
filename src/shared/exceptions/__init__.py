"""
Shared exceptions module
"""
from .standardized_errors import (
    StandardErrorResponse,
    ErrorDetail,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ResourceNotFoundError,
    BusinessLogicError,
    SessionError,
    TooManyRequestsError,
    InternalServerError,
    ErrorMessages,
    create_validation_error_details
)

__all__ = [
    "StandardErrorResponse",
    "ErrorDetail",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "ResourceNotFoundError",
    "BusinessLogicError",
    "SessionError",
    "TooManyRequestsError",
    "InternalServerError",
    "ErrorMessages",
    "create_validation_error_details"
]