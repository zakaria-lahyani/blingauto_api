from typing import Optional, Dict, Any


class BaseError(Exception):
    """Base exception class for application errors."""
    
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(BaseError):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class AuthenticationError(BaseError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=kwargs,
        )


class AuthorizationError(BaseError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
            details=kwargs,
        )


class NotFoundError(BaseError):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, identifier: Optional[str] = None, **kwargs):
        message = f"{resource} not found"
        details = kwargs
        if identifier:
            details["identifier"] = identifier
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class ConflictError(BaseError):
    """Raised when there's a conflict with existing data."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=kwargs,
        )


class BusinessRuleViolationError(BaseError):
    """Raised when a business rule is violated."""
    
    def __init__(self, message: str, rule: Optional[str] = None, **kwargs):
        details = kwargs
        if rule:
            details["rule"] = rule
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            status_code=422,
            details=details,
        )


class InvalidTokenError(BaseError):
    """Raised when JWT token is invalid."""
    
    def __init__(self, message: str = "Invalid token", **kwargs):
        super().__init__(
            message=message,
            code="INVALID_TOKEN",
            status_code=401,
            details=kwargs,
        )


class RateLimitError(BaseError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        reset_time: Optional[int] = None,
        **kwargs
    ):
        details = kwargs
        if reset_time:
            details["reset_time"] = reset_time
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
        )


class ExternalServiceError(BaseError):
    """Raised when an external service fails."""
    
    def __init__(self, service: str, message: str, **kwargs):
        super().__init__(
            message=f"External service error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service, **kwargs},
        )


class InternalError(BaseError):
    """Raised for internal server errors."""
    
    def __init__(self, message: str = "Internal server error", **kwargs):
        super().__init__(
            message=message,
            code="INTERNAL_ERROR",
            status_code=500,
            details=kwargs,
        )